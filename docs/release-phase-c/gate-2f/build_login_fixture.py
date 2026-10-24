"""Test-only SDK aliases in isolated copy; never modifies normal Firebase code/config."""
import os
from pathlib import Path
import subprocess
import json
import time
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / '.local-tooling/node-24.22.1-validation'
WORK = BASE / 'work/gate1b/frontend'
NODE = BASE / 'runtime/node-v24.22.1-win-x64/node.exe'
fixture = WORK / 'gate2f-sdk-fixture'
fixture.mkdir(exist_ok=True)
(fixture / 'app.js').write_text('export const getApps=()=>[]; export const initializeApp=(options,name)=>({options,name});')
(fixture / 'auth.js').write_text('''
export const inMemoryPersistence="OFFLINE_MEMORY_FIXTURE";
export const browserPopupRedirectResolver="OFFLINE_POPUP_FIXTURE";
export const initializeAuth=()=>({});
let changed;
export const onIdTokenChanged=(_, next)=>{changed=next; queueMicrotask(()=>next(null));return ()=>{changed=undefined;};};
export class GoogleAuthProvider {setCustomParameters(value){window.__fixtureParameters=value;}}
function result(provider){
 const outcome=window.__fixtureOutcome||"valid";
 const errors={cancel:"auth/popup-closed-by-user",blocked:"auth/popup-blocked",collision:"auth/account-exists-with-different-credential",signup:"auth/admin-restricted-operation"};
 if(errors[outcome])return Promise.reject({code:errors[outcome],message:"SENSITIVE_MOCK_DETAIL"});
 const uid=outcome==="unlinked"?"unlinked":provider;
 const user={uid,getIdToken:async()=>"offline-firebase-id-"+uid};
 queueMicrotask(()=>changed?.(user));return Promise.resolve({user});
}
export const signInWithPopup=()=>result("google");
export const signInWithEmailAndPassword=()=>result("password");
export const signOut=async()=>{changed?.(null);};
export const sendPasswordResetEmail=async()=>{throw Error("Recovery not authorized in offline browser fixture");};
''')
config = (ROOT / 'frontend/next.config.ts').read_text()
config = '\n'.join('  distDir: ".next-gate2f-ui-fixture",' if line.strip().startswith('distDir:') else line for line in config.splitlines())
config = config.replace('const nextConfig: NextConfig = {', 'const nextConfig: NextConfig = {\n  turbopack: { resolveAlias: {"firebase/app":"./gate2f-sdk-fixture/app.js", "firebase/auth":"./gate2f-sdk-fixture/auth.js"} },')
(WORK / 'next.config.ts').write_text(config)
env = os.environ.copy()
for key in list(env):
    if any(word in key.upper() for word in ('CREDENTIAL', 'API_KEY', 'FIREBASE', 'NEBIUS', 'SENTRY')):
        env.pop(key, None)
env.update(PATH=str(NODE.parent)+os.pathsep+env.get('PATH',''), NODE_OPTIONS='--require="'+(BASE/'gate2f-guard.cjs').as_posix()+'"',
    TEMP=str(BASE/'work/temp'),TMP=str(BASE/'work/temp'),NEXT_TELEMETRY_DISABLED='1',GEOAI_LOCAL_REVIEW='true',GEOAI_LOCAL_API_PORT='8003',
    NEXT_PUBLIC_API_URL='/local-api',NEXT_PUBLIC_FIREBASE_AUTH_ENABLED='true',NEXT_PUBLIC_FIREBASE_PASSWORD_PROVIDER_ENABLED='true',NEXT_PUBLIC_FIREBASE_GOOGLE_PROVIDER_ENABLED='true',
    NEXT_PUBLIC_FIREBASE_PROJECT_ID='synthetic-auth-project',NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN='synthetic-auth-project.firebaseapp.com',
    NEXT_PUBLIC_FIREBASE_API_KEY='synthetic-public-browser-key-not-real',NEXT_PUBLIC_FIREBASE_APP_ID='1:123:web:abc123',NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED='false')
start=time.monotonic()
with (OUT/'offline-ui-build.log').open('wb') as log:
    child=subprocess.Popen([str(NODE),'node_modules/next/dist/bin/next','build'],cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try: code=child.wait(timeout=180)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20);code=-1
(OUT/'offline-ui-build.json').write_text(json.dumps(dict(exit_code=code,elapsed_seconds=round(time.monotonic()-start,2),test_sdk_aliases_only=True,not_real_firebase=True),indent=2))
raise SystemExit(code)
