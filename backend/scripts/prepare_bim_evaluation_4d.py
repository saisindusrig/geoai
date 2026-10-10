"""Create one fresh synthetic scenario database and frozen packet. No inference."""
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    scenario=sys.argv[1]
    # Set DB before importing any application session/models.
    import prepare_live_bim_4c as preparation
    preparation.OUT=ROOT/'.cad-proof-output'/('4d-'+scenario+'-'+uuid4().hex)
    preparation.OUT.mkdir()
    preparation.DATABASE=preparation.OUT/'acceptance.db'
    os.environ['DATABASE_URL']='sqlite:///'+preparation.DATABASE.as_posix()
    from app.experimental.bim_model_evaluation import REQUESTS, CANDIDATES, request_body
    preparation.REQUEST=REQUESTS[scenario]
    from app.services.ai import nebius
    async def forbidden(*args,**kwargs):raise RuntimeError('INFERENCE_FORBIDDEN_DURING_PREPARATION')
    nebius._request=forbidden
    # Reuse synthetic setup without starting unrelated application background jobs.
    import fastapi.testclient
    from types import SimpleNamespace
    original_client=fastapi.testclient.TestClient
    class OfflineClient:
        def __init__(self,app):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,path,json):
            from app.db.session import SessionLocal
            from app.experimental.bim_orchestration import start
            with SessionLocal() as db:
                run=start(db,project_id=490001,user_id=490001,
                          message_id=json['message_id'],request_id=json['request_id'])
            return SimpleNamespace(status_code=200,json=lambda:run)
    fastapi.testclient.TestClient=OfflineClient
    try:
        with contextlib.redirect_stdout(io.StringIO()):preparation.prepare()
    finally:
        fastapi.testclient.TestClient=original_client
    from app.db.session import SessionLocal
    from app.experimental import bim_orchestration as orchestration
    from app.experimental.bim_authoring import stage_packet,stage_context
    from app.experimental.cad_contract import digest
    from app.experimental.cad_artifacts import PrivateStore
    manifest=json.loads((preparation.OUT/'prepared.json').read_text())
    with SessionLocal() as db:
        row,data=orchestration._load(db,490001,490001,manifest['runId'],PrivateStore())
        _,snapshot,_=orchestration.frozen(db,490001,490001,manifest['messageId'])
        assert digest(snapshot)==data['frozenHash'] and row.metadata_json['calls']==0 and not data['checkpoints']
    payload=stage_packet('UNDERSTAND',request_text=preparation.REQUEST)
    payload['trustedContext']=stage_context('UNDERSTAND',snapshot,data['frozenHash'])
    packet=dict(system=payload.pop('instruction'),payload=payload)
    _,reservation=request_body(packet,CANDIDATES[0],CANDIDATES)
    manifest.update(scenario=scenario,packetHash=digest(packet),frozenContextHash=data['frozenHash'],
        inputReservationTokens=reservation,inputCeiling=8192,normalCalls=5,maxCalls=5,maxGeneratedOutputTokens=17500,
        executionAuthorized=False,paidRequestsSent=0,automaticRetry=False,continueToPlan=False)
    manifest['endpointTransport']='DIRECT_OWNED_ORCHESTRATION_NO_APP_STARTUP'
    (preparation.OUT/'prepared.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (preparation.OUT/'understand-request.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
    ledger=dict(status='PREPARED_NOT_AUTHORIZED',scenario=scenario,packetHash=digest(packet),
                models=list(CANDIDATES),requestCount=0,dispatchCount=0,acceptedCheckpoints=0,retries=0)
    with (preparation.OUT/'evaluation-ledger.json').open('x',encoding='utf-8') as handle:
        json.dump(ledger,handle,indent=2);handle.flush();os.fsync(handle.fileno())
    print(json.dumps(dict(directory=str(preparation.OUT),packetHash=digest(packet),reservation=reservation),indent=2))


if __name__=='__main__':main()
