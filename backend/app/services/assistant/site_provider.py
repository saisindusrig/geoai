"""Nebius-only streaming transport. No fallback, retries, or model escalation."""
import asyncio
import json
import hashlib
import codecs
from decimal import Decimal, ROUND_CEILING
import httpx
from app.services.ai.nebius_config import resolve

MODELS = {'zai-org/GLM-5.3-Flash':(.15,.50),'zai-org/GLM-5.3':(1.40,4.40)}
MAX_INPUT_BYTES = 90000
MAX_OUTPUT = 4096


def estimate_usd(model, prompt, output):
    prices=MODELS[model]
    value=(Decimal(prompt)*Decimal(str(prices[0]))+Decimal(output)*Decimal(str(prices[1])))/Decimal(1000000)
    return float(value.quantize(Decimal('0.000000000001'),rounding=ROUND_CEILING))


class ProviderFailure(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def request_body(messages, model, tools):
    if model not in MODELS:
        raise ValueError('Unsupported Nebius model')
    body = {'model':model,'messages':messages,'max_tokens':MAX_OUTPUT,'stream':True,
            'stream_options':{'include_usage':True},'temperature':.1,'reasoning_effort':'low'}
    if tools:
        body.update(tools=tools,tool_choice='auto')
    encoded=json.dumps(body,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    if len(encoded)>MAX_INPUT_BYTES:
        raise ValueError('Context exceeds the bounded provider request size')
    return body,encoded


def reservation(messages, model, tools):
    body,encoded=request_body(messages,model,tools)
    # Byte-level tokenizer ceiling plus explicit chat/tool-format allowance.
    # Includes system, history, Unicode, schemas, tool arguments/results and output.
    # Provider tokenization/billing is external: contradictory usage fails closed.
    overhead=1024+64*len(messages)+256*len(tools)
    input_bound=len(encoded)+overhead
    return {'request_sha256':hashlib.sha256(encoded).hexdigest(),'input_bytes':len(encoded),
            'input_token_bound':input_bound,'output_token_cap':body['max_tokens'],
            'tokens':input_bound+body['max_tokens'],
            'reserved_usd':estimate_usd(model,input_bound,body['max_tokens']),
            'model':model,'input_usd_per_million':MODELS[model][0],'output_usd_per_million':MODELS[model][1],
            'state':'RESERVED','actual_charge':'UNKNOWN'}


def reported_accounting(quote, usage):
    if not isinstance(usage,dict):
        return None
    prompt=usage.get('prompt_tokens');output=usage.get('completion_tokens')
    if any(type(v) is not int or v<0 for v in (prompt,output)) or prompt==0:
        return None
    if 'total_tokens' in usage and (type(usage['total_tokens']) is not int or usage['total_tokens']!=prompt+output):
        return None
    reasoning=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens') if isinstance(usage.get('completion_tokens_details') or {},dict) else None
    if reasoning is not None and (type(reasoning) is not int or reasoning<0 or reasoning>output):
        return None
    # Reasoning tokens are included in completion_tokens, never added twice.
    return {'tokens':prompt+output,'estimated_usd':estimate_usd(quote['model'],prompt,output),
            'within_bound':prompt<=quote['input_token_bound'] and output<=quote['output_token_cap']}


async def sse_lines(response):
    decoder=codecs.getincrementaldecoder('utf-8')()
    buffer='';received=0
    async for chunk in response.aiter_bytes():
        received+=len(chunk)
        if received>1500000:raise ValueError('Nebius response exceeds size limit')
        buffer+=decoder.decode(chunk)
        while '\n' in buffer:
            line,buffer=buffer.split('\n',1)
            if len(line)>256000:raise ValueError('Nebius SSE line exceeds size limit')
            yield line.rstrip('\r')
        if len(buffer)>256000:raise ValueError('Nebius SSE line exceeds size limit')
    buffer+=decoder.decode(b'',final=True)
    if buffer:yield buffer.rstrip('\r')


async def stream(messages, model, tools):
    config = resolve(model=model, timeout=40)
    if config.base_url != 'https://api.tokenfactory.nebius.com/v1' or not config.api_key:
        raise ValueError('Nebius backend credentials or official endpoint unavailable')
    body,encoded = request_body(messages,model,tools)
    calls = {}; text = ''; finish = None; usage = None; done = False; returned_model=None
    async with asyncio.timeout(45):
        async with httpx.AsyncClient(timeout=40, follow_redirects=False) as client:
            async with client.stream('POST',config.url('chat/completions'),headers={**config.headers(),'Content-Type':'application/json'},content=encoded) as response:
                if response.status_code != 200:
                    raise ProviderFailure('PROVIDER_RATE_LIMITED' if response.status_code==429 else 'PROVIDER_UNAVAILABLE', 'Nebius quota reached. Retry manually later.' if response.status_code==429 else 'Nebius inference unavailable. Retry manually.')
                async for line in sse_lines(response):
                    if not line.startswith('data:'):
                        continue
                    data = line[5:].strip()
                    if data == '[DONE]':
                        done = True
                        break
                    event = json.loads(data)
                    if event.get('model') is not None:
                        if event['model'] != model:
                            raise ProviderFailure('MODEL_MISMATCH','Nebius returned a different model. Inference blocked pending provider/accounting review.')
                        returned_model=event['model']
                    if event.get('usage'):
                        usage = event['usage']
                        yield {'type':'usage','usage':usage,'actual_charge':'UNKNOWN'}
                    for choice in event.get('choices',[]):
                        if choice.get('index',0) != 0:
                            raise ValueError('Unexpected completion choice')
                        delta = choice.get('delta') or {}
                        content = delta.get('content')
                        if content:
                            if not isinstance(content,str):
                                raise ValueError('Invalid provider text')
                            text += content
                            if len(text)>24000:
                                raise ValueError('Response text limit reached')
                            yield {'type':'delta','text':content}
                        for part in delta.get('tool_calls') or []:
                            index = part['index']
                            if not isinstance(index,int) or index<0 or index>3:
                                raise ValueError('Tool count limit exceeded')
                            call = calls.setdefault(index,{'id':'','type':'function','function':{'name':'','arguments':''}})
                            if part.get('type','function') != 'function':
                                raise ValueError('Unsupported tool type')
                            call['id'] += part.get('id','')
                            call['function']['name'] += part.get('function',{}).get('name','')
                            call['function']['arguments'] += part.get('function',{}).get('arguments','')
                        if choice.get('finish_reason'):
                            finish = choice['finish_reason']
    if done and returned_model is None:
        raise ProviderFailure('MODEL_UNCONFIRMED','Nebius did not identify the returned model. Inference blocked pending provider/accounting review.')
    if not done or finish not in ('stop','tool_calls') or (not text.strip() and not calls):
        raise ValueError('Nebius response incomplete or empty. Retry manually.')
    ordered = [calls[i] for i in sorted(calls)]
    if (finish=='tool_calls' and not ordered) or (ordered and (finish!='tool_calls' or any(not c['id'] or len(c['id'])>128 for c in ordered) or len({c['id'] for c in ordered})!=len(ordered))):
        raise ValueError('Invalid native tool response')
    yield {'type':'completion','message':{'role':'assistant','content':text or None,**({'tool_calls':ordered} if ordered else {})},'usage':usage,'returned_model':returned_model}
