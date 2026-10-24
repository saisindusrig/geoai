from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import bearing_capacity as api
from test_rectangular_bearing import fixture
from test_physical_column import seed

def test_finite_exact_authorization_and_staleness(db_session,monkeypatch):
 seed(db_session);binding={'model_revision_id':1,'finite_formulation_review':{'classification':'SYNTHETIC_VERIFICATION'},'actual_cad_capacity':'BLOCKED'};monkeypatch.setattr(api,'context',lambda *args:deepcopy(binding))
 q=api.Preview(model_revision_id=1,benchmark=fixture());p=api.preview(1,q,db_session,1)
 def auth(proposal,h=None,yes=True):return api.authorize(1,api.Authorize(proposal_id=proposal['id'],proposal_sha256=h or proposal['result']['proposal_sha256'],authorize_synthetic_bearing=yes),db_session,1)
 for h,yes in [('0'*64,True),(None,False)]:
  with pytest.raises(HTTPException):auth(p,h,yes)
 r=auth(p);assert r['result']['computed']['ultimate_gross_kpa']==pytest.approx(308.4955592153876)
 newer=api.preview(1,q,db_session,1)
 with pytest.raises(HTTPException):auth(p)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE'
 binding['source_binding_sha256']='changed'
 with pytest.raises(HTTPException):auth(newer)
 binding.pop('finite_formulation_review')
 with pytest.raises(HTTPException):api.preview(1,q,db_session,1)
