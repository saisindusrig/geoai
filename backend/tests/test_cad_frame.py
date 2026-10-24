from copy import deepcopy
import asyncio,json
from pathlib import Path
import pytest
from fastapi import HTTPException
from app.services.design import cad_frame as cad,physical_frame as frame,drawing_cad as drawing
from app.api.routes import physical_frames as route,cad_frames as api,engineering_study as study
from app.db.models import ModelRevision,EngineeringAnalysis
from test_drawing_cad import build,fixture
from test_physical_column import seed
from test_drawing_strength import source,correction,FILE

IDS=['drawing-cad:614f117ae2a74794:'+h for h in ['9C','96','AE']]
def documents():
 resolved=build()['proposed_document'];q=fixture()
 for i in q['items']:i['operation']='update_generated'
 q['items'][0]['top_mm']=3260
 tall=build(q,resolved)['proposed_document'];return tall,resolved
def inputs(d):
 g=frame.geometry(d,IDS,allow_rigid_offsets=True)
 return dict(component_ids=IDS,sections=[dict(component_id=m['component_id'],shape='solid_rectangle',elastic_modulus_pa=200e9,area_m2=m['solid_rectangle_area_m2'],inertia_m4=m['solid_rectangle_inertia_m4'],material_name='Synthetic solid rectangular steel',material_source='Explicit synthetic 200 GPa elastic assumption, not manufacturer/project data',section_source='Explicit synthetic solid rectangle; nominal envelope alone does not establish a steel section') for m in g['members']],connections=[dict(**j,behavior='rigid_offset',offset_m=g['connection_offsets'][i]['offset_m'],idealization_approved=True,source='Explicit short massless planar rigid arm verification only; no capacity') for i,j in enumerate(g['candidate_joints'])],supports='both_column_bases_fixed',support_source='Explicit synthetic fixed bases; no footing stiffness assumed',load_pattern='equal_horizontal_column_head_loads',load_n=20000,load_source='Synthetic verification total 20 kN East; equal 10 kN at each head',purpose='VERIFICATION_ONLY',elements_per_member=2,units='SI')
def hand():
 # Independent symmetry/strain-energy condensation; no global stiffness/solver functions.
 # q=(u,v,theta), head displacements [u,-v,theta] / [u,v,theta].
 # U=12EIc/H³ u²+12EIc/H² uθ+4EIc/H θ²+EAc/H v²
 #   +6EIb/ell³(2v-B theta)². B=column span=5.7; ell=physical beam length=6.
 E,Ac,Ic,Ib,H,B,ell,P=200e9,.09,.000675,.00045,3.2,5.7,6.,20000.
 a=24*E*Ic/H**3;b=12*E*Ic/H**2;c=2*E*Ac/H+48*E*Ib/ell**3;d=-24*E*Ib*B/ell**3;f=8*E*Ic/H+12*E*Ib*B**2/ell**3
 effective=f-d*d/c;u=P/(a-b*b/effective);theta=-b*u/effective;v=-d*theta/c
 ry=E*Ac/H*v;moment=6*E*Ic/H**2*u+2*E*Ic/H*theta
 yleft=-v-.15*theta;yright=v+.15*theta
 beam_shear=12*E*Ib/ell**3*(yleft-yright)+12*E*Ib/ell**2*theta
 beam_end_moment=6*E*Ib/ell**2*(yleft-yright)+6*E*Ib/ell*theta
 return dict(left=[u,-v,theta],right=[u,v,theta],left_reaction=[-P/2,ry,moment],right_reaction=[-P/2,-ry,moment],beam_local_left_shear_n=beam_shear,beam_local_end_moment_nm=beam_end_moment,beam_internal_start_moment_nm=-beam_end_moment,beam_internal_end_moment_nm=beam_end_moment,rigid_offset_couple_nm=-.15*beam_shear,moment_equilibrium_nm=2*moment-B*ry-P*H,method='Independent three-DOF symmetric strain energy; actual 6 m elastic beam, 5.7 m column span and explicit ±0.15 m arms. Equal horizontal load gives zero beam axial force, so common 0.05 m vertical offsets do not contribute axial work. End force/diagram checks use the separately substituted Euler-Bernoulli end-force formulas. Not valid for arbitrary loading.')
