"""Refresh the initialized loopback development API without migrations or seeding.
Not a production launcher. Firebase, paid inference and offline AI fallback stay off.
"""
import asyncio
import sqlite3
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'backend'))
with sqlite3.connect((root/'backend/dev.db').as_uri()+'?mode=ro',uri=True) as db:
    names={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    if not {'users','projects','model_revisions'}.issubset(names):
        raise RuntimeError('An existing initialized local database is required; no migration or seeding is permitted.')
from app.core.config import settings
settings.DATABASE_URL='sqlite:///'+str(root/'backend/dev.db')
settings.FIREBASE_AUTH_ENABLED=False
settings.AUTH_REQUIRE_JWT=False
settings.AI_PROVIDER='nebius';settings.GEOAI_OFFLINE_PLATFORM_DEMO=False
settings.ASSISTANT_INFERENCE_APPROVED=False;settings.ASSISTANT_BUDGET_USD=0
settings.ENGINEERING_AI_MODE='disabled';settings.ENGINEERING_AI_BUDGET_APPROVED=False;settings.ENGINEERING_AI_BUDGET_USD=0
settings.NEBIUS_ENFORCE_AGENT_BUDGET=True
settings.S3_ACCESS_KEY='';settings.S3_SECRET_KEY=''
for name in ('NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','SENTRY_DSN'):setattr(settings,name,'')
if __name__=='__main__':
    import uvicorn
    server=uvicorn.Server(uvicorn.Config('app.main:app',host='127.0.0.1',port=8001,proxy_headers=False,lifespan='off'))
    asyncio.run(server.serve(),loop_factory=asyncio.SelectorEventLoop if sys.platform=='win32' else None)
