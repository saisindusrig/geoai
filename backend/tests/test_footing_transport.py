import json
from pathlib import Path
from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import footing_transport as api
from app.db.models import ModelRevision
from test_physical_column import seed

def fixture():return json.loads((Path(__file__).resolve().parents[2]/'docs/footing-transport/verification-fixture.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('bad',['column_base','footing_depth','plate_lateral','plate_below','wrong_footing','duplicate_column','duplicate_footing','unreviewed','source','nan'])
def test_invalid_reference_and_identity_rejection(db_session,monkeypatch,bad):
 f=fixture();seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=f['document'];db_session.commit();monkeypatch.setattr(api,'audit_data',lambda *args:deepcopy(f['audit']));links=f['links']
 if bad=='column_base':links[0]['column_reference_m'][2]=.01
 if bad=='footing_depth':links[0]['footing_reference_m'][2]=-.5
 if bad=='plate_lateral':links[0]['plate_reference_m'][0]+=.01
 if bad=='plate_below':links[0]['plate_reference_m'][2]=-.5
 if bad=='wrong_footing':links[0]['footing_id']='absent'
 if bad=='duplicate_column':links[1]['column_id']=links[0]['column_id']
 if bad=='duplicate_footing':links[1]['footing_id']=links[0]['footing_id']
 if bad=='unreviewed':links[0]['reviewed']=False
 if bad=='source':links[0]['source']=''
 if bad=='nan':links[0]['footing_reference_m'][0]=float('nan')
 with pytest.raises((HTTPException,ValueError)):api.calculate(1,api.Preview(model_revision_id=1,links=links),db_session,1)
def test_four_actual_demands_equilibrium_authorization_staleness(db_session,monkeypatch):
 f=fixture();seed(db_session);rev=db_session.get(ModelRevision,1);rev.document_json=f['document'];db_session.commit();monkeypatch.setattr(api,'audit_data',lambda *args:deepcopy(f['audit']));q=api.Preview(model_revision_id=1,links=f['links']);r=api.calculate(1,q,db_session,1);assert r['global_origin_moment_check']['passed'];assert r['soil_pressure']=='BLOCKED'
 for x in r['rows']:assert x['My_nm']==pytest.approx(x['source_reaction']['moment_negative_north_nm']-.45*x['source_reaction']['shear_east_n']);assert x['torsion_Mz_nm']==0
 p=api.preview(1,q,db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_transport=True),db_session,1)
 result=api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_transport=True),db_session,1);assert result['status']=='VERIFIED_DEMANDS_ONLY'
 newer=api.preview(1,q,db_session,1);assert newer['id']!=p['id'];assert api.history(1,1,db_session,1)['records'][1]['status']=='STALE'
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_transport=True),db_session,1)
 f['audit']['model_sha256']='changed'
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=newer['id'],proposal_sha256=newer['result']['proposal_sha256'],authorize_transport=True),db_session,1)