def test_audit_preserves_original_unequal_heights_and_blocks():
 tall,resolved=documents();before=deepcopy(tall);r=cad.audit(tall,IDS)
 assert r['status'].startswith('BLOCKED');assert r['column_top_difference_m']==pytest.approx(.06);assert r['observed_connections'][0]['offset_enu_m']==pytest.approx([-.15,0,-.01]);assert r['observed_connections'][1]['offset_enu_m']==pytest.approx([.15,0,.05]);assert tall==before
 with pytest.raises(ValueError):frame.geometry(tall,IDS,allow_rigid_offsets=True)
 assert cad.audit(resolved,IDS)['status']=='GEOMETRY_CANDIDATE_EXPLICIT_INPUTS_REQUIRED'
@pytest.mark.parametrize('bad',['source_id','component_id','hash','geometry','classification','generator','slab','missing','duplicate'])
def test_source_identity_and_geometry_rejection(bad):
 _,d=documents();c=next(c for c in d['components'] if c['id']==IDS[0]);ids=IDS.copy();m=c['metadata']['drawing_cad']
 if bad=='source_id':m['source_entity_id']='fake'
 if bad=='component_id':c['id']='drawing-cad:fake';ids[0]=c['id']
 if bad=='hash':m['component_sha256']='0'*64
 if bad=='geometry':c['geometry']['size'][2]+=1
 if bad=='classification':m['classification']='REAL_PROJECT'
 if bad=='generator':m['generator']='unknown'
 if bad=='slab':ids[0]='drawing-cad:614f117ae2a74794:95'
 if bad=='missing':ids[0]='missing'
 if bad=='duplicate':ids[0]=ids[1]
 with pytest.raises(ValueError):cad.audit(d,ids)
@pytest.mark.parametrize('bad',['E','A','I','load','support','joint','offset','unapproved','missing_source','arbitrary'])
def test_explicit_analytical_input_rejections(bad):
 _,d=documents();q=inputs(d)
 if bad=='E':q['sections'][0]['elastic_modulus_pa']=0
 if bad=='A':q['sections'][0]['area_m2']=.001
 if bad=='I':q['sections'][0]['inertia_m4']=.000001
 if bad=='load':q.pop('load_n')
 if bad=='support':q['supports']='soil'
 if bad=='joint':q['connections'][0]['behavior']='rigid'
 if bad=='offset':q['connections'][0]['offset_m'][1]+=.001
 if bad=='unapproved':q['connections'][0]['idealization_approved']=False
 if bad=='missing_source':q['sections'][0]['material_source']=''
 if bad=='arbitrary':q['solver_script']='arbitrary'
 with pytest.raises(ValueError):frame.graph(d,q)
