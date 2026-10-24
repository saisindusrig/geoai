import os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'.local-tooling/node-24.22.1-validation';NODE=BASE/'runtime/node-v24.22.1-win-x64/node.exe';env=os.environ.copy()
old=next((v for k,v in env.items() if k.lower()=='path'),'')
for k in list(env):
 if k.lower()=='path' or k in ('GEOAI_BETA_VALIDATION','GOOGLE_APPLICATION_CREDENTIALS','FIREBASE_AUTH_CREDENTIALS_FILE','NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY'):env.pop(k,None)
env.update(PATH=str(NODE.parent)+os.pathsep+old,NODE_OPTIONS='--require="'+(BASE/'gate1b-guard.cjs').as_posix()+'"',TMP=str(BASE/'work/temp'),TEMP=str(BASE/'work/temp'),NEXT_TELEMETRY_DISABLED='1',GEOAI_LOCAL_REVIEW='true',GEOAI_LOCAL_API_PORT='8003',FIREBASE_AUTH_ENABLED='false')
assert (BASE/'work/gate1b/frontend/.next-phase1/BUILD_ID').is_file()
subprocess.run([str(NODE),'node_modules/next/dist/bin/next','start','-p','3017','-H','127.0.0.1'],cwd=BASE/'work/gate1b/frontend',env=env,check=True)
