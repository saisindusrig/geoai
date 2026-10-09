"""One GET then at most one tiny POST. Never invokes the benchmark or pilot."""
import argparse
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from app.services.ai.nebius_config import use_env_file, safe_loading_diagnostics
from app.services.ai.nebius import available_assistant_models, assistant_json, assistant_diagnostics
from app.services.ai.provider import AssistantProviderError
from .run_geoai import load, ROOT
from .reporting import redact


def match_candidates(config, ids):
    import re
    def label(value):return re.sub(r'[^a-z0-9]','',value.lower())
    for candidate in config.candidates:
        matches=[item for item in ids if label(item.rsplit('/',1)[-1])==label(candidate.display_name)]
        if len(matches)==1:
            candidate.model_id=matches[0];candidate.verified=True;candidate.availability='AVAILABLE'
            candidate.availability_note='Exact requested model name verified by provider catalogue (separator/case normalization only).'
        else:
            candidate.model_id=None;candidate.verified=False
            candidate.availability='UNAVAILABLE' if not matches else 'UNKNOWN'
            candidate.availability_note='Requested model absent from verified catalogue; no substitution.' if not matches else 'Ambiguous exact model-name matches; manual mapping required.'
    return config


async def check(*, env_file=None):
    before=safe_loading_diagnostics()
    if env_file:use_env_file(env_file)
    report={'before':before,'after':safe_loading_diagnostics(),'model_list':None,'structured_chat':{'status':'NOT_ATTEMPTED'},
        'model_list_requests':0,'completion_requests':0,'checked_at':datetime.now(timezone.utc).isoformat()}
    started=time.monotonic()
    report['model_list_requests']=1
    try:
        ids=await available_assistant_models()
    except AssistantProviderError as exc:
        report['model_list']={'status':exc.code,'diagnostics':exc.diagnostics,'latency_seconds':round(time.monotonic()-started,3)}
        return report
    report['model_list']={'status':'AVAILABLE','httpStatus':200,'latency_seconds':round(time.monotonic()-started,3),
        'relevant_ids':[item for item in ids if any(name in item.lower() for name in ('qwen','glm','nemotron','kimi'))]}
    config,_=load()
    config=match_candidates(config,ids)
    config.catalogue_verification={'status':'VERIFIED_CATALOGUE','checked_at':report['checked_at'],'httpStatus':200}
    (ROOT/'geoai_models.json').write_text(json.dumps(config.model_dump(),indent=2),encoding='utf-8')
    report['candidates']=[c.model_dump() for c in config.candidates]
    verified=[c for c in config.candidates if c.verified]
    # A tiny check may use any relevant listed ID if the requested variants are absent.
    model=verified[0].model_id if verified else next(iter(report['model_list']['relevant_ids']),None)
    if not model:return report
    started=time.monotonic();report['completion_requests']=1
    try:
        response=await assistant_json('Return exactly {"status":"ok"}. No other fields.',{'connectivityCheck':True},model=model,max_output_tokens=256,timeout=25)
        report['structured_chat']={'status':'STRUCTURED_CONNECTIVITY_OK' if response=={'status':'ok'} else 'INVALID_RESPONSE',
            'model':model,'httpStatus':200,'latency_seconds':round(time.monotonic()-started,3)}
    except AssistantProviderError as exc:
        report['structured_chat']={'status':exc.code,'diagnostics':exc.diagnostics,'latency_seconds':round(time.monotonic()-started,3)}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'results'/'connectivity.json')
    args=parser.parse_args()
    result=redact(asyncio.run(check(env_file=args.env_file)))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
