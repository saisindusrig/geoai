"""Attested local test backend. Never falls back to the original database."""
import os,sys,asyncio
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TEST=ROOT/'docs/foundation-system/isolated'
DB=TEST/'foundation.db'
assert DB.is_file(),'Prepare the isolated working database from the existing snapshot first'
os.environ['DATABASE_URL']='sqlite:///'+DB.as_posix()
os.environ['LOCAL_STORAGE_DIR']=(TEST/'storage').as_posix()
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/scripts')]
import serve_beam_frame_local
from app.db.session import engine
from app.core.config import settings
assert Path(engine.url.database).resolve()==DB.resolve()
settings.PUBLIC_API_URL='http://127.0.0.1:18001'
settings.CORS_ALLOWED_ORIGINS='http://localhost:13001,http://127.0.0.1:13001'
from app.main import app
from app.api.routes import engineering_study
engineering_study.ROOT=TEST/'drawing-references'
@app.get('/__foundation_validation')
def attestation():return dict(mode='foundation-isolated-20261015',database=str(DB.resolve()),paid_inference=False,port=18001)
if __name__=='__main__':
 import uvicorn
 server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=18001))
 asyncio.run(server.serve(),loop_factory=asyncio.SelectorEventLoop if sys.platform=='win32' else None)
