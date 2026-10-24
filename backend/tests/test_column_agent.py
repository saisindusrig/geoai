import asyncio
from copy import deepcopy
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.core.config import settings
from app.api.routes import column_agent as route,physical_columns as columns
from app.services.ai import column_agent as agent,nebius
from app.db.models import EngineeringAnalysis,ModelRevision
from test_physical_column import seed,inputs,ID

@pytest.fixture(autouse=True)
def mock_only(monkeypatch):
    monkeypatch.setattr(settings,'ENVIRONMENT','development')
    monkeypatch.setattr(settings,'ENGINEERING_AI_MODE','mock')
    monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_APPROVED',False)
    monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_USD',0)
    async def forbidden(*a,**k):raise AssertionError('Paid network request attempted')
    monkeypatch.setattr(nebius,'_request',forbidden)

def prepare(db,provider='mock',model='zai-org/GLM-5.3'):
    return asyncio.run(route.prepare(1,route.Prepare(model_revision_id=1,component_id=ID,provider=provider,model=model),db,1))

def test_missing_explicit_inputs_and_budget_gate(db_session):
    seed(db_session);result=prepare(db_session)
    assert result['status']=='NEEDS_INPUT' and result['result']['missing']==agent.FIELDS
    assert result['result']['engineering_inputs'] is None and result['result']['input_record_id'] is None
    assert result['result']['usage']['actual_charged_usd']==0
    with pytest.raises(HTTPException) as exc:route.authorize(1,route.Authorize(proposal_id=result['id'],proposal_sha256=result['result']['proposal_sha256'],authorize_solver=True),db_session,1)
    assert exc.value.status_code==409
    with pytest.raises(HTTPException) as exc:prepare(db_session,'nebius')
    assert exc.value.status_code==403
    assert not db_session.query(EngineeringAnalysis).filter_by(analysis_type=columns.RUN_TYPE).count()

def test_mock_proposal_approval_actual_solver_explanation_and_history(db_session):
    original=seed(db_session)
    saved=columns.save_inputs(1,columns.Input(model_revision_id=1,component_id=ID,**inputs()),db_session,1)
    proposal=prepare(db_session,model='zai-org/GLM-5.3-Flash')
    assert proposal['status']=='AWAITING_SOLVER_AUTHORIZATION'
    assert proposal['result']['engineering_inputs']==inputs()
    assert not db_session.query(EngineeringAnalysis).filter_by(analysis_type=columns.RUN_TYPE).count()
    authorization=route.Authorize(proposal_id=proposal['id'],proposal_sha256=proposal['result']['proposal_sha256'],authorize_solver=True)
    result=route.authorize(1,authorization,db_session,1)
    assert result['status']=='VERIFIED' and result['result']['values_si']['reaction_n']==pytest.approx(100000)
    assert route.authorize(1,authorization,db_session,1)['id']==result['id']
    explanation=asyncio.run(route.explain(1,proposal['id'],db_session,1))
    assert explanation['record']['result']['explanation']['evidence_sha256']==route.digest(result['result'])
    assert explanation['record']['result']['usage']['mock']
    assert db_session.get(ModelRevision,1).document_json==original
    changed=inputs();changed['compression_n']=50000
    columns.save_inputs(1,columns.Input(model_revision_id=1,component_id=ID,base_input_id=saved['id'],**changed),db_session,1)
    assert all(r['status']=='STALE' for r in route.history(1,ID,db_session,1)['records'])
    with pytest.raises(HTTPException):route.authorize(1,authorization,db_session,1)
    with pytest.raises(HTTPException):asyncio.run(route.explain(1,proposal['id'],db_session,1))

@pytest.mark.parametrize('change',[{'name':'execute_code'},{'arguments':{'model_revision_id':1,'component_id':ID,'input_record_id':1,'code':'wipe'}},{'arguments':{'model_revision_id':'1','component_id':ID,'input_record_id':1}}])
def test_restricted_tool_schema(change):
    tool={'name':'prepare_column_analysis','arguments':{'model_revision_id':1,'component_id':ID,'input_record_id':1}};tool.update(change)
    with pytest.raises(ValidationError):agent.Tool.model_validate(tool)

@pytest.mark.parametrize('corruption',['component','input','invent','missing'])
def test_model_arguments_rejected_before_solver(db_session,monkeypatch,corruption):
    seed(db_session)
    async def malicious(stage,payload,*args):
        tool=deepcopy(payload['arguments']);missing=deepcopy(payload['missing'])
        if corruption=='component':tool['component_id']='another-column'
        if corruption=='input':tool['input_record_id']=100
        if corruption=='invent':tool['elastic_modulus_pa']=200e9
        if corruption=='missing':missing=[]
        return {'summary':'untrusted text','missing_properties':missing,'tool':{'name':'prepare_column_analysis','arguments':tool}},{}
    monkeypatch.setattr(agent,'infer',malicious)
    with pytest.raises(HTTPException) as exc:prepare(db_session)
    assert exc.value.status_code==502
    assert not db_session.query(EngineeringAnalysis).filter_by(analysis_type=columns.RUN_TYPE).count()

