from concurrent.futures import ThreadPoolExecutor
import time
import pytest
from app.experimental.bim_testing_budget import TestingBudget as Budget, money


def contract(rate='1000'):
    # Synthetic rates only; never provider confirmation.
    return dict(accountPricingVerified=True,allBillableTokensBounded=True,feesIncluded=True,
                validUntilEpoch=time.time()+60,inputUsdPerMillion=rate,outputUsdPerMillion=rate,
                sourceHash='0'*64,model='MOCK')


def prepared(tmp_path,opening=0):
    ledger=Budget(tmp_path/'budget.db');ledger.create(opening_spend_usd=opening)
    ledger.authorize_batch('first',authority='OFFLINE_MOCK_ONLY',phase='UNDERSTAND',max_requests=15)
    return ledger


def reserve(ledger,id='1',**kwargs):return ledger.reserve(id,batch=kwargs.get('batch','first'),model='MOCK',contract=kwargs.get('contract',contract()))


def test_cumulative_across_models_phases_and_no_reset(tmp_path):
    ledger=prepared(tmp_path)
    assert reserve(ledger)==money('11.692')
    ledger.finish('1',actual_usd='1')
    ledger.authorize_batch('second',authority='SEPARATE_MOCK_AUTHORITY',phase='PLAN_EXPAND',max_requests=1)
    with pytest.raises(ValueError,match='EXHAUSTED'):reserve(ledger,'2',batch='second')
    assert ledger.snapshot()['heldNanodollars']==money('11.692')
    with pytest.raises(FileExistsError):ledger.create(opening_spend_usd=0)


def test_unknown_opening_and_unauthorized_batch(tmp_path):
    ledger=prepared(tmp_path,None)
    with pytest.raises(ValueError,match='UNRECONCILED'):reserve(ledger)
    ledger=prepared(tmp_path/'other')
    with pytest.raises(ValueError,match='AUTHORIZATION'):reserve(ledger,batch='missing')


@pytest.mark.parametrize('key',['accountPricingVerified','allBillableTokensBounded','feesIncluded'])
def test_unverified_contract_blocks_before_reservation(tmp_path,key):
    ledger=prepared(tmp_path);value=contract();value[key]=False
    with pytest.raises(ValueError,match='UNVERIFIED'):reserve(ledger,contract=value)
    assert ledger.snapshot()['requests']==0


def test_expired_contract(tmp_path):
    ledger=prepared(tmp_path);value=contract();value['validUntilEpoch']=0
    with pytest.raises(ValueError,match='STALE'):reserve(ledger,contract=value)


@pytest.mark.parametrize('uncertain,actual',[(True,None),(False,None),(False,'12')])
def test_uncertain_or_unaccounted_never_frees_reservation(tmp_path,uncertain,actual):
    ledger=prepared(tmp_path);reserve(ledger)
    ledger.finish('1',uncertain=uncertain,actual_usd=actual)
    with pytest.raises(ValueError,match='HALTED'):reserve(ledger,'2')
    assert ledger.snapshot()['heldNanodollars']==money('11.692')


def test_concurrent_and_crash_reservation_fail_closed(tmp_path):
    ledger=prepared(tmp_path)
    def attempt(id):
        try:reserve(ledger,id);return True
        except ValueError:return False
    with ThreadPoolExecutor(2) as pool:assert sum(pool.map(attempt,['1','2']))==1
    restarted=Budget(ledger.path)
    with pytest.raises(ValueError,match='ACTIVE'):reserve(restarted,'3')


def test_round_up_no_float_and_unknowns(tmp_path):
    assert money('0.0000000001')==1
    for value in [True,-1,'NaN','Infinity']:
        with pytest.raises(ValueError):money(value)
    ledger=prepared(tmp_path,20)
    with pytest.raises(ValueError,match='EXHAUSTED'):reserve(ledger)
