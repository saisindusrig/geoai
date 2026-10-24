"""Read-only audit and drawing evidence gate for CAD-derived analytical mappings."""
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from sqlalchemy.orm import Session
from app.db.models import EngineeringAnalysis,Project
from app.db.session import get_db
from app.core.security import get_current_user_id
from app.services.design import cad_frame as cad,drawing_cad as drawing
import math

router=APIRouter(prefix='/api/projects/{project_id}/engineering/cad-frame',tags=['engineering'])
class Audit(drawing.Strict):
 model_revision_id:int=Field(gt=0)
 component_ids:list[str]=Field(min_length=3,max_length=3)
def source_provenance(rev,graph,db,user):
 from app.api.routes.drawing_cad import source_context
 members=graph.get('members',[])
 linked=[m for m in members if m.get('cad_source')]
 if not linked:return None
 _,source,review=source_context(rev.project_id,rev.id,db,user)
 entities={e['id']:e for e in source.result_json['entities']}
 for m in linked:
  s=m['cad_source'];e=entities.get(s['source_entity_id'])
  if s['source_sha256']!=source.result_json['source_sha256'] or not e or not drawing.rectangle(e):raise HTTPException(409,'CAD member drawing provenance is stale or unsupported')
 return dict(source_project_id=rev.project_id,source_reference_id=source.id,source_file_sha256=source.result_json['source_sha256'],source_record_sha256=drawing.digest(source.result_json),review_record_id=review.id,review_record_sha256=drawing.digest(review.result_json),component_sources={m['component_id']:m['cad_source'] for m in linked},source_classification='SYNTHETIC_VERIFICATION')
@router.post('/audit')
def audit(project_id:int,payload:Audit,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 from app.api.routes.drawing_cad import source_context
 rev,source,review=source_context(project_id,payload.model_revision_id,db,user_id)
 if not rev.document_json.get('metadata',{}).get('cad_frame_review'):raise HTTPException(422,'Separate CAD-to-FEA review copy required')
 try:r=cad.audit(rev.document_json,payload.component_ids)
 except ValueError as e:raise HTTPException(422,str(e))
 g={'members':[dict(component_id=m['component_id'],cad_source=m['source']) for m in r['members']]}
 return dict(**r,model_revision_id=rev.id,source_provenance=source_provenance(rev,g,db,user_id))
@router.get('/comparison')
def comparison(project_id:int,analysis_id:int,baseline_project_id:int,baseline_analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 from app.api.routes import physical_frames as frames
 a=frames.out(frames.owned(project_id,analysis_id,frames.RUN,db,user_id),db,user_id);b=frames.out(frames.owned(baseline_project_id,baseline_analysis_id,frames.RUN,db,user_id),db,user_id)
 if a['status']!='VERIFIED' or b['status']!='VERIFIED':raise HTTPException(409,'Two current verified saved results required; stale comparison blocked')
 x,y=a['result'],b['result'];qx,qy=x['inputs'],y['inputs'];gx,gy=x['physical_to_analytical_graph'],y['physical_to_analytical_graph']
 if not gx.get('unequal_heights') or gy.get('unequal_heights') or set(qx['component_ids'])!=set(qy['component_ids']):raise HTTPException(422,'Unequal CAD case and corresponding equal-height source identities required')
 if qx.get('load_cases') or qy.get('load_cases') or any(qx[k]!=qy[k] for k in ['load_pattern','load_n','supports']):raise HTTPException(422,'Comparison requires identical explicit horizontal loads and supports')
 sx={s['component_id']:s for s in qx['sections']};sy={s['component_id']:s for s in qy['sections']}
 if any(sx[id]['shape']!=sy[id]['shape'] or any(not math.isclose(sx[id][k],sy[id][k],rel_tol=1e-12,abs_tol=0) for k in ['elastic_modulus_pa','area_m2','inertia_m4']) for id in sx):raise HTTPException(422,'Explicit section/material numerical values must match; no invented equivalence')
 if x['cad_source_provenance']['source_file_sha256']!=y['cad_source_provenance']['source_file_sha256']:raise HTTPException(422,'Original drawing byte identities must match')
 heads=[]
 for tag in [2,3]:
  u=next(n['displacement_m'] for n in x['nodes'] if n['id']==tag);v=next(n['displacement_m'] for n in y['nodes'] if n['id']==tag)
  heads.append(dict(node=tag,component_id=next(m['component_id'] for m in gx['members'] if m['axis']=='Up' and m['node_ids'][1]==tag),unequal_displacement_si=u,equal_displacement_si=v,delta_si=[i-j for i,j in zip(u,v)]))
 reactions=[]
 for tag in [1,4]:
  u=next(n for n in x['reactions'] if n['node']==tag);v=next(n for n in y['reactions'] if n['node']==tag)
  reactions.append(dict(node=tag,unequal={k:u[k] for k in ['fx_n','fy_n','moment_nm']},equal={k:v[k] for k in ['fx_n','fy_n','moment_nm']},delta={k:u[k]-v[k] for k in ['fx_n','fy_n','moment_nm']}))
 heights=lambda g:[g['members'][i]['length_m'] for i in [0,2]]
 return dict(status='COMPARABLE_EXPLICIT_SYNTHETIC_CASES',unequal=dict(project_id=project_id,analysis_id=analysis_id,revision_id=a['model_revision_id'],column_heights_m=heights(gx),beam_offsets_m=gx['beam_offsets_m']),equal=dict(project_id=baseline_project_id,analysis_id=baseline_analysis_id,revision_id=b['model_revision_id'],column_heights_m=heights(gy),beam_offsets_m=gy['beam_offsets_m']),heads=heads,reactions=reactions,external_horizontal_load_moment_nm=dict(unequal=qx['load_n']/2*sum(heights(gx)),equal=qy['load_n']/2*sum(heights(gy))),explanation='Same declared E/A/I, horizontal forces and fixed bases; original unequal geometry changes left-column stiffness, retained head elevation and left rigid arm. The beam elastic centreline remains horizontal at its saved elevation. Equal-height geometry is a separate prior verification case, never substituted into the unequal model. Different load application heights also change the external overturning moment. Full six-head-DOF energy verification replaces symmetry reduction.',engineering_approval='DISABLED',code_checks='DISABLED')
@router.get('/comparison-baselines')
def baselines(project_id:int,analysis_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 from app.api.routes import physical_frames as frames
 frames.owned(project_id,analysis_id,frames.RUN,db,user_id)
 rows=db.query(EngineeringAnalysis).join(Project,EngineeringAnalysis.project_id==Project.id).filter(Project.user_id==user_id,EngineeringAnalysis.analysis_type==frames.RUN).order_by(EngineeringAnalysis.id.desc()).all();choices=[]
 for row in rows:
  if row.project_id==project_id:continue
  try:
   c=comparison(project_id,analysis_id,row.project_id,row.id,db,user_id);choices.append(c['equal'])
  except HTTPException:continue
 return dict(baselines=choices)
