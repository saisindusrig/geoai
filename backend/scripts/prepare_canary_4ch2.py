"""Fresh offline candidate and immutable preparation ledger; no dispatch."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def prepare():
    failed=ROOT/".cad-proof-output"/"4c-understand-canary-981cd96192534cfebc42a739366700b5"
    protected=hashes(failed)
    from prepare_understand_canary import prepare as prepare_candidate
    with contextlib.redirect_stdout(io.StringIO()):prepare_candidate()
    import prepare_live_bim_4c as preparation
    out=preparation.OUT
    from app.experimental.canary_execution import require, validate_transport, OneRequestGuard, MODEL
    from app.experimental import bim_orchestration as orchestration
    from app.experimental.bim_authoring import stage_packet,stage_context
    from app.experimental.cad_contract import digest
    from app.experimental.cad_artifacts import PrivateStore
    from app.db.session import SessionLocal
    from app.db.models import ModelRevision,GeneratedFile
    from app.services.assistant.storage import rows
    manifest=json.loads((out/"prepared.json").read_text())
    artifact=json.loads((out/"understand-request.json").read_text())
    expected={"system":artifact["system"],"payload":artifact["payload"]}
    with SessionLocal() as db:
        orchestration.authorize(db,490001,490001)
        row,data=orchestration._load(db,490001,490001,manifest["runId"],PrivateStore())
        _,snapshot,_=orchestration.frozen(db,490001,490001,manifest["messageId"])
        require(digest(snapshot)==data["frozenHash"]==manifest["frozenContextHash"],"CANARY_FROZEN_SOURCE_MISMATCH")
        packet=stage_packet("UNDERSTAND",request_text=snapshot["userRequest"])
        packet["trustedContext"]=stage_context("UNDERSTAND",snapshot,data["frozenHash"])
        current={"system":packet.pop("instruction"),"payload":packet}
        require(digest(current)==digest(expected)==artifact["packetHash"],"CANARY_PACKET_MISMATCH")
        require(snapshot["userRequest"]==preparation.REQUEST,"CANARY_ORIGINAL_REQUEST_MISMATCH")
        require(row.metadata_json["calls"]==0 and not data["checkpoints"] and row.metadata_json["status"]=="READY","CANARY_RUN_ALREADY_CLAIMED")
        revision=db.get(ModelRevision,manifest["revisionId"])
        require(digest(revision.document_json)==manifest["originalDocumentHash"],"CANARY_REVISION_MISMATCH")
        require(not rows(db,"proposal_approvals",490001) and not rows(db,"design_proposal_versions",490001),"CANARY_UNAUTHORIZED_EFFECT")
        require(db.query(GeneratedFile).filter(GeneratedFile.project_id==490001,GeneratedFile.file_type.in_(["cad_manifest_v1","cad_review_v1"])).count()==0,"CANARY_UNAUTHORIZED_EFFECT")
    reservation=validate_transport(expected,"POST","chat/completions",dict(model=MODEL,timeout=45,
        payload=dict(model=MODEL,max_tokens=3500,temperature=.1,response_format={"type":"json_object"},messages=[
            dict(role="system",content=current["system"]),dict(role="user",content=json.dumps(current["payload"],separators=(",",":"),default=str))])))
    # This immutable preparation record is not a dispatch claim or authorization.
    # The execution runner separately creates canary-execution.json exclusively.
    ledger=OneRequestGuard(out/"prepared-request-ledger.json",expected,run_id=manifest["runId"],authorization="NOT_AUTHORIZED_PREPARATION_ONLY")
    ledger.data.update(state="PREPARED_AWAITING_AUTHORIZATION",executionAuthorized=False,
        actualReservationTokens=reservation,frozenContextHash=manifest["frozenContextHash"],
        dispatchLedgerName="canary-execution.json",featureGatesVerified=True)
    ledger.save()
    require(hashes(failed)==protected,"CANARY_FAILED_RUN_CHANGED")
    result=dict(status="PREPARED_AWAITING_MOCK_PREFLIGHT_AND_NEW_AUTHORIZATION",preparedDirectory=str(out),
        runId=manifest["runId"],actorId=490001,projectId=490001,packetHash=artifact["packetHash"],
        frozenContextHash=manifest["frozenContextHash"],actualInputReservationTokens=reservation,inputCeiling=7292,
        messageContentBytes=reservation-1024,model=MODEL,maxOutputTokens=3500,timeoutSeconds=45,
        paidRequests=0,requests=0,acceptedCheckpoints=0,featureGatesVerified=True,previousRunUnchanged=True,
        preparationLedger=str(ledger.path),executionAuthorized=False,modelRevisionUnchanged=True)
    (out/"4ch2-preparation.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":prepare()