def test_ownership_hash_and_revision_guard(db_session):
    original=seed(db_session);columns.save_inputs(1,columns.Input(model_revision_id=1,component_id=ID,**inputs()),db_session,1)
    p=prepare(db_session)
    with pytest.raises(HTTPException):route.history(1,ID,db_session,99)
    with pytest.raises(HTTPException):route.authorize(1,route.Authorize(proposal_id=p['id'],proposal_sha256='a'*64,authorize_solver=True),db_session,1)
    db_session.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json=deepcopy(original),source='manual_edit',user_id=1));db_session.commit()
    assert route.history(1,ID,db_session,1)['records'][0]['status']=='STALE'
    with pytest.raises(HTTPException):route.authorize(1,route.Authorize(proposal_id=p['id'],proposal_sha256=p['result']['proposal_sha256'],authorize_solver=True),db_session,1)

def test_cloud_transport_mock_usage_and_budget(db_session,monkeypatch):
    seed(db_session);monkeypatch.setattr(settings,'ENGINEERING_AI_MODE','nebius');monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_APPROVED',True);monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_USD',.1);monkeypatch.setattr(settings,'NEBIUS_API_KEY','fake-unit-test-only');monkeypatch.setattr(settings,'NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1')
    calls=[]
    async def transport(method,endpoint,**kw):
        calls.append((method,endpoint));assert endpoint in ['models','chat/completions']
        if endpoint=='models':return {'data':[{'id':'zai-org/GLM-5.3'}]}
        import json
        payload=json.loads(kw['payload']['messages'][1]['content'])
        answer={'summary':'Only the supported isolated axial proposal.','missing_properties':payload['missing'],'tool':{'name':'prepare_column_analysis','arguments':payload['arguments']}}
        return {'model':'zai-org/GLM-5.3','usage':{'prompt_tokens':100,'completion_tokens':50},'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}]}
    monkeypatch.setattr(nebius,'_request',transport)
    result=prepare(db_session,'nebius');assert result['result']['usage']['estimated_cost_usd']==pytest.approx(.00036)
    assert calls==[('GET','models'),('POST','chat/completions')]
    assert route.availability(1,db_session,1)['budget_accounted_usd']==pytest.approx(.00036)
    monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_USD',.00036)
    with pytest.raises(HTTPException) as exc:prepare(db_session,'nebius')
    assert exc.value.status_code==403

@pytest.mark.parametrize('summary',['The steel modulus should be 200 GPa.','This column is structurally safe.','This design is compliant.'])
def test_invented_quantities_and_approval_claims_rejected(db_session,monkeypatch,summary):
    seed(db_session)
    async def response(stage,payload,*args):return {'summary':summary,'missing_properties':payload['missing'],'tool':{'name':'prepare_column_analysis','arguments':payload['arguments']}},{}
    monkeypatch.setattr(agent,'infer',response)
    with pytest.raises(HTTPException) as exc:prepare(db_session)
    assert exc.value.status_code==502

def test_unknown_cloud_usage_reserves_budget_without_retry(db_session,monkeypatch):
    seed(db_session);monkeypatch.setattr(settings,'ENGINEERING_AI_MODE','nebius');monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_APPROVED',True);monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_USD',.1);monkeypatch.setattr(settings,'NEBIUS_API_KEY','fake-unit-test-only')
    async def response(*args,**kwargs):raise ValueError('Ambiguous provider failure')
    monkeypatch.setattr(agent,'infer',response)
    with pytest.raises(HTTPException) as exc:prepare(db_session,'nebius')
    assert exc.value.status_code==502
    reserved=route.availability(1,db_session,1)['budget_accounted_usd']
    assert 0<reserved<.1
    monkeypatch.setattr(settings,'ENGINEERING_AI_BUDGET_USD',reserved)
    with pytest.raises(HTTPException) as exc:prepare(db_session,'nebius')
    assert exc.value.status_code==403

def test_readonly_full_project_context_review_and_staleness(db_session):
    original=seed(db_session)
    revision,context=route.project_context(1,1,db_session,1)
    assert context['component_count']==len(original['components'])
    assert len(context['components'])==context['component_count']
    review=asyncio.run(route.project_review(1,route.ReviewRequest(model_revision_id=1,provider='mock',model='zai-org/GLM-5.3-Flash'),db_session,1))
    assert review['status']=='REVIEW_UNVERIFIED'
    columns.save_inputs(1,columns.Input(model_revision_id=1,component_id=ID,**inputs()),db_session,1)
    assert route.project_reviews(1,db_session,1)['records'][0]['status']=='STALE'
    assert db_session.get(ModelRevision,1).document_json==original

def test_long_explanation_redaction_preserves_complete_text(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_API_KEY','synthetic-secret-for-redaction-test')
    text=('Independent equilibrium and verification limitations. '*20)+'synthetic-secret-for-redaction-test'
    output=nebius.sanitized(text,max_length=3000)
    assert len(output)>300
    assert 'synthetic-secret-for-redaction-test' not in output
    assert output.endswith('[REDACTED]')


def test_unbudgeted_legacy_nebius_requests_blocked(monkeypatch):
    monkeypatch.setattr(settings,'NEBIUS_ENFORCE_AGENT_BUDGET',True)
    from app.services.ai.provider import AssistantProviderError
    # Call actual helper (not the test fixture's mocked transport).
    import importlib
    module=importlib.reload(nebius)
    with pytest.raises(AssistantProviderError) as exc:asyncio.run(module._request('POST','chat/completions'))
    assert exc.value.code=='BUDGET_REQUIRED'
