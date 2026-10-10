"""Offline-tested shared experimental budget; no provider/production integration.

Reviewed billing bounds, an opening reconciliation and explicit batch authority
are prerequisites. Missing accounting is never interpreted as free usage.
"""
from decimal import Decimal, ROUND_CEILING
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3

LIMIT = 20_000_000_000  # integer nanodollars; USD only


def money(value):
    if isinstance(value, bool):raise ValueError('INVALID_USD')
    number=Decimal(str(value))
    if not number.is_finite() or number<0:raise ValueError('INVALID_USD')
    return int((number*1_000_000_000).to_integral_value(rounding=ROUND_CEILING))


class TestingBudget:
    def __init__(self,path):
        self.path=Path(path)

    def create(self, *, opening_spend_usd=None):
        # Never reset an existing cumulative ledger, even an incomplete one.
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('x'):pass
        opening=None if opening_spend_usd is None else money(opening_spend_usd)
        if opening is not None and opening>LIMIT:raise ValueError('BUDGET_EXHAUSTED')
        with self.connect() as db:
            db.executescript('''
                create table budget (id integer primary key, opening integer, halted integer);
                create table batches (id text primary key, authority text, max_requests integer, phase text);
                create table requests (id text primary key, batch text, model text,
                    reservation integer, actual integer, status text, contract text);
            ''')
            db.execute('insert into budget values (1,?,0)',(opening,))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        try:
            db.execute('pragma synchronous=FULL')
            with db:yield db
        finally:db.close()

    def authorize_batch(self,batch, *, authority, phase, max_requests):
        if not authority or phase not in {'UNDERSTAND','PLAN_EXPAND'} or type(max_requests) is not int or not 0<max_requests<=15:
            raise ValueError('BATCH_AUTHORIZATION_REQUIRED')
        with self.connect() as db:
            db.execute('insert into batches values (?,?,?,?)',(batch,authority,max_requests,phase))

    def reserve(self,request_id, *, batch, model, contract):
        # An operator-reviewed upper-bound contract, not public-price guesswork.
        required={'accountPricingVerified','allBillableTokensBounded','feesIncluded','validUntilEpoch',
                  'inputUsdPerMillion','outputUsdPerMillion','sourceHash','model'}
        import time
        if set(contract)!=required or any(contract[k] is not True for k in
                ('accountPricingVerified','allBillableTokensBounded','feesIncluded')):
            raise ValueError('BILLING_CONTRACT_UNVERIFIED')
        if contract['model']!=model or len(contract['sourceHash'])!=64 or any(c not in '0123456789abcdef' for c in contract['sourceHash']) or contract['validUntilEpoch']<=time.time():
            raise ValueError('BILLING_CONTRACT_STALE')
        # Full ceilings, not expected usage, cached-input discounts or average cost.
        cost=money((Decimal(str(contract['inputUsdPerMillion']))*8192+
                    Decimal(str(contract['outputUsdPerMillion']))*3500)/1_000_000)
        if Decimal(str(contract['inputUsdPerMillion']))<0 or Decimal(str(contract['outputUsdPerMillion']))<0:
            raise ValueError('INVALID_USD')
        with self.connect() as db:
            db.execute('begin immediate')
            opening,halted=db.execute('select opening,halted from budget where id=1').fetchone()
            if opening is None:raise ValueError('OPENING_SPEND_UNRECONCILED')
            if halted:raise ValueError('BUDGET_HALTED')
            entry=db.execute('select max_requests from batches where id=?',(batch,)).fetchone()
            if not entry:raise ValueError('BATCH_AUTHORIZATION_REQUIRED')
            if db.execute("select count(*) from requests where status='RESERVED'").fetchone()[0]:
                raise ValueError('SEQUENTIAL_REQUEST_ACTIVE')
            if db.execute('select count(*) from requests where batch=?',(batch,)).fetchone()[0]>=entry[0]:
                raise ValueError('BATCH_REQUEST_LIMIT')
            held=db.execute('select coalesce(sum(reservation),0) from requests').fetchone()[0]
            if opening+held+cost>LIMIT:raise ValueError('BUDGET_EXHAUSTED')
            db.execute('insert into requests values (?,?,?,?,NULL,?,?)',
                       (request_id,batch,model,cost,'RESERVED',json.dumps(contract,sort_keys=True)))
        return cost

    def finish(self,request_id, *, actual_usd=None, uncertain=False):
        actual=None if actual_usd is None else money(actual_usd)
        with self.connect() as db:
            db.execute('begin immediate')
            row=db.execute('select reservation,status from requests where id=?',(request_id,)).fetchone()
            if not row or row[1]!='RESERVED':raise ValueError('NO_REPLAY_OR_RECONCILIATION_RESET')
            halt=uncertain or actual is None or actual>row[0]
            db.execute('update requests set actual=?,status=? where id=?',
                       (actual,'UNCERTAIN' if uncertain else 'ACCOUNTING_BLOCKED' if halt else 'RECONCILED',request_id))
            if halt:db.execute('update budget set halted=1 where id=1')
        # Keep full worst-case charge held even after cheaper actual usage.

    def snapshot(self):
        with self.connect() as db:
            opening,halted=db.execute('select opening,halted from budget where id=1').fetchone()
            held,count=db.execute('select coalesce(sum(reservation),0),count(*) from requests').fetchone()
            actual=db.execute('select sum(actual) from requests').fetchone()[0]
        return dict(capUsd='20.00',developmentReserveUsd='20.00',accountBudgetUserReportedUsd='40.00',
                    openingSpendNanodollars=opening,heldNanodollars=held,actualNanodollars=actual,
                    requests=count,halted=bool(halted),ready=opening is not None and not halted)
