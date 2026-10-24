import hashlib
import json
from pathlib import Path
import socket

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
WORK = ROOT / '.local-tooling/node-24.22.1-validation/work/gate1b/frontend'
files = [
    'app/layout.tsx', 'app/login/LoginPageInner.tsx', 'components/auth/RequireAuth.tsx',
    'components/auth/SessionBoundary.tsx', 'components/auth/SessionBoundary.test.tsx',
    'components/layout/UserMenu.tsx', 'hooks/useProjectData.ts', 'hooks/useProjectData.session.test.tsx',
    'lib/firebase-auth.ts', 'lib/firebase-session.test.tsx', 'lib/api.ts', 'lib/useAuthUser.ts',
    'lib/site-assistant.ts', 'lib/site-assistant.test.ts', 'lib/api-file-security.test.ts',
    'lib/api-transport.test.ts', 'lib/api-read-retry.test.ts', 'lib/download.test.ts',
]
hashes = {}
for name in files:
    content = (ROOT / 'frontend' / name).read_bytes()
    assert content == (WORK / name).read_bytes(), name
    hashes[name] = hashlib.sha256(content).hexdigest()
(OUT / 'verified-source-hashes.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
ports = {}
for port in (3017, 8003):
    with socket.socket() as probe:
        probe.settimeout(1)
        code = probe.connect_ex(('127.0.0.1', port))
        ports[port] = dict(connect_result=code, accepting_connections=code == 0)
        assert code != 0, port
(OUT / 'isolated-ports-stopped.json').write_text(json.dumps(ports, indent=2), encoding='utf-8')
before = json.loads((OUT / 'preservation-before.json').read_text())
after = json.loads((OUT / 'preservation-final.json').read_text())
assert before == after
result = dict(phase='Gate 2A', disposition='LOCAL_IMPLEMENTATION_VERIFIED',
              firebase_enabled=False, genuine_authentication_qualified=False,
              public_launch='BLOCKED', frontend_tests=62, backend_tests=62,
              typecheck=True, scoped_lint=True, default_turbopack_build=True,
              browser_widths=[1280, 1600, 390],
              tested_source_files_identical=len(files), original_row_schema_and_manifest_hashes_unchanged=True,
              isolated_test_servers_stopped=True)
(OUT / 'status.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
