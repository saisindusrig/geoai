"""Read-only verification of the three selected offline preparation fixtures."""
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['DATABASE_URL']='sqlite://'
from app.experimental.cad_contract import digest
from app.experimental.bim_model_evaluation import CANDIDATES,request_body

SELECTED={
    'platform':'4d-platform-4005c5d4343f4c81a2e21497f1a2f2c7',
    'bridge':'4d-bridge-39f073205971470a9829fd0a9789c693',
    'mixed':'4d-mixed-cd1c0ac81a464aa188be8feb993d192f'}


def main():
    catalog=json.loads((ROOT/'.cad-proof-output/4d-discovery-a2cb4310f7ec4a87996e8bebc5c20a07/catalog.json').read_text())
    results=[]
    for scenario,name in SELECTED.items():
        folder=ROOT/'.cad-proof-output'/name
        manifest=json.loads((folder/'prepared.json').read_text())
        packet=json.loads((folder/'understand-request.json').read_text())
        ledger=json.loads((folder/'evaluation-ledger.json').read_text())
        assert digest(packet)==manifest['packetHash']==ledger['packetHash']
        assert ledger['requestCount']==ledger['dispatchCount']==ledger['acceptedCheckpoints']==0
        assert not manifest['executionAuthorized'] and manifest['paidRequestsSent']==0
        for model in CANDIDATES:
            _,reservation=request_body(packet,model,catalog['models'])
            assert reservation==manifest['inputReservationTokens']
        with sqlite3.connect('file:'+ (folder/'acceptance.db').as_posix()+'?mode=ro',uri=True) as db:
            revisions=db.execute('select document_json from model_revisions').fetchall()
            assert len(revisions)==1 and digest(json.loads(revisions[0][0]))==manifest['originalDocumentHash']
            assert db.execute("select count(*) from generated_files where file_type in ('cad_manifest_v1','cad_review_v1')").fetchone()[0]==0
            for table in ('design_proposal_versions','proposal_approvals'):
                assert db.execute('select count(*) from '+table).fetchone()[0]==0
        results.append(dict(scenario=scenario,directory=str(folder),packetHash=manifest['packetHash'],
                            reservation=reservation,revisionUnchanged=True,paidRequests=0,checkpoints=0,
                            proposals=0,approvals=0,cadArtifacts=0))
    evidence=dict(status='PREPARED_NOT_AUTHORIZED',maxRequests=15,inputCeiling=122880,
                  actualReservation=sum(r['reservation'] for r in results)*5,maxOutputTokens=52500,
                  fixtures=results,scoreboard=[dict(model=m,executed=0,total=3,status='NOT_MEASURED') for m in CANDIDATES])
    (ROOT/'.cad-proof-output/4d-preflight.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
