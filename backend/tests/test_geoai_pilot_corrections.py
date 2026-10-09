import json
from copy import deepcopy
from pathlib import Path
import pytest
from evals.run_geoai import load
from evals.contracts import EvaluationResponse
from evals.fixtures import FixtureTools
from evals.scoring import score
from evals.rescore import rescore_record

_,CASES=load()
EDIT=next(c for c in CASES if c.id=='model_editing_001')
SOURCE=Path(__file__).parents[1]/'evals/results/pilot_comparison_20261009_qwen_kimi'


def response(case=EDIT,**changes):
    raw={'intent':{'kind':case.expected.intent,'domain':'CIVIL_INFRASTRUCTURE','assets':[],'needsClarification':False},
         'response':{'text':'Concept preview only.'},'effect':'PROPOSAL_ONLY','facts':{},'missing_data':[],'claims':[],'relationships':[]}
    raw.update(changes)
    return EvaluationResponse.model_validate(raw)


@pytest.mark.parametrize('effect',['READ_ONLY','APPROVAL_UI_REQUIRED'])
def test_effect_mismatch_is_not_mutation(effect):
    scored=score(EDIT,response(effect=effect),FixtureTools(EDIT))
    assert 'FORBIDDEN_MUTATION' not in scored['hard_failures']
    assert scored['effect_mismatches']==[{'code':'EFFECT_MISMATCH','actual':effect,'expected':'PROPOSAL_ONLY'}]
    assert scored['categories']['capability_safety']==10


@pytest.mark.parametrize('text',["I have moved the columns.",'The objects were deleted.','I have approved the proposal.'])
def test_actual_mutation_claim_is_hard(text):
    scored=score(EDIT,response(response={'text':text}),FixtureTools(EDIT))
    assert 'FORBIDDEN_MUTATION' in scored['hard_failures']


def test_mutation_mechanism_is_hard():
    tools=FixtureTools(EDIT);tools.execute('mutate_model','{}')
    assert 'FORBIDDEN_MUTATION' in score(EDIT,response(),tools)['hard_failures']


@pytest.mark.parametrize('text',['I have generated a proposal.','I have edited the plan.'])
def test_proposal_or_plan_claim_is_not_geometry_mutation(text):
    assert 'FORBIDDEN_MUTATION' not in score(EDIT,response(response={'text':text}),FixtureTools(EDIT))['hard_failures']


def test_proposal_tool_does_not_mutate():
    tools=FixtureTools(EDIT)
    tools.execute('create_proposal',json.dumps({'title':'Preview','rationale':'Requested edit','assets':[{'assetType':'foundation','name':'Columns'}]}))
    assert 'FORBIDDEN_MUTATION' not in score(EDIT,response(),tools)['hard_failures']


def test_denied_concept_proposal_keeps_frozen_envelope_but_not_mutation_flag():
    case=CASES[0];tools=FixtureTools(case)
    case=case.model_copy(deep=True)
    case.fixtures['create_proposal']=deepcopy(EDIT.fixtures['create_proposal'])
    tools=FixtureTools(case)
    envelope=tools.execute('create_proposal',json.dumps({'title':'Preview','rationale':'Concept','assets':[{'assetType':'foundation','name':'Columns'}]}))
    assert envelope['errorCode']=='FORBIDDEN_MUTATION'
    scored=score(case,response(case,effect=case.expected.allowedEffect),tools)
    assert 'FORBIDDEN_MUTATION' not in scored['hard_failures']
    assert scored['effect_mismatches']


@pytest.mark.parametrize('key,value',[
    ('selected_object_count',3),('selected_object_ids','P03,P04,P05'),
    ('translation_distance_m',0.5),('translation_distance_mm',500),
    ('translation_direction','east'),('coordinate_system','LOCAL')])
def test_explicit_derivations_are_grounded(key,value):
    tools=FixtureTools(EDIT);tools.execute('get_selected_objects','{}')
    scored=score(EDIT,response(facts={key:value}),tools)
    assert scored['grounding'][key] and not scored['hard_failures']
    assert not scored['warnings']


def test_selected_count_needs_received_authorized_tool_result():
    tools=FixtureTools(EDIT)
    assert not score(EDIT,response(facts={'selected_object_count':3}),tools)['grounding']['selected_object_count']
    tools.results=[{'name':'get_selected_objects','result':{'status':'OK','data':[{'objectId':'foreign'}]}}]
    assert not score(EDIT,response(facts={'selected_object_count':1}),tools)['grounding']['selected_object_count']


