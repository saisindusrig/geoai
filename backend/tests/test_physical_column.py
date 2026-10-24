from copy import deepcopy
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.routes import physical_columns as route
from app.db.models import User,Project,DesignScenario,ModelRevision,EngineeringAnalysis
from app.services.design import physical_column as physical,opensees_benchmark as solver

ID='industrial-platform-5x3:column-ne'


def doc():
    return json.loads((Path(__file__).parent/'fixtures/platform_attachments.json').read_text(encoding='utf-8'))


def inputs():
    return dict(purpose='VERIFICATION_ONLY',material_name='Verification elastic steel',material_source='Explicit synthetic E for verification only',
        elastic_modulus_pa=200e9,section_kind='solid_rectangle',section_width_m=.3,section_depth_m=.3,
        section_source='Explicit solid rectangle matching saved envelope for verification',compression_n=100000,
        load_source='Centered synthetic compression for verification',support_kind='axial_linear_spring',
        support_stiffness_n_per_m=100e6,support_source='Prescribed synthetic spring; not soil data',isolated_axial_only=True,
        elements=2,solver_units='SI')


def seed(db):
    d=doc()
    db.add(User(id=1,name='Reviewer',email='physical-column@example.com',role='admin',plan='admin'))
    db.add(Project(id=1,user_id=1,name='Physical column',project_type=d['project_type']))
    db.add(DesignScenario(id=1,project_id=1,name='Saved platform',status='completed'))
    db.add(ModelRevision(id=1,project_id=1,design_scenario_id=1,revision_number=1,document_json=d,source='import',user_id=1))
    db.commit()
    return d


@pytest.fixture(autouse=True)
def artifacts(tmp_path,monkeypatch):
    monkeypatch.setattr(solver,'ARTIFACTS',tmp_path)


def test_geometry_identity_length_orientation_and_rotated_section():
    d=doc();c=next(c for c in d['components'] if c['id']==ID)
    c['transform']['rotation_deg'][2]=37
    before=deepcopy(d);g=physical.geometry(d,ID)
    assert g['length_m']==pytest.approx(2.6)
    assert g['axis_enu']==[0,0,1] and g['rotation_deg']==[0,0,37]
    assert g['head_enu_m'][2]-g['base_enu_m'][2]==pytest.approx(2.6)
    assert g['component_id']==ID and len(g['excluded_component_ids'])==41
    assert d==before


@pytest.mark.parametrize('change',['tilt','scale','not_column','not_box','nan','parent','duplicate','units','missing'])
def test_unsupported_or_invalid_saved_geometry(change):
    d=doc();c=next(c for c in d['components'] if c['id']==ID)
    if change=='tilt':c['transform']['rotation_deg'][0]=10
    if change=='scale':c['transform']['scale'][2]=2
    if change=='not_column':c['category']='beam'
    if change=='not_box':c['geometry']['kind']='cylinder'
    if change=='nan':c['geometry']['size'][2]=float('nan')
    if change=='parent':c['parent_id']='some-parent'
    if change=='duplicate':d['components'].append(deepcopy(c))
    if change=='units':d['units']='imperial'
    if change=='missing':d['components'].remove(c)
    with pytest.raises(ValueError):physical.geometry(d,ID)


def test_section_must_match_and_large_displacement_is_unsupported():
    g=physical.geometry(doc(),ID);i=inputs();i['section_width_m']=.2
    with pytest.raises(ValueError,match='match'):physical.parameters(g,i)
    i=inputs();i['support_stiffness_n_per_m']=1
    with pytest.raises(ValueError,match='small-displacement'):physical.parameters(g,i)


@pytest.mark.parametrize('segments,units,load',[(1,'SI',100000),(2,'SI',100000),(4,'SI',100000),(2,'N-mm',100000),(2,'SI',50000),(2,'SI',200000)])
def test_real_saved_geometry_solver_matches_independent_mechanics(segments,units,load):
    g=physical.geometry(doc(),ID);i=inputs();i.update(elements=segments,solver_units=units,compression_n=load)
    result=physical.run(g,i)
    assert result['status']=='VERIFIED',result.get('error')
    expected_shortening=load*2.6/(200e9*.09)
    assert result['values_si']['column_shortening_m']==pytest.approx(expected_shortening,rel=1e-6)
    assert result['values_si']['total_displacement_m']==pytest.approx(expected_shortening+load/100e6,rel=1e-6)
    assert result['values_si']['compression_stress_pa']==pytest.approx(load/.09,rel=1e-6)
    assert result['values_si']['reaction_n']==pytest.approx(load,rel=1e-6)
    assert result['independent_reference']['shortening_m']==pytest.approx(expected_shortening,rel=1e-6)
    assert all(row['component_id']==ID for row in result['analytical_mapping'])
    assert result['analytical_mapping'][-1]['position_enu_m']==pytest.approx(g['head_enu_m'])
    assert result['engineering_approval']=='DISABLED' and result['code_checks']=='DISABLED'


