"""Run existing backend regressions against fresh local data, with paid AI off."""
import os
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
RUN = ROOT / '.cache/production-beta' / os.environ.get('GEOAI_BETA_TEST_RUN', 'backend-tests')
RUN.mkdir(parents=True, exist_ok=True)
os.environ.update(DATABASE_URL=f'sqlite:///{(RUN / "tests.db").as_posix()}',
                  LOCAL_STORAGE_DIR=str(RUN/'storage'),
                  GEOAI_ENGINEERING_ARTIFACT_ROOT=str(RUN/'solver'),
                  AI_PROVIDER='mock', ENGINEERING_AI_MODE='mock',
                  ENGINEERING_AI_BUDGET_APPROVED='false', ENGINEERING_AI_BUDGET_USD='0',
                  NEBIUS_ENFORCE_AGENT_BUDGET='false', SENTRY_DSN='',
                  S3_ACCESS_KEY='', S3_SECRET_KEY='')
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
sys.path.insert(0, str(ROOT/'backend'))
import serve_phase1_local  # noqa: E402
# Mock transports remain available to provider contract tests. The real HTTP
# transports cannot reach cloud services, regardless of test setting overrides.
import httpx
_sync_send = httpx.HTTPTransport.handle_request
_async_send = httpx.AsyncHTTPTransport.handle_async_request
def offline_send(self, request):
    if request.url.host not in {'localhost', '127.0.0.1', '::1'}:
        raise AssertionError('External HTTP transport disabled during beta regressions')
    return _sync_send(self, request)
async def offline_async_send(self, request):
    if request.url.host not in {'localhost', '127.0.0.1', '::1'}:
        raise AssertionError('External HTTP transport disabled during beta regressions')
    return await _async_send(self, request)
httpx.HTTPTransport.handle_request = offline_send
httpx.AsyncHTTPTransport.handle_async_request = offline_async_send
print('Initializing isolated beta test database', flush=True)
from app.db.init_db import init_db  # noqa: E402
init_db()
print('Collecting backend regressions', flush=True)
import pytest  # noqa: E402
raise SystemExit(pytest.main(sys.argv[1:] or ['tests', '-q', '--tb=short', f'--junitxml={ROOT / "docs/production-beta/backend-tests.xml"}']))
