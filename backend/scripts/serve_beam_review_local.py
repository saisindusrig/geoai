"""Synthetic Milestone 9 browser server. Never opens original DB/storage/history."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
OUT=ROOT/'docs/milestone-9';ISOLATED=OUT/'isolated';ISOLATED.mkdir(parents=True,exist_ok=True)
from app.core.config import settings
settings.DATABASE_URL='sqlite:///'+str(ISOLATED/'beam-review.db')
settings.LOCAL_STORAGE_DIR=str(ISOLATED/'storage')
settings.ASSISTANT_HISTORY_DB=str(ISOLATED/'assistant-history.db')
settings.AI_PROVIDER='nebius';settings.GEOAI_OFFLINE_PLATFORM_DEMO=False
settings.ASSISTANT_INFERENCE_APPROVED=False;settings.ASSISTANT_BUDGET_USD=0
settings.ENGINEERING_AI_MODE='disabled';settings.ENGINEERING_AI_BUDGET_APPROVED=False;settings.ENGINEERING_AI_BUDGET_USD=0
settings.NEBIUS_ENFORCE_AGENT_BUDGET=True;settings.AUTH_REQUIRE_JWT=False;settings.USAGE_LIMITS_ENABLED=False
settings.CORS_ALLOWED_ORIGINS='http://127.0.0.1:3001,http://localhost:3001'
settings.S3_ACCESS_KEY='';settings.S3_SECRET_KEY=''
for name in ('NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','SENTRY_DSN'):setattr(settings,name,'')
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.models import Project,DesignScenario,ModelRevision
from app.services.assistant.workspace_tools import execute
from app.api.routes.site_assistant import Context

def seed(run_id=0):
 init_db()
 from app.db.models import Base
 from app.db.session import engine
 Base.metadata.create_all(bind=engine)
 commands={}
 with SessionLocal() as db:
  for width in (1280,1600):
   pid=980000+10000*run_id+width
   if not db.get(Project,pid):
    db.add(Project(id=pid,user_id=1,name=f'Synthetic beam review {width}',project_type='building',units='metric',center_lat=12.9716,center_lng=77.5946));db.flush()
    db.add(DesignScenario(id=pid,project_id=pid,name='Synthetic primitive editor',status='completed'));db.flush()
    components=[dict(id=f'original-{i}',name=f'Existing reference column {i+1}',category='column',parent_id=None,visible=True,locked=False,geometry={'kind':'box','size':[.4,.4,3]},transform={'position':[x,2.*i,1.5],'rotation_deg':[0,0,0],'scale':[1,1,1]},material={'name':'Conceptual reference','color':'#60A5FA','roughness':.75,'metalness':0},quantity={'included':False}) for i,x in enumerate([-2.,2.])]
    doc=dict(schema_version=1,project_id=pid,scenario_id=pid,project_type='building',units='metric',origin=dict(lng=77.5946,lat=12.9716,elevation_m=0,heading_deg=0),generator_parameters={},metadata={'source':'isolated_synthetic_fixture','frame':'local_enu_meters'},components=components)
    db.add(ModelRevision(id=pid,project_id=pid,design_scenario_id=pid,revision_number=1,document_json=doc,source='manual_edit',user_id=1));db.commit()
   current=db.query(ModelRevision).filter_by(project_id=pid).order_by(ModelRevision.id.desc()).first()
   if current.id!=pid:raise RuntimeError('Fixture already saved. Use retained evidence or a new isolated fixture; never reset it.')
   context=Context(project_id=pid,revision_id=pid)
   args=dict(project_id=pid,revision_id=pid,primitive='beam',units='mm',endpoints=[[-2000.,0.,3500.],[2000.,2000.,4500.]],width=300.,depth=450.,position_reference='local_enu',point_source='user_explicit_enu',parent_id=None,provenance='user_dimensions_conceptual')
   commands[str(width)]={name:execute('prepare_beam_preview',{**args,'name':label},db,1,context) for name,label in [('first','Beam proposal A'),('second','Beam proposal B'),('stale','Beam proposal C'),('final','Beam proposal D')]}
   commands[str(width)]['cancel']=execute('cancel_primitive_preview',{'project_id':pid},db,1,context)
 (OUT/'commands.json').write_text(json.dumps(commands,indent=2))

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',type=int,default=0,choices=range(100));args=parser.parse_args()
 seed(args.run_id)
 import uvicorn
 server=uvicorn.Server(uvicorn.Config('app.main:app',host='127.0.0.1',port=8003,proxy_headers=False))
 asyncio.run(server.serve(),loop_factory=asyncio.SelectorEventLoop if sys.platform=='win32' else None)
