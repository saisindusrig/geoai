"""Scope Gate 2H verification to the retained isolated copy and portable runtime."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'.local-tooling/node-24.22.1-validation'
WORK=BASE/'work/gate1b/frontend'
assert hashlib.sha256((BASE/'runtime/node-v24.22.1-win-x64/node.exe').read_bytes()).hexdigest()=='d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5'
files=['lib/firebase-auth.ts','lib/firebase-auth.test.ts','lib/firebase-staging-config.test.ts']
hashes={}
for name in files:
    content=(ROOT/'frontend'/name).read_bytes();(WORK/name).write_bytes(content)
    hashes[name]=hashlib.sha256(content).hexdigest()
(OUT/'verified-source-hashes.json').write_text(json.dumps(hashes,indent=2))
guard=(BASE/'gate2f-guard.cjs').read_text().replace('gate-2f','gate-2h').replace('gate2f-ipc-policy.cjs','gate2h-ipc-policy.cjs')
(BASE/'gate2h-guard.cjs').write_text(guard)
policy=(BASE/'gate2f-ipc-policy.cjs').read_text().replace('gate2f','gate2h')
(BASE/'gate2h-ipc-policy.cjs').write_text(policy)
runner=(OUT.parent/'gate-2f/run_frontend_checks.py').read_text().replace('gate2f','gate2h')
runner=runner.replace("'lib/firebase-session.test.tsx', 'app/login/LoginPageInner.test.tsx'", "'lib/firebase-staging-config.test.ts', 'lib/firebase-auth.test.ts', 'lib/firebase-session.test.tsx', 'app/login/LoginPageInner.test.tsx'")
runner=runner.replace("'lib/firebase-auth.ts', 'lib/firebase-session.test.tsx'", "'lib/firebase-auth.ts', 'lib/firebase-staging-config.test.ts', 'lib/firebase-auth.test.ts', 'lib/firebase-session.test.tsx'")
runner=runner.replace('env.update(PATH=', "env['STRUVO_FIREBASE_TEMPLATE_FIXTURE']=str(OUT/'frontend.staging.env.template')\nenv.update(PATH=")
(OUT/'run_frontend_checks.py').write_text(runner)
print('Gate 2H isolated source, Node checksum, no-network guards and focused checks prepared.')
