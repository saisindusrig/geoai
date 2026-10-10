"""Authorized read-only verbose catalog/public OpenAPI investigation; no inference."""
import json
import sys
import hashlib
import sqlite3
from decimal import Decimal
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from app.services.ai.nebius_config import resolve
    config=resolve(timeout=45)
    ids=['moonshotai/Kimi-K3','deepseek-ai/DeepSeek-V4-Pro','zai-org/GLM-5.2',
         'MiniMaxAI/MiniMax-M3','nvidia/nemotron-3-super-120b-a12b']
    out=ROOT/'.cad-proof-output'/('4db1-billing-'+uuid4().hex)
    out.mkdir()
    with httpx.Client(timeout=45,follow_redirects=False) as client:
        response=client.get(config.url('models'),params={'verbose':'true'},headers=config.headers())
        if response.status_code!=200:raise RuntimeError('CATALOG_UNAVAILABLE')
        rows=response.json().get('data',[])
        api=client.get('https://api.tokenfactory.nebius.com/openapi.json')
        if api.status_code!=200:raise RuntimeError('OPENAPI_UNAVAILABLE')
        schema=api.json()
    selected=[]
    for model in ids:
        row=next(r for r in rows if r['id']==model)
        # Preserve only public catalog prices, never account/payment data.
        pricing={k:v for k,v in row.get('pricing',{}).items() if k in
                 {'prompt','completion','image','price_per_video_second','request','price_per_minute','input_cache_read'}}
        p,c=Decimal(pricing['prompt']),Decimal(pricing['completion'])
        selected.append(dict(model=model,pricing=pricing,
            interpretedInputUsdPerMillion=str(p*1_000_000),interpretedOutputUsdPerMillion=str(c*1_000_000),
            conditionalRequestUsd=str(p*8192+c*3500),currencyUnitsConfirmed=False,
            accountEffectiveConfirmed=False,hardLiabilityConfirmed=False))
    ledger=ROOT/'.cad-proof-output/4d-cumulative-budget.sqlite'
    before=hashlib.sha256(ledger.read_bytes()).hexdigest()
    with sqlite3.connect('file:'+ledger.as_posix()+'?mode=ro',uri=True) as db:
        opening,halted=db.execute('select opening,halted from budget where id=1').fetchone()
        requests=db.execute('select count(*) from requests').fetchone()[0]
        batches=db.execute('select count(*) from batches').fetchone()[0]
    assert hashlib.sha256(ledger.read_bytes()).hexdigest()==before
    evidence=dict(timestampUtc=datetime.now(timezone.utc).isoformat(),source=config.url('models')+'?verbose=true',
        inferenceRequests=0,models=selected,conditionalFiveCallUsd=str(sum(Decimal(r['conditionalRequestUsd']) for r in selected)),
        conditionalFifteenCallUsd=str(3*sum(Decimal(r['conditionalRequestUsd']) for r in selected)),
        pricingSchema=schema.get('components',{}).get('schemas',{}).get('Pricing'),
        billingRelatedDocumentedPaths=[p for p in schema.get('paths',{}) if any(k in p.lower() for k in ('balance','billing','consumption','usage'))],
        ledger=dict(openingSpendNanodollars=opening,halted=bool(halted),requests=requests,authorizedBatches=batches,
                    sha256=before,unchanged=True),status='BLOCKED_ACCOUNT_RECONCILIATION_AND_LIABILITY')
    (out/'billing-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps(dict(evidencePath=str(out/'billing-evidence.json'),**evidence),indent=2))


if __name__=='__main__':main()
