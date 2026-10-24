"""Owned immutable foundation study copies and explicitly authorized calculations."""
from copy import deepcopy
import hashlib,html,json
from pathlib import Path
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy.orm import Session
from pydantic import Field
from app.db.session import get_db
from app.db.models import Project,DesignScenario,ModelRevision,EngineeringAnalysis
from app.core.security import get_current_user_id
from app.api.routes.projects import get_owned_project
from app.api.routes.physical_frames import context as model_context
from app.api.routes import rc_flexure as reference
from app.api.routes import engineering_study as drawings
from app.api.routes import footing_transport as reaction_api
from app.services.assistant.storage import lock_project
from app.services.design import foundation_system as s,footing_flexure as demand,drawing_cad as cad
from app.services.design.frame_loads import Strict
router=APIRouter(prefix='/api/projects/{project_id}/engineering/foundation-system',tags=['engineering'])
PROPOSAL='FOUNDATION_SYSTEM_PROPOSAL';RESULT='FOUNDATION_SYSTEM_RESULT'

def manifest():
 modules=[s,demand,s.rc_flexure,s.soil_contact,s.rectangular_bearing,s.demand_transport]
 return {**{m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules},'foundation_api':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

def context(pid,rid,db,user):
 rev,_=model_context(pid,rid,db,user)
 marker=rev.document_json.get('metadata',{}).get('foundation_system')
 if not marker:raise HTTPException(422,'Create a separate foundation study from reference project 804 first')
 source=db.query(ModelRevision).filter_by(project_id=marker['source_project_id'],id=marker['source_revision_id']).first()
 if not source:raise HTTPException(409,'Source revision unavailable')
 binding,g,_=reference.context(source.project_id,source.id,db,user)
 if cad.digest(binding)!=marker['source_binding_sha256']:raise HTTPException(409,'Source evidence changed; study must be re-reviewed')
 m=source.document_json['metadata']['rc_flexure_review']
 r=db.query(EngineeringAnalysis).filter_by(project_id=m['source_project_id'],id=m['demand_result_id'],analysis_type='FOOTING_FLEXURE_RESULT').first()
 if not r:raise HTTPException(409,'Exact saved source demand unavailable')
 q=demand.Input(**r.result_json['inputs']['benchmark'])
 # A study can be edited by the existing editor. Width/thickness are read from
 # its saved identities; no connection, load or soil values inferred from CAD.
 parts={p['id']:p for p in rev.document_json['components']}
 try:f=parts[q.footing_id];col=parts[q.column_id];B,L,h=f['geometry']['size'];ce,cn=col['geometry']['size'][:2];top=f['transform']['position'][2]+h/2
 except (KeyError,ValueError) as e:raise HTTPException(422,'Saved footing/column envelopes missing') from e
 try:
  q=demand.Input(**{**q.model_dump(),'B_m':B,'L_m':L,'thickness_m':h,'column_east_m':ce,'column_north_m':cn,'bearing_reference_up_m':top-h,'load_reference_up_m':top,'uniform_net_pressure_kpa':q.column_load_kn/(B*L)})
  g=demand.audit_geometry(rev.document_json,q)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return dict(model_revision_id=rid,model_document_sha256=cad.digest(rev.document_json),source=marker,source_current_binding=binding,method_manifest=manifest()),g,q

class Copy(Strict):
 model_revision_id:int=Field(gt=0)
 authorize_separate_study:Literal[True]
@router.post('/copy')
def copy_study(project_id:int,q:Copy,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id)
 if project_id!=804:raise HTTPException(422,'This reference workflow starts from project 804 only')
 rev,_=model_context(project_id,q.model_revision_id,db,user_id)
 binding,_,_=reference.context(project_id,rev.id,db,user_id)
 original=db.get(Project,project_id)
 p=Project(user_id=user_id,name='Foundation integrated study · reference 804',project_type=original.project_type,status='draft',units=original.units,center_lat=original.center_lat,center_lng=original.center_lng,origin_lat=original.origin_lat,origin_lng=original.origin_lng)
 db.add(p);db.flush()
 doc=deepcopy(rev.document_json)
 doc.setdefault('metadata',{})['foundation_system']=dict(source_project_id=project_id,source_revision_id=rev.id,source_binding_sha256=cad.digest(binding),classification='SYNTHETIC_VERIFICATION')
 scenario=DesignScenario(project_id=p.id,name='Integrated foundation review',status='complete',design_output_json=deepcopy(rev.scenario.design_output_json),input_parameters_json=deepcopy(rev.scenario.input_parameters_json),assumptions_json=deepcopy(rev.scenario.assumptions_json))
 db.add(scenario);db.flush()
 doc['project_id']=p.id
 doc['scenario_id']=scenario.id
 doc['metadata'].pop('cad_geometry_authorization_id',None)
 new=ModelRevision(project_id=p.id,design_scenario_id=scenario.id,revision_number=1,document_json=doc,source='manual_edit',user_id=user_id,prompt='Authorized separate foundation study; original project unchanged')
 db.add(new);db.flush()
 # Small owned drawing references are required by the existing supervised CAD
 # editing workflow. Preserve original bytes and link their exact provenance.
 src=drawings.latest(project_id,rev.design_scenario_id,drawings.SOURCE,db)
 review=drawings.latest(project_id,rev.design_scenario_id,drawings.REVIEW,db)
 source_data=deepcopy(src.result_json)
 source_data.update(scenario_id=scenario.id,model_document_sha256=cad.digest(doc),copied_from=dict(project_id=project_id,record_id=src.id,sha256=cad.digest(src.result_json)))
 new_src=EngineeringAnalysis(project_id=p.id,model_revision_id=new.id,analysis_type=drawings.SOURCE,algorithm_version=src.algorithm_version,status=src.status,result_json=source_data,actor_user_id=user_id)
 db.add(new_src);db.flush()
 review_data=deepcopy(review.result_json)
 review_data.update(scenario_id=scenario.id,model_document_sha256=cad.digest(doc),source_reference_id=new_src.id,copied_from=dict(project_id=project_id,record_id=review.id,sha256=cad.digest(review.result_json)))
 new_review=EngineeringAnalysis(project_id=p.id,model_revision_id=new.id,analysis_type=drawings.REVIEW,algorithm_version=review.algorithm_version,status=review.status,result_json=review_data,actor_user_id=user_id)
 db.add(new_review)
 drawing_bytes=(drawings.ROOT/str(project_id)/(source_data['source_sha256']+'.dxf')).read_bytes()
 if hashlib.sha256(drawing_bytes).hexdigest()!=source_data['source_sha256']:raise HTTPException(409,'Original source bytes changed during copy')
 target=drawings.ROOT/str(p.id)/(source_data['source_sha256']+'.dxf')
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and target.read_bytes()!=drawing_bytes:raise HTTPException(409,'Study source path conflict')
 if not target.exists():target.write_bytes(drawing_bytes)
 db.commit();db.refresh(new)
 return dict(project_id=p.id,scenario_id=scenario.id,model_revision_id=new.id,source_project_id=804,engineering_approval='DISABLED')

class ReactionLink(Strict):
 project_id:int=Field(gt=0)
 model_revision_id:int=Field(gt=0)
 result_id:int=Field(gt=0)
 reviewed_exact_column_and_footing:Literal[True]

class Preview(Strict):
 model_revision_id:int=Field(gt=0)
 inputs:s.Input
 reaction_link:ReactionLink|None=None
class Authorize(Strict):
 proposal_id:int=Field(gt=0)
 proposal_sha256:str=Field(min_length=64,max_length=64)
 authorize_calculation:Literal[True]

def fixture(source):
 return dict(classification='SYNTHETIC_VERIFICATION',profile='IS456-2000-A1A2',jurisdiction='Synthetic local verification; no adopted site jurisdiction',load_standard='MANUALLY_DECLARED_NO_AUTOMATIC_COMBINATIONS',factored_column_kn=source.column_load_kn*1.5,factored_action_source='SYNTHETIC fixture action only: 1.5 times reference for a numerical example. Not an adopted code combination or actual project factored action.',concrete_cylinder_mpa=25,concrete_cube_mpa=25,steel_yield_mpa=500,steel_modulus_mpa=200000,concrete_unit_weight_kn_m3=25,steel_density_kg_m3=7850,cover_mm=75,aggregate_mm=20,east_west=dict(diameter_mm=20,count=8),north_south=dict(diameter_mm=20,count=8),stiffness_kn_m3=20000,undrained_strength_kpa=75,soil_global_factor=3,material_source='Synthetic independently declared cylinder/cube/steel strengths and densities; no material certificates or conversions.',soil_source='Synthetic homogeneous surface phi-zero undrained idealization; no groundwater. Explicit stiffness and strength are independent inputs; no site investigation.',detailing_source='Synthetic uncoated straight deformed uniform bottom mats, East-West below North-South. No hooks, curtailment, laps or dowels.',reviewed_synthetic_patch=True)

def reaction_binding(binding,g,source,link,db,user):
 if link is None:return binding,source
 data=reaction_api.history(link.project_id,link.model_revision_id,db,user)
 record=next((r for r in data['records'] if r['id']==link.result_id),None)
 if not record or record['status']!='VERIFIED_DEMANDS_ONLY':raise HTTPException(409,'Exact current verified transported OpenSees reaction result required')
 saved=db.query(EngineeringAnalysis).filter_by(project_id=link.project_id,id=link.result_id,analysis_type='FOOTING_TRANSPORT_RESULT').first()
 if not saved:raise HTTPException(422,'Reaction link must reference a result, never a proposal')
 matches=[r for r in record['result']['rows'] if r['column_id']==g['column_id'] and r['footing_id']==g['footing_id']]
 if len(matches)!=1:raise HTTPException(422,'Exact saved CAD column and footing identities must match the reaction mapping')
 row=matches[0];ref=row['link'];E,N=g['center_east_north_m']
 if any(abs(a-b)>1e-8 for a,b in zip(ref['column_reference_m'],[E,N,g['column_face_up_m']])) or any(abs(a-b)>1e-8 for a,b in zip(ref['footing_reference_m'],[E,N,g['bearing_up_m']])):raise HTTPException(422,'Current saved geometry and reaction reference planes differ; re-map reactions explicitly')
 if max(map(abs,[*row['horizontal_shear_enu_n'],row['Mx_nm'],row['My_nm'],row['torsion_Mz_nm']]))>1e-7:raise HTTPException(422,'Linked reaction contains shear, moment or torsion outside the concentric uniform-pressure RC profile; retain existing transport evidence without a capacity inference')
 if row['compression_n']<=0:raise HTTPException(422,'Positive service compression required')
 source=demand.Input(**{**source.model_dump(),'column_load_kn':row['compression_n']/1000,'uniform_net_pressure_kpa':row['compression_n']/1000/(source.B_m*source.L_m),'load_source':f'Owned current transported OpenSees support reaction result {link.project_id}/{link.result_id}; foundation action opposite solver reaction. Explicit reviewed exact CAD identity mapping.'})
 return {**binding,'reaction_link':dict(**link.model_dump(),result_sha256=cad.digest(record['result']),source_audit_sha256=cad.digest(record['result']['audit']))},source

def prepare(pid,q,db,user):
 binding,g,source=context(pid,q.model_revision_id,db,user)
 binding,source=reaction_binding(binding,g,source,q.reaction_link,db,user)
 try:computed=s.calculate(q.inputs,g,source)
 except ValueError as e:raise HTTPException(422,str(e)) from e
 return dict(inputs=q.model_dump(),binding=binding,computed=computed,computed_sha256=cad.digest(computed),engineering_approval='DISABLED')

def store(pid,rid,kind,status,body,db,user):
 r=EngineeringAnalysis(project_id=pid,model_revision_id=rid,analysis_type=kind,algorithm_version=s.VERSION,status=status,result_json=body,actor_user_id=user)
 db.add(r);db.commit();db.refresh(r);return dict(id=r.id,type=r.analysis_type,status=status,result=body)

def rows(pid,db):return db.query(EngineeringAnalysis).filter_by(project_id=pid).filter(EngineeringAnalysis.analysis_type.in_([PROPOSAL,RESULT])).order_by(EngineeringAnalysis.id.desc()).all()

def formatted(row,binding,latest):
 body=row.result_json
 current=(cad.digest(body['binding'])==cad.digest(binding) and cad.digest(body['computed'])==body['computed_sha256'] and (row.id==latest if row.analysis_type==PROPOSAL else body['authorized_proposal_id']==latest))
 return dict(id=row.id,type=row.analysis_type,status=row.status if current else 'STALE',result=body)

@router.get('')
def history(project_id:int,model_revision_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding,g,source=context(project_id,model_revision_id,db,user_id);records=rows(project_id,db);latest=next((r.id for r in records if r.analysis_type==PROPOSAL),None)
 out=[]
 for r in records:
  try:
   b,_=reaction_binding(binding,g,source,Preview(**r.result_json['inputs']).reaction_link,db,user_id);out.append(formatted(r,b,latest))
  except (HTTPException,ValueError):out.append(dict(id=r.id,type=r.analysis_type,status='STALE',result=r.result_json))
 return dict(binding=binding,geometry=g,source_service_column_kn=source.column_load_kn,profiles=s.PROFILES,fixture=fixture(source),records=out,engineering_approval='DISABLED')

@router.post('/preview')
def preview(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);lock_project(db,project_id)
 body=prepare(project_id,q,db,user_id);body['proposal_sha256']=cad.digest(body)
 return store(project_id,q.model_revision_id,PROPOSAL,'AWAITING_EXPLICIT_REVIEW',body,db,user_id)

@router.post('/authorize')
def authorize(project_id:int,q:Authorize,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id);lock_project(db,project_id)
 records=rows(project_id,db);latest=next((r for r in records if r.analysis_type==PROPOSAL),None)
 if not latest or latest.id!=q.proposal_id:raise HTTPException(409,'Exact latest proposal required')
 fresh=prepare(project_id,Preview(**latest.result_json['inputs']),db,user_id)
 if cad.digest(fresh)!=q.proposal_sha256 or q.proposal_sha256!=latest.result_json['proposal_sha256']:raise HTTPException(409,'Proposal, source evidence, model or implementation changed; prepare again')
 prior=next((r for r in records if r.analysis_type==RESULT and r.result_json.get('authorized_proposal_id')==latest.id),None)
 if prior:return dict(id=prior.id,type=RESULT,status=prior.status,result=prior.result_json)
 return store(project_id,latest.model_revision_id,RESULT,'REVIEWED_SYNTHETIC_CALCULATION',{**latest.result_json,'authorized_proposal_id':latest.id,'authorization':dict(actor_user_id=user_id,scope='Calculation evidence only; no model change or safety approval')},db,user_id)

@router.post('/alternatives')
def alternatives(project_id:int,q:Preview,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 binding,g,source=context(project_id,q.model_revision_id,db,user_id)
 _,source=reaction_binding(binding,g,source,q.reaction_link,db,user_id)
 try:return s.alternatives(q.inputs,g,source)
 except ValueError as e:raise HTTPException(422,str(e)) from e

@router.get('/report/{result_id}')
def report(project_id:int,result_id:int,db:Session=Depends(get_db),user_id:int=Depends(get_current_user_id)):
 get_owned_project(project_id,db,user_id)
 row=db.query(EngineeringAnalysis).filter_by(project_id=project_id,id=result_id,analysis_type=RESULT).first()
 if not row:raise HTTPException(404,'Owned reviewed result not found')
 state='STALE';reason=''
 try:
  binding,g,source=context(project_id,row.model_revision_id,db,user_id)
  binding,_=reaction_binding(binding,g,source,Preview(**row.result_json['inputs']).reaction_link,db,user_id)
  latest=next((r.id for r in rows(project_id,db) if r.analysis_type==PROPOSAL),None);state=formatted(row,binding,latest)['status']
 except HTTPException as e:reason=str(e.detail)
 body=row.result_json;computed=body['computed']
 def section(title,value):return '<section><h2>'+html.escape(title)+'</h2><pre>'+html.escape(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False))+'</pre></section>'
 content='<!doctype html><html lang="en"><meta charset="utf-8"><title>Foundation calculation evidence</title><style>body{max-width:1000px;margin:2em auto;font:15px system-ui;padding:1em}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}h1{font-size:24px}section{break-inside:avoid}strong{color:#9b2518}@media print{body{margin:0}}</style><h1>Foundation calculation evidence</h1><strong>INCOMPLETE ENGINEERING REVIEW — NOT A SAFETY CERTIFICATE</strong>'
 content+=f'<p>Project {project_id}; result {result_id}; revision {row.model_revision_id}; status {html.escape(state)}. {html.escape(reason)}</p>'
 for title,value in [('Inputs and sources',body['inputs']),('Evidence binding and implementation hashes',body['binding']),('Review authorization',body.get('authorization')),('Actions and assumptions',computed['actions']),('Geometry and static transport',{'geometry':computed['geometry'],'transfer':computed['transfer']}),('Soil pressure and Winkler displacement',computed['contact']),('Bearing strength reference',computed['bearing']),('Unfactored bending',computed['unfactored_bending']),('Factored bending',computed['factored_bending']),('RC strength, reinforcement, detailing and quantities',computed['rc']),('Edition profile and limitations',{'profile':computed['profile'],'limitations':computed['limitations'],'engineering_approval':'DISABLED','actual_foundation_safety':'BLOCKED','computed_sha256':body['computed_sha256']})]:content+=section(title,value)
 content+='<p>Primary requirements: <a href="'+s.ACI+'">ACI published 318-14 footing example</a>; <a href="'+s.IS+'">BIS IS456:2000 scan</a>. Only listed subsets implemented. Independent benchmarks are maintained with the local foundation module tests.</p></html>'
 return Response(content,media_type='text/html',headers={'Content-Disposition':f'attachment; filename="foundation-{project_id}-{result_id}.html"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
