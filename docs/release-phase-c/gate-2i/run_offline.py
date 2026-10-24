"""Run only packet validation, using existing code and no live services/credential discovery."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'.local-tooling/node-24.22.1-validation'
WORK=BASE/'work/gate1b/frontend'
NODE=BASE/'runtime/node-v24.22.1-win-x64/node.exe'
assert hashlib.sha256(NODE.read_bytes()).hexdigest()=='d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5'
source=ROOT/'frontend/lib/firebase-auth.ts'
assert source.read_bytes()==(WORK/'lib/firebase-auth.ts').read_bytes()
(WORK/'lib/gate2i-review.test.ts').write_bytes((OUT/'offline-review.test.ts').read_bytes())
guard=(BASE/'gate2h-guard.cjs').read_text().replace('gate-2h','gate-2i')
(BASE/'gate2i-guard.cjs').write_text(guard)
env={key:value for key,value in os.environ.items() if key in ('SYSTEMROOT','SystemRoot','COMSPEC','PATHEXT','WINDIR')}
env.update(PATH=str(NODE.parent)+os.pathsep+r'C:\Windows\System32',NODE_OPTIONS='--require="'+(BASE/'gate2i-guard.cjs').as_posix()+'"',
 TEMP=str(BASE/'work/temp'),TMP=str(BASE/'work/temp'),STRUVO_GATE2I_REVIEW_DIR=str(OUT),NEXT_PUBLIC_FIREBASE_AUTH_ENABLED='false',
 NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED='false',NEXT_TELEMETRY_DISABLED='1')
start=time.monotonic()
with (OUT/'offline-tests.log').open('wb') as log:
 child=subprocess.Popen([str(NODE),'node_modules/vitest/vitest.mjs','run','--maxWorkers=1','lib/gate2i-review.test.ts'],cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 try: code=child.wait(timeout=60)
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=15);code=-1
result=dict(exit_code=code,elapsed_seconds=round(time.monotonic()-start,2),runtime='24.22.1',validator_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 owner_supplied_console_reference_match='PASS' if code==0 else 'NOT_QUALIFIED',independent_live_verification=False,genuine_authentication=False)
(OUT/'offline-test-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2));raise SystemExit(code)
