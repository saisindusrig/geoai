import asyncio
import pytest
from app.experimental.platform_demo_provider import PlatformDemoProvider,MODEL
from app.services.ai.provider import ModelRoute


@pytest.mark.parametrize('stage',['UNDERSTAND','PLAN','EXPAND','RELATE'])
def test_injected_override_only(stage):
    calls=[]
    class Fake:
        async def complete(self,system,payload,route):calls.append(route);return {'mock':True}
    route=ModelRoute('nebius','Qwen/Qwen3.5-397B-A17B','PRIMARY',False,3500,45)
    result=asyncio.run(PlatformDemoProvider(Fake()).complete('system',{'stage':stage},route))
    assert result=={'mock':True} and calls[0].model==MODEL
    assert route.model=='Qwen/Qwen3.5-397B-A17B' and len(calls)==1


def test_reject_limits_before_provider():
    class Fake:
        async def complete(self,*args):pytest.fail('must not dispatch')
    with pytest.raises(ValueError,match='LIMIT_MISMATCH'):
        asyncio.run(PlatformDemoProvider(Fake()).complete('system',{'stage':'UNDERSTAND'},ModelRoute('nebius','Qwen','PRIMARY',False,3501,45)))
