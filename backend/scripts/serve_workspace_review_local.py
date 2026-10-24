"""Milestone 7 browser review: inference disabled, no offline AI fallback."""
import asyncio
import sys
import serve_phase1_local
from app.core.config import settings

settings.AI_PROVIDER = 'nebius'
settings.GEOAI_OFFLINE_PLATFORM_DEMO = False
settings.ENGINEERING_AI_MODE = 'disabled'
settings.ENGINEERING_AI_BUDGET_APPROVED = False
settings.ENGINEERING_AI_BUDGET_USD = 0
settings.NEBIUS_ENFORCE_AGENT_BUDGET = True
settings.ASSISTANT_INFERENCE_APPROVED = False
settings.ASSISTANT_BUDGET_USD = 0

if __name__ == '__main__':
    import uvicorn
    server = uvicorn.Server(uvicorn.Config('app.main:app', host='127.0.0.1', port=8001, proxy_headers=False))
    asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop if sys.platform == 'win32' else None)
