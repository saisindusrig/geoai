"""Integration stabilization is tested entirely with deterministic providers."""
import asyncio
import copy
import json
import pytest
from pydantic import ValidationError
from app.domain.assistant_design_input import DesignIntent, GenericProposalArguments, UNKNOWN_FIELDS
from app.domain.assistant_runtime import ProviderResponse
from app.domain.stage1 import CivilIntent
from app.db.models import ModelRevision, DesignScenario
from app.services.ai.provider import AssistantProviderError
from app.services.assistant import runtime
from app.services.assistant.context import build_context
from app.services.assistant.context_preflight import assert_current_model
from app.services.assistant.reference_context import references, resolve_evidence
from app.services.assistant.selection_context import local_selection, selection_capabilities
from app.services.assistant.clarification import redundant, suppress_intent
from app.services.assistant.design_flow import design_intent, normalize_proposal, repair_payload, validation_errors, eligible
from app.services.assistant.ai3d_validation import site_summary, AI3DDesignValidator
from app.services.assistant.policy import evaluate
from app.services.assistant.storage import rows, owned_row
from app.services.assistant.tool_boundary import parse_arguments
from test_assistant_runtime import message
from test_site_workspace import site_db
from test_ai3d_v1 import fixture

class Provider:
    def __init__(self,replies):self.replies=iter(replies);self.calls=[]
    async def complete(self,system,payload,route):
        self.calls.append((system,payload,route));return next(self.replies)

def generic(db):
    msg,rid=message(db,'Create a pedestrian bridge here.')
    summary=site_summary(db,1,msg['context'])
    design=fixture(selection=summary['selectionReference'])
    intent=design_intent(design);intent['unknowns']=list(UNKNOWN_FIELDS)
    return msg,rid,intent

def execute(db,msg,rid,intent,repair=None):
    runtime.queue_run(db,1,1,rid)
    replies=[evaluate(msg)['intent'],{'toolCalls':[{'name':'create_proposal','arguments':{'design':intent}}]}]
    if repair is not None:replies.append(repair)
    replies.append({'text':'Review the conceptual proposal. Engineering approval remains unknown.'})
    provider=Provider(replies);asyncio.run(runtime.process(db,1,rid,provider))
    return owned_row(db,'assistant_runs',1,rid),provider

def outside(intent):
    data=copy.deepcopy(intent);data['objects'][0]['parameters']['points']=[[300,30,3],[325,30,3],[345,30,3]]
    return data

def test_typed_reference_separation(site_db):
    msg,_=message(site_db);refs=references(site_db,1,msg['context'])
    assert refs['selectionReference']['kind']=='SELECTION_VERSION'
    assert refs['siteProfileReference']['kind']=='SITE_PROFILE_VERSION'
    assert refs['modelRevisionReference']['kind']=='MODEL_REVISION'
    assert all(r['kind']=='EVIDENCE' for r in refs['evidenceReference'])
    assert refs['selectionReference']['id'] not in {r['id'] for r in refs['evidenceReference']}

def test_selection_id_cannot_be_persisted_as_evidence(site_db):
    msg,_=message(site_db);diagnostics=[]
    evidence=resolve_evidence(site_db,1,msg['context'],[msg['context']['siteSelectionVersionId']],[],diagnostics)
    assert msg['context']['siteSelectionVersionId'] not in evidence
    assert diagnostics[0]['event']=='REFERENCE_TYPE_MISMATCH'
    assert evidence
    for eid in evidence:owned_row(site_db,'site_evidence',1,eid)

def test_evidence_alias_is_resolved_by_server(site_db):
    msg,_=message(site_db);refs=references(site_db,1,msg['context'])
    expected=sorted(r['id'] for r in refs['evidenceReference'])
    assert resolve_evidence(site_db,1,msg['context'],['terrain-profile','site-evidence-1'],[],[])==expected
    assert resolve_evidence(site_db,1,msg['context'],[],[],[])==expected

