from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import rc_flexure as api
from test_physical_column import seed
from test_rc_flexure import fixture

def test_authorization_identity_immutability_and_staleness(db_session,monkeypatch):
 seed(db_session);binding={'revision':1,'source':'unchanged'};geometry={'footing_id':fixture().footing_id,'footing_size_m':[1.2,1.2,.45]};demand={'id':563}
 monkeypatch.setattr(api,'context',lambda *args:(deepcopy(binding),deepcopy(geometry),deepcopy(demand)))
 def preview(**kw):return api.preview(1,api.Preview(model_revision_id=1,benchmark=fixture(**kw)),db_session,1)
 def auth(p,h=None,yes=True):return api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=h or p['result']['proposal_sha256'],authorize_synthetic_nominal=yes),db_session,1)
 p=preview()
 for h,yes in [('0'*64,True),(None,False)]:
  with pytest.raises(HTTPException):auth(p,h,yes)
 r=auth(p);saved=deepcopy(r);assert r['result']['computed']['design_strength_knm'] is None
 p2=preview(declared_action_knm=300)
 with pytest.raises(HTTPException):auth(p)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE';assert saved==r
 binding['source']='changed'
 with pytest.raises(HTTPException):auth(p2)
 with pytest.raises(HTTPException):preview(demand_result_id=99)
 with pytest.raises(HTTPException):preview(section_width_mm=1100)
