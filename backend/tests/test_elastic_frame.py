import asyncio,json
from copy import deepcopy
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.services.design import elastic_frame as solver
from app.services.ai import column_agent as agent,nebius
from app.api.routes import elastic_frames as route
from app.core.config import settings
from app.db.models import ModelRevision,EngineeringAnalysis
from test_physical_column import seed

@pytest.mark.parametrize('kind',['cantilever','portal'])
def test_real_solver_mesh_units_and_scaling(kind):
 suite=solver.suite(kind);assert suite['status']=='VERIFIED'
 actual=[r for r in suite['cases'] if r['inputs']['kind']==kind]
 head=[next(n for n in r['nodes'] if n['id']==2)['displacement_m'] for r in actual]
 for r in actual:
  assert r['solver_version']=='3.8.0'
  assert max(map(abs,r['equilibrium_residual_si']))<1e-4
  assert all(v['passed'] for v in r['comparisons'].values())
 for u in head[:-1]:assert u==pytest.approx(head[0],abs=1e-10)
 assert head[-1]==pytest.approx([v*.5 for v in head[0]],abs=1e-10)
 if kind=='cantilever':
  assert head[0][1]==pytest.approx(-.005625)
  r=actual[0];assert r['reactions'][0]['moment_nm']==pytest.approx(3000)
  assert r['elements'][0]['samples'][0]['moment_nm']==pytest.approx(-3000)
  assert r['elements'][-1]['samples'][-1]['moment_nm']==pytest.approx(0,abs=1e-6)
 else:assert head[0][0]==pytest.approx(.00217611726769)

@pytest.mark.parametrize('change',[{'inertia_m4':0},{'area_m2':-1},{'load_n':float('nan')},{'joints':'pinned'},{'restraints':'soil'},{'units':'imperial'},{'elements_per_member':3},{'code':'exec'}])
def test_invalid_inputs(change):
 with pytest.raises(ValidationError):solver.Inputs.model_validate({**solver.fixture('portal'),**change})

def test_frame_agent_authorization_staleness_and_no_paid_calls(db_session,monkeypatch):
 seed(db_session);r=db_session.get(ModelRevision,1);doc=deepcopy(r.document_json);doc['metadata']['elastic_benchmark']={'kind':'portal','length_m':4,'height_m':3}
 doc['components']=doc['components'][:3]
 for c,(position,size,category) in zip(doc['components'],[([0,0,1.5],[.08,.08,3],'column'),([2,0,3],[4,.08,.08],'beam'),([4,0,1.5],[.08,.08,3],'column')]):c.update(category=category,geometry={'kind':'box','size':size},parent_id=None);c['transform'].update(position=position,rotation_deg=[0,0,0],scale=[1,1,1])
 r.document_json=doc;db_session.commit()
 monkeypatch.setattr(settings,'ENGINEERING_AI_MODE','mock');monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_APPROVED',False)
 async def forbidden(*args,**kwargs):raise AssertionError('No paid inference')
 monkeypatch.setattr(nebius,'_request',forbidden)
 prepare=lambda provider='mock':asyncio.run(route.proposal(1,route.Prepare(model_revision_id=1,provider=provider,model='zai-org/GLM-5.3-Flash'),db_session,1))
 p=prepare();assert p['status']=='NEEDS_INPUT'
 with pytest.raises(HTTPException):prepare('nebius')
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1)
 saved=route.inputs(1,route.Save(model_revision_id=1,**solver.fixture('portal')),db_session,1);p=prepare()
 with pytest.raises(HTTPException):route.run(1,route.Authorize(proposal_id=p['id'],proposal_sha256='0'*64,authorize_solver=True),db_session,1)
 auth=route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True);result=route.run(1,auth,db_session,1);assert result['status']=='VERIFIED';assert route.run(1,auth,db_session,1)['id']==result['id']
 explained=asyncio.run(route.explain(1,p['id'],db_session,1));assert explained['result']['explanation']['analysis_id']==result['id'];assert explained['result']['usage']['mock']
 route.inputs(1,route.Save(model_revision_id=1,base_input_id=saved['id'],**{**solver.fixture('portal'),'load_n':10000}),db_session,1)
 assert next(x for x in route.history(1,db_session,1)['records'] if x['id']==result['id'])['status']=='STALE'
 with pytest.raises(HTTPException):route.run(1,auth,db_session,1)
 changed=deepcopy(db_session.get(ModelRevision,1).document_json);changed['components'][0]['transform']['position'][0]=.1;db_session.get(ModelRevision,1).document_json=changed;db_session.commit()
 assert route.out(db_session.query(EngineeringAnalysis).filter_by(id=result['id']).first(),db_session,1)['status']=='STALE'
 with pytest.raises(HTTPException):prepare()

@pytest.mark.parametrize('text',['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'])
def test_strict_structured_json(text):
 with pytest.raises(ValueError):agent.strict_json(text)

def test_saved_real_nebius_fixture_replay():
 from pathlib import Path
 evidence=json.loads((Path(__file__).resolve().parents[2]/'docs/live-nebius/live-evidence.json').read_text())
 validated=0
 for event in evidence:
  if event['status']!=200:continue
  result=event['response'].get('result') or event['response'].get('record',{}).get('result',{})
  if 'proposal' in result:agent.Proposal.model_validate(result['proposal']);validated+=1
  elif 'review' in result:agent.ProjectReview.model_validate(result['review']);validated+=1
  elif 'explanation' in result:agent.Explanation.model_validate(result['explanation']);validated+=1
 assert validated==13

