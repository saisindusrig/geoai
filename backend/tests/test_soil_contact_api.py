from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import soil_contact as api
from test_soil_contact import fixture
from test_physical_column import seed

def test_exact_authorization_and_stale_dependencies(db_session,monkeypatch):
 seed(db_session);binding={'model_revision_id':1,'source_transport_sha256':'original','actual_soil_analysis':'BLOCKED'}
 monkeypatch.setattr(api,'context',lambda *args:deepcopy(binding))
 q=api.Preview(model_revision_id=1,benchmark=fixture());p=api.preview(1,q,db_session,1)
 for h,yes in [('0'*64,True),(p['result']['proposal_sha256'],False)]:
  with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=h,authorize_synthetic_benchmark=yes),db_session,1)
 auth=api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_synthetic_benchmark=True)
 r=api.authorize(1,auth,db_session,1);assert r['status']=='VERIFIED_SYNTHETIC';assert r['result']['computed']['actual_project_analysis']=='BLOCKED'
 api.preview(1,q,db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,auth,db_session,1)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE'
 p=api.preview(1,q,db_session,1);binding['source_transport_sha256']='changed'
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_synthetic_benchmark=True),db_session,1)
 assert all(x['status']=='STALE' for x in api.history(1,1,db_session,1)['records'])
