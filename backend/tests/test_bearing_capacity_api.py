from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import bearing_capacity as api
from test_bearing_capacity import fixture
from test_physical_column import seed
def test_exact_authorization_profile_and_model_staleness(db_session,monkeypatch):
 seed(db_session);binding={'model_revision_id':1,'copied_profile_sha256':'source','actual_cad_capacity':'BLOCKED'};monkeypatch.setattr(api,'context',lambda *args:deepcopy(binding));q=api.Preview(model_revision_id=1,benchmark=fixture());p=api.preview(1,q,db_session,1)
 for h,yes in [('0'*64,True),(p['result']['proposal_sha256'],False)]:
  with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=h,authorize_synthetic_bearing=yes),db_session,1)
 auth=api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_synthetic_bearing=True);r=api.authorize(1,auth,db_session,1);assert r['status']=='VERIFIED_SYNTHETIC'
 newer=api.preview(1,q,db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,auth,db_session,1)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE'
 binding['copied_profile_sha256']='changed'
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=newer['id'],proposal_sha256=newer['result']['proposal_sha256'],authorize_synthetic_bearing=True),db_session,1)
 assert all(x['status']=='STALE' for x in api.history(1,1,db_session,1)['records'])
