"""Read-only method readiness and current-result identities. No solve/proposal writes.

Delegate source/revision/authorization freshness to the existing history adapters;
delegate input applicability to the same validators used by the execution routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.api.routes.physical_frames import context
from app.api.routes import physical_frames, slab_transfers, spatial_frames, coupled_floors, foundation_system
from app.services.design import physical_frame, slab_transfer, spatial_frame, opensees_benchmark as common

router = APIRouter(prefix='/api/projects/{project_id}/engineering', tags=['engineering'])
METHODS = {
 'frame': (physical_frames, physical_frames.RUN),
 'slab': (slab_transfers, slab_transfers.RUN),
 'spatial': (spatial_frames, spatial_frames.RUN),
 'coupled': (coupled_floors, coupled_floors.RUN),
 'foundation': (foundation_system, foundation_system.RESULT),
}

def case_names(body):
 if 'cases' in body:
  cases=body['cases']
  if not cases or any(c.get('status')!='VERIFIED' for c in cases):return []
  return [c['case']['name'] for c in cases]
 if 'frames' in body:
  return list(dict.fromkeys(f['result'].get('case_name','Saved case') for f in body['frames']))
 if 'computed' in body:return ['Saved foundation actions']
 return list(dict.fromkeys([body.get('case_name','Saved case'),*[c.get('case_name','Saved case') for c in body.get('load_case_results',[])]]))

@router.get('/capabilities')
def capabilities(project_id:int, model_revision_id:int=Query(gt=0), selected_ids:str='', db:Session=Depends(get_db), user_id:int=Depends(get_current_user_id),saved_only:bool=False):
 # Ownership first; even unsupported/old revisions must not leak other projects.
 rev,_=context(project_id,model_revision_id,db,user_id,latest=False)
 try:context(project_id,model_revision_id,db,user_id)
 except HTTPException as e:
  if e.status_code!=409:raise
  return dict(project_id=project_id,model_revision_id=model_revision_id,model_document_sha256=common.digest(rev.document_json),methods={k:dict(status='STALE',reason='Select the latest saved model revision.',can_review=False,current_results=[],history=[]) for k in METHODS},engineering_approval='DISABLED')
 doc=rev.document_json;meta=doc.get('metadata',{});selection=[i for i in selected_ids.split(',') if i]
 if len(selection)>3:selection=[]
 methods={}
 for key,(route,run_type) in METHODS.items():
  item=dict(status='MISSING_INPUTS',reason='Declare and review the method inputs first.',can_review=False,current_results=[],history=[])
  methods[key]=item
  try:
   if key=='spatial' and not meta.get('spatial_frame_review'):raise HTTPException(422,'No reviewed spatial-frame input is bound to this saved model.')
   if key=='coupled' and not meta.get('coupled_floor_review'):raise HTTPException(422,'Only the prescribed synthetic one-storey shell–frame fixture is supported.')
   if key=='foundation' and not meta.get('foundation_system'):raise HTTPException(422,'No integrated foundation study is bound to this model; reference evidence remains separate.')
   if key=='frame':h=route.history(project_id,db,user_id,compact=True)
   elif key=='foundation':h=route.history(project_id,model_revision_id,db,user_id)
   else:h=route.history(project_id,db,user_id)
   records=h['records']
   # Classify by actual persisted analysis type, never payload shape alone.
   from app.db.models import EngineeringAnalysis
   ids=[r['id'] for r in records]
   saved={r.id:r for r in db.query(EngineeringAnalysis).filter(EngineeringAnalysis.project_id==project_id,EngineeringAnalysis.id.in_(ids)).all()}
   for r in records:
    source=saved.get(r['id'])
    if not source or source.analysis_type!=run_type:continue
    body=r['result'];names=case_names(body)
    current=source.model_revision_id==model_revision_id and r['status'] in ('VERIFIED','REVIEWED_SYNTHETIC_CALCULATION') and bool(names)
    entry=dict(id=r['id'],project_id=project_id,model_revision_id=source.model_revision_id,method=key,status=r['status'],load_cases=names,model_document_sha256=common.digest(doc) if key=='foundation' else body.get('model_document_sha256'))
    if current and entry['model_document_sha256']==common.digest(doc):item['current_results'].append(entry)
    item['history'].append({**entry,'current':current and entry['model_document_sha256']==common.digest(doc)})
   if key=='frame':
    inp=next((r for r in records if saved.get(r['id']) and saved[r['id']].analysis_type==route.INPUT and r['model_revision_id']==model_revision_id and r['status']!='STALE'),None)
    if inp:physical_frame.graph(doc,inp['result']['inputs']);item.update(status='SUPPORTED',can_review=True,reason='Saved planar inputs pass the existing method validator. Exact authorization is still required.')
    elif selection:physical_frame.geometry(doc,selection,allow_rigid_offsets=True);item['reason']='Selected geometry passes planar inspection. Explicit material, load, support and joint inputs are still required.'
    else:item['reason']='Select two columns and a beam for backend geometry inspection; declare materials, loads and joints.'
   elif key=='slab':
    inp=next((r for r in records if saved.get(r['id']) and saved[r['id']].analysis_type==route.INPUT and r['model_revision_id']==model_revision_id and r['status']!='STALE'),None)
    if inp:slab_transfer.graphs(doc,inp['result']['inputs']);item.update(status='SUPPORTED',can_review=True,reason='Reviewed one-way LOAD-ONLY inputs pass the existing validator. No slab stiffness or diaphragm.')
    else:item['reason']='Explicit slab/support mapping, pressure, declarations and supporting frame inputs are required; no shell behavior is inferred.'
   elif key=='spatial':spatial_frame.validate(meta['spatial_frame_review']['input'],doc);item.update(status='SUPPORTED',can_review=True,reason='Reviewed linear spatial-frame inputs validated. Floors remain LOAD-ONLY.')
   elif key=='coupled':route.check_document(doc);item.update(status='SUPPORTED',can_review=True,reason='Exact synthetic one-storey shell–frame fixture only. No arbitrary meshes, lateral shell or diaphragm.')
   else:
    inp=next((r for r in records if r['status']!='STALE'),None)
    if inp:
     if not saved_only:route.prepare(project_id,route.Preview(**inp['result']['inputs']),db,user_id)
     item.update(status='SUPPORTED',can_review=True,reason='Saved foundation source binding inspected without recalculation; review and authorization gates remain in the existing tools.' if saved_only else 'Saved bounded foundation inputs and source binding validated; unsupported checks remain disabled.')
    else:item['reason']='Bound foundation study found; independently declared material, actions, soil and detailing inputs are required.'
   if not item['current_results'] and any(r['status']=='STALE' for r in records):item.update(status='STALE',reason='Historical evidence is stale for the current model/source or latest review. Prepare and authorize a new exact review.')
  except HTTPException as e:
   if e.status_code in (401,403):raise
   item.update(status='STALE' if e.status_code==409 else 'UNSUPPORTED',reason=str(e.detail),can_review=False,current_results=[])
  except (ValueError,KeyError,TypeError):
   item.update(status='MISSING_INPUTS',reason='Saved inputs or source bindings do not pass the existing method validator. Review inputs; historical evidence is retained.',can_review=False,current_results=[])
 return dict(project_id=project_id,model_revision_id=model_revision_id,model_document_sha256=common.digest(doc),methods=methods,engineering_approval='DISABLED')
