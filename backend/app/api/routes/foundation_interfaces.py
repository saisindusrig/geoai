"""Owned saved solver demand, reviewed interface assumptions and restricted arithmetic."""
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from typing import Literal
from app.db.models import EngineeringAnalysis,ModelRevision
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context
from app.api.routes import slab_transfers
from app.services.design import foundation_interface as calc,opensees_benchmark as common

router=APIRouter(prefix='/api/projects/{project_id}/engineering/foundation-interface',tags=['engineering'])
INPUT='FOUNDATION_INTERFACE_INPUT';RUN='FOUNDATION_COMPRESSION_RESULT'
class Inspect(calc.Selection):
 model_revision_id:int=Field(gt=0)
class Save(calc.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Authorize(calc.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_calculation:Literal[True]
def latest(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def source(id,db,user):
 row=db.query(EngineeringAnalysis).filter_by(id=id,analysis_type=slab_transfers.RUN).first()
 if not row:raise HTTPException(404,'Owned saved slab/frame solver evidence required')
 get_owned_project(row.project_id,db,user)
 if slab_transfers.output(row,db,user)['status']!='VERIFIED':raise HTTPException(409,'Source solver geometry or engineering inputs are stale')
 return row
def prepare(pid,rid,q,db,user):
 rev,_=context(pid,rid,db,user);src=source(q['source_analysis_id'],db,user);sr=db.get(ModelRevision,src.model_revision_id)
 # Cross-project reuse must be traceable to an explicitly copied source, never an arbitrary row.
 if src.project_id!=pid:
  origin=rev.document_json.get('metadata',{}).get('foundation_interface_review',{})
  if origin.get('source_project_id')!=src.project_id or origin.get('source_revision_id')!=src.model_revision_id:raise HTTPException(422,'Source must be the exact declared copied-project solver revision')
 by={c['id']:c for c in sr.document_json['components']};current={c['id']:c for c in rev.document_json['components']}
 if rev.document_json['components']!=sr.document_json['components']:raise HTTPException(422,'Copied model components changed from source solver revision; rerun analysis before transferring demands')
 for id in (q['column_id'],q['plate_id'],q['footing_id']):
  if id not in by or current.get(id)!=by[id]:raise HTTPException(422,'Selected physical interface changed from source solver revision; rerun analysis')
 if rev.document_json['origin']!=sr.document_json['origin']:raise HTTPException(422,'Source coordinate origin changed; rerun analysis')
 try:p=calc.prepare(rev.document_json,q,calc.demands(src.result_json,q['source_beam_id'],q['column_id']))
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
 return rev,src,p
def output(row,db,user):
 r=row.result_json;status=row.status
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user);i=latest(row.project_id,rev.design_scenario_id,db);src=source(r['inputs']['source_analysis_id'],db,user)
  if common.digest(rev.document_json)!=r['model_document_sha256'] or common.digest(src.result_json)!=r['source_evidence_sha256'] or (row.id if row.analysis_type==INPUT else r['input_record_id'])!=(i.id if i else None):status='STALE'
 except HTTPException:status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def record(pid,rid,kind,status,r,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='foundation-interface/2-contact' if r.get('inputs',{}).get('demand_scope')=='actual_N_M_contact_feasibility' else 'foundation-interface/1-compression',status=status,result_json=r,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);row=db.query(EngineeringAnalysis).filter_by(id=id,project_id=pid,analysis_type=kind).first()
 if not row:raise HTTPException(404,'Interface evidence not found')
 return row
@router.post('/inspect')
def inspect(project_id:int,payload:Inspect,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id)
 try:return calc.geometry(rev.document_json,payload.model_dump(exclude={'model_revision_id'}))
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
@router.get('/sources')
def sources(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,model_revision_id,db,user_id);pid=rev.document_json.get('metadata',{}).get('foundation_interface_review',{}).get('source_project_id',project_id);get_owned_project(pid,db,user_id)
 rows=db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=slab_transfers.RUN).order_by(EngineeringAnalysis.id.desc()).limit(20).all();out=[]
 for row in rows:
  status=slab_transfers.output(row,db,user_id)['status']
  for f in row.result_json['frames']:
   for m in f['result']['physical_to_analytical_graph']['members']:
    if m['axis']=='Up':out.append(dict(analysis_id=row.id,source_project_id=pid,source_revision_id=row.model_revision_id,beam_id=f['beam_id'],column_id=m['component_id'],status=status,run_id=f['result']['run_id'],solver_version=f['result']['solver_version'],demand=calc.demands(row.result_json,f['beam_id'],m['component_id'])))
 return dict(sources=out)
@router.post('/inputs')
def save(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 q=payload.model_dump(exclude={'model_revision_id','base_input_id'});rev,src,p=prepare(project_id,payload.model_revision_id,q,db,user_id);old=latest(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(old.id if old else None):raise HTTPException(409,'Interface inputs changed; reload')
 p.update(scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),source_evidence_sha256=common.digest(src.result_json),source_project_id=src.project_id,source_analysis_id=src.id)
 p['input_sha256']=common.digest(p)
 return output(record(project_id,rev.id,INPUT,'AWAITING_AUTHORIZATION',p,db,user_id),db,user_id)
@router.post('/authorize-calculate')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,payload.input_id,INPUT,db,user_id);p=row.result_json
 if p['input_sha256']!=payload.input_sha256 or output(row,db,user_id)['status']=='STALE':raise HTTPException(409,'Exact current reviewed interface proposal required')
 if p.get('analysis_id'):return output(owned(project_id,p['analysis_id'],RUN,db,user_id),db,user_id)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'New reviewed proposal required')
 prepare(project_id,row.model_revision_id,p['inputs'],db,user_id)
 r=calc.calculate(p);r.update(input_record_id=row.id,authorization=dict(actor_user_id=user_id,authorized_at=datetime.now(timezone.utc).isoformat(),scope='Exact isolated concentric compression arithmetic; NOT structural approval'))
 a=record(project_id,row.model_revision_id,RUN,r['status'],r,db,user_id);row.result_json={**p,'analysis_id':a.id};row.status='CALCULATION_COMPLETED';db.commit();return output(a,db,user_id)
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(30).all();return dict(records=[output(r,db,user_id) for r in rows])
@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 return output(owned(project_id,analysis_id,RUN,db,user_id),db,user_id)
