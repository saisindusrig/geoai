"""Explicit synthetic fixture review and solver authorization, isolated DB only."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('spatial_isolated',Path(__file__).with_name('run_isolated.py'))
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
from app.db.session import SessionLocal,engine
from app.db.models import Project
from app.api.routes import spatial_frames as route
from app.api.routes.physical_frames import Authorize
assert Path(engine.url.database).resolve()==(ROOT/'docs/foundation-system/isolated/foundation.db').resolve()
db=SessionLocal();source=db.get(Project,793);assert source
out=[]
for storeys in (1,2):
 fixture=route.fixture(793,route.Fixture(storeys=storeys,review_parametric_geometry=True),db,source.user_id)
 proposal=route.review(fixture['project_id'],route.Review(model_revision_id=fixture['model_revision_id'],inputs=fixture['inputs']),db,source.user_id)
 result=route.run(fixture['project_id'],Authorize(proposal_id=proposal['id'],proposal_sha256=proposal['result']['proposal_sha256'],authorize_solver=True),db,source.user_id)
 assert result['status']=='VERIFIED';out.append(dict(fixture=fixture,review_id=proposal['id'],analysis=result))
Path(__file__).with_name('demo.json').write_text(json.dumps(out,indent=2));db.close()
print([(r['fixture']['project_id'],r['fixture']['model_revision_id'],r['analysis']['id']) for r in out])
