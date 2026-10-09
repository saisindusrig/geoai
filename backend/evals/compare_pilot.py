"""Combine recorded Qwen/Kimi pilot results offline, preserving their provenance."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from .run_geoai import load
from .reporting import write_reports, redact
from .pilot_report import render

PILOT = ['multi_asset_001','unknown_data_001','site_aware_001','model_editing_001','unusual_assets_001']
MODELS = ['qwen','kimi']


def combine(previous, remaining, destination):
    previous,remaining,destination = map(Path,(previous,remaining,destination))
    config,cases = load()
    cases = [next(c for c in cases if c.id==key) for key in PILOT]
    manifest=json.loads((remaining/'run_manifest.json').read_text())
    state=json.loads((remaining/'run_state.json').read_text())
    assert state['status']=='COMPLETE' and state['completed_evaluations']==8
    assert manifest['model_aliases']==MODELS
    assert [c['id'] for c in manifest['cases']]==PILOT[1:]
    assert manifest['cases']==redact([c.model_dump() for c in cases[1:]])
    assert manifest['configuration']==redact(config.model_dump())
    ledger=[json.loads(line) for line in (remaining/'request_ledger.jsonl').read_text().splitlines()]
    started=[entry for entry in ledger if entry['event']=='REQUEST_STARTED']
    assert {r['model_alias'] for r in started}==set(MODELS)
    assert {r['case_id'] for r in started}==set(PILOT[1:])
    results={};hashes={};comparison=[]
    for alias in MODELS:
        paths=[previous/(alias+'.json'),remaining/(alias+'.json')]
        rows=[]
        for path in paths:
            content=path.read_bytes();hashes[str(path.resolve())]=hashlib.sha256(content).hexdigest()
            saved=json.loads(content)
            for row in saved:
                row['source_result_path']=str(path.resolve())
                row['reused_evaluation']=path.parent==previous
            rows.extend(saved)
        assert [row['case_id'] for row in rows]==PILOT
        for row in rows[1:]:
            checkpoint=json.loads((remaining/'checkpoints'/alias/(row['case_id']+'.json')).read_text())
            assert all(row[key]==value for key,value in checkpoint.items())
        results[alias]=rows
        counts=Counter(code for row in rows for code in row['scoring']['hard_failures'])
        warnings=[{'case':row['case_id'],**warning} for row in rows for warning in row['scoring'].get('warnings',[])]
        comparison.append({'model':alias,'total_score':sum(r['scoring']['score'] for r in rows),
            'maximum_total':500,'mean_score':sum(r['scoring']['score'] for r in rows)/5,
            'per_case':{r['case_id']:r['scoring']['score'] for r in rows},'hard_failures':dict(counts),
            'hard_failure_cases':sum(bool(r['scoring']['hard_failures']) for r in rows),'warnings':warnings,
            'valid_outputs':sum(r['structured_output_valid'] for r in rows),'evaluations':5,
            'average_latency_seconds':round(sum(r['latency_seconds'] for r in rows)/5,4),
            'known_output_tokens':sum(r['output_tokens'] or 0 for r in rows),
            'missing_output_usage_cases':sum(r['output_tokens'] is None for r in rows),
            'completion_requests':sum(r['requests'] for r in rows),
            'new_completion_requests':sum(r['requests'] for r in rows[1:]),
            'estimated_cost':sum(r['estimated_cost'] for r in rows) if all(r['estimated_cost'] is not None for r in rows) else None})
    assert len(started)==sum(r['requests'] for rows in results.values() for r in rows[1:])
    summary=write_reports(destination,config,cases,results)
    assert summary['primary_candidate'] is None and summary['fast_candidate'] is None
    audit={'models':comparison,'new_evaluations':8,'reused_evaluations':2,'new_completion_requests':len(started),
        'only_new_models':MODELS,'only_new_cases':PILOT[1:],'frozen_configuration_verified':True,
        'source_hashes':hashes,'production_configuration_changed':False,
        'note':'Multi-asset scores reuse the corrected offline smoke results. Historical per-attempt finish metadata is unavailable for those two reused evaluations. No production recommendation.'}
    (destination/'comparison.json').write_text(json.dumps(redact(audit),indent=2),encoding='utf-8')
    render(destination)
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','remaining','destination'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    print(json.dumps(combine(args.previous,args.remaining,args.destination),indent=2))