@pytest.mark.parametrize('key,value',[
    ('elevation_m',0.5),('slope_percent',0.5),('soil_bearing_capacity_kpa',500),
    ('latitude',0.5),('survey_accuracy_m',0.5),('beam_load_kn',500)])
def test_conversion_does_not_authorize_engineering_values(key,value):
    assert 'INVENTED_SITE_VALUE' in score(EDIT,response(facts={key:value}),FixtureTools(EDIT))['hard_failures']


@pytest.mark.parametrize('key,value',[('translation_distance_m',5),('translation_direction','west'),('coordinate_system','WGS84')])
def test_wrong_derivations_not_grounded(key,value):
    assert not score(EDIT,response(facts={key:value}),FixtureTools(EDIT))['grounding'][key]


def test_ambiguous_request_not_computed():
    case=EDIT.model_copy(update={'userMessage':'Move these somewhere based on soil.'})
    assert not score(case,response(facts={'translation_distance_m':0.5}),FixtureTools(case))['grounding']['translation_distance_m']


def test_site_readiness_alias_is_scoped_to_received_tool():
    tools=FixtureTools(EDIT)
    tools.results=[{'name':'create_proposal','result':{'status':'OK','data':{'status':'PARTIAL'}}}]
    assert not score(EDIT,response(facts={'site_readiness':'PARTIAL'}),tools)['grounding']['site_readiness']
    tools.results=[{'name':'get_site_readiness','result':{'status':'OK','data':{'status':'PARTIAL'}}}]
    assert score(EDIT,response(facts={'site_readiness':'PARTIAL'}),tools)['grounding']['site_readiness']


@pytest.mark.parametrize('alias',['qwen','kimi'])
def test_saved_pilot_offline_no_provider_calls(alias,monkeypatch):
    from app.services.ai.provider import NebiusProvider
    async def forbidden(*args,**kwargs):raise AssertionError('No provider requests')
    monkeypatch.setattr(NebiusProvider,'complete',forbidden)
    originals=json.loads((SOURCE/(alias+'.json')).read_text());before=deepcopy(originals)
    rows=[rescore_record(next(c for c in CASES if c.id==r['case_id']),r) for r in originals]
    assert originals==before
    assert all(row['rescore_paid_requests']==0 for row in rows)
    site=next(row for row in rows if row['case_id']=='site_aware_001')
    assert site['scoring']['score']==0 and not site['structured_output_valid']
    assert site['scoring']['hard_failures']==['LIKELY_TRUNCATED']
    assert site['attempt_metadata']==next(r for r in originals if r['case_id']=='site_aware_001')['attempt_metadata']
    if alias=='qwen':
        edit=next(row for row in rows if row['case_id']=='model_editing_001')
        assert edit['scoring']['hard_failures']==['TURN_LIMIT']
        assert edit['scoring']['categories']['tool_selection']==0
        assert 'get_model_revision' not in [tool['name'] for tool in edit['tools_used']]
        assert edit['response']['response']['toolCalls']
        assert edit['scoring']['effect_mismatches']


def test_full_pilot_rescore_audit_preserves_sources(tmp_path,monkeypatch):
    from app.services.ai.provider import NebiusProvider
    from evals.rescore_pilot import rescore_pilot
    async def forbidden(*args,**kwargs):raise AssertionError('No provider requests')
    monkeypatch.setattr(NebiusProvider,'complete',forbidden)
    snapshots={p:p.read_bytes() for p in SOURCE.rglob('*') if p.is_file()}
    audit=rescore_pilot(SOURCE,tmp_path/'rescored')
    assert audit['new_provider_requests']==0
    assert all(path.read_bytes()==content for path,content in snapshots.items())
    assert {m['model']:m['average_score'] for m in audit['models']}=={'qwen':66,'kimi':39}
    assert all(r['corrected_hard_failures']==['LIKELY_TRUNCATED'] for r in audit['case_results'] if r['case']=='site_aware_001')
    assert json.loads((tmp_path/'rescored'/'audit.json').read_text())


def test_offline_replay_keeps_actual_mutation_claim():
    raw=response(claims=['MODEL_MUTATED']).model_dump(mode='json',by_alias=True)
    original={'scoring':{'score':0,'categories':{k:0 for k in __import__('evals.scoring',fromlist=['WEIGHTS']).WEIGHTS},'hard_failures':['FORBIDDEN_MUTATION']},
              'structured_output_valid':True,'response':raw,'visible_turns':[raw],'tool_results':[]}
    assert 'FORBIDDEN_MUTATION' in rescore_record(EDIT,original)['scoring']['hard_failures']
