"""Read-only status discrimination; no provider transport or ledger writes."""
import pytest
from app.api.routes import site_assistant as route
from app.core.config import settings

@pytest.mark.parametrize('field,value,code', [('daily_requests',3,'DAILY_REQUEST_LIMIT'),('accounted_daily_tokens',200000,'TOKEN_LIMIT'),('accounted_usd',.05,'BUDGET_LIMIT'),('active_user',1,'CONCURRENCY_LIMIT')])
def test_status_exact_limit(monkeypatch,field,value,code):
 monkeypatch.setattr(settings,'ASSISTANT_INFERENCE_APPROVED',True)
 monkeypatch.setattr(settings,'ASSISTANT_DAILY_REQUESTS',3)
 monkeypatch.setattr(settings,'ASSISTANT_DAILY_TOKENS',200000)
 monkeypatch.setattr(settings,'ASSISTANT_BUDGET_USD',.05)
 monkeypatch.setattr(route,'enabled',lambda:True)
 state=dict(accounted_usd=0,daily_requests=0,accounted_daily_tokens=0,active_global=0,active_user=0,recent_requests=0,accounting_blocked=False)
 state[field]=value
 monkeypatch.setattr(route.site_store,'snapshot',lambda _:state)
 result=route.status(1)
 assert result['code']==code and result['state']=='RATE_LIMITED'
 assert result['requestAllowance']==3
 if code=='DAILY_REQUEST_LIMIT':assert '3 of 3 turns' in result['message']
