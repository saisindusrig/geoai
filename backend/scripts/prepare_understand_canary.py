"""Offline preparation only. This entry point cannot execute a paid request."""
import contextlib
import io
import json
import os
from uuid import uuid4

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
def safe_usage(body):
    from app.experimental.canary_execution import safe_usage as extract
    return extract(body)


def prepare():
    import prepare_live_bim_4c as preparation
    preparation.OUT = preparation.ROOT / ".cad-proof-output" / ("4c-understand-canary-" + uuid4().hex)
    preparation.OUT.mkdir()
    preparation.DATABASE = preparation.OUT / "acceptance.db"
    os.environ["DATABASE_URL"] = "sqlite:///" + preparation.DATABASE.as_posix()
    from app.services.ai import nebius

    async def forbidden_transport(*args, **kwargs):
        raise RuntimeError("Paid requests prohibited during canary preparation")

    nebius._request = forbidden_transport
    with contextlib.redirect_stdout(io.StringIO()):
        preparation.prepare()

    from app.db.session import SessionLocal
    from app.db.models import GeneratedFile, ModelRevision
    from app.experimental import bim_orchestration as orchestration
    from app.experimental.bim_authoring import stage_packet, stage_context
    from app.experimental.cad_artifacts import PrivateStore
    from app.experimental.cad_contract import digest
    from app.services.ai.provider import ModelRouter, RoutingMetadata
    from app.experimental.canary_execution import require

    path = preparation.OUT / "prepared.json"
    manifest = json.loads(path.read_text())
    route = ModelRouter().route(RoutingMetadata(intent="DESIGN_REQUEST", requested_effect="PROPOSAL_ONLY", complexity="COMPLEX", engineering_sensitive=True))
    require((route.model, route.tier, route.max_output_tokens, route.timeout) == ("Qwen/Qwen3.5-397B-A17B", "PRIMARY", 3500, 45), "CANARY_ROUTE_MISMATCH")
    with SessionLocal() as db:
        row = db.get(GeneratedFile, manifest["runId"])
        data = json.loads(PrivateStore().get(preparation.PROJECT, row.metadata_json["snapshotHash"]))
        require(orchestration._state(data)[0] == "UNDERSTAND", "CANARY_STAGE_MISMATCH")
        require(row.metadata_json["calls"] == 0 and not data["checkpoints"], "CANARY_RUN_ALREADY_CLAIMED")
        revision = db.get(ModelRevision, manifest["revisionId"])
        require(digest(revision.document_json) == manifest["originalDocumentHash"], "CANARY_REVISION_MISMATCH")
    packet = stage_packet("UNDERSTAND", request_text=data["frozen"]["userRequest"])
    packet["trustedContext"] = stage_context("UNDERSTAND", data["frozen"], data["frozenHash"])
    system = packet.pop("instruction")
    content_bytes = len(system.encode("utf-8")) + len(json.dumps(packet, separators=(",", ":"), default=str).encode("utf-8"))
    require(content_bytes + 1024 <= 7292, "CANARY_INPUT_LIMIT", actualReservation=content_bytes+1024, ceiling=7292)
    manifest.update(normalCalls=1, maxCalls=1, maxGeneratedOutputTokens=3500, inputReservationTokens=7292,
        messageContentBytes=content_bytes, automaticRetry=False, continueToPlan=False,
        frozenContextHash=data["frozenHash"], paidRequestsSent=0,
        executionAuthorized=False, stopAfter="UNDERSTAND",
        telemetryPolicy="Safe finish reason, numeric usage and optional reasoning-token counts only; no private reasoning text or raw responses")
    artifact = dict(system=system, payload=packet, controls=manifest)
    artifact["packetHash"] = digest(dict(system=system, payload=packet))
    packet_path = preparation.OUT / "understand-request.json"
    packet_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(dict(manifestPath=str(path), packetPath=str(packet_path), **manifest), indent=2))


if __name__ == "__main__":
    prepare()
