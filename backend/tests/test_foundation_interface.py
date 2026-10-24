import json,math
from pathlib import Path
from copy import deepcopy
import pytest
from app.services.design import foundation_interface as f,opensees_benchmark as common

ROOT=Path(__file__).resolve().parents[2]
def document():return json.loads((ROOT/'docs/foundation-interface/source-geometry.json').read_text(encoding='utf-8'))
def source():return json.loads((ROOT/'docs/foundation-interface/source-solver-evidence.json').read_text(encoding='utf-8'))
def fixture():
 d=document();col=next(c for c in d['components'] if c['name']=='column-sw');plate=next(c for c in d['components'] if c['category']=='base_plate' and c['parent_id']==col['id']);foot=next(c for c in d['components'] if c['category']=='foundation' and c['parent_id']==col['id']);x,y,_=col['transform']['position']
 return dict(column_id=col['id'],plate_id=plate['id'],footing_id=foot['id'],source_analysis_id=301,source_beam_id='industrial-platform-5x3:beam-south',plate_dimensions_m=[.65,.65,.025],footing_dimensions_m=[1.2,1.2,.45],dimension_source='Explicit saved conceptual geometry review',steel=dict(material_name='Synthetic steel',elastic_modulus_pa=200e9,yield_strength_mpa=250,source='Synthetic properties; not used for capacity'),concrete=dict(strength_mpa=30,strength_basis='cylinder',source='Synthetic cylinder strength, capacity excluded'),reinforcement=dict(status='not_defined_capacity_excluded',information='No reinforcement bars saved, capacity excluded',source='Synthetic explicit exclusion'),soil=dict(status='not_defined_soil_analysis_excluded',assumptions='No soil data, no soil capacity or settlement calculation',source='Synthetic explicit exclusion'),anchors=dict(status='synthetic_engineer_declared_unverified',information='New synthetic locations only; no original anchors, capacity unverified',items=[dict(id=f'anchor-{i}',position_enu_m=[x+dx,y+dy,0],diameter_m=.02,embedment_m=.3,source='Synthetic declared geometry only') for i,(dx,dy) in enumerate([(-.24,-.24),(-.24,.24),(.24,-.24),(.24,.24)])]),contact_assumption='concentric_full_contact_massless_rigid_plate',contact_source='Synthetic nominal full rigid contact; no bearing capacity check',demand_scope='explicit_axial_component_only',excluded_shear_moment_acknowledged=True,rigid_plate_idealization_approved=True,geometry_reviewed=True,purpose='SYNTHETIC_VERIFICATION_ONLY')
def prepared(q=None,d=None):
 q=q or fixture();d=d or document();return f.prepare(d,q,f.demands(source(),q['source_beam_id'],q['column_id']))

def test_source_actual_geometry_and_signed_demand():
 p=prepared();assert all(x['definition']=='CONCEPTUAL_PLACEHOLDER' for x in p['geometry']['objects']);assert p['geometry']['saved_anchor_ids']==[]
 a=p['demand'];assert a['compression_n']==pytest.approx(30000);assert a['horizontal_shear_east_n']==pytest.approx(-10765.080571577306);assert a['moment_about_negative_north_nm']==pytest.approx(11753.693592818216)
 assert a['demand_on_interface_enu_force_n']==pytest.approx([-10765.080571577306,0,-30000]);assert a['demand_on_interface_enu_moment_nm']==pytest.approx([0,-11753.693592818216,0])
 assert p['scope'].startswith('Isolated axial');assert all(x['status']=='NOT_YET_VERIFIED' for x in p['unsupported'])

def test_known_answer_units_integration_and_scaling():
 r=f.benchmark();assert r['status']=='VERIFIED';assert r['result']['pressure_kpa']==500;assert r['result']['pressure_mpa']==.5
 p=f.calculate(prepared());b=p['bearing'];assert b['pressure_kpa']==pytest.approx(71.00591715976331);assert b['area_m2']==pytest.approx(.4225);assert b['pressure_mpa']==pytest.approx(.07100591715976331);assert abs(b['equilibrium_error_n'])<1e-8
 assert f.pressure(15000,.65,.65)['pressure_pa']==pytest.approx(b['pressure_pa']/2)
 assert f.pressure(30000,650/1000,650/1000)==f.pressure(30000,.65,.65)
 assert p['full_connection_status']=='NOT_YET_VERIFIED';assert p['engineering_approval']=='DISABLED';assert not p['concrete_strength_used_in_calculation']

def test_zero_shear_moment_full_reaction_concentric_case():
 q=fixture();q['demand_scope']='full_reaction_concentric_only';q['excluded_shear_moment_acknowledged']=False;a=f.demands(source(),q['source_beam_id'],q['column_id']);a['horizontal_shear_east_n']=0;a['moment_about_negative_north_nm']=0
 p=f.calculate(f.prepare(document(),q,a));assert p['bearing']['pressure_kpa']==pytest.approx(71.00591715976331)

