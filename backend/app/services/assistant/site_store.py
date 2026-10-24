"""Owner-scoped assistant history and durable conservative spending reservations.

Separate operational store: never migrates or writes engineering databases.
SQLite transactions serialize reservations across local workers; restart retains
unknown-cost reservations. A killed request's lease expires after five minutes.
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from decimal import Decimal,ROUND_CEILING
from fastapi import HTTPException
from app.core.config import settings


def _money(*values):
    value=sum((Decimal(str(v)) for v in values),Decimal(0))
    return float(max(Decimal(0),value).quantize(Decimal('0.000000000001'),rounding=ROUND_CEILING))


@contextmanager
def connection():
    db = sqlite3.connect(settings.ASSISTANT_HISTORY_DB, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        db.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, owner INTEGER NOT NULL, scope INTEGER NOT NULL, started REAL NOT NULL, status TEXT NOT NULL, model TEXT NOT NULL, reserved REAL NOT NULL, tokens INTEGER NOT NULL, payload TEXT NOT NULL)')
        db.execute('BEGIN IMMEDIATE')
        for row in db.execute("SELECT id,payload FROM tasks WHERE status='RUNNING' AND started<?", (time.time()-300,)).fetchall():
            value=json.loads(row['payload'])
            value['status']='INTERRUPTED'
            value['error']='Previous request interrupted. Reservation retained; retry requires a new explicit request.'
            db.execute('UPDATE tasks SET status=?,payload=? WHERE id=?', ('INTERRUPTED',json.dumps(value),row['id']))
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def history(owner, scope=None):
    with connection() as db:
        query='SELECT payload FROM tasks WHERE owner=?'
        args=(owner,)
        if scope is not None:
            query+=' AND scope=?';args=(owner,scope)
        return [json.loads(row['payload']) for row in db.execute(query+' ORDER BY started DESC LIMIT 30', args)][::-1]


def reserve(owner, scope, task_id, model, amount, tokens, payload):
    now = time.time()
    with connection() as db:
        old = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if old:
            if old['owner'] != owner or old['scope'] != scope:
                raise HTTPException(404, 'Task not found')
            if json.loads(old['payload'])['request'] != payload['request']:
                raise HTTPException(409, 'Request identity already used with different context')
            return json.loads(old['payload'])
        _enforce(db,owner,amount,tokens,new_turn=True)
        db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)', (task_id,owner,scope,now,'RUNNING',model,amount,tokens,json.dumps(payload)))
    return None


def finish(owner, task_id, payload):
    # Accounting columns are changed only by atomic reservation/settlement below.
    with connection() as db:
        db.execute('UPDATE tasks SET status=?, payload=? WHERE id=? AND owner=?', (payload['status'],json.dumps(payload),task_id,owner))


def _snapshot(db,owner):
    now=time.time()
    daily=db.execute('SELECT COUNT(*), COALESCE(SUM(tokens),0) FROM tasks WHERE owner=? AND started>?',(owner,now-86400)).fetchone()
    spent=sum((Decimal(str(r[0])) for r in db.execute('SELECT reserved FROM tasks')),Decimal(0))
    return {'accounted_usd':float(spent),'daily_requests':daily[0],'accounted_daily_tokens':daily[1],
            'active_global':db.execute("SELECT COUNT(*) FROM tasks WHERE status='RUNNING' AND started>?",(now-300,)).fetchone()[0],
            'active_user':db.execute("SELECT COUNT(*) FROM tasks WHERE owner=? AND status='RUNNING' AND started>?",(owner,now-300)).fetchone()[0],
            'recent_requests':db.execute('SELECT COUNT(*) FROM tasks WHERE owner=? AND started>?',(owner,now-60)).fetchone()[0],
            'accounting_blocked':bool(db.execute("SELECT EXISTS(SELECT 1 FROM tasks WHERE json_extract(payload,'$.accounting_blocked')=1)").fetchone()[0])}


def snapshot(owner):
    with connection() as db:
        return _snapshot(db,owner)


def _enforce(db,owner,amount,tokens,*,new_turn):
    state=_snapshot(db,owner)
    code=None
    if state['accounting_blocked']:code='ACCOUNTING_REVIEW_REQUIRED'
    elif new_turn and (state['active_global']>=2 or state['active_user']):code='CONCURRENCY_LIMIT'
    elif new_turn and state['recent_requests']>=10:code='RATE_LIMITED'
    elif new_turn and state['daily_requests']>=settings.ASSISTANT_DAILY_REQUESTS:code='DAILY_REQUEST_LIMIT'
    elif state['accounted_daily_tokens']+tokens>settings.ASSISTANT_DAILY_TOKENS:code='TOKEN_LIMIT'
    elif sum((Decimal(str(r[0])) for r in db.execute('SELECT reserved FROM tasks')),Decimal(0))+Decimal(str(amount))>Decimal(str(settings.ASSISTANT_BUDGET_USD)):code='BUDGET_LIMIT'
    if code:
        message='Inference disabled: review provider identity and accounting before any further request.' if code=='ACCOUNTING_REVIEW_REQUIRED' else f'Assistant {code.lower().replace("_"," ")} reached. No further inference requested. Retry manually after reviewing the allowance.'
        raise HTTPException(503 if code=='ACCOUNTING_REVIEW_REQUIRED' else 429,{'code':code,'message':message,
                            'availability':'DISABLED' if code=='ACCOUNTING_REVIEW_REQUIRED' else 'RATE_LIMITED'})


def reserve_next(owner,task_id,quote,task):
    """Reserve a continuation only after its exact tool results exist."""
    with connection() as db:
        row=db.execute('SELECT * FROM tasks WHERE id=? AND owner=?',(task_id,owner)).fetchone()
        if not row or row['status']!='RUNNING':raise HTTPException(409,'Task is not active')
        stored=json.loads(row['payload'])
        if len(stored.get('requests',[]))!=1:raise HTTPException(409,'Continuation was already reserved')
        _enforce(db,owner,quote['reserved_usd'],quote['tokens'],new_turn=False)
        task['requests'].append(quote)
        task['reserved_usd']=_money(row['reserved'],quote['reserved_usd'])
        task['budget_accounted_usd']=task['reserved_usd']
        db.execute('UPDATE tasks SET reserved=?,tokens=?,payload=? WHERE id=? AND owner=?',
                   (task['reserved_usd'],row['tokens']+quote['tokens'],json.dumps(task),task_id,owner))


def settle(owner,task_id,index,usage,task,*,not_sent=False):
    """Reported token costs are estimates, never actual provider charges."""
    from app.services.assistant.site_provider import reported_accounting
    with connection() as db:
        row=db.execute('SELECT * FROM tasks WHERE id=? AND owner=?',(task_id,owner)).fetchone()
        if not row:raise HTTPException(404,'Task not found')
        stored=json.loads(row['payload'])
        quote=stored['requests'][index]
        if quote['state']!='RESERVED':
            return  # Exactly once: duplicate terminal/usage events cannot refund twice.
        accounting=reported_accounting(quote,usage)
        cost=quote['reserved_usd'];tokens=quote['tokens']
        if not_sent:
            quote['state']='NOT_SENT';cost=0;tokens=0
        elif accounting is None:
            quote['state']='USAGE_UNKNOWN'
        elif accounting['within_bound']:
            cost=accounting['estimated_usd'];tokens=accounting['tokens']
            quote.update(state='REPORTED_ESTIMATE',reported_usage=usage,estimated_usd=cost)
        else:
            cost=max(cost,accounting['estimated_usd']);tokens=max(tokens,accounting['tokens'])
            quote.update(state='BOUND_EXCEEDED',reported_usage=usage,estimated_usd=accounting['estimated_usd'])
            task['accounting_blocked']=True
        total_cost=_money(row['reserved'],-quote['reserved_usd'],cost)
        total_tokens=max(0,row['tokens']-quote['tokens']+tokens)
        task['requests'][index]=quote
        task['reserved_usd']=total_cost
        task['budget_accounted_usd']=total_cost
        task['accounted_tokens']=total_tokens
        db.execute('UPDATE tasks SET reserved=?,tokens=?,payload=? WHERE id=? AND owner=?',
                   (total_cost,total_tokens,json.dumps(task),task_id,owner))
