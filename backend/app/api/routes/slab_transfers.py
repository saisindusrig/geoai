"""Saved one-way slab transfer previews and exact engineer-authorized local solves."""
import json,hashlib
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from typing import Literal
from app.db.models import EngineeringAnalysis
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context
from app.api.routes.opensees import lock
from app.services.design import slab_transfer as solver,opensees_benchmark as common,physical_frame

router=APIRouter(prefix='/api/projects/{project_id}/engineering/slab-transfer',tags=['engineering'])
INPUT='SLAB_TRANSFER_INPUT';RUN='OPENSEES_SLAB_TRANSFER'
class Inspect(solver.Selection):
 model_revision_id:int=Field(gt=0)
class Save(solver.Inputs):
 model_revision_id:int=Field(gt=0)
 base_input_id:int|None=None
class Authorize(solver.Strict):
 input_id:int=Field(gt=0)
 input_sha256:str=Field(min_length=64,max_length=64)
 authorize_solver:Literal[True]

def latest(pid,sid,db):
 return db.query(EngineeringAnalysis).filter_by(project_id=pid,analysis_type=INPUT).filter(EngineeringAnalysis.result_json['scenario_id'].as_integer()==sid).order_by(EngineeringAnalysis.id.desc()).first()
def output(row,db,user):
 status=row.status;r=row.result_json
 try:
  rev,_=context(row.project_id,row.model_revision_id,db,user);i=latest(row.project_id,rev.design_scenario_id,db)
  if r.get('cad_source_provenance') and provenance(rev,r['inputs'],db,user)!=r['cad_source_provenance']:status='STALE'
  if common.digest(rev.document_json)!=r['model_document_sha256'] or (row.id if row.analysis_type==INPUT else r['input_record_id'])!=(i.id if i else None):status='STALE'
 except (HTTPException,ValueError,KeyError):status='STALE'
 return dict(id=row.id,model_revision_id=row.model_revision_id,status=status,result=r)
def record(pid,rid,kind,status,data,db,user):
 row=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version='cad-slab-unequal/1' if data.get('cad_source_provenance') else 'slab-transfer/1',status=status,result_json=data,actor_user_id=user);db.add(row);db.commit();db.refresh(row);return row
def owned(pid,id,kind,db,user):
 get_owned_project(pid,db,user);row=db.query(EngineeringAnalysis).filter_by(project_id=pid,id=id,analysis_type=kind).first()
 if not row:raise HTTPException(404,'Slab transfer evidence not found')
 return row
def provenance(rev,q,db,user):
 if not rev.document_json.get('metadata',{}).get('cad_slab_path_review'):return None
 from app.api.routes.cad_frames import source_provenance
 from app.services.design.cad_frame import identity
 ids={q['slab_id'],*q['beam_ids'],*(id for f in q['frames'] for id in f['component_ids'])}
 return source_provenance(rev,{'members':[dict(component_id=c['id'],cad_source=identity(c)) for c in rev.document_json['components'] if c['id'] in ids]},db,user)

