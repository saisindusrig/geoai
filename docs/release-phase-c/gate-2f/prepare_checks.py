"""Refresh only changed sources in the retained isolated frontend; no dotenv."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.local-tooling/node-24.22.1-validation'
WORK = BASE / 'work/gate1b/frontend'
files = ['lib/firebase-auth.ts', 'lib/firebase-session.test.tsx', 'app/login/LoginPageInner.tsx',
         'app/login/LoginPageInner.test.tsx', 'components/auth/SessionBoundary.tsx', 'components/auth/SessionBoundary.test.tsx']
hashes = {}
for name in files:
    source = (ROOT / 'frontend' / name).read_bytes()
    (WORK / name).write_bytes(source)
    hashes[name] = hashlib.sha256(source).hexdigest()
(OUT / 'verified-source-hashes.json').write_text(json.dumps(hashes, indent=2))
runtime = BASE / 'runtime/node-v24.22.1-win-x64/node.exe'
assert hashlib.sha256(runtime.read_bytes()).hexdigest() == 'd702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5'
policy = (BASE / 'gate2a-ipc-policy.cjs').read_text().replace('next-gate2a', 'next-gate2f(?:-ui-fixture)?')
(BASE / 'gate2f-ipc-policy.cjs').write_text(policy)
guard = (BASE / 'gate2a-guard.cjs').read_text().replace('docs/release-phase-c/gate-2a', 'docs/release-phase-c/gate-2f').replace('gate2a-ipc-policy.cjs', 'gate2f-ipc-policy.cjs')
(BASE / 'gate2f-guard.cjs').write_text(guard)
runner = (OUT.parent / 'gate-2a/run_frontend_checks.py').read_text().replace('gate2a-guard.cjs', 'gate2f-guard.cjs').replace('.next-gate2a', '.next-gate2f')
runner = runner.replace("commands = {", "commands = {\n    'frontend-tests': [str(NODE), 'node_modules/vitest/vitest.mjs', 'run', '--maxWorkers=2', 'lib/firebase-session.test.tsx', 'app/login/LoginPageInner.test.tsx', 'components/auth/SessionBoundary.test.tsx', 'hooks/useProjectData.session.test.tsx', 'lib/site-assistant.test.ts', 'lib/api-file-security.test.ts', 'lib/api-transport.test.ts', 'lib/api-read-retry.test.ts', 'lib/download.test.ts'],")
runner = runner.replace("'lib/firebase-auth.ts', 'lib/firebase-session.test.tsx', 'lib/api.ts'", "'app/login/LoginPageInner.test.tsx', 'lib/firebase-auth.ts', 'lib/firebase-session.test.tsx', 'lib/api.ts'")
(OUT / 'run_frontend_checks.py').write_text(runner)
print('Isolated sources and checks prepared; approved portable Node only.')
