from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import footing_flexure as api
from app.db.models import ModelRevision
from test_physical_column import seed
from test_footing_flexure import fixture,document

def test_exact_authorization_immutable_records_geometry_and_source_staleness(db_session,monkeypatch):
 seed(db_session);db_session.get(ModelRevision,1).document_json=document();db_session.commit();binding={'model_revision_id':1,'source_sha':'same'};monkeypatch.setattr(api,'context',lambda *args:deepcopy(binding));q=api.Preview(model_revision_id=1,benchmark=fixture());p=api.preview(1,q,db_session,1)
 def auth(p,h=None,yes=True):return api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=h or p['result']['proposal_sha256'],authorize_synthetic_demand=yes),db_session,1)
 for h,yes in [('0'*64,True),(None,False)]:
  with pytest.raises(HTTPException):auth(p,h,yes)
 r=auth(p);saved=deepcopy(r);assert r['result']['computed']['faces'][0]['full_cut_moment_knm']==pytest.approx(12.15)
 newer=api.preview(1,api.Preview(model_revision_id=1,benchmark=fixture(column_load_kn=288,uniform_net_pressure_kpa=200)),db_session,1)
 with pytest.raises(HTTPException):auth(p)
 assert next(x for x in api.history(1,1,db_session,1)['records'] if x['id']==r['id'])['status']=='STALE';assert r==saved
 binding['source_sha']='changed'
 with pytest.raises(HTTPException):auth(newer)
 binding['source_sha']='same';doc=document();doc['components'][1]['transform']['position'][0]+=.01;db_session.get(ModelRevision,1).document_json=doc;db_session.commit()
 with pytest.raises(HTTPException):auth(newer)
