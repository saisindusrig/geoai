"""Only tmp_path databases/evidence. No original snapshot, restore or solver."""
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.services import storage
from app.services.recovery_policy import assess_recovery


@pytest.fixture
def local(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, 'LOCAL_STORAGE_DIR', str(tmp_path))
    monkeypatch.setattr(storage.settings, 'ENVIRONMENT', 'development')
    monkeypatch.setattr(storage, '_get_s3', lambda: None)
    return tmp_path


def test_atomic_publish_failure_preserves_existing_final_bytes(local, monkeypatch):
    key='projects/1/result.bin'
    storage.save_file(key,b'previous verified bytes','application/octet-stream')
    def interrupted(*args): raise OSError('Synthetic interrupted publication')
    monkeypatch.setattr(storage.os,'replace',interrupted)
    with pytest.raises(OSError): storage.save_file(key,b'partial replacement','application/octet-stream')
    assert (local/key).read_bytes()==b'previous verified bytes'
    assert not list(local.rglob('.publish-*'))


def test_flush_failure_publishes_nothing(local,monkeypatch):
    def unavailable(*args): raise OSError('Synthetic disk failure')
    monkeypatch.setattr(storage.os,'fsync',unavailable)
    with pytest.raises(OSError):storage.save_file('projects/1/new.bin',b'new','application/octet-stream')
    assert not (local/'projects/1/new.bin').exists()
    assert not list(local.rglob('.publish-*'))


@pytest.mark.parametrize('key',['../escape','/outside','projects\\1\\escape',''])
def test_storage_keys_cannot_escape_root(local,key):
    with pytest.raises(ValueError):storage.save_file(key,b'x','application/octet-stream')


def test_production_storage_never_falls_back_or_creates_bucket(monkeypatch):
    monkeypatch.setattr(storage.settings,'ENVIRONMENT','production')
    monkeypatch.setattr(storage.settings,'S3_ACCESS_KEY','')
    storage.reset_storage_cache()
    for _ in range(2):
        with pytest.raises(RuntimeError):storage._get_s3()
    storage.reset_storage_cache()


@pytest.mark.parametrize('state',['AUTHORIZED','RUNNING','PUBLISHING','INTERRUPTED','FAILED','COMPLETED'])
def test_uncertain_worker_crash_duplicate_and_partial_publication_never_rerun(state):
    result=assess_recovery(state=state,exact_authorization=True,current_source=True,database_available=True,storage_available=True,complete_manifest=False,artifact_hashes_match=False)
    assert result.state=='REVIEW_REQUIRED' and not result.may_execute


@pytest.mark.parametrize('change',[
    {'database_available':False},{'storage_available':False},
    {'current_source':False},{'exact_authorization':False}])
def test_failure_and_stale_sources_cannot_resume(change):
    values=dict(state='RUNNING',exact_authorization=True,current_source=True,database_available=True,storage_available=True,complete_manifest=True,artifact_hashes_match=True)
    decision=assess_recovery(**{**values,**change})
    assert decision.state in ('UNAVAILABLE','REJECTED') and not decision.may_execute


def test_completed_duplicate_only_returns_existing_evidence():
    decision=assess_recovery(state='COMPLETED',exact_authorization=True,current_source=True,database_available=True,storage_available=True,complete_manifest=True,artifact_hashes_match=True)
    assert decision.state=='COMPLETED' and not decision.may_execute


