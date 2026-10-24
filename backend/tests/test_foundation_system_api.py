from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.api.routes import foundation_system as api
from app.db.models import EngineeringAnalysis
from test_physical_column import seed
from test_footing_flexure import fixture as source_fixture,document
from test_foundation_system import q,geometry

def test_exact_hash_review_ownership_and_stale(db_session,monkeypatch):
 seed(db_session);binding={'revision':1,'implementation':'v1'};g=geometry();src=source_fixture()
 monkeypatch.setattr(api,'context',lambda *args:(deepcopy(binding),deepcopy(g),src))
 preview=api.Preview(model_revision_id=1,inputs=q())
 p=api.preview(1,preview,db_session,1)
 bad=api.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_calculation=True)
 with pytest.raises(HTTPException):api.authorize(1,bad,db_session,1)
 auth=api.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_calculation=True)
 r=api.authorize(1,auth,db_session,1)
 assert api.authorize(1,auth,db_session,1)['id']==r['id']
 with pytest.raises(HTTPException):api.authorize(1,auth,db_session,999)
 before=deepcopy(r)
 p2=api.preview(1,preview,db_session,1)
 with pytest.raises(HTTPException):api.authorize(1,auth,db_session,1)
 assert api.history(1,1,db_session,1)['records'][1]['status']=='STALE'
 binding['implementation']='v2'
 assert all(row['status']=='STALE' for row in api.history(1,1,db_session,1)['records'])
 with pytest.raises(HTTPException):api.authorize(1,api.Authorize(proposal_id=p2['id'],proposal_sha256=p2['result']['proposal_sha256'],authorize_calculation=True),db_session,1)
 assert r==before

def test_reaction_binding_no_shear_or_moment_discarded(db_session,monkeypatch):
 seed(db_session);src=source_fixture();g=geometry()
 row=dict(column_id='c',footing_id='f',link=dict(column_reference_m=[.15,.15,0],footing_reference_m=[.15,.15,-.45]),compression_n=200000,horizontal_shear_enu_n=[0,0],Mx_nm=0,My_nm=0,torsion_Mz_nm=0)
 result=dict(rows=[row],audit={'solver_evidence':'current exact dependency'})
 db_session.add(EngineeringAnalysis(id=88,project_id=1,model_revision_id=1,analysis_type='FOOTING_TRANSPORT_RESULT',algorithm_version='wrench/1',status='VERIFIED_DEMANDS_ONLY',result_json=result,actor_user_id=1));db_session.commit()
 monkeypatch.setattr(api.reaction_api,'history',lambda *args:dict(records=[dict(id=88,status='VERIFIED_DEMANDS_ONLY',result=deepcopy(result))]))
 link=api.ReactionLink(project_id=1,model_revision_id=1,result_id=88,reviewed_exact_column_and_footing=True)
 binding,loaded=api.reaction_binding({},g,src,link,db_session,1)
 assert loaded.column_load_kn==200 and loaded.uniform_net_pressure_kpa==pytest.approx(200/1.44)
 assert binding['reaction_link']['result_sha256']
 for key in ['Mx_nm','My_nm','torsion_Mz_nm']:
  row[key]=1
  with pytest.raises(HTTPException):api.reaction_binding({},g,src,link,db_session,1)
  row[key]=0
 row['horizontal_shear_enu_n']=[1,0]
 with pytest.raises(HTTPException):api.reaction_binding({},g,src,link,db_session,1)

def test_offline_foundation_explanation_never_mutates_or_claims_approval():
 from app.services.assistant.engineering_guidance import answer
 computed=api.s.calculate(q(),geometry(),source_fixture())
 context=dict(projectId=1,revisionId=1,revisionNumber=1,stale=False,selected=[],analyses=[dict(id=90,type='FOUNDATION_SYSTEM_RESULT',status='REVIEWED_SYNTHETIC_CALCULATION',stale=False,foundation=computed)],missing=[],drawingReferences=[])
 before=deepcopy(context)
 text,_=answer('Compare foundation reinforcement and explain punching',context)
 assert '971' not in text # Full precision is in saved evidence; concise explanation reports status.
 assert 'EXCEEDS_IMPLEMENTED_CHECK' in text and '216' in text
 assert 'chat cannot apply or authorize' in text and 'engineering' in text.lower()
 assert context==before
 context['analyses'][0]['stale']=True
 assert 'No current reviewed' in answer('foundation',context)[0]