@pytest.mark.parametrize('change',[{'material_name':''},{'elastic_modulus_pa':None},{'compression_n':0},{'support_stiffness_n_per_m':-1},
    {'section_kind':'I-section'},{'isolated_axial_only':False},{'purpose':''},{'load_source':' '},{'elastic_modulus_pa':float('inf')},{'length_m':3}])
def test_explicit_required_supported_inputs(change):
    p=inputs();p.update(change)
    with pytest.raises(ValidationError):route.Input(model_revision_id=1,component_id=ID,**p)


def test_api_immutable_input_revisions_material_load_staleness_and_geometry(db_session):
    original=seed(db_session)
    data=route.history(1,1,ID,db_session,1)
    assert data['latest_input'] is None and data['analyses']==[]
    with pytest.raises(HTTPException) as exc:route.run(1,route.Run(model_revision_id=1,component_id=ID,input_record_id=123),db_session,1)
    assert exc.value.status_code==409
    first=route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,**inputs()),db_session,1)
    result=route.run(1,route.Run(model_revision_id=1,component_id=ID,input_record_id=first['id']),db_session,1)
    assert result['status']=='VERIFIED' and result['result']['physical_component']['length_m']==pytest.approx(2.6)
    assert route.history(1,1,ID,db_session,1)['analyses'][0]['status']=='VERIFIED'
    new_inputs=inputs();new_inputs['elastic_modulus_pa']=190e9
    second=route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,base_input_id=first['id'],**new_inputs),db_session,1)
    assert second['id']!=first['id']
    assert route.history(1,1,ID,db_session,1)['analyses'][0]['status']=='STALE'
    assert db_session.get(EngineeringAnalysis,first['id']).result_json['engineering_inputs']==inputs()
    with pytest.raises(HTTPException) as exc:route.run(1,route.Run(model_revision_id=1,component_id=ID,input_record_id=first['id']),db_session,1)
    assert exc.value.status_code==409
    current=route.run(1,route.Run(model_revision_id=1,component_id=ID,input_record_id=second['id']),db_session,1)
    new_inputs['compression_n']=50000
    third=route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,base_input_id=second['id'],**new_inputs),db_session,1)
    assert route.history(1,1,ID,db_session,1)['analyses'][0]['status']=='STALE'
    assert 'model BasicBuilder' in route.artifact(1,current['id'],'model.tcl',db_session,1)['contents']
    with pytest.raises(HTTPException):route.artifact(1,current['id'],'unknown.txt',db_session,1)
    with pytest.raises(HTTPException):route.history(1,1,ID,db_session,99)
    assert db_session.get(ModelRevision,1).document_json==original
    # A newer unchanged geometry revision still requires an explicit new association.
    db_session.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json=deepcopy(original),source='manual_edit',user_id=1));db_session.commit()
    assert route.history(1,2,ID,db_session,1)['latest_input']['status']=='STALE'
    assert route.history(1,2,ID,db_session,1)['analyses'][0]['status']=='STALE'
    with pytest.raises(HTTPException):route.run(1,route.Run(model_revision_id=2,component_id=ID,input_record_id=third['id']),db_session,1)


def test_geometry_and_input_conflicts_block_run(db_session):
    seed(db_session)
    p=inputs();p['section_depth_m']=.4
    with pytest.raises(HTTPException) as exc:route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,**p),db_session,1)
    assert exc.value.status_code==422
    p=inputs();saved=route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,**p),db_session,1)
    with pytest.raises(HTTPException) as exc:route.save_inputs(1,route.Input(model_revision_id=1,component_id=ID,**p),db_session,1)
    assert exc.value.status_code==409
    assert saved['status']=='INPUT_READY'