@pytest.mark.parametrize('bad',['missing_steel','missing_concrete','strength_basis','soil','reinforcement','anchor_status','anchor_position','anchor_diameter','embedment','anchor_overlap','anchor_column','nan','uplift','moment_full','ack','approval','dimensions','missing_object','reference','gap','eccentric','rotation','opening','unknown_units','arbitrary_code'])
def test_missing_and_unsupported(bad):
 q=fixture();d=document();by={c['id']:c for c in d['components']};a=f.demands(source(),q['source_beam_id'],q['column_id'])
 if bad=='missing_steel':q.pop('steel')
 if bad=='missing_concrete':q['concrete']['strength_mpa']=0
 if bad=='strength_basis':q['concrete'].pop('strength_basis')
 if bad=='soil':q['soil']['assumptions']=''
 if bad=='reinforcement':q.pop('reinforcement')
 if bad=='anchor_status':q['anchors']['status']='not_defined_anchor_analysis_excluded'
 if bad=='anchor_position':q['anchors']['items'][0]['position_enu_m'][0]+=1
 if bad=='anchor_diameter':q['anchors']['items'][0]['diameter_m']=0
 if bad=='embedment':q['anchors']['items'][0]['embedment_m']=1
 if bad=='anchor_overlap':q['anchors']['items'][1]['position_enu_m']=q['anchors']['items'][0]['position_enu_m'][:]
 if bad=='anchor_column':q['anchors']['items'][0]['position_enu_m'][:2]=by[q['column_id']]['transform']['position'][:2]
 if bad=='nan':q['steel']['elastic_modulus_pa']=float('nan')
 if bad=='uplift':a['compression_n']=-30
 if bad=='moment_full':q['demand_scope']='full_reaction_concentric_only'
 if bad=='ack':q['excluded_shear_moment_acknowledged']=False
 if bad=='approval':q['rigid_plate_idealization_approved']=False
 if bad=='dimensions':q['plate_dimensions_m'][0]=.7
 if bad=='missing_object':q['footing_id']='absent'
 if bad=='reference':by[q['plate_id']]['metadata']['references']=[]
 if bad=='gap':by[q['footing_id']]['transform']['position'][2]-=.02
 if bad=='eccentric':by[q['plate_id']]['transform']['position'][0]+=.01
 if bad=='rotation':by[q['plate_id']]['transform']['rotation_deg'][2]=1
 if bad=='opening':by[q['plate_id']]['geometry']['holes']=[{'radius':.01}]
 if bad=='unknown_units':d['units']='imperial'
 if bad=='arbitrary_code':q['solver_script']='danger'
 with pytest.raises((ValueError,KeyError,TypeError)):f.prepare(d,q,a)

@pytest.mark.parametrize('values',[(0,.5,.4),(-1,.5,.4),(100000,0,.4),(100000,.5,float('nan'))])
def test_invalid_pressure_inputs(values):
 with pytest.raises(ValueError):f.pressure(*values)

@pytest.mark.parametrize('method',['compression','contact'])
def test_authorization_source_staleness_and_history(db_session,method):
 from test_physical_column import seed
 from app.db.models import ModelRevision,EngineeringAnalysis
 from app.api.routes import foundation_interfaces as api,slab_transfers
 from fastapi import HTTPException
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=document();db_session.commit();s=source();s.update(model_revision_id=1,scenario_id=rev.design_scenario_id,model_document_sha256=common.digest(rev.document_json))
 i=EngineeringAnalysis(project_id=1,model_revision_id=1,analysis_type=slab_transfers.INPUT,algorithm_version='test',status='SOLVER_COMPLETED',result_json=dict(inputs=s['inputs'],scenario_id=rev.design_scenario_id,model_document_sha256=s['model_document_sha256']),actor_user_id=1);db_session.add(i);db_session.flush();s['input_record_id']=i.id
 src=EngineeringAnalysis(project_id=1,model_revision_id=1,analysis_type=slab_transfers.RUN,algorithm_version='test',status='VERIFIED',result_json=s,actor_user_id=1);db_session.add(src);db_session.commit();q=fixture();q['source_analysis_id']=src.id
 if method=='contact':q.update(demand_scope='actual_N_M_contact_feasibility',contact_assumption='rigid_plate_contact_feasibility',contact_reference_assumption='column_base_N_M_only_no_shear_translation')
 row=api.save(1,api.Save(**q,model_revision_id=1),db_session,1)
 with pytest.raises(HTTPException):api.run(1,api.Authorize(input_id=row['id'],input_sha256='0'*64,authorize_calculation=True),db_session,1)
 r=api.run(1,api.Authorize(input_id=row['id'],input_sha256=row['result']['input_sha256'],authorize_calculation=True),db_session,1);assert r['status']==('VERIFIED_CONTACT_FEASIBILITY_ONLY' if method=='contact' else 'VERIFIED_COMPRESSION_IDEALIZATION_ONLY')
 with pytest.raises(HTTPException):api.evidence(2,r['id'],db_session,1)
 before=deepcopy(src.result_json);api.history(1,db_session,1);assert src.result_json==before
 q['steel']['yield_strength_mpa']=275;api.save(1,api.Save(**q,model_revision_id=1,base_input_id=row['id']),db_session,1);assert api.output(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
 # Changing source engineering inputs invalidates downstream evidence even with identical geometry.
 db_session.add(EngineeringAnalysis(project_id=1,model_revision_id=1,analysis_type=slab_transfers.INPUT,algorithm_version='test',status='AWAITING_AUTHORIZATION',result_json=i.result_json,actor_user_id=1));db_session.commit()
 with pytest.raises(HTTPException):api.source(src.id,db_session,1)
 assert api.output(db_session.get(EngineeringAnalysis,r['id']),db_session,1)['status']=='STALE'
