"""Reuse the existing isolated database; never copy or open original data for writes."""
import importlib.util,sys,asyncio
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('isolated_base',ROOT/'docs/foundation-system/run_isolated.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from app.services.design import spatial_frame
spatial_frame.ARTIFACTS=Path(__file__).parent/'solver-evidence'
@base.app.get('/__spatial_validation')
def attestation():return dict(database=str(base.DB.resolve()),original_writes=False,paid_inference=False,artifacts=str(spatial_frame.ARTIFACTS),port=18001)
if __name__=='__main__':
 import uvicorn
 server=uvicorn.Server(uvicorn.Config(base.app,host='127.0.0.1',port=18001))
 asyncio.run(server.serve(),loop_factory=asyncio.SelectorEventLoop if sys.platform=='win32' else None)
