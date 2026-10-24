"""Append separate empty/planar UI test projects only to the existing isolated DB."""
import importlib.util,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
path=OUT/'review-projects.json'
if path.exists():raise SystemExit('Existing test projects retained; no duplicate creation')
spec=importlib.util.spec_from_file_location('isolated',ROOT/'docs/spatial-frame/run_isolated.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from app.db.session import SessionLocal
from app.db.models import Project,DesignScenario,ModelRevision
from app.services.design.spatial_review import fixture
doc,_=fixture(1);template=copy.deepcopy(doc['components'][0]);doc['metadata']={'frame':'local_enu_meters','source':'separate_guided_ui_verification_fixture'}
components=[]
for id,kind,pos,size in [('guided-left','column',[0,0,1.5],[.3,.3,3]),('guided-beam','beam',[2,0,3],[4,.3,.3]),('guided-right','column',[4,0,1.5],[.3,.3,3])]:
 c=copy.deepcopy(template);c.update(id=id,name=id,category=kind);c['geometry']={'kind':'box','size':size};c['transform']['position']=pos;components.append(c)
results=[]
with SessionLocal() as db:
 for name,cs in [('Fresh guided workflow',[]),('Guided planar analysis verification',components)]:
  p=Project(user_id=1,name=name,project_type='unclassified',units='metric',center_lat=12.9716,center_lng=77.5946,boundary_geojson={'type':'Polygon','coordinates':[[[77.5945,12.9715],[77.5948,12.9715],[77.5948,12.9718],[77.5945,12.9718],[77.5945,12.9715]]]});db.add(p);db.flush()
  s=DesignScenario(project_id=p.id,name='Separate UI review only',status='completed');db.add(s);db.flush();d=copy.deepcopy(doc);d.update(project_id=p.id,scenario_id=s.id,components=cs)
  r=ModelRevision(project_id=p.id,design_scenario_id=s.id,revision_number=1,document_json=d,source='manual_edit',prompt='Isolated guided workflow test; no original project modified',user_id=1);db.add(r);db.flush();results.append(dict(project_id=p.id,scenario_id=s.id,revision_id=r.id))
 db.commit()
path.write_text(json.dumps(dict(database=str(base.base.DB.resolve()),original_writes=False,projects=results),indent=2));print(results)
