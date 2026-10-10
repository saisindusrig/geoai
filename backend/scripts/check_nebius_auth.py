"""One GET /models, then one PRIMARY completion only after success. No retries."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.ai.nebius import available_assistant_models
from app.services.ai.nebius_config import safe_loading_diagnostics
from app.services.ai.provider import NebiusProvider, ModelRouter, RoutingMetadata, AssistantProviderError

async def main():
    path=Path('live-results/auth-restoration-v1.json')
    if path.exists():raise RuntimeError('This authentication batch has already been used; no retry authorized.')
    path.parent.mkdir(parents=True,exist_ok=True)
    result={'configuration':safe_loading_diagnostics(),'modelListRequests':0,'completionRequests':0,'modelList':'NOT_RUN','completion':'NOT_RUN'}
    def save():
        path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    save()
    route=ModelRouter().route(RoutingMetadata(intent='CLASSIFY'))
    if route.model!='Qwen/Qwen3.5-397B-A17B' or route.tier!='PRIMARY':raise RuntimeError('MODEL_GUARD')
    try:
        result['modelListRequests']=1;save()
        models=await available_assistant_models()
        result.update(modelList='HTTP_200',primaryAvailable=route.model in models);save()
    except AssistantProviderError as exc:
        result.update(modelList=exc.code,modelListHttpStatus=exc.diagnostics.get('httpStatus'));save()
        print(json.dumps(result));return
    try:
        result['completionRequests']=1;save()
        metadata=[]
        response=await NebiusProvider(metadata_sink=metadata).complete('Return exactly {"status":"ok"} as JSON.',{'connectivityCheck':True},route)
        result.update(completion='OK' if response=={'status':'ok'} else 'INVALID_RESPONSE',completionHttpStatus=200,metadata=metadata)
    except AssistantProviderError as exc:
        result.update(completion=exc.code,completionHttpStatus=exc.diagnostics.get('httpStatus'))
    save();print(json.dumps(result))

if __name__=='__main__':asyncio.run(main())