@router.get('/cad-audit')
def cad_audit(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 from app.api.routes.drawing_cad import source_context
 from app.services.design import drawing_cad as cad
 rev,source,review=source_context(project_id,model_revision_id,db,user_id);doc=rev.document_json
 if not doc.get('metadata',{}).get('cad_slab_path_review'):raise HTTPException(422,'Separate CAD slab load-path review required')
 saved={c.get('metadata',{}).get('drawing_cad',{}).get('source_entity_id') for c in doc['components']}
 missing=[dict(entity_id=e['id'],handle=e['handle'],layer=e['layer'],plan_points_m=e.get('points_m'),missing_inputs=['Explicit elevations and member dimensions','Material/source identification','Geometric declarations and individually reviewed analytical joints']) for e in source.result_json['entities'] if e.get('layer') in ['BEAMS','COLUMNS'] and cad.rectangle(e) and e['id'] not in saved]
 candidates=[e for e in source.result_json['entities'] if e.get('layer') in ['BEAMS','COLUMNS'] and cad.rectangle(e)]
 northmost={layer:max(sum(p[1] for p in e['points_m'])/len(e['points_m']) for e in candidates if e['layer']==layer and (layer=='COLUMNS' or e['plan_dimensions_m'][0]>e['plan_dimensions_m'][1])) for layer in ['BEAMS','COLUMNS']}
 for e in missing:
  points=e['plan_points_m'];e['required_for_practice_one_way_path']=abs(sum(p[1] for p in points)/len(points)-northmost[e['layer']])<1e-8 and (e['layer']=='COLUMNS' or max(p[0] for p in points)-min(p[0] for p in points)>max(p[1] for p in points)-min(p[1] for p in points))
 return dict(status='BLOCKED_MISSING_REVIEWED_SUPPORT_GEOMETRY' if any(e['required_for_practice_one_way_path'] for e in missing) else 'REVIEW_SUPPORTED_LOAD_PATH_INPUTS',missing_source_members=missing,legacy_context_ids=[c['id'] for c in doc['components'] if not cad.is_generated(c)],source_reference_id=source.id,review_record_id=review.id,source_sha256=source.result_json['source_sha256'],notice='DXF plan outlines are references, not supports. North supporting members are missing until explicitly mapped, previewed and authorized. Transverse edge outlines are also absent and are not required by the narrowly declared one-way idealization. The overlapping legacy platform is a separate preserved context only after explicit exclusion review.',engineering_approval='DISABLED')

@router.post('/inspect')
def inspect(project_id:int,payload:Inspect,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id)
 try:return solver.geometry(rev.document_json,payload.model_dump(exclude={'model_revision_id'}))
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
@router.post('/inputs')
def save(project_id:int,payload:Save,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 rev,_=context(project_id,payload.model_revision_id,db,user_id);q=payload.model_dump(exclude={'model_revision_id','base_input_id'})
 try:t,gs=solver.graphs(rev.document_json,q)
 except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
 old=latest(project_id,rev.design_scenario_id,db)
 if payload.base_input_id!=(old.id if old else None):raise HTTPException(409,'Engineering inputs changed; reload')
 data=dict(inputs=q,transfer=t,frame_graphs=gs,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json),engineering_approval='DISABLED',code_checks='DISABLED')
 data['cad_source_provenance']=provenance(rev,q,db,user_id)
 data['input_sha256']=common.digest(data)
 return output(record(project_id,rev.id,INPUT,'AWAITING_AUTHORIZATION',data,db,user_id),db,user_id)
@router.post('/authorize-run')
def run(project_id:int,payload:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,payload.input_id,INPUT,db,user_id);data=row.result_json
 if payload.input_sha256!=data['input_sha256'] or output(row,db,user_id)['status']=='STALE':raise HTTPException(409,'Exact current saved slab proposal required')
 if data.get('analysis_id'):return output(owned(project_id,data['analysis_id'],RUN,db,user_id),db,user_id)
 if row.status!='AWAITING_AUTHORIZATION':raise HTTPException(409,'Prepare a new proposal after a failed execution')
 if not lock.acquire(blocking=False):raise HTTPException(409,'Local solver busy')
 try:
  rev,_=context(project_id,row.model_revision_id,db,user_id)
  authorization=dict(actor_user_id=user_id,authorized_at=datetime.now(timezone.utc).isoformat(),scope='Exact two-frame slab load transfer numerical verification; no safety approval')
  row.status='AUTHORIZED';row.result_json={**data,'authorization':authorization};db.commit()
  r=solver.run(rev.document_json,data['inputs'])
  # Recheck model/input freshness after the synchronous solver work.
  context(project_id,rev.id,db,user_id)
  if latest(project_id,rev.design_scenario_id,db).id!=row.id:raise ValueError('Inputs changed during solver execution')
  if provenance(rev,data['inputs'],db,user_id)!=data.get('cad_source_provenance'):raise ValueError('Drawing source/review changed during solver execution')
  r.update(cad_source_provenance=data.get('cad_source_provenance'),model_document_sha256=data['model_document_sha256'],model_revision_id=rev.id,input_record_id=row.id,scenario_id=rev.design_scenario_id,authorization=authorization)
  for f in r['frames']:
   f['result'].update(cad_source_provenance=data.get('cad_source_provenance'),slab_load_transfer=r['transfer'],model_revision_id=rev.id,model_document_sha256=data['model_document_sha256'],input_record_id=row.id)
   (common.ARTIFACTS/f['result']['run_id']/'manifest.json').write_text(json.dumps(f['result'],indent=2),encoding='utf-8')
  result=record(project_id,rev.id,RUN,'VERIFIED',r,db,user_id);row.result_json={**row.result_json,'analysis_id':result.id};row.status='SOLVER_COMPLETED';db.commit();return output(result,db,user_id)
 except (ValueError,RuntimeError,OSError,TypeError) as e:
  row.status='SOLVER_FAILED';row.result_json={**row.result_json,'error':str(e)};db.commit();raise HTTPException(503,str(e))
 finally:lock.release()
@router.get('')
def history(project_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);rows=db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_([INPUT,RUN])).order_by(EngineeringAnalysis.id.desc()).limit(30).all();records=[]
 for row in rows:
  o=output(row,db,user_id);r=o['result']
  if row.analysis_type==RUN:
   o['result']={**r,'beam_references':[{k:v for k,v in b.items() if k!='solver'} for b in r['beam_references']],'frames':[{'beam_id':f['beam_id'],'result':{k:v for k,v in f['result'].items() if k not in ('independent_reference','load_case_results')}} for f in r['frames']]}
  records.append(o)
 return dict(records=records,limitations=solver.LIMITS)
@router.get('/{analysis_id}/evidence')
def evidence(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,analysis_id,RUN,db,user_id);return output(row,db,user_id)
@router.get('/frame/{beam_id}/{analysis_id}/artifacts/{filename}')
def artifact(project_id:int,beam_id:str,analysis_id:int,filename:str,case_name:str|None=None,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=owned(project_id,analysis_id,RUN,db,user_id)
 if filename not in physical_frame.FILES or case_name not in (None,'Slab tributary'):raise HTTPException(404,'Unknown solver artifact')
 f=next((f for f in row.result_json['frames'] if f['beam_id']==beam_id),None)
 if not f:raise HTTPException(404,'Unknown saved frame')
 path=common.ARTIFACTS/f['result']['run_id']/filename
 if not path.is_file():raise HTTPException(404,'Artifact missing')
 return dict(contents=path.read_text(encoding='utf-8'),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
