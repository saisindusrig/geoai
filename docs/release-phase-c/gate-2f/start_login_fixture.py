"""Switch only the owned isolated frontend, never normal website processes."""
import json
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.local-tooling/node-24.22.1-validation'
NODE = BASE / 'runtime/node-v24.22.1-win-x64/node.exe'
owned = json.loads((OUT/'owned-server-processes.json').read_text())
assert owned['frontend'] == 1616  # this run's recorded owned service only
subprocess.run(['taskkill','/PID',str(owned['frontend']),'/T','/F'],check=True,capture_output=True,timeout=20)
env=os.environ.copy()
for key in list(env):
    if any(word in key.upper() for word in ('CREDENTIAL','API_KEY','FIREBASE','NEBIUS','SENTRY')): env.pop(key,None)
env.update(PATH=str(NODE.parent)+os.pathsep+env.get('PATH',''), NODE_OPTIONS='--require="'+(BASE/'gate2f-guard.cjs').as_posix()+'"',
    NEXT_TELEMETRY_DISABLED='1',GEOAI_LOCAL_REVIEW='true',GEOAI_LOCAL_API_PORT='8003',NEXT_PUBLIC_API_URL='/local-api')
with (OUT/'offline-ui-server.log').open('wb') as log:
    child=subprocess.Popen([str(NODE),'node_modules/next/dist/bin/next','start','-p','3017','-H','127.0.0.1'],cwd=BASE/'work/gate1b/frontend',env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
(OUT/'fixture-frontend-pid.json').write_text(json.dumps({'frontend':child.pid},indent=2))
print(child.pid)
