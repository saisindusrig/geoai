"""Gate 1D offline checks. No SDK initialization, credentials, or live requests."""
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import faulthandler

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'backend/tests'))
# Do not inherit configuration or credentials, or read dotenv sources.
os.environ.clear()
os.environ.update(SYSTEMROOT=r'C:\Windows', PATH=r'C:\Windows\System32',
                  DATABASE_URL='sqlite://', FIREBASE_AUTH_ENABLED='false',
                  NEBIUS_API_KEY='', SENTRY_DSN='', ENVIRONMENT='development')
temp = tempfile.TemporaryDirectory(prefix='struvocivil-gate1d-')
os.environ.update(USERPROFILE=temp.name, TEMP=temp.name, TMP=temp.name)
os.environ['LOCAL_STORAGE_DIR'] = temp.name
os.environ['ASSISTANT_HISTORY_DB'] = str(Path(temp.name) / 'synthetic-history.db')
from pydantic_settings import BaseSettings
original_init = BaseSettings.__init__
def isolated_init(self, *args, **kwargs):
    kwargs['_env_file'] = None
    original_init(self, *args, **kwargs)
BaseSettings.__init__ = isolated_init

network_attempts = []
def denied(*args, **kwargs):
    network_attempts.append('blocked')
    raise RuntimeError('Gate 1D forbids external network access')
socket.create_connection = denied
original_connect = socket.socket.connect
def isolated_connect(self, address):
    # Windows asyncio creates a private loopback socketpair for its wakeup pipe.
    # Permit only that standard-library call site, never application networking.
    if sys._getframe(1).f_code is socket._fallback_socketpair.__code__:
        assert address[0] in ('127.0.0.1', '::1')
        return original_connect(self, address)
    return denied(self, address)
socket.socket.connect = isolated_connect
socket.socket.connect_ex = denied

def audit(event, args):
    if event == 'sqlite3.connect' and str(args[0]) != ':memory:':
        candidate = str(args[0]).lower().replace('\\', '/')
        if '/backend/' in candidate:
            raise RuntimeError('Original backend database access forbidden in tests')
sys.addaudithook(audit)

import firebase_admin
from firebase_admin import auth, credentials
import google.auth
firebase_admin.initialize_app = denied
credentials.Certificate = denied
credentials.ApplicationDefault = denied
google.auth.default = denied
from app.core.config import settings
from app.core import firebase_auth
from fastapi import HTTPException
assert importlib.metadata.version('firebase-admin') == '7.7.0'
assert firebase_admin.__version__ == '7.7.0'
assert not firebase_admin._apps
assert settings.FIREBASE_AUTH_ENABLED is False
assert settings.NEBIUS_API_KEY == ''
assert firebase_auth.readiness()['code'] == 'DISABLED'
def rejected():
    try:
        firebase_auth.verify_identity('synthetic-not-a-token')
    except HTTPException as exc:
        assert exc.status_code == 503
        return
    raise AssertionError('Adapter accepted unavailable authentication')
rejected()
settings.FIREBASE_AUTH_ENABLED = True
settings.AUTH_REQUIRE_JWT = True
assert firebase_auth.readiness()['code'] == 'PROJECT_REQUIRED'
rejected()
settings.FIREBASE_PROJECT_ID = 'synthetic-auth-project'
settings.FIREBASE_AUTH_CREDENTIALS_FILE = ''
assert firebase_auth.readiness()['code'] == 'CREDENTIALS_MISSING'
rejected()
settings.FIREBASE_AUTH_ENABLED = False
settings.AUTH_REQUIRE_JWT = False
settings.FIREBASE_PROJECT_ID = ''
import pytest
faulthandler.dump_traceback_later(90, exit=True)
code = pytest.main(['-q', '-p', 'no:cacheprovider',
    str(ROOT / 'backend/tests/test_firebase_auth.py'),
    str(ROOT / 'backend/tests/test_release_phase_b.py')])
faulthandler.cancel_dump_traceback_later()
assert not firebase_admin._apps
result = dict(sdk_version=firebase_admin.__version__, official_import=True,
              default_disabled=True, missing_project_fail_closed=True,
              missing_credentials_fail_closed=True, sdk_apps_initialized=0,
              forbidden_network_or_credential_attempts=len(network_attempts),
              pytest_exit=int(code), genuine_firebase_qualification=False)
(OUT / 'offline-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
sys.exit(code or bool(network_attempts))
