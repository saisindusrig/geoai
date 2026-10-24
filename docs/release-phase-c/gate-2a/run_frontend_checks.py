"""Validate only the retained isolated frontend with the approved portable runtime."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.local-tooling/node-24.22.1-validation'
WORK = BASE / 'work/gate1b/frontend'
NODE = BASE / 'runtime/node-v24.22.1-win-x64/node.exe'
env = os.environ.copy()
for key in list(env):
    if any(word in key.upper() for word in ('CREDENTIAL', 'API_KEY', 'FIREBASE', 'NEBIUS', 'SENTRY')):
        env.pop(key, None)
env.update(PATH=str(NODE.parent) + os.pathsep + env.get('PATH', ''),
           NODE_OPTIONS='--require="' + (BASE / 'gate2a-guard.cjs').as_posix() + '"',
           TEMP=str(BASE / 'work/temp'), TMP=str(BASE / 'work/temp'),
           NEXT_PUBLIC_FIREBASE_AUTH_ENABLED='false', NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED='false',
           NEXT_PUBLIC_API_URL='/local-api', GEOAI_LOCAL_API_PORT='8003',
           GEOAI_LOCAL_REVIEW='true',
           NEXT_TELEMETRY_DISABLED='1', NPM_CONFIG_UPDATE_NOTIFIER='false')
config = WORK / 'next.config.ts'
source = (ROOT / 'frontend/next.config.ts').read_text(encoding='utf-8')
lines = source.splitlines()
config.write_text('\n'.join('  distDir: ".next-gate2a",' if line.strip().startswith('distDir:') else line for line in lines) + '\n', encoding='utf-8')
commands = {
    'typescript': [str(NODE), 'node_modules/typescript/bin/tsc', '--noEmit', '--incremental', 'false'],
    'lint': [str(NODE), 'node_modules/eslint/bin/eslint.js',
             'lib/firebase-auth.ts', 'lib/firebase-session.test.tsx', 'lib/api.ts', 'lib/site-assistant.ts',
             'lib/site-assistant.test.ts', 'lib/useAuthUser.ts', 'components/auth/SessionBoundary.tsx',
             'components/auth/SessionBoundary.test.tsx', 'components/auth/RequireAuth.tsx',
             'components/layout/UserMenu.tsx', 'app/layout.tsx', 'app/login/LoginPageInner.tsx',
             'hooks/useProjectData.ts', 'hooks/useProjectData.session.test.tsx', 'lib/api-file-security.test.ts',
             'lib/api-transport.test.ts', 'lib/api-read-retry.test.ts', 'lib/download.test.ts'],
    'build': [str(NODE), str(NODE.parent / 'node_modules/npm/bin/npm-cli.js'), 'run', 'build'],
}
results = {}
for name, command in commands.items():
    start = time.monotonic()
    with (OUT / (name + '.log')).open('wb') as log:
        process = subprocess.Popen(command, cwd=WORK, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code = process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            # Only this controller's just-created validation process tree.
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            code = -1
    results[name] = dict(exit_code=code, elapsed_seconds=round(time.monotonic() - start, 2))
    (OUT / 'frontend-checks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(name, results[name], flush=True)
    if code:
        raise SystemExit(code)