@pytest.mark.parametrize('requested',['invented-id','other-project-evidence'])
def test_arbitrary_evidence_never_accepted(site_db,requested):
    msg,_=message(site_db)
    with pytest.raises(AssistantProviderError,match='EVIDENCE_REFERENCE_INVALID'):
        resolve_evidence(site_db,1,msg['context'],[requested],[],[])

@pytest.mark.parametrize('question,kind,count,expected',[
    ('Where does the bridge start and end?','ENDPOINTS',0,True),
    ('Could you select the two endpoints?','ENDPOINTS',0,True),
    ('Please mark the area again.','AREA',0,True),
    ('Which component should I move?','AREA',1,True),
    ('Which component should I move?','AREA',2,False),
    ('Please mark the area and specify soil bearing capacity.','AREA',0,False),
    ('What deck width should I use?','ENDPOINTS',0,False),
    ('Where does the bridge start and end?','POINT',0,False),
    ('Could you select endpoints and specify the road?','ENDPOINTS',0,False)])
def test_clarification_is_exclusively_grounded(question,kind,count,expected):
    assert redundant(question,kind,count)==expected

def test_intent_clarification_suppression():
    intent=CivilIntent.model_validate({'kind':'DESIGN_REQUEST','domain':'CIVIL_INFRASTRUCTURE','assets':[],
        'needsClarification':True,'clarificationQuestion':'Please select two endpoints.'})
    diagnostics=[];updated=suppress_intent(intent,'ENDPOINTS',0,diagnostics)
    assert not updated.needs_clarification and updated.clarification_question is None
    assert intent.needs_clarification and diagnostics

@pytest.mark.parametrize('kind,expected',[('AREA',['WITHIN_AREA','AVOID_AREA']),('ROUTE',['FOLLOW_ROUTE','START_AT','END_AT','AVOID_AREA']),
    ('ENDPOINTS',['START_AT','END_AT','AVOID_AREA']),('POINT',['AVOID_AREA'])])
def test_selection_constraint_advertisement(kind,expected):
    assert selection_capabilities(kind)['supportedConstraints']==expected

def test_wrong_selection_constraint_rejected(site_db):
    msg,_,intent=generic(site_db)
    args=normalize_proposal(site_db,1,msg,{'design':intent});design=args['assets'][0]['ai3dDesign']
    design['constraints']=[{'id':'follow','kind':'FOLLOW_ROUTE','targetId':'path'}]
    issues=validation_errors(site_db,1,msg['context'],design)
    assert issues[0]['code']=='CONSTRAINT_NOT_APPLICABLE' and eligible(issues)

def test_area_local_bounds_are_required_context(site_db):
    msg,_=message(site_db);context=build_context(site_db,1,msg,evaluate(msg))
    selected=context['selectionContext']
    assert selected['coordinateFrame']=='LOCAL_ENU' and selected['localPolygon']['type']=='Polygon'
    assert selected['widthM']>200 and selected['heightM']>100
    assert selected['boundingBox']['minX']==0 and selected['centroid'][0]>0
    assert selected['usableCoordinateRange']['z']=='UNKNOWN; preview only'
    assert selected['orientationDeg']==0

def test_compact_payload_stamps_server_owned_metadata(site_db):
    msg,_,intent=generic(site_db);args=normalize_proposal(site_db,1,msg,{'design':intent})
    design=args['assets'][0]['ai3dDesign'];summary=site_summary(site_db,1,msg['context'])
    assert design['siteSelection']==summary['selectionReference'] and design['sourceModelRevisionId']=='1'
    assert design['inputSource']=='PREVIEW_ASSUMPTION' and set(UNKNOWN_FIELDS)<=set(design['unknowns'])
    assert len(json.dumps({'design':intent}))<len(json.dumps(args))

@pytest.mark.parametrize('field',['siteSelection','sourceModelRevisionId','proposalId','evidenceIds','aiChosenPreviewParameters'])
def test_model_cannot_supply_authority_in_compact_design(site_db,field):
    _,_,intent=generic(site_db)
    with pytest.raises(ValidationError):GenericProposalArguments.model_validate({'design':{**intent,field:'invented'}})

