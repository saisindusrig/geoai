"""Read-only capability consistency against existing validators and history gates."""
from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import analysis_capabilities as cap, physical_frames as physical, spatial_frames as spatial
from app.db.models import ModelRevision, EngineeringAnalysis
from app.services.design import spatial_review, coupled_floor
from test_physical_column import seed
from test_physical_frame import document, inputs

def get(db,selection=''):
 return cap.capabilities(1,1,selection,db,1)

def test_geometry_counts_never_grant_support_and_selection_uses_validator(db_session):
 seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=document(rev.document_json);db_session.commit()
 before=db_session.query(EngineeringAnalysis).count()
 r=get(db_session);assert r['methods']['frame']['status']=='MISSING_INPUTS'
 assert not r['methods']['frame']['can_review']
 r=get(db_session,','.join(c['id'] for c in rev.document_json['components']))
 assert r['methods']['frame']['status']=='MISSING_INPUTS'
 assert 'passes planar inspection' in r['methods']['frame']['reason']
 assert r['methods']['coupled']['status']=='UNSUPPORTED'
 assert r['methods']['foundation']['status']=='UNSUPPORTED'
 assert r['methods']['slab']['status']=='MISSING_INPUTS'
 assert db_session.query(EngineeringAnalysis).count()==before

def test_saved_input_validation_is_reused_and_does_not_execute(db_session,monkeypatch):
 seed(db_session);rev=db_session.get(ModelRevision,1);doc=document(rev.document_json);rev.document_json=doc;db_session.commit()
 physical.inputs(1,physical.Save(model_revision_id=1,**inputs(doc)),db_session,1)
 monkeypatch.setattr(physical.solver,'run',lambda *a:pytest.fail('Capability reads cannot execute'))
 r=get(db_session);assert r['methods']['frame']['status']=='SUPPORTED' and r['methods']['frame']['can_review']
 assert not r['methods']['frame']['current_results']

def test_latest_review_invalidates_old_result_and_history_remains(db_session):
 seed(db_session);doc,q=spatial_review.fixture(1);doc.update(project_id=1,scenario_id=1);db_session.get(ModelRevision,1).document_json=doc;db_session.commit()
 p=spatial.review(1,spatial.Review(model_revision_id=1,inputs=q),db_session,1)
 body=dict(proposal_id=p['id'],model_document_sha256=p['result']['model_document_sha256'],cases=[dict(status='VERIFIED',case={'name':'Gravity'})])
 old=spatial.record(1,1,spatial.RUN,'VERIFIED',body,db_session,1)
 r=get(db_session)['methods']['spatial'];assert [x['id'] for x in r['current_results']]==[old.id],r
 assert r['current_results'][0]['load_cases']==['Gravity']
 second=spatial.record(1,1,spatial.RUN,'VERIFIED',{**body,'cases':[dict(status='VERIFIED',case={'name':'Lateral'})]},db_session,1)
 current=get(db_session)['methods']['spatial']['current_results']
 assert {r['id']:r['load_cases'] for r in current}=={old.id:['Gravity'],second.id:['Lateral']}
 spatial.review(1,spatial.Review(model_revision_id=1,inputs=q),db_session,1)
 r=get(db_session)['methods']['spatial'];assert r['status']=='STALE' and r['can_review']
 assert not r['current_results'] and {h['id'] for h in r['history']}=={old.id,second.id} and all(not h['current'] for h in r['history'])

def test_failed_and_unverified_child_cases_never_current(db_session):
 seed(db_session);doc,q=spatial_review.fixture(1);doc.update(project_id=1,scenario_id=1);db_session.get(ModelRevision,1).document_json=doc;db_session.commit()
 p=spatial.review(1,spatial.Review(model_revision_id=1,inputs=q),db_session,1)
 for status,child in [('VERIFICATION_FAILED','VERIFIED'),('VERIFIED','VERIFICATION_FAILED')]:
  spatial.record(1,1,spatial.RUN,status,dict(proposal_id=p['id'],model_document_sha256=p['result']['model_document_sha256'],cases=[dict(status=child,case={'name':'Gravity'})]),db_session,1)
 assert not get(db_session)['methods']['spatial']['current_results']

def test_old_revision_and_foreign_ownership_fail_closed(db_session):
 seed(db_session);old=db_session.get(ModelRevision,1)
 db_session.add(ModelRevision(project_id=1,design_scenario_id=1,revision_number=2,document_json=old.document_json,source='manual_edit',user_id=1));db_session.commit()
 r=get(db_session);assert all(m['status']=='STALE' and not m['can_review'] for m in r['methods'].values())
 with pytest.raises(HTTPException):cap.capabilities(1,1,'',db_session,99)
 with pytest.raises(HTTPException):cap.capabilities(1,999,'',db_session,1)

def test_synthetic_marker_alone_cannot_enable_shell_or_spatial(db_session):
 seed(db_session);rev=db_session.get(ModelRevision,1);doc=deepcopy(rev.document_json);doc['metadata']['coupled_floor_review']={'mesh':16};doc['metadata']['spatial_frame_review']={'input':{}};rev.document_json=doc;db_session.commit()
 r=get(db_session);assert not r['methods']['coupled']['can_review'] and not r['methods']['spatial']['can_review']
 assert not r['methods']['coupled']['current_results']

def test_exact_coupled_fixture_validator_reused_without_solve(db_session,monkeypatch):
 seed(db_session);doc=coupled_floor.fixture();doc.update(project_id=1,scenario_id=1);db_session.get(ModelRevision,1).document_json=doc;db_session.commit()
 monkeypatch.setattr(coupled_floor,'validated_run',lambda:pytest.fail('No solver from capability reads'))
 r=get(db_session)['methods']['coupled'];assert r['status']=='SUPPORTED' and r['can_review'] and not r['current_results']

def test_case_names_and_distinct_same_method_results():
 assert cap.case_names({'case_name':'Main','load_case_results':[{'case_name':'Wind'},{'case_name':'Main'}]})==['Main','Wind']
 assert cap.case_names({'computed':{}})==['Saved foundation actions']
 assert cap.case_names({'cases':[{'status':'FAILED','case':{'name':'Bad'}}]})==[]