def test_synthetic_sqlite_backup_restore_preserves_ids_hashes_relationships_and_rollback(tmp_path):
    # All bytes below originate in this test. Original databases are never opened.
    original=tmp_path/'synthetic.db'; backup=tmp_path/'synthetic-backup.db'; restored=tmp_path/'synthetic-restored.db'
    artifact=tmp_path/'synthetic-proof.bin';artifact.write_bytes(b'Synthetic evidence, no numerical calculation')
    document=json.dumps({'project_id':11,'revision_id':22,'components':[]},sort_keys=True)
    sha=hashlib.sha256(document.encode()).hexdigest();proof=hashlib.sha256(artifact.read_bytes()).hexdigest()
    with sqlite3.connect(original) as db:
        db.executescript('PRAGMA foreign_keys=ON; CREATE TABLE projects(id INTEGER PRIMARY KEY,owner INTEGER); CREATE TABLE revisions(id INTEGER PRIMARY KEY,project INTEGER REFERENCES projects(id),document TEXT,sha TEXT); CREATE TABLE results(id INTEGER PRIMARY KEY,revision INTEGER REFERENCES revisions(id),proof TEXT);')
        db.execute('INSERT INTO projects VALUES(11,7)');db.execute('INSERT INTO revisions VALUES(22,11,?,?)',(document,sha));db.execute('INSERT INTO results VALUES(33,22,?)',(proof,));db.commit()
        try:
            db.execute('INSERT INTO results VALUES(44,22,?)',('uncommitted',));raise OSError('Synthetic database failure')
        except OSError:db.rollback()
        with sqlite3.connect(backup) as target:db.backup(target)
    with sqlite3.connect(backup) as source, sqlite3.connect(restored) as target:source.backup(target)
    with sqlite3.connect(restored) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('SELECT p.id,p.owner,r.id,s.id,r.sha,s.proof FROM projects p JOIN revisions r ON r.project=p.id JOIN results s ON s.revision=r.id').fetchone()==(11,7,22,33,sha,proof)
        assert db.execute('SELECT count(*) FROM results').fetchone()[0]==1
    artifact.write_bytes(b'corrupted synthetic file')
    assert hashlib.sha256(artifact.read_bytes()).hexdigest()!=proof


def test_assistant_spending_transactions_across_connections_survive_restart(tmp_path,monkeypatch):
    from app.services.assistant import site_store
    from app.core.config import settings
    from fastapi import HTTPException
    monkeypatch.setattr(settings,'ASSISTANT_HISTORY_DB',str(tmp_path/'synthetic-ledger.db'))
    monkeypatch.setattr(settings,'ASSISTANT_BUDGET_USD',1.)
    monkeypatch.setattr(settings,'ASSISTANT_DAILY_TOKENS',100000)
    monkeypatch.setattr(settings,'ASSISTANT_DAILY_REQUESTS',100)
    def reserve(owner):
        try:
            task={'id':str(owner),'request':{'owner':owner},'status':'RUNNING'}
            site_store.reserve(owner,owner,str(owner),'mock',.6,10,task)
            return True
        except HTTPException:return False
    with ThreadPoolExecutor(max_workers=2) as workers:outcomes=list(workers.map(reserve,[1,2]))
    assert sorted(outcomes)==[False,True]
    assert site_store.snapshot(1)['accounted_usd']==.6
    with site_store.connection() as db:db.execute('UPDATE tasks SET started=0')
    # Reopened ledger marks the interrupted lease, retaining its full reservation.
    assert site_store.snapshot(2)['accounted_usd']==.6
    with site_store.connection() as db:assert db.execute('SELECT status FROM tasks').fetchone()[0]=='INTERRUPTED'

@pytest.mark.parametrize('status',['AUTHORIZED','SOLVER_FAILED'])
def test_real_engineering_route_never_reexecutes_uncertain_attempt(db_session,monkeypatch,status):
    from app.api.routes import physical_frames as route
    from app.db.models import ModelRevision,EngineeringAnalysis
    from app.services.design.opensees_benchmark import digest
    from test_physical_column import seed
    from fastapi import HTTPException
    seed(db_session)
    document=db_session.get(ModelRevision,1).document_json
    result={'model_document_sha256':digest(document),'input_record_id':None,'proposal_sha256':'a'*64,'missing':[],'component_ids':[]}
    row=EngineeringAnalysis(id=99,project_id=1,model_revision_id=1,analysis_type=route.PROPOSAL,algorithm_version='synthetic-recovery',status=status,actor_user_id=1,result_json=result)
    db_session.add(row);db_session.commit()
    def forbidden(*args,**kwargs):raise AssertionError('Solver must never execute during recovery test')
    monkeypatch.setattr(route.solver,'run',forbidden)
    with pytest.raises(HTTPException) as error:route.run(1,route.Authorize(proposal_id=99,proposal_sha256='a'*64,authorize_solver=True),db_session,1)
    assert error.value.status_code==409 and row.status==status
    # Even an apparently pending request must still match the original document hash.
    row.status='AWAITING_AUTHORIZATION';row.result_json={**result,'model_document_sha256':'stale'};db_session.commit()
    with pytest.raises(HTTPException) as error:route.run(1,route.Authorize(proposal_id=99,proposal_sha256='a'*64,authorize_solver=True),db_session,1)
    assert error.value.status_code==409