def test_typed_object_arguments_and_string_compatibility(site_db):
    _,_,intent=generic(site_db);args={'design':intent}
    assert parse_arguments('create_proposal',args)==parse_arguments('create_proposal',json.dumps(args))
    assert isinstance(ProviderResponse.model_validate({'toolCalls':[{'name':'create_proposal','arguments':args}]}).tool_calls[0].arguments,dict)

def test_successful_design_repair_exactly_once(site_db):
    msg,rid,intent=generic(site_db)
    run,provider=execute(site_db,msg,rid,outside(intent),intent)
    assert run['status']=='COMPLETE' and len(provider.calls)==4
    repairs=[p for _,p,_ in provider.calls if p.get('designRepair')]
    assert len(repairs)==1 and 'recentMessages' not in repairs[0]
    assert repairs[0]['validationErrors'][0]['code']=='OUTSIDE_SELECTED_AREA'
    assert provider.calls[2][2].max_output_tokens==3500
    assert any(d['event']=='DESIGN_REPAIR_SUCCESS' for d in run['context_snapshot']['modelRoutingDiagnostics'])
    assert len(rows(site_db,'design_proposal_versions',1))==1
    assert not rows(site_db,'proposal_approvals',1) and len(rows(site_db,'model_revisions',1))==1

@pytest.mark.parametrize('mode',['still-outside','schema','unknown-removal'])
def test_failed_repair_stops_without_loop_or_dispatch(site_db,mode):
    msg,rid,intent=generic(site_db)
    repaired=outside(intent) if mode=='still-outside' else {'invalid':True} if mode=='schema' else {**intent,'unknowns':[]}
    run,provider=execute(site_db,msg,rid,outside(intent),repaired)
    assert run['error_code']=='DESIGN_REPAIR_FAILED' and len(provider.calls)==3
    assert not rows(site_db,'design_proposal_versions',1) and not rows(site_db,'assistant_tool_executions',1)

def test_valid_design_uses_no_repair(site_db):
    msg,rid,intent=generic(site_db);run,provider=execute(site_db,msg,rid,intent)
    assert run['status']=='COMPLETE' and not any(p.get('designRepair') for _,p,_ in provider.calls)

def test_stale_preflight_spends_no_provider_calls(site_db):
    msg,rid,_=generic(site_db)
    site_db.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json=copy.deepcopy(site_db.get(ModelRevision,1).document_json)))
    site_db.commit();runtime.queue_run(site_db,1,1,rid);provider=Provider([])
    asyncio.run(runtime.process(site_db,1,rid,provider))
    assert owned_row(site_db,'assistant_runs',1,rid)['error_code']=='CONTEXT_REFRESH_REQUIRED'
    assert not provider.calls

def test_current_preflight_and_unrelated_project_revision(site_db):
    msg,_,_=generic(site_db)
    assert_current_model(site_db,1,msg['context'])
    site_db.add(DesignScenario(id=2,project_id=2,name='Other'));site_db.flush()
    site_db.add(ModelRevision(id=2,project_id=2,design_scenario_id=2,revision_number=1,document_json={'components':[]}));site_db.commit()
    assert_current_model(site_db,1,msg['context'])

def test_compact_repair_omits_history_and_authority(site_db):
    msg,_,intent=generic(site_db);summary=site_summary(site_db,1,msg['context'])
    design=normalize_proposal(site_db,1,msg,{'design':outside(intent)})['assets'][0]['ai3dDesign']
    payload=repair_payload(msg,summary,design,validation_errors(site_db,1,msg['context'],design))
    assert 'siteSelection' not in payload['originalDesign'] and 'sourceModelRevisionId' not in payload['originalDesign']
    assert 'context' not in payload and 'toolResults' not in payload
    assert payload['supportedConstraints']==['WITHIN_AREA','AVOID_AREA']

