"""Add explicit synthetic display-site bounds to review projects only."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('isolated',Path(__file__).with_name('run_isolated.py'));runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
from app.db.session import SessionLocal,engine
from app.db.models import Project
assert Path(engine.url.database).resolve()==ROOT/'docs/foundation-system/isolated/foundation.db'
db=SessionLocal()
for d in json.loads(Path(__file__).with_name('demo.json').read_text()):
 p=db.get(Project,d['fixture']['project_id']);assert p.name.startswith('Spatial review')
 p.boundary_geojson={'type':'Polygon','coordinates':[[[77.5945,12.9715],[77.5948,12.9715],[77.5948,12.9718],[77.5945,12.9718],[77.5945,12.9715]]]}
db.commit();db.close()
