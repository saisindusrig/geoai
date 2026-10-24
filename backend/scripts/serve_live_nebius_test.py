"""Local user-authorized $10 Nebius test. Other AI/cloud services remain disabled."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
credential=settings.NEBIUS_API_KEY
import serve_phase1_local
settings.NEBIUS_API_KEY=credential
settings.ENGINEERING_AI_MODE='nebius'
settings.ENGINEERING_AI_BUDGET_APPROVED=True
settings.ENGINEERING_AI_BUDGET_USD=10
settings.NEBIUS_ENFORCE_AGENT_BUDGET=True
settings.NEBIUS_BASE_URL='https://api.tokenfactory.nebius.com/v1'
if __name__=='__main__':
    import uvicorn
    uvicorn.run('app.main:app',host='127.0.0.1',port=8001)
