import sys,runpy,types,json,asyncio
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'backend'))
captured={}
class Config:
 def __init__(self,*args,**kwargs):captured.update(kwargs)
class Server:
 def __init__(self,config):pass
 async def serve(self):pass
sys.modules['uvicorn']=types.SimpleNamespace(Config=Config,Server=Server)
asyncio.run=lambda coroutine,**kwargs:coroutine.close()
sys.argv=['serve_assistant_acceptance.py','--human-approved-spending','--budget-usd','0.05','--daily-tokens','200000']
runpy.run_path(str(root/'backend/scripts/serve_assistant_acceptance.py'),run_name='__main__')
from app.core.config import settings
from app.services.assistant import site_provider
assert list(site_provider.MODELS)==['zai-org/GLM-5.3-Flash']
try:site_provider.request_body([], 'zai-org/GLM-5.3', [])
except ValueError:pass
else:raise AssertionError('Advanced model not rejected')
assert settings.ASSISTANT_DAILY_REQUESTS==3 and settings.ASSISTANT_BUDGET_USD==.05
assert captured['host']=='127.0.0.1' and captured['port']==8001
result={'inference_requests':0,'flash_only':True,'advanced_rejected_before_transport':True,'max_turns_per_user':3,'budget_usd':.05,'loopback_only':True}
(root/'docs/milestone-6.2/launcher-check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
