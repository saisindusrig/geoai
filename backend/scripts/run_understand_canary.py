"""One freshly prepared, separately authorized UNDERSTAND action; no retries."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FAILED = ROOT / ".cad-proof-output" / "4c-understand-canary-981cd96192534cfebc42a739366700b5"


def execute(out, authorization):
    out = Path(out).resolve()
    if out.parent != (ROOT / ".cad-proof-output").resolve() or out == FAILED.resolve():
        from app.experimental.canary_execution import CanaryError
        raise CanaryError("CANARY_FRESH_RUN_REQUIRED")
    os.environ["DATABASE_URL"] = "sqlite:///" + (out / "acceptance.db").as_posix()
    from app.experimental.canary_execution import require, OneRequestGuard, MODEL, validate_transport, stack_evidence
    require(not (out / "canary-execution.json").exists(), "CANARY_LEDGER_EXISTS_NO_REPLAY")
    for key in ("GEOAI_EXPERIMENTAL_CAD", "GEOAI_EXPERIMENTAL_BIM_AUTHORING"):
        os.environ[key] = "true"
    for key in ("GEOAI_CAD_TEST_USER_IDS", "GEOAI_BIM_AUTHORING_USER_IDS", "GEOAI_CAD_TEST_PROJECT_IDS", "GEOAI_BIM_AUTHORING_PROJECT_IDS"):
        os.environ[key] = "490001"
    from app.core.config import settings
    settings.LOCAL_STORAGE_DIR = str(out / "public")
    from app.services import storage
    storage._s3_configured = lambda: False
    storage._get_s3 = lambda: None
    from app.db.session import SessionLocal
    from app.db.models import GeneratedFile, ModelRevision
    from app.experimental import bim_orchestration as orchestration, cad_worker
    from app.experimental.bim_authoring import stage_packet, stage_context
    from app.experimental.cad_artifacts import PrivateStore
    from app.experimental.cad_contract import digest
    from app.services.ai import nebius
    from app.services.ai.provider import ModelRouter, RoutingMetadata, NebiusProvider
    from app.services.assistant.storage import rows
    manifest = json.loads((out / "prepared.json").read_text())
    prepared = json.loads((out / "understand-request.json").read_text())
    expected = dict(system=prepared["system"], payload=prepared["payload"])
    require(digest(expected) == prepared["packetHash"], "CANARY_PREPARED_HASH_MISMATCH")
    require(manifest["testActorId"] == manifest["testProjectId"] == 490001, "CANARY_ACTOR_PROJECT_MISMATCH")
    require(manifest["database"] == str(out / "acceptance.db"), "CANARY_DATABASE_MISMATCH")
    require(manifest["model"] == MODEL and manifest["maxOutputTokensPerCall"] == 3500 and manifest["timeoutSeconds"] == 45,
            "CANARY_PREPARED_LIMIT_MISMATCH")
    require(manifest["maxCalls"] == 1 and manifest["inputReservationTokens"] == 7292 and not manifest["automaticRetry"]
            and not manifest["continueToPlan"], "CANARY_PREPARED_POLICY_MISMATCH")
    route = ModelRouter().route(RoutingMetadata(intent="DESIGN_REQUEST", requested_effect="PROPOSAL_ONLY", complexity="COMPLEX", engineering_sensitive=True))
    require((route.model, route.tier, route.max_output_tokens, route.timeout) == (MODEL, "PRIMARY", 3500, 45), "CANARY_ROUTE_MISMATCH")
    with SessionLocal() as db:
        run_id = manifest["runId"]
        row = db.get(GeneratedFile, run_id)
        require(row is not None and row.project_id == 490001, "CANARY_RUN_MISSING")
        store = PrivateStore()
        data = json.loads(store.get(490001, row.metadata_json["snapshotHash"]))
        require(row.metadata_json["status"] == "READY" and row.metadata_json["calls"] == 0 and not data["checkpoints"]
                and not any(row.metadata_json["attempts"].values()), "CANARY_RUN_ALREADY_CLAIMED")
        _, frozen, _ = orchestration.frozen(db, 490001, 490001, manifest["messageId"])
        require(digest(frozen) == data["frozenHash"] == manifest["frozenContextHash"], "CANARY_FROZEN_SOURCE_MISMATCH")
        packet = stage_packet("UNDERSTAND", request_text=frozen["userRequest"])
        packet["trustedContext"] = stage_context("UNDERSTAND", frozen, data["frozenHash"])
        current = dict(system=packet.pop("instruction"), payload=packet)
        require(digest(current) == prepared["packetHash"], "CANARY_CURRENT_PACKET_MISMATCH")
        before = {str(r.id): digest(r.document_json) for r in db.query(ModelRevision).filter_by(project_id=490001)}
        require(before == {str(manifest["revisionId"]): manifest["originalDocumentHash"]}, "CANARY_REVISION_MISMATCH")
        validate_transport(expected, "POST", "chat/completions", dict(model=MODEL, timeout=45,
            payload=dict(model=MODEL, max_tokens=3500, temperature=.1, response_format={"type":"json_object"},
                messages=[dict(role="system", content=current["system"]),
                          dict(role="user", content=json.dumps(current["payload"], separators=(",", ":"), default=str))])))
        db.commit()
        guard = OneRequestGuard(out / "canary-execution.json", expected, run_id=run_id, authorization=authorization)
        original, original_compile = nebius._request, cad_worker.compile_batch
        metadata, action = [], {}
        async def guarded(method, endpoint, **kwargs):
            return await guard.dispatch(original, method, endpoint, **kwargs)
        def forbidden(*args, **kwargs):require(False, "CANARY_CAD_BUILD_FORBIDDEN")
        nebius._request, cad_worker.compile_batch = guarded, forbidden
        try:
            result = asyncio.run(orchestration.advance(db, project_id=490001, user_id=490001, run_id=run_id,
                provider=NebiusProvider(usage_sink={}, metadata_sink=metadata), store=store))
            action.update(runStatus=result["status"], errorCode=result.get("errorCode"), completedStages=result.get("completedStages", []))
        except BaseException as exc:
            db.rollback()
            guard.fail_before_transport(exc)
            action.update(actionErrorCode=getattr(exc, "code", "CANARY_ACTION_FAILED"), stack=stack_evidence(exc))
        finally:
            nebius._request, cad_worker.compile_batch = original, original_compile
            db.expire_all()
            after = {str(r.id): digest(r.document_json) for r in db.query(ModelRevision).filter_by(project_id=490001)}
            row = db.get(GeneratedFile, run_id)
            checkpoint = json.loads(store.get(490001, row.metadata_json["snapshotHash"]))
            guard.finish(**action, revisionsUnchanged=before == after, revisionHashes=after,
                strictCheckpointAccepted=any(c["key"] == "UNDERSTAND" for c in checkpoint["checkpoints"]),
                approvalCount=len(rows(db, "proposal_approvals", 490001)), proposalCount=len(rows(db, "design_proposal_versions", 490001)),
                cadArtifactCount=db.query(GeneratedFile).filter(GeneratedFile.project_id == 490001,
                    GeneratedFile.file_type.in_(["cad_manifest_v1", "cad_review_v1"])).count(), providerMetadata=metadata)
            print(json.dumps(guard.data, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-authorized", action="store_true", required=True)
    parser.add_argument("--prepared-directory", required=True)
    parser.add_argument("--authorization-reference", required=True)
    args = parser.parse_args()
    execute(args.prepared_directory, args.authorization_reference)
