from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import soil_profile as api
from app.services.design.elastic_settlement import Profile
from test_elastic_settlement import fixture_profile,fixture_load
from test_physical_column import seed

def setup(db,monkeypatch):
 seed(db);binding={'model_revision_id':1,'source_transport_sha256':'source','actual_soil_analysis':'BLOCKED'}
 monkeypatch.setattr(api,'context',lambda *args:deepcopy(binding));return binding

def test_profile_versions_authorization_and_staleness(db_session,monkeypatch):
 binding=setup(db_session,monkeypatch);profile=Profile(**fixture_profile())
 saved=api.save(1,api.Save(model_revision_id=1,profile=profile),db_session,1)
 with pytest.raises(HTTPException):api.save(1,api.Save(model_revision_id=1,profile=profile),db_session,1)
 q=api.Preview(model_revision_id=1,profile_id=saved['id'],load=fixture_load());p=api.preview(1,q,db_session,1)
 for h,consent in [('0'*64,True),(p['result']['proposal_sha256'],False)]:
  with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=h,authorize_synthetic_settlement=consent),db_session,1)
 auth=api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_synthetic_settlement=True)
 r=api.authorize(1,auth,db_session,1);assert r['result']['computed']['winkler_displacement']=='NOT_USED_OR_ADDED'
 newer=api.preview(1,q,db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,auth,db_session,1)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE'
 api.save(1,api.Save(model_revision_id=1,base_profile_id=saved['id'],profile=profile),db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=newer['id'],proposal_sha256=newer['result']['proposal_sha256'],authorize_synthetic_settlement=True),db_session,1)
 binding['source_transport_sha256']='changed'
 assert all(x['status']=='STALE' for x in api.history(1,1,db_session,1)['records'])

@pytest.mark.parametrize('bad',['actual','finite','missing_E','wrong_plane','unknown'])
def test_saved_profile_does_not_imply_supported_calculation(db_session,monkeypatch,bad):
 setup(db_session,monkeypatch);p=fixture_profile();load=fixture_load()
 if bad=='actual':
  p['classification']='REAL_PROJECT';p['layers'][0]['extent_kind']='ENGINEER_ASSUMED'
  for key in ['E_mpa','poisson','unit_weight_kn_m3']:p['layers'][0][key]['kind']='ENGINEER_ASSUMED'
 if bad=='finite':p['layers'][0].update(extent='FINITE',bottom_depth_m=5)
 if bad=='unknown':p['layers'][0]['extent']='UNKNOWN'
 if bad=='missing_E':p['layers'][0]['E_mpa']=None
 if bad=='wrong_plane':load=fixture_load(reference_up_m=-.45)
 saved=api.save(1,api.Save(model_revision_id=1,profile=Profile(**p)),db_session,1)
 assert saved['status']=='SAVED_UNAPPROVED';assert saved['result']['actual_soil_analysis']=='BLOCKED'
 with pytest.raises(HTTPException):api.preview(1,api.Preview(model_revision_id=1,profile_id=saved['id'],load=load),db_session,1)
