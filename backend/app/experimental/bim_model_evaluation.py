"""Isolated offline screening contracts. No provider client or production routing."""
import json
import asyncio
import os
from pathlib import Path
from uuid import uuid4
from app.domain.bim_authoring import AuthoringIntent
from app.experimental.bim_orchestration import _validate
from app.services.assistant.conversations import reject_secrets
from app.experimental.bim_inference_profiles import safe_diagnostics
from app.experimental.cad_contract import digest

CANDIDATES = (
    'moonshotai/Kimi-K3', 'deepseek-ai/DeepSeek-V4-Pro', 'zai-org/GLM-5.2',
    'MiniMaxAI/MiniMax-M3', 'nvidia/nemotron-3-super-120b-a12b')
REQUESTS = {
    'platform': 'Design a conceptual elevated industrial maintenance platform, 5 m by 3 m at 3 m height, organized into three assemblies: columns, primary and secondary steel beams, and platform slab. Preserve these metre dimensions as preview assumptions, not structural sizing. Use supported sections and materials only.',
    'bridge': 'Design a conceptual two-span bridge: each span 6 m long, deck 3 m wide, supports 3 m high. Decompose beams, deck, three support lines of piers and conceptual bearing blocks. Use repeated straight supported members and deck solids, not curved alignments or prestressing.',
    'mixed': 'Design a conceptual mixed infrastructure project: a two-span road crossing (each span 6 m, deck width 3 m, support height 3 m) and an adjacent supported utility platform (5 m by 3 m at 3 m height). Represent utility support with columns, beams and slab only; pipe routing and road alignment geometry are unsupported. Keep the two systems distinct.'
}
for key in REQUESTS:
    REQUESTS[key] += ' Soil, loads, terrain accuracy, foundations, clearances and code compliance are UNKNOWN; no engineering approval exists. Identify unsupported requests explicitly in assumptions/unknown explanations without inventing recipes. This is an unverified preliminary concept. No CAD Build or approval.'


def request_body(packet, model, catalog):
    if model not in CANDIDATES or model not in catalog:
        raise ValueError('MODEL_NOT_CATALOG_ELIGIBLE')
    messages = [{'role':'system','content':packet['system']},
                {'role':'user','content':json.dumps(packet['payload'],separators=(',',':'),default=str)}]
    reservation = sum(len(m['content'].encode('utf-8')) for m in messages)+1024
    if reservation > 8192:
        raise ValueError('EVALUATION_INPUT_LIMIT')
    return dict(model=model,messages=messages,temperature=.1,max_tokens=3500,
                response_format={'type':'json_object'}), reservation


def validate_screening(body, context):
    """Strict existing validators plus recorded human review, not HTTP success."""
    metadata = safe_diagnostics(body)
    if not metadata['strict_schema_valid']:
        return dict(metadata, serverAccepted=False, engineeringReview='NOT_ELIGIBLE')
    output = json.loads(body['choices'][0]['message']['content'])
    reject_secrets(output)
    intent = AuthoringIntent.model_validate(output)
    _validate('UNDERSTAND', intent, {}, context, None)
    # Requirements/unknown completeness needs rubric review; never auto-declare success.
    return dict(metadata, serverAccepted=True, engineeringReview='PENDING_REQUIRED_RUBRIC_REVIEW')


async def mock_screen_once(directory, *, scenario, model, packet, expected_hash, catalog,
                           context, fake_transport, execution_mode='OFFLINE_MOCK_ONLY'):
    """Mock-only rehearsal. There is deliberately no live execution entry point.

    Exclusive per-cell files bound the finite 5x3 matrix. Incomplete claims fail
    closed. Any transport exception stops the entire rehearsal without replay.
    """
    if scenario not in REQUESTS or digest(packet)!=expected_hash:
        raise ValueError('STALE_EVALUATION_PACKET')
    body,reservation=request_body(packet,model,catalog)
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'STOP').exists():raise ValueError('EVALUATION_STOPPED')
    path=directory/(scenario+'-'+str(CANDIDATES.index(model))+'.json')
    if execution_mode not in {'OFFLINE_MOCK_ONLY','AUTHORIZED_EXPERIMENT'}:raise ValueError('INVALID_EXECUTION_MODE')
    state=dict(mode=execution_mode,model=model,scenario=scenario,packetHash=expected_hash,
               inputReservationTokens=reservation,maxOutputTokens=3500,timeoutSeconds=45,
               requestCount=1,retries=0,state='DISPATCH_INTENT_RECORDED',terminal=False)
    with path.open('x',encoding='utf-8') as handle:
        json.dump(state,handle);handle.flush();os.fsync(handle.fileno())
    try:
        async with asyncio.timeout(45):
            response=await fake_transport(body,45)
    except BaseException:
        state.update(state='TRANSPORT_OUTCOME_UNCERTAIN',terminal=True)
        with (directory/'STOP').open('a',encoding='utf-8') as handle:
            handle.write('TRANSPORT_OUTCOME_UNCERTAIN');handle.flush();os.fsync(handle.fileno())
        temporary=path.with_suffix('.'+uuid4().hex+'.tmp')
        with temporary.open('x',encoding='utf-8') as handle:
            json.dump(state,handle);handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,path)
        raise
    try:
        result=validate_screening(response,context)
    except ValueError:
        result=dict(serverAccepted=False,engineeringReview='VALIDATOR_REJECTED')
    state.update(state='RESPONSE_RECEIVED',terminal=True,result=result)
    temporary=path.with_suffix('.'+uuid4().hex+'.tmp')
    with temporary.open('x',encoding='utf-8') as handle:
        json.dump(state,handle);handle.flush();os.fsync(handle.fileno())
    os.replace(temporary,path)
    return result
