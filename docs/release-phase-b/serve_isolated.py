"""Synthetic-only browser API. Hard boundary: rejects writes and cannot run solvers."""
import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'backend'))
runpy.run_path(str(root/'backend/scripts/serve_beam_review_local.py'),run_name='isolated_configuration_only')
from app.core.config import settings
settings.FIREBASE_AUTH_ENABLED=False
assert Path(settings.LOCAL_STORAGE_DIR).resolve().is_relative_to(root/'docs/milestone-9/isolated')
assert Path(settings.ASSISTANT_HISTORY_DB).resolve().is_relative_to(root/'docs/milestone-9/isolated')
assert settings.DATABASE_URL.startswith('sqlite:///')
assert Path(settings.DATABASE_URL[len('sqlite:///'):]).resolve().is_relative_to(root/'docs/milestone-9/isolated')
from app.main import app
from starlette.responses import JSONResponse
@app.middleware('http')
async def isolated_boundary(request,call_next):
    if request.method not in ('GET','HEAD'):
        return JSONResponse({'detail':'Synthetic browser server rejects all writes'},status_code=405,headers={'X-Struvo-Test-Isolated':'phase-b'})
    response=await call_next(request);response.headers['X-Struvo-Test-Isolated']='phase-b';return response
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8003,proxy_headers=False,lifespan='off')
