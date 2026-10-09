"""Offline correctness gates for the recorded three-case FAST comparison."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from .pilot_report import render

IDS=['fast_explanation_001','fast_asset_intent_001','fast_selection_001']


def review(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'run_manifest.json').read_text())
    state=json.loads((directory/'run_state.json').read_text())
    assert state['status']=='COMPLETE' and state['completed_evaluations']==6
    assert manifest['model_aliases']==['qwen','cheap']
    assert [c['id'] for c in manifest['cases']]==IDS
    results={alias:json.loads((directory/(alias+'.json')).read_text()) for alias in ('qwen','cheap')}
    metrics={};issues={}
    for alias,rows in results.items():
        assert [r['case_id'] for r in rows]==IDS
        issues[alias]=[];per_case=[]
        for row in rows:
            other=next(r for r in results['cheap' if alias=='qwen' else 'qwen'] if r['case_id']==row['case_id'])
            assert row['context_hash']==other['context_hash']
            response=row.get('response')
            reasons=[]
            if not row['structured_output_valid']:reasons.append('INVALID_STRUCTURED_OUTPUT')
            reasons.extend(row['scoring']['hard_failures'])
            if response:
                if response['effect']!='READ_ONLY':reasons.append('NOT_READ_ONLY')
                if row['case_id']=='fast_asset_intent_001':
                    assets=response['intent']['assets']
                    if response['intent']['kind']!='DESIGN_REQUEST' or len(assets)!=1 or assets[0].get('assetFamily')!='BRIDGE':reasons.append('INCORRECT_ASSET_INTENT')
                if row['case_id']=='fast_selection_001':
                    calls=row['tools_used']
                    if [c['name'] for c in calls]!=['get_selected_objects']:reasons.append('INCORRECT_SELECTION_TOOLS')
                    # Exact object identities must be visible; no invented IDs allowed.
                    text=response['response']['text']+' '+json.dumps(response['facts'])
                    if set(re.findall(r'\b[A-Z]\d{2,}\b',text))!={'P03','P04','P05'}:reasons.append('INCORRECT_SELECTED_OBJECTS')
                if row['case_id']!='fast_selection_001' and row['tools_used']:reasons.append('UNNECESSARY_TOOL_CALLS')
            counts=Counter((c['name'],c['arguments']) for c in row['tools_used'])
            redundant=sum(count-1 for count in counts.values())
            if redundant:reasons.append('REDUNDANT_TOOL_CALLS')
            issues[alias].extend({'case':row['case_id'],'reason':reason} for reason in sorted(set(reasons)))
            per_case.append({'case':row['case_id'],'score':row['scoring']['score'],
                'hard_failures':row['scoring']['hard_failures'],'warnings':row['scoring'].get('warnings',[]),
                'valid':row['structured_output_valid'],'finish_reasons':[a['finish_reason'] for a in row.get('attempt_metadata',[])],
                'requests':row['requests'],'repairs':row['repair_requests'],'redundant_calls':redundant,
                'tool_calls':row['tools_used'],'gate_issues':sorted(set(reasons))})
        metrics[alias]={'per_case':per_case,'valid_outputs':sum(r['structured_output_valid'] for r in rows),
            'mean_score':round(sum(r['scoring']['score'] for r in rows)/3,3),
            'mean_latency_seconds':round(sum(r['latency_seconds'] for r in rows)/3,4),
            'input_tokens':sum(r['input_tokens'] or 0 for r in rows),'output_tokens':sum(r['output_tokens'] or 0 for r in rows),
            'missing_token_usage':sum(r['output_tokens'] is None for r in rows),
            'completion_requests':sum(r['requests'] for r in rows),'repair_requests':sum(r['repair_requests'] for r in rows),
            'estimated_cost':sum(r['estimated_cost'] for r in rows) if all(r['estimated_cost'] is not None for r in rows) else None}
    ledger=[json.loads(line) for line in (directory/'request_ledger.jsonl').read_text().splitlines()]
    starts=[r for r in ledger if r['event']=='REQUEST_STARTED']
    assert {r['model_alias'] for r in starts}=={'qwen','cheap'} and {r['case_id'] for r in starts}==set(IDS)
    audit={'recommendation':'ACCEPT FAST_MODEL' if not issues['cheap'] else 'REJECT FAST_MODEL FOR NOW',
        'correctness_gate_issues':issues,'metrics':metrics,'evaluations':6,
        'completion_requests':len(starts),'same_frozen_context_hashes':True,
        'acceptance_note':'Correctness gates precede efficiency. Manual review of capability assertions is still required before applying ACCEPT.',
        'new_review_provider_requests':0}
    (directory/'fast-review.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    render(directory)
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    print(json.dumps(review(parser.parse_args().directory),indent=2))
