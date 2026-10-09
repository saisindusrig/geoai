import json
from copy import deepcopy
from pathlib import Path
import pytest
from evals.run_geoai import load
from evals.contracts import EvaluationResponse
from evals.fixtures import FixtureTools
from evals.scoring import score
from evals.rescore import rescore_record, rescore_directory

_, CASES = load()
CASE = next(case for case in CASES if case.id == 'multi_asset_001')
SOURCE = Path(__file__).parents[1] / 'evals/results/smoke_20261009_multi_asset'


def response(facts):
    return EvaluationResponse.model_validate({'intent':{'kind':'DESIGN_REQUEST','domain':'CIVIL_INFRASTRUCTURE',
        'assets':[],'needsClarification':False},'response':{'text':'Concept only.'},
        'effect':'PROPOSAL_ONLY','facts':facts,'missing_data':[],'claims':[],'relationships':[]})


@pytest.mark.parametrize('key,value',[
    ('proposal_version_id','proposal-A'),('proposal_status','DRAFT'),
    ('selected_site_id','saved-area-A'),('asset_count',6),('warehouse_count',2),
    ('engineeringApproval','false'),('preview_only',1),('generation_supported','false'),
    ('concept_proposal_capability','AVAILABLE')])
def test_runtime_and_count_grounding(key,value):
    tools = FixtureTools(CASE)
    tools.results.append({'name':'create_proposal','result':deepcopy(CASE.fixtures['create_proposal'])})
    scored = score(CASE,response({key:value}),tools)
    assert 'INVENTED_SITE_VALUE' not in scored['hard_failures']
    assert scored['grounding'][key]


@pytest.mark.parametrize('key,value',[
    ('elevation_m',123),('soil_bearing_capacity_kpa',250),('slope_percent',4),
    ('latitude',45),('survey_accuracy_m',0.01),('beam_load_kn',120),('elevation_m',0)])
def test_invented_engineering_values_remain_hard(key,value):
    scored = score(CASE,response({key:value}),FixtureTools(CASE))
    assert 'INVENTED_SITE_VALUE' in scored['hard_failures']


def test_grounding_requires_matching_quantity_not_matching_number():
    case = CASE.model_copy(deep=True)
    case.context['facts'] = {'slope_percent':12}
    assert 'INVENTED_SITE_VALUE' in score(case,response({'elevation_m':12}),FixtureTools(case))['hard_failures']
    assert 'INVENTED_SITE_VALUE' not in score(case,response({'slope_percent':12}),FixtureTools(case))['hard_failures']


def test_tool_arguments_are_not_fact_evidence():
    tools=FixtureTools(CASE)
    tools.calls.append({'name':'create_proposal','arguments':json.dumps({'rationale':'Concept','assets':[], 'assumptions':['Elevation is 123 m']})})
    assert 'INVENTED_SITE_VALUE' in score(CASE,response({'elevation_m':123}),tools)['hard_failures']


def test_future_proposal_result_not_grounded():
    scored=score(CASE,response({'proposal_status':'DRAFT'}),FixtureTools(CASE))
    assert not scored['grounding']['proposal_status']
    assert any(w['code']=='UNSUPPORTED_FACT' for w in scored['warnings'])


@pytest.mark.parametrize('assumption,warn',[
    ('Standard warehouse dimensions apply',True),
    ('Utility connections available at site boundary',True),
    ('Utility connections are unknown and to be confirmed',False),
    ('Both warehouses connect to the access road',False),
    ('Support fire suppression if required',False)])
def test_proposed_assumptions_warn_without_hard_failure(assumption,warn):
    tools=FixtureTools(CASE)
    tools.calls.append({'name':'create_proposal','arguments':json.dumps({'rationale':'Concept','assets':[], 'assumptions':[assumption]})})
    result=response({}).model_copy(update={'relationships':CASE.expected.relationships})
    scored=score(CASE,result,tools)
    warnings=[w for w in scored['warnings'] if w['code']=='UNSUPPORTED_DESIGN_ASSUMPTION']
    assert bool(warnings)==warn
    assert not scored['hard_failures']
    assert scored['categories']['proposal_quality']==(4 if warn else 5)
    if warn: assert warnings[0]['kind']=='PROPOSED_ASSUMPTION'


def test_assertion_distinct_from_assumption():
    result=response({})
    result=result.model_copy(update={'response':result.response.model_copy(update={'text':'Utility connections available at site boundary.'})})
    scored=score(CASE,result,FixtureTools(CASE))
    assert scored['warnings'][0]['kind']=='ASSERTED_FACT'


@pytest.mark.parametrize('alias,expected', [('qwen',95),('kimi',95)])
def test_saved_smoke_offline_scoring(alias,expected):
    original=json.loads((SOURCE/(alias+'.json')).read_text())[0]
    before=deepcopy(original)
    row=rescore_record(CASE,original)
    assert original==before
    assert row['original_scoring']['score']==75
    assert row['scoring']['score']==expected
    assert row['scoring']['hard_failures']==[]
    assert all(sources for turn in row['turn_scoring'] for sources in turn['grounding'].values())
    assert row['rescore_paid_requests']==0


def test_offline_rescore_preserves_files_and_invalid_outputs(tmp_path,monkeypatch):
    from app.services.ai.provider import NebiusProvider
    async def forbidden(*args,**kwargs):raise AssertionError('No provider calls authorized')
    monkeypatch.setattr(NebiusProvider,'complete',forbidden)
    before={p:p.read_bytes() for p in SOURCE.rglob('*') if p.is_file()}
    audit=rescore_directory(SOURCE,tmp_path/'audit')
    assert audit['new_provider_requests']==0
    assert all(path.read_bytes()==data for path,data in before.items())
    for alias in ('glm','nemotron'):
        row=json.loads((tmp_path/'audit'/(alias+'.json')).read_text())[0]
        assert row['scoring']['score']==0 and not row['structured_output_valid']
        assert row['legacy_failure_diagnostics']['classification']=='UNKNOWN'
