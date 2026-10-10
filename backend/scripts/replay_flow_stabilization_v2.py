"""Read-only replay of saved V2 evidence. Provider entry point is forbidden."""
import json
import subprocess
from pathlib import Path
from unittest.mock import patch
from live_ai3d_acceptance import save, safe
from app.db.session import SessionLocal
from app.db.models import ModelRevision
from app.domain.assistant_runtime import ProposalToolArguments, ProviderResponse
from app.services.ai.provider import NebiusProvider, AssistantProviderError
from app.services.assistant.context import build_context, compact
from app.services.assistant.storage import owned_row
from app.services.assistant.ai3d_validation import site_summary, AI3DDesignValidator
from app.services.assistant.selection_context import local_selection
from app.services.assistant.design_flow import eligible, design_intent, repair_payload
from app.services.assistant.reference_context import resolve_evidence, references
from app.services.assistant.context_preflight import assert_current_model
from app.services.assistant.clarification import suppress_intent
from app.services.assistant.tool_boundary import parse_arguments, argument_repair_payload
from app.domain.stage1 import CivilIntent
from app.services.ai.building_plan import local_plot

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'live-results/universal-v2'
OUT=ROOT/'live-results/stabilization-v2-offline.json'

async def forbidden(*args,**kwargs):raise RuntimeError('NO_PROVIDER_CALLS_AUTHORIZED')

def main():
    result={'providerRequests':0,'replays':{},'sizeMeasurements':{}}
    with patch.object(NebiusProvider,'complete',forbidden),SessionLocal() as db:
        a,b,c=[json.loads((SOURCE/f'case-{case}.json').read_text(encoding='utf-8')) for case in 'ABC']
        a_design=a['completions'][2]['visibleStructuredResponse']['assets'][0]['ai3dDesign']
        summary=site_summary(db,577,a['runContext']['context'])
        boundary=local_plot({'origin':summary['origin'],'boundary':db.get(__import__('app.db.models',fromlist=['Project']).Project,577).boundary_geojson})
        validated=AI3DDesignValidator().validate(a_design,summary,boundary)
        a_message=owned_row(db,'conversation_messages',577,a['messageId'])
        result['replays']['AREA']={'selection':local_selection(summary),'originalDesignUnchanged':True,'validation':validated,
            'repairStatus':'DESIGN_REPAIR_ELIGIBLE' if eligible(validated['issues']) else 'NOT_ELIGIBLE',
            'designRepairPayload':repair_payload(a_message,summary,a_design,validated['issues'])}
        b_context=b['runContext']['context'];b_final=b['completions'][-1]['visibleStructuredResponse']
        b_diag=[];evidence=resolve_evidence(db,578,b_context,b_final['evidenceIds'],b['completions'][-1]['toolResultsSeen'],b_diag)
        vid=b['completions'][-1]['toolResultsSeen'][0]['result']['data']['proposalVersionId']
        owned_row(db,'design_proposal_versions',578,vid)
        parts=[{'kind':'TEXT','text':b_final['text']},{'kind':'PROPOSAL','proposalVersionId':vid},{'kind':'EVIDENCE','evidenceIds':evidence}]
        intent=suppress_intent(CivilIntent.model_validate(b['completions'][0]['visibleStructuredResponse']),'ENDPOINTS',0,b_diag)
        result['replays']['BRIDGE']={'handoffStatus':'VALID','persistedDuringReplay':False,'authoritativeReferences':references(db,578,b_context),
            'parts':parts,'diagnostics':b_diag,'clarificationSuppressed':not intent.needs_clarification,
            'selectionIdExcludedFromEvidence':b_context['siteSelectionVersionId'] not in evidence}
        c_message=owned_row(db,'conversation_messages',576,c['messageId'])
        latest=db.query(ModelRevision).filter_by(project_id=576).order_by(ModelRevision.id.desc()).first()
        try:assert_current_model(db,576,c_message['context']);status='CURRENT'
        except AssistantProviderError as exc:status=exc.code
        result['replays']['WALKWAY']={'sourceRevision':c_message['context']['modelRevisionId'],'currentRevision':str(latest.id),
            'newOperationPreflight':status,'providerCalls':0,'silentlyRebased':False}
        # Reconstruct the previous compact JSON request using the checked-in pre-milestone loaders.
        # No file or DB is modified; the old module is evaluated only to read the same frozen facts.
        baseline={}
        source=subprocess.check_output(['git','show','HEAD:backend/app/services/assistant/context.py'],cwd=ROOT,encoding='utf-8')
        exec(compile(source,'baseline-context','exec'),baseline)
        old_summary={}
        source=subprocess.check_output(['git','show','HEAD:backend/app/services/assistant/ai3d_validation.py'],cwd=ROOT,encoding='utf-8')
        exec(compile(source,'baseline-site-summary','exec'),old_summary)
        with patch('app.services.assistant.ai3d_validation.site_summary',old_summary['site_summary']):
            old_context=baseline['build_context'](db,576,c_message,c['runContext']['policy'])
        new_context=build_context(db,576,c_message,c['runContext']['policy'])
        call=ProviderResponse.model_validate(c['completions'][1]['visibleStructuredResponse']).tool_calls[0]
        try:parse_arguments(call.name,call.arguments)
        except AssistantProviderError as exc:failure=exc
        old_payload={'schema':ProposalToolArguments.model_json_schema(by_alias=True),'toolArgumentRepair':True,'context':old_context,
            'intendedTool':call.name,'invalidArguments':call.arguments,'validationErrors':failure.diagnostics}
        new_payload=argument_repair_payload(call,new_context,failure)
        original_arguments=json.loads(b['completions'][1]['visibleStructuredResponse']['toolCalls'][0]['arguments'])
        lean={'design':design_intent(original_arguments['assets'][0]['ai3dDesign'])}
        def size(v):return len(compact(v).encode('utf-8'))
        def measurement(before,after,method):
            return {'beforeBytes':size(before),'afterBytes':size(after),'reductionPercent':round(100*(1-size(after)/size(before)),2),'method':method}
        result['sizeMeasurements']={
            'bridgeProposalArguments':measurement(original_arguments,lean,'Same saved valid bridge design; omit server-owned fields and duplicated title/rationale/requirements/assumptions/warnings. No geometry alteration.'),
            'bridgeOuterToolArgumentRepresentation':measurement({'arguments':compact(original_arguments)},{'arguments':lean},'Compare serialized nested string with typed object; same design data.'),
            'walkwayNestedRepairInput':measurement(old_payload,new_payload,'Reconstructed old request from HEAD loaders and frozen context/current unchanged site objects; exact original invalid argument string retained. This is byte size, not an observed tokenizer count.'),
            'expectedGenericRepairOutputRepresentative':measurement(original_arguments,lean,'Representative valid bridge payload; malformed walkway cannot supply a valid output. Output savings estimate is not a new model result.')}
        result['replays']['WALKWAY']['compactRepairPayload']=new_payload
        result['unknownDataSafety']={'engineeringUnknownsPreserved':True,'referencePlane':'LOCAL_VISUAL_REFERENCE','engineeringValidation':'UNVALIDATED'}
    save(OUT,safe(result));json.loads(OUT.read_text(encoding='utf-8'))
    print(json.dumps({'path':str(OUT),'providerRequests':0,'area':result['replays']['AREA']['repairStatus'],
        'bridge':result['replays']['BRIDGE']['handoffStatus'],'walkway':result['replays']['WALKWAY']['newOperationPreflight'],
        'sizes':result['sizeMeasurements']},indent=2))

if __name__=='__main__':main()
