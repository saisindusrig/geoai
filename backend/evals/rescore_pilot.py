"""Audited offline rescoring of a saved two-model pilot. No provider execution."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from .run_geoai import load
from .rescore import rescore_record
from .reporting import write_reports, redact
from .pilot_report import render


def rescore_pilot(source,destination):
    source,destination=Path(source),Path(destination)
    original_summary=json.loads((source/'summary.json').read_text())
    config,all_cases=load()
    cases=[next(c for c in all_cases if c.id==key) for key in original_summary['case_ids']]
    assert original_summary['evaluation_configuration']==redact(config.model_dump())
    assert original_summary['dataset_hash']==hashlib.sha256(json.dumps([c.model_dump() for c in cases],sort_keys=True).encode()).hexdigest()
    from app.services.assistant.prompts import SYSTEM
    assert original_summary['system_instructions']==redact(SYSTEM)
    aliases=[m['model'] for m in original_summary['models']]
    assert aliases==['qwen','kimi'] and len(cases)==5
    snapshots={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
    results={};audit_rows=[]
    for alias in aliases:
        original_rows=json.loads((source/(alias+'.json')).read_text())
        assert [r['case_id'] for r in original_rows]==[c.id for c in cases]
        rows=[rescore_record(case,row) for case,row in zip(cases,original_rows)]
        results[alias]=rows
        for row in rows:
            audit_rows.append({'model':alias,'case':row['case_id'],'original_score':row['original_scoring']['score'],
                'corrected_score':row['scoring']['score'],'delta':row['score_delta'],
                'original_hard_failures':row['original_scoring']['hard_failures'],
                'corrected_hard_failures':row['scoring']['hard_failures'],
                'effect_mismatches':row['scoring'].get('effect_mismatches',[]),
                'reasoning':row['rescore_reasons'],'category_deltas':row.get('category_deltas',{})})
    summary=write_reports(destination,config,cases,results)
    metrics=[]
    for alias,rows in results.items():
        metrics.append({'model':alias,'total_score':sum(r['scoring']['score'] for r in rows),
            'average_score':sum(r['scoring']['score'] for r in rows)/len(rows),
            'per_case':{r['case_id']:r['scoring']['score'] for r in rows},
            'hard_failures':dict(Counter(code for r in rows for code in r['scoring']['hard_failures'])),
            'effect_mismatch_cases':{r['case_id']:r['scoring'].get('effect_mismatches',[]) for r in rows if r['scoring'].get('effect_mismatches')},
            'truncated_cases':sum('LIKELY_TRUNCATED' in r['scoring']['hard_failures'] for r in rows),
            'truncated_attempts':sum(a.get('failure_class')=='LIKELY_TRUNCATED' for r in rows for a in r.get('attempt_metadata',[])),
            'valid_structured_outputs':sum(r['structured_output_valid'] for r in rows),'evaluations':len(rows),
            'warnings':[{'case':r['case_id'],**warning} for r in rows for warning in r['scoring'].get('warnings',[])]})
    audit={'mode':'OFFLINE_PILOT_RESCORE','new_provider_requests':0,'source_file_hashes':snapshots,
           'case_results':audit_rows,'models':metrics,'production_configuration_changed':False,
           'recommendation_status':'NO_PRODUCTION_SELECTION; SHARED_SITE_RESPONSE_CONTRACT_FAILURE_REQUIRES_INVESTIGATION',
           'shared_site_failure':'Both site_aware_001 results remain invalid and LIKELY_TRUNCATED; no token-limit change.',
           'editing_defects':'Qwen omitted get_model_revision, repeated proposal/tool calls, ended with pending tools and TURN_LIMIT; referencedObjects/revision grounding incomplete. Scores retain zero tool-selection, proposal-quality and capability-safety points.'}
    (destination/'audit.json').write_text(json.dumps(redact(audit),indent=2),encoding='utf-8')
    review={'scope':'Offline corrected-score review; original records and numeric reviewer ratings preserved.',
        'limitations':['Effect-label differences are reported separately from real mutation. No actual unauthorized mutation was evidenced in the validated saved pilot outputs.',audit['shared_site_failure'],audit['editing_defects']],
        'cases':{key:{alias:'Original score '+str(next(r for r in audit_rows if r['model']==alias and r['case']==key)['original_score'])+'; corrected score '+str(next(r for r in audit_rows if r['model']==alias and r['case']==key)['corrected_score'])+'. See scoring, grounding and per-attempt evidence below.' for alias in aliases} for key in original_summary['case_ids']}}
    (destination/'case_review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
    render(destination)
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in snapshots.items())
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    print(json.dumps(rescore_pilot(args.source,args.destination),indent=2))
