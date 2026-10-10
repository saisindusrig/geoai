"""Five-cell experimental runner. Production routing is never invoked."""
import time
from app.experimental.bim_model_evaluation import CANDIDATES, request_body, mock_screen_once
from app.experimental.cad_contract import digest


async def compare(directory, *, budget, batch, packet, packet_hash, catalog, contracts,
                  context, transport, verify_source, authority, mock=False):
    if not authority or digest(packet)!=packet_hash:
        raise ValueError('EXPLICIT_AUTHORITY_AND_FROZEN_PACKET_REQUIRED')
    if set(contracts)!=set(CANDIDATES):raise ValueError('EXACT_FIVE_CONTRACTS_REQUIRED')
    # Check every model and billing prerequisite before claiming the batch.
    for model in CANDIDATES:
        request_body(packet,model,catalog)
        c=contracts[model]
        if c.get('model')!=model or any(c.get(k) is not True for k in
            ('accountPricingVerified','allBillableTokensBounded','feesIncluded')):
            raise ValueError('BILLING_CONTRACT_UNVERIFIED')
        if c.get('validUntilEpoch',0)<=time.time():raise ValueError('BILLING_CONTRACT_STALE')
    if not budget.snapshot()['ready']:raise ValueError('BUDGET_NOT_RECONCILED')
    verify_source()
    budget.authorize_batch(batch,authority=authority,phase='UNDERSTAND',max_requests=5)
    results=[]
    for model in CANDIDATES:
        verify_source()
        request_id=batch+':'+model
        budget.reserve(request_id,batch=batch,model=model,contract=contracts[model])
        timing={}
        async def guarded(body,timeout):
            verify_source()
            started=time.monotonic()
            response=await transport(body,timeout)
            # A verified provider-reported USD value is required to reconcile.
            # No arbitrary response cost field or token-derived estimate is actual cost.
            if not isinstance(response,dict) or set(response)!={'body','actualUsd'}:
                raise ValueError('TRANSPORT_ENVELOPE_INVALID')
            elapsed=time.monotonic()-started
            timing['elapsed']=elapsed
            actual=response['actualUsd']
            budget.finish(request_id,actual_usd=actual)
            verify_source()
            result=response['body']
            if isinstance(result,dict):result=dict(result)
            return result
        try:
            result=await mock_screen_once(directory,scenario='platform',model=model,packet=packet,
                expected_hash=packet_hash,catalog=catalog,context=context,fake_transport=guarded,
                execution_mode='OFFLINE_MOCK_ONLY' if mock else 'AUTHORIZED_EXPERIMENT')
        except BaseException:
            # Already reconciled outcomes still remain no-replay in the cell guard.
            try:budget.finish(request_id,uncertain=True)
            except ValueError:pass
            raise
        result.update(model=model,mode='OFFLINE_MOCK' if mock else 'AUTHORIZED_EXPERIMENT',
                      latencySeconds=round(timing['elapsed'],3))
        results.append(result)
        if not budget.snapshot()['ready']:break
    return results
