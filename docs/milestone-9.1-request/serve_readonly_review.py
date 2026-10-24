import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'backend'))
runpy.run_path(str(root/'backend/scripts/serve_beam_review_local.py'),run_name='isolated_configuration_only')
import uvicorn
uvicorn.run('app.main:app',host='127.0.0.1',port=8003,log_level='warning')
