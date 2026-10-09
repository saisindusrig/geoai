"""Render recorded pilot results only. Never calls a model or rescoring function."""
import argparse
import html
import json
from pathlib import Path


def render(directory):
    summary=json.loads((directory/'summary.json').read_text())
    models=summary['models']
    records={m['model']:json.loads((directory/(m['model']+'.json')).read_text()) for m in models}
    review_path=directory/'case_review.json'
    review=json.loads(review_path.read_text()) if review_path.exists() else {}
    esc=lambda value:html.escape(str(value))
    pretty=lambda value:esc(json.dumps(value,indent=2,ensure_ascii=False))
    def money(value):return 'Unknown' if value is None else f'{value:.6f}'
    heads=['Model','Total score /'+str(100*len(summary['case_ids'])),'Mean score /100','Hard-failure cases / events','Valid outputs','Tool errors','Mean case latency (s)','Input tokens','Output tokens','Completion requests','Estimated cost']
    rows=[]
    for model in models:
        values=[model['model'],sum(row['scoring']['score'] for row in records[model['model']]),model['score'],f"{model['hard_failure_cases']} / {sum(model['hard_failures'].values())}",
            f"{model['valid_structured_outputs']} / {model['cases']}",model['tool_errors'],model['latency_seconds'],
            model['input_tokens'],model['output_tokens'],model['requests'],money(model['estimated_cost'])]
        rows.append('<tr>'+''.join('<td>'+esc(v if v is not None else 'Unknown')+'</td>' for v in values)+'</tr>')
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>GeoAI evaluation — comparison and manual review</title>',
        '<style>body{font:15px/1.5 system-ui,sans-serif;margin:32px auto;max-width:1400px;padding:0 24px;color:#17212b;background:#fafafa}h1{font-size:26px}h2{margin-top:40px}h3{font-size:19px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;border-bottom:1px solid #d4d9df;text-align:left;vertical-align:top}th{background:#edf0f2}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eff2f4;padding:12px;font-size:12px}.scroll{overflow:auto}.answer{white-space:pre-wrap;border-left:3px solid #326c80;padding:12px 20px;background:white}.review{display:flex;flex-wrap:wrap;gap:14px;padding:15px 0}select{margin-left:5px}textarea{width:98%;height:65px}section{border-top:1px solid #d4d9df;padding-top:18px;margin-top:24px}.notice{padding:12px;background:#edf0f2}a{color:#245d74}@media print{details{display:block}table{font-size:10px}section{break-before:page}}</style>',
        '<h1>GeoAI evaluation</h1><p>'+str(len(models))+' models · '+str(len(summary['case_ids']))+' frozen cases · visible outputs only · manual ratings intentionally blank.</p>',
        '<p class="notice">Scores are the frozen evaluator’s observations, not engineering approval or a production model recommendation. Hard failures remain visible independently of averages. Costs are unknown where no provider pricing was configured.</p>',
        '<h2>Model comparison</h2><div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in heads)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>',
        '<p>Latency is mean elapsed time per case, including schema repair and tool rounds. Token totals are provider-reported prompt/completion usage. Tool calls use local deterministic fixtures and incur no separate site API requests.</p>',
        '<h2>Case breakdown</h2><div class="scroll"><table><thead><tr><th>Case / category</th>'+''.join('<th>'+esc(m['model'])+'</th>' for m in models)+'</tr></thead><tbody>']
    for case_id in summary['case_ids']:
        matches={key:next(r for r in rows if r['case_id']==case_id) for key,rows in records.items()}
        parts.append('<tr><th>'+esc(case_id)+'<br>'+esc(next(iter(matches.values()))['category'])+'</th>'+''.join('<td>'+esc(f"{matches[m['model']]['scoring']['score']} /100; hard failures: {', '.join(matches[m['model']]['scoring']['hard_failures']) or 'none'}")+'</td>' for m in models)+'</tr>')
    parts+=['</tbody></table></div><h2>Manual review — models side by side</h2>',
        '<style>.comparison{display:grid;grid-template-columns:repeat('+str(len(models))+',minmax(0,1fr));gap:24px}.comparison section{min-width:0;margin:0}.comparison .answer{min-height:120px}@media(max-width:900px){.comparison{grid-template-columns:1fr}}</style>']
    if review:
        parts.append('<p>'+esc(review.get('scope',''))+'</p><details open><summary>Scoring limitations to review</summary><ul>'+''.join('<li>'+esc(item)+'</li>' for item in review.get('limitations',[]))+'</ul></details>')
    for case_id in summary['case_ids']:
        parts.append('<h3>'+esc(case_id)+'</h3><div class="comparison">')
        for model in models:
            key=model['model'];row=next(r for r in records[key] if r['case_id']==case_id)
            response=row.get('response')
            text=response['response']['text'] if response else 'No valid final structured response captured. See provider error and validation failures below.'
            clarification=(response or {}).get('response',{}).get('clarification')
            parts += ['<section><h3>'+esc(key)+'</h3><p><b>Exact model:</b> '+esc(row['model'])+'</p>',
                '<p><b>User request:</b> '+esc(row['user_request'])+'</p>',
                '<p><b>Automatic score:</b> '+esc(row['scoring']['score'])+' /100 · <b>Valid structured output:</b> '+esc(row['structured_output_valid'])+'</p>',
                '<p><b>Hard failures:</b> '+esc(', '.join(row['scoring']['hard_failures']) or 'None recorded')+' · <b>Provider error:</b> '+esc(row['provider_error'] or 'None')+'</p>',
                '<p><b>Elapsed:</b> '+esc(row['latency_seconds'])+'s · <b>Requests:</b> '+esc(row['requests'])+' · <b>Schema repairs:</b> '+esc(row['repair_requests'])+'</p>',
                '<h4>Visible final Assistant answer</h4><div class="answer">'+esc(text)+'</div>']
            finding=review.get('cases',{}).get(case_id,{}).get(key)
            if finding:parts.append('<p><b>Preliminary review:</b> '+esc(finding)+'</p>')
            if clarification:parts.append('<p><b>Clarification:</b> '+esc(clarification.get('question',''))+'</p>')
            for label,value in [('Expected behavior',row['expected']),('Recorded scoring and warnings',row['scoring']),('Per-attempt diagnostics',row.get('attempt_metadata',[])),('Tools, arguments, and fixture results',row['tool_results']),('All validated visible turns',row['visible_turns'])]:
                parts.append('<details><summary>'+esc(label)+'</summary><pre>'+pretty(value)+'</pre></details>')
            parts.append('<div class="review">'+''.join('<label>'+esc(label)+' /5 <select aria-label="'+esc(key+' '+row['case_id']+' '+label)+'"><option value=""></option>'+''.join('<option>'+str(n)+'</option>' for n in range(1,6))+'</select></label>' for label in ['Reasoning usefulness','Clarification quality','Tool-use quality','Proposal usefulness','Capability honesty','Overall preference'])+'</div><label>Reviewer notes<textarea></textarea></label></section>')
        parts.append('</div>')
    parts.append('</html>')
    destination=directory/'manual-review.html'
    destination.write_text('\n'.join(parts),encoding='utf-8')
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    print(render(parser.parse_args().directory))
