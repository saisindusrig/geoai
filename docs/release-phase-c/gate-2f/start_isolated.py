"""Start only synthetic read-only API and isolated built frontend; never normal ports."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.local-tooling/node-24.22.1-validation'
NODE = BASE / 'runtime/node-v24.22.1-win-x64/node.exe'
for port in (3017, 8003):
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', port)) == 0:
            raise SystemExit(f'Validation port {port} occupied; no existing process will be disturbed.')
env = os.environ.copy()
for key in list(env):
    if any(word in key.upper() for word in ('CREDENTIAL', 'API_KEY', 'FIREBASE', 'NEBIUS', 'SENTRY')):
        env.pop(key, None)
env.update(PATH=str(NODE.parent) + os.pathsep + env.get('PATH', ''),
           NODE_OPTIONS='--require="' + (BASE / 'gate2f-guard.cjs').as_posix() + '"',
           TEMP=str(BASE / 'work/temp'), TMP=str(BASE / 'work/temp'),
           NEXT_PUBLIC_FIREBASE_AUTH_ENABLED='false', NEXT_PUBLIC_API_URL='/local-api',
           GEOAI_LOCAL_REVIEW='true',
           GEOAI_LOCAL_API_PORT='8003', NEXT_TELEMETRY_DISABLED='1')
commands = {
    'api': ([str(ROOT / 'backend/.venv/Scripts/python.exe'), str(OUT / 'serve_isolated.py')], ROOT),
    'frontend': ([str(NODE), 'node_modules/next/dist/bin/next', 'start', '-p', '3017', '-H', '127.0.0.1'], BASE / 'work/gate1b/frontend'),
}
processes = {}
for name, (command, cwd) in commands.items():
    with (OUT / (name + '-server.log')).open('wb') as log:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    processes[name] = child.pid
(OUT / 'owned-server-processes.json').write_text(json.dumps(processes, indent=2), encoding='utf-8')
print(processes)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for url in ('http://127.0.0.1:8003/api/health', 'http://127.0.0.1:3017/'):
    deadline = time.monotonic() + 40
    while True:
        try:
            with opener.open(url, timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        if time.monotonic() > deadline:
            raise SystemExit('Isolated validation service readiness timed out')
        time.sleep(0.25)
print('Both isolated services ready')
