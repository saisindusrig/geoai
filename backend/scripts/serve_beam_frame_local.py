"""Local beam/frame review; no cloud inference authorized for this milestone."""
import serve_phase1_local
from app.core.config import settings
settings.ENGINEERING_AI_MODE='mock'
settings.ENGINEERING_AI_BUDGET_APPROVED=False
settings.ENGINEERING_AI_BUDGET_USD=0
settings.NEBIUS_ENFORCE_AGENT_BUDGET=True
if __name__=='__main__':
 import uvicorn
 uvicorn.run('app.main:app',host='127.0.0.1',port=8001)