def test_unanchored_discussion_is_not_a_stale_model(site_db):
    assert_current_model(site_db,1,{'modelRevisionId':None,'scenarioId':None,'siteSelectionVersionId':None})

def test_saved_endpoint_constraints_match_actual_selection():
    from test_ai3d_v1 import object_
    design=fixture('road');design['objects'][0]['parameters']['points']=[[5,30,0],[45,30,0]]
    design['objects'].append(object_('end','POINT',position=[45,30,0]))
    design['constraints']=[{'id':'end-at','kind':'END_AT','targetId':'path','referenceId':'end'}]
    summary={'selectionReference':design['siteSelection'],'sourceModelRevisionId':'1','selectionKind':'ENDPOINTS',
        'localGeometry':{'type':'LineString','coordinates':[[5,30],[46,30]]}}
    assert 'SAVED_ENDPOINT_MISMATCH' in {i['code'] for i in AI3DDesignValidator().validate(design,summary)['issues']}
    summary['localGeometry']['coordinates'][-1]=[45,30]
    assert not AI3DDesignValidator().validate(design,summary)['issues']

def test_fresh_context_required_cannot_retry_old_frozen_request(site_db):
    from fastapi import HTTPException
    from app.services.assistant.storage import update
    msg,rid,_=generic(site_db)
    update(site_db,'assistant_runs',1,rid,status='FAILED',error_code='CONTEXT_REFRESH_REQUIRED');site_db.commit()
    with pytest.raises(HTTPException) as exc:runtime.retry_run(site_db,1,1,rid,'do-not-retry')
    assert exc.value.detail['code']=='CONTEXT_REFRESH_REQUIRED'

def test_generic_nested_repair_keeps_attached_geometry(site_db):
    from app.services.assistant.tool_boundary import argument_repair_payload
    msg,_,intent=generic(site_db)
    call=ProviderResponse.model_validate({'toolCalls':[{'name':'create_proposal','arguments':{'design':intent}}]}).tool_calls[0]
    context={'currentMessage':msg['parts'],'selectionContext':{'selectionType':'AREA'},'relevantComponents':[{'id':'road','geometry':{'kind':'box'},'metadata':{'irrelevant':'omit'}}],'recentMessages':['omit']}
    payload=argument_repair_payload(call,context,AssistantProviderError('TOOL_ARGUMENT_SCHEMA_INVALID'))
    assert payload['context']['attachedGeometry']==[{'id':'road','geometry':{'kind':'box'}}]
    assert 'recentMessages' not in payload['context']

def test_specialist_argument_repair_retains_original_grounding():
    from app.services.assistant.tool_boundary import argument_repair_payload
    call=ProviderResponse.model_validate({'toolCalls':[{'name':'create_proposal','arguments':'{"buildingPatch":'}]}).tool_calls[0]
    context={'relevantComponents':[{'metadata':{'specificationId':'saved-spec'}}],'frozenContext':{'modelRevisionId':'1'}}
    assert argument_repair_payload(call,context,AssistantProviderError('TOOL_ARGUMENT_JSON_INVALID'))['context']==context

def test_bridge_review_handoff_resolves_selection_reference(site_db):
    msg,rid,intent=generic(site_db)
    runtime.queue_run(site_db,1,1,rid)
    provider=Provider([evaluate(msg)['intent'],{'toolCalls':[{'name':'create_proposal','arguments':{'design':intent}}]},
        {'text':'Review the conceptual bridge proposal.','evidenceIds':[msg['context']['siteSelectionVersionId']]}])
    asyncio.run(runtime.process(site_db,1,rid,provider))
    assert owned_row(site_db,'assistant_runs',1,rid)['status']=='COMPLETE'
    reply=rows(site_db,'conversation_messages',1)[-1]
    assert any(p['kind']=='PROPOSAL' for p in reply['parts'])
    for part in reply['parts']:
        if part['kind']=='EVIDENCE':assert msg['context']['siteSelectionVersionId'] not in part['evidenceIds']
