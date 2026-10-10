"""Execute the repaired runner on a disposable copy with fake transport only."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def preflight(directory):
    candidate=Path(directory).resolve()
    if candidate.parent!=(ROOT/".cad-proof-output").resolve():raise RuntimeError("ISOLATED_CANDIDATE_REQUIRED")
    failed=ROOT/".cad-proof-output"/"4c-understand-canary-981cd96192534cfebc42a739366700b5"
    before,old_before=hashes(candidate),hashes(failed)
    mock=ROOT/".cad-proof-output"/("4ch2-mock-"+uuid4().hex)
    shutil.copytree(candidate,mock)
    manifest=json.loads((mock/"prepared.json").read_text())
    manifest["database"]=str(mock/"acceptance.db")
    (mock/"prepared.json").write_text(json.dumps(manifest,indent=2))
    os.environ["DATABASE_URL"]="sqlite:///"+(mock/"acceptance.db").as_posix()
    from app.services.ai import nebius
    from app.experimental.canary_execution import CanaryError,require
    from app.experimental.bim_authoring_fixtures import authoring_case
    import httpx
    def forbidden_http(*args,**kwargs):raise RuntimeError("ALL_REAL_HTTP_FORBIDDEN_IN_PREFLIGHT")
    async def forbidden_async_http(*args,**kwargs):raise RuntimeError("ALL_REAL_HTTP_FORBIDDEN_IN_PREFLIGHT")
    httpx.Client.send=forbidden_http
    httpx.AsyncClient.send=forbidden_async_http
    calls=[]
    observed=[]
    async def fake_transport(*args,**kwargs):
        state=json.loads((mock/"canary-execution.json").read_text())
        require(state["state"]=="DISPATCH_INTENT_RECORDED" and state["requestCount"]==1,"MOCK_DURABLE_INTENT_REQUIRED")
        observed.append(state["state"])
        calls.append(1)
        return {"choices":[{"finish_reason":"stop","message":{"content":json.dumps(
            authoring_case("platform").intent.model_dump(mode="json",by_alias=True))}}],
            "usage":{"prompt_tokens":2000,"completion_tokens":200,"total_tokens":2200,
                "completion_tokens_details":{"reasoning_tokens":80}}}
    nebius._request=fake_transport
    from run_understand_canary import execute
    with contextlib.redirect_stdout(io.StringIO()):execute(mock,"OFFLINE_MOCK_ONLY_NOT_PAID_AUTHORIZATION")
    evidence=json.loads((mock/"canary-execution.json").read_text())
    require(len(calls)==1 and evidence["requestCount"]==1 and evidence["terminal"],"MOCK_SINGLE_INVOCATION_REQUIRED")
    require(evidence["strictSchemaValid"] and evidence["strictCheckpointAccepted"] and evidence["completedStages"]==["UNDERSTAND"],"MOCK_UNDERSTAND_ACCEPTANCE_REQUIRED")
    require(evidence["revisionsUnchanged"] and evidence["approvalCount"]==evidence["proposalCount"]==evidence["cadArtifactCount"]==0,"MOCK_UNAUTHORIZED_EFFECT")
    try:execute(mock,"OFFLINE_REPLAY_PROBE")
    except CanaryError as exc:
        require(exc.code=="CANARY_LEDGER_EXISTS_NO_REPLAY","MOCK_REPLAY_REJECTION_REQUIRED")
        replay_code=exc.code
    else:raise RuntimeError("MOCK_REPLAY_WAS_NOT_REJECTED")
    require(len(calls)==1,"MOCK_REPLAY_INVOKED_TRANSPORT")
    require(hashes(candidate)==before and hashes(failed)==old_before,"PROTECTED_CANARY_CHANGED")
    # Verify the actual candidate state read-only, independently of mock sessions.
    import sqlite3
    with sqlite3.connect("file:"+(candidate/"acceptance.db").as_posix()+"?mode=ro",uri=True) as db:
        metadata=json.loads(db.execute("SELECT metadata_json FROM generated_files WHERE id=?",(manifest["runId"],)).fetchone()[0])
    require(metadata["calls"]==0 and metadata["status"]=="READY" and not any(metadata["attempts"].values()),"LIVE_CANDIDATE_CLAIMED")
    preparation=json.loads((candidate/"prepared-request-ledger.json").read_text())
    require(preparation["requestCount"]==0 and not preparation["executionAuthorized"] and preparation["transportOutcome"]=="NOT_STARTED","LIVE_CANDIDATE_DISPATCHED")
    result=dict(status="READY_FOR_SEPARATE_EXPLICIT_PAID_AUTHORIZATION",preparedDirectory=str(candidate),mockDirectory=str(mock),
        fakeOutboundInvocations=1,paidRequests=0,liveCandidateRequests=0,liveCandidateAcceptedCheckpoints=0,
        mockedJsonValid=evidence["jsonSyntaxValid"],mockedStrictSchemaValid=evidence["strictSchemaValid"],
        mockedCheckpointAccepted=evidence["strictCheckpointAccepted"],mockedRevisionUnchanged=evidence["revisionsUnchanged"],
        transitions=["REQUEST_RESERVED",*observed,evidence["state"]],replayRejected=True,replayCode=replay_code,
        candidateFilesUnchangedDuringPreflight=True,previousRunUnchanged=True,executionAuthorized=False)
    (mock/"preflight-result.json").write_text(json.dumps(result,indent=2))
    (candidate/"4ch2-preflight.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--prepared-directory",required=True)
    preflight(parser.parse_args().prepared_directory)
