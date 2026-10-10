"""Explicitly authorized experimental runner; default invocation cannot dispatch."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute-authorized',action='store_true')
    parser.add_argument('--authorization-reference')
    parser.add_argument('--reviewed-billing-file',type=Path)
    args=parser.parse_args()
    if not args.execute_authorized or not args.authorization_reference or not args.reviewed_billing_file:
        raise SystemExit('PREPARATION_ONLY: separate batch authority and reviewed billing required')
    folder=ROOT/'.cad-proof-output/4d-platform-4005c5d4343f4c81a2e21497f1a2f2c7'
    manifest=json.loads((folder/'prepared.json').read_text())
    packet=json.loads((folder/'understand-request.json').read_text())
    os.environ['DATABASE_URL']='sqlite:///'+(folder/'acceptance.db').as_posix()
    for key in ('GEOAI_EXPERIMENTAL_CAD','GEOAI_EXPERIMENTAL_BIM_AUTHORING'):os.environ[key]='true'
    for key in ('GEOAI_CAD_TEST_USER_IDS','GEOAI_CAD_TEST_PROJECT_IDS','GEOAI_BIM_AUTHORING_USER_IDS','GEOAI_BIM_AUTHORING_PROJECT_IDS'):os.environ[key]='490001'
    from app.core.config import settings
    settings.LOCAL_STORAGE_DIR=str(folder/'public')
    from app.services import storage
    storage._s3_configured=lambda:False
    from app.db.session import SessionLocal
    from app.experimental.bim_orchestration import frozen,authorize
    from app.experimental.cad_contract import digest
    from app.experimental.bim_testing_budget import TestingBudget
    from app.experimental.bim_live_comparison import compare
    from app.services.ai.nebius_config import resolve
    import httpx
    billing=json.loads(args.reviewed_billing_file.read_text())
    # No fabricated cost path: trusted reviewed JSON pointer + USD unit is mandatory.
    if billing.get('actualCostUnit')!='USD' or not isinstance(billing.get('actualCostPath'),list) or not billing['actualCostPath']:
        raise SystemExit('PROVIDER_ACTUAL_USD_ACCOUNTING_UNVERIFIED')
    baseline={p.relative_to(folder).as_posix():digest(p.read_bytes().hex()) for p in folder.rglob('*') if p.is_file()}
    holder={}
    def verify():
        if digest(packet)!=manifest['packetHash']:raise ValueError('PACKET_MISMATCH')
        for name,sha in baseline.items():
            if digest((folder/name).read_bytes().hex())!=sha:raise ValueError('PREPARED_STATE_CHANGED')
        with SessionLocal() as db:
            authorize(db,490001,490001)
            context,snapshot,_=frozen(db,490001,490001,manifest['messageId'])
            if digest(snapshot)!=manifest['frozenContextHash']:raise ValueError('STALE_FROZEN_CONTEXT')
            holder['context']=context
    verify()
    async def transport(body,timeout):
        config=resolve(model=body['model'],timeout=timeout)
        async with httpx.AsyncClient(timeout=timeout,follow_redirects=False) as client:
            response=await client.post(config.url('chat/completions'),headers=config.headers(),json=body)
        # Error bodies are never printed or persisted. Unknown billability halts.
        if response.status_code!=200:raise ValueError('PROVIDER_HTTP_ERROR')
        value=response.json();cost=value
        for key in billing['actualCostPath']:
            cost=cost[key]
        return {'body':value,'actualUsd':cost}
    catalog=json.loads((ROOT/'.cad-proof-output/4d-discovery-a2cb4310f7ec4a87996e8bebc5c20a07/catalog.json').read_text())['models']
    # Stable identity: repeated CLI invocation cannot create another five calls.
    batch='4d-first-five-'+manifest['packetHash']
    out=ROOT/'.cad-proof-output'/batch
    results=asyncio.run(compare(out,budget=TestingBudget(ROOT/'.cad-proof-output/4d-cumulative-budget.sqlite'),
        batch=batch,packet=packet,packet_hash=manifest['packetHash'],catalog=catalog,contracts=billing['contracts'],
        context=holder['context'],transport=transport,verify_source=verify,authority=args.authorization_reference))
    verify()
    (out/'scoreboard.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'batch':batch,'requests':len(results),'report':str(out/'scoreboard.json')}))


if __name__=='__main__':main()
