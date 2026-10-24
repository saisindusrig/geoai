"""Run scoped API acceptance tests against a dedicated disposable SQLite file."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
target = Path(__file__).resolve().parents[2] / 'docs/release/regressions.sqlite'
os.environ['DATABASE_URL'] = f'sqlite:///{target.as_posix()}'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:1/15'
os.environ['LOCAL_STORAGE_DIR'] = str(target.parent / 'test-storage')

from app.core.config import settings
assert settings.DATABASE_URL == f'sqlite:///{target.as_posix()}', 'Refuse non-fixture database'
from app.db.models import Base, User, ProjectTemplate
from app.db.session import engine, SessionLocal
Base.metadata.create_all(engine)
with SessionLocal() as db:
    if not db.get(User, 1):
        db.add(User(id=1, name='Acceptance fixture', email='acceptance@example.invalid', role='admin', plan='admin'))
        db.commit()
    if not db.query(ProjectTemplate).first():
        db.add(ProjectTemplate(project_type='building', name='Acceptance template', default_parameters_json={}))
        db.commit()

import pytest
raise SystemExit(pytest.main(['tests/test_project_folders.py','tests/test_job_reliability.py','tests/test_auth_ownership.py','tests/test_admin_roles_audit.py','tests/test_model_revisions.py','tests/test_structural_layout.py','-q']))
