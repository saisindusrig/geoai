from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import EngineeringAnalysis,ModelRevision
from app.core.security import get_current_user_id
from app.api.routes.cad_soil import audit_data
from app.services.design import demand_transport as d,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/footing-transport',tags=['engineering'])
class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 links:list[d.Link]=Field(min_length=4,max_length=4)
class Authorize(Strict):
 proposal_id:int
 proposal_sha256:str
 authorize_transport:bool

def calculate(pid,q,db,user):
 a=audit_data(pid,q.model_revision_id,db,user);by={c['id']:c for c in db.get(ModelRevision,q.model_revision_id).document_json['components']};rows={r['column_id']:r for r in a['rows']}
 if len({l.column_id for l in q.links})!=4 or {l.column_id for l in q.links}!=set(rows) or len({l.footing_id for l in q.links})!=4:raise HTTPException(422,'Exactly four distinct source-column and footing identities required')
 out=[]
 for l in q.links:
  r=rows[l.column_id];f=by.get(l.footing_id)
  if not l.reviewed or not f or f['category']!='foundation' or not cad.is_generated(f):raise HTTPException(422,'Explicit reviewed saved CAD footing required')
  if f['metadata']['drawing_cad']['component_sha256']!=cad.component_hash(f):raise HTTPException(422,'Footing provenance changed')
  p=f['transform']['position'];s=f['geometry']['size'];B=r['base_enu_m']
  if any(abs(a-b)>1e-8 for a,b in zip(l.column_reference_m,B)) or any(abs(p[i]-B[i])>1e-8 for i in [0,1]):raise HTTPException(422,'Reference must match exact saved column base and corresponding footing centre')
  if any(abs(l.footing_reference_m[i]-p[i])>1e-8 for i in [0,1]) or abs(l.footing_reference_m[2]-(p[2]-s[2]/2))>1e-8:raise HTTPException(422,'Supported target is the explicit saved footing underside centre')
  if any(abs(l.plate_reference_m[i]-B[i])>1e-8 for i in [0,1]) or not l.footing_reference_m[2]<=l.plate_reference_m[2]<=B[2]:raise HTTPException(422,'Declared intermediate interface must be concentric and between column base and footing underside; no physical plate inferred')
  # Solver reactions act on structure; demand applied to foundation is the opposite wrench.
  F=[-r['shear_east_n'],0,-r['compression_n']];M=[0,r['moment_negative_north_nm'],0]
  plate=d.transport(F,M,B,l.plate_reference_m);soil=d.transport(F,plate['moment_enu_nm'],l.plate_reference_m,l.footing_reference_m);direct=d.transport(F,M,B,l.footing_reference_m)
  if any(abs(x-y)>1e-7 for x,y in zip(soil['moment_enu_nm'],direct['moment_enu_nm'])):raise HTTPException(422,'Sequential/direct transport mismatch')
  out.append(dict(column_id=l.column_id,footing_id=l.footing_id,source_reaction=r,link=l.model_dump(),plate_demand=plate,footing_demand=soil,compression_n=-F[2],horizontal_shear_enu_n=F[:2],Mx_nm=soil['moment_enu_nm'][0],My_nm=soil['moment_enu_nm'][1],torsion_Mz_nm=soil['moment_enu_nm'][2],missing='Physical plate/anchors/connection resistance, concrete/reinforcement and sourced soil/contact behavior unverified; actual soil pressure BLOCKED'))
 # Independently balance each transported wrench about the global ENU origin.
 old_total=[0.,0.,0.];new_total=[0.,0.,0.]
 for row in out:
  src=row['source_reaction'];F=[-src['shear_east_n'],0.,-src['compression_n']];O=row['link']['column_reference_m'];P=row['link']['footing_reference_m'];M=[0.,src['moment_negative_north_nm'],0.];T=[row['Mx_nm'],row['My_nm'],row['torsion_Mz_nm']]
  for pos,couple,total in [(O,M,old_total),(P,T,new_total)]:
   lever=[pos[1]*F[2]-pos[2]*F[1],pos[2]*F[0]-pos[0]*F[2],pos[0]*F[1]-pos[1]*F[0]]
   for i in range(3):total[i]+=couple[i]+lever[i]
 residual=[x-y for x,y in zip(new_total,old_total)]
 if max(map(abs,residual))>1e-7:raise HTTPException(422,'Global transported-demand equilibrium failed')
 return dict(global_origin_moment_check=dict(old_nm=old_total,new_nm=new_total,residual_nm=residual,passed=True,method='Independent component-wise global-origin sums of source and transported wrenches'),audit=a,rows=out,inputs=q.model_dump(),benchmarks=d.benchmarks(),engineering_approval='DISABLED',soil_pressure='BLOCKED',scope='Mathematical demand transport only; intermediate plate reference is engineer-declared interface, not a saved or verified physical base plate')
@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 r=calculate(project_id,q,db,user_id);r['proposal_sha256']=cad.digest(r);row=EngineeringAnalysis(project_id=project_id,model_revision_id=q.model_revision_id,analysis_type='FOOTING_TRANSPORT_PROPOSAL',algorithm_version='wrench/1',status='AWAITING_AUTHORIZATION',result_json=r,actor_user_id=user_id);db.add(row);db.commit();db.refresh(row);return dict(id=row.id,status=row.status,result=r)
@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=q.proposal_id,analysis_type='FOOTING_TRANSPORT_PROPOSAL').first()
 if not row:raise HTTPException(404,'Proposal not found')
 latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='FOOTING_TRANSPORT_PROPOSAL').order_by(EngineeringAnalysis.id.desc()).first()
 if latest.id!=row.id:raise HTTPException(409,'Reference mapping changed; authorize latest proposal')
 current=calculate(project_id,Preview(**row.result_json['inputs']),db,user_id)
 if not q.authorize_transport or q.proposal_sha256!=row.result_json['proposal_sha256'] or cad.digest(current)!=q.proposal_sha256:raise HTTPException(409,'Exact current mapping authorization required')
 r=EngineeringAnalysis(project_id=project_id,model_revision_id=row.model_revision_id,analysis_type='FOOTING_TRANSPORT_RESULT',algorithm_version='wrench/1',status='VERIFIED_DEMANDS_ONLY',result_json={**current,'authorized_proposal_id':row.id},actor_user_id=user_id);db.add(r);db.commit();db.refresh(r);return dict(id=r.id,status=r.status,result=current)
@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 audit_data(project_id,model_revision_id,db,user_id);out=[];latest=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type='FOOTING_TRANSPORT_PROPOSAL').order_by(EngineeringAnalysis.id.desc()).first()
 for r in db.query(EngineeringAnalysis).filter_by(project_id=project_id).filter(EngineeringAnalysis.analysis_type.in_(['FOOTING_TRANSPORT_PROPOSAL','FOOTING_TRANSPORT_RESULT'])).order_by(EngineeringAnalysis.id.desc()).all():
  try:current=calculate(project_id,Preview(**r.result_json['inputs']),db,user_id);valid=r.model_revision_id==model_revision_id and cad.digest(current)==cad.digest({k:v for k,v in r.result_json.items() if k not in ['proposal_sha256','authorized_proposal_id']})
  except (HTTPException,ValueError):valid=False
  if r.analysis_type=='FOOTING_TRANSPORT_RESULT' and r.result_json.get('authorized_proposal_id')!=(latest.id if latest else None):valid=False
  out.append(dict(id=r.id,status=r.status if valid else 'STALE',result=r.result_json))
 return dict(records=out)
