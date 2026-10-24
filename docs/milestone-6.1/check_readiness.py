"""Local inspection and OPTIONAL non-inference catalogue GET. Never POSTs inference."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.core.config import settings
from app.services.ai.nebius_config import resolve
from app.services.ai.nebius import available_assistant_models
from app.services.assistant import site_provider,site_tools
from app.api.routes.site_assistant import SYSTEM,Context,provider_context
from app.db.session import SessionLocal

parser=argparse.ArgumentParser();parser.add_argument('--catalogue',action='store_true');args=parser.parse_args()
out={'inference_requests':0,'approval_changed':False,'configuration_source':'backend resolver in diagnostic process; review runtime may deliberately clear its key'}
try:
    config=resolve(model='zai-org/GLM-5.3-Flash')
    out.update(credentials_configured=bool(config.api_key),official_endpoint=config.base_url=='https://api.tokenfactory.nebius.com/v1',
               spending_approved=settings.ASSISTANT_INFERENCE_APPROVED,budget_usd=settings.ASSISTANT_BUDGET_USD)
except ValueError:out.update(credentials_configured=False,official_endpoint=False)
if args.catalogue:
    try:
        models=asyncio.run(available_assistant_models())
        out['catalogue']={model:model in models for model in site_provider.MODELS}
    except Exception as exc:out['catalogue_error_type']=type(exc).__name__
schema_path=ROOT/'docs/milestone-6/provider-openapi.json'
schema=json.loads(schema_path.read_text())
props=schema['components']['schemas']['ChatCompletionRequest']['properties']
out['retained_official_schema_sha256']=hashlib.sha256(schema_path.read_bytes()).hexdigest()
out['api_fields']={key:key in props for key in ('stream','stream_options','tools','tool_choice','max_tokens','reasoning_effort')}
quotes={}
with SessionLocal() as db:
    from app.db.models import Project
    for label,request,owner in [('website_help',Context(page='/dashboard'),1),('saved_project',Context(page='/projects/793/workspace',project_id=793,revision_id=103),db.get(Project,793).user_id)]:
        context=provider_context(site_tools.context(db,owner,request))
        messages=[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps({'request':'Where can I inspect saved evidence without running an analysis?','context':context},ensure_ascii=False)}]
        quotes[label]=site_provider.reservation(messages,'zai-org/GLM-5.3-Flash',site_tools.definitions())
quotes['synthetic_long_wire']=site_provider.reservation([{'role':'system','content':SYSTEM},{'role':'user','content':'x'*70000}],'zai-org/GLM-5.3-Flash',site_tools.definitions())
out['reservations']=quotes
Path(__file__).with_name('provider-readiness.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