def test_real_solver_hand_equilibrium_mesh_units_load_scale_material():
 _,d=documents();q=inputs(d);h=hand();results=[]
 for n in [1,2,4]:
  r=frame.run({**q,'elements_per_member':n},d);assert r['status']=='VERIFIED';assert max(map(abs,r['equilibrium_residual_si']))<1e-4;assert {e['component_id'] for e in r['elements']}==set(IDS)
  assert all(c['passed'] for c in r['comparisons'].values());assert all(m['cad_source']['source_entity_id'].startswith('dxf:') for m in r['physical_to_analytical_graph']['members'])
  assert next(n for n in r['nodes'] if n['id']==2)['displacement_m']==pytest.approx(h['left'],abs=1e-10)
  beam=[e for e in r['elements'] if e['component_id']==IDS[1]]
  assert beam[0]['local_end_forces_si'][1]==pytest.approx(h['beam_local_left_shear_n'],abs=1e-6)
  assert beam[0]['local_end_forces_si'][2]==pytest.approx(h['beam_local_end_moment_nm'],abs=1e-6)
  assert beam[0]['samples'][0]['moment_nm']==pytest.approx(h['beam_internal_start_moment_nm'],abs=1e-6)
  assert beam[-1]['samples'][-1]['moment_nm']==pytest.approx(h['beam_internal_end_moment_nm'],abs=1e-6)
  assert all(t['offset_moment_nm']==pytest.approx(h['rigid_offset_couple_nm'],abs=1e-6) for t in r['rigid_offset_transfers'])
  for a,e in zip(r['reactions'],[h['left_reaction'],h['right_reaction']]):assert [a['fx_n'],a['fy_n'],a['moment_nm']]==pytest.approx(e,abs=1e-6)
  results.append(r)
 tip=lambda r:next(n for n in r['nodes'] if n['id']==2)['displacement_m']
 assert tip(frame.run({**q,'units':'N-mm'},d))==pytest.approx(tip(results[0]),abs=1e-10)
 assert tip(frame.run({**q,'load_n':10000},d))==pytest.approx([v*.5 for v in tip(results[0])],abs=1e-10)
 softer=deepcopy(q)
 for s in softer['sections']:s['elastic_modulus_pa']/=2
 assert tip(frame.run(softer,d))==pytest.approx([v*2 for v in tip(results[0])],abs=1e-10)
 assert abs(h['moment_equilibrium_nm'])<1e-8
def test_source_review_staleness_missing_properties_and_authorization(db_session,tmp_path,monkeypatch):
 db=db_session;seed(db);rev=db.get(ModelRevision,1);_,d=documents();d['metadata']['drawing_review']={'classification':'SYNTHETIC_VERIFICATION'};d['metadata']['cad_frame_review']={'source_project_id':789};rev.document_json=d;db.commit()
 monkeypatch.setattr(study,'ROOT',tmp_path);p=tmp_path/'1';p.mkdir();s=source();file=p/(s['source_sha256']+'.dxf');file.write_bytes(FILE.read_bytes());src=study.record(1,rev,study.SOURCE,'REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL',s,db,1);review=study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1)
 q=inputs(d);prepare=lambda:asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,component_ids=IDS,provider='mock',model='zai-org/GLM-5.3-Flash',allow_rigid_offsets=True),db,1))
 prop=prepare();assert prop['status']=='NEEDS_INPUT';assert prop['result']['cad_source_provenance']['source_reference_id']==src.id
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_solver=True),db,1)
 inp=route.inputs(1,route.Save(model_revision_id=1,**q),db,1);prop=prepare();assert prop['status']=='AWAITING_AUTHORIZATION'
 result=route.run(1,route.Authorize(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_solver=True),db,1);assert result['status']=='VERIFIED'
 explanation=asyncio.run(route.explain(1,prop['id'],db,1));assert explanation['result']['usage']['mock']
 file.write_bytes(file.read_bytes()+b'\n');assert route.out(db.get(EngineeringAnalysis,prop['id']),db,1)['status']=='STALE';assert route.out(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='STALE';assert route.out(db.get(EngineeringAnalysis,explanation['id']),db,1)['status']=='STALE'
 file.write_bytes(FILE.read_bytes());assert route.out(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='VERIFIED'
 study.record(1,rev,study.REVIEW,'REVIEWED_REFERENCE_ANALYSIS_BLOCKED',dict(inputs=correction(),source_reference_id=src.id),db,1);assert route.out(db.get(EngineeringAnalysis,inp['id']),db,1)['status']=='STALE';assert route.out(db.get(EngineeringAnalysis,result['id']),db,1)['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=prop['id'],proposal_sha256=prop['result']['proposal_sha256'],authorize_solver=True),db,1)
 assert review.result_json['inputs']==correction()
