import os,time,json,subprocess,psutil
from pathlib import Path
root=Path.cwd();base=root/'.local-tooling/node-24.22.1-validation';out=root/'docs/release-phase-c/gate-1c';env=os.environ.copy()
for k in ('GOOGLE_APPLICATION_CREDENTIALS','FIREBASE_AUTH_CREDENTIALS_FILE','NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','GEOAI_BETA_VALIDATION'):env.pop(k,None)
env.update(NODE_OPTIONS='--require="'+(base/'gate1c-guard.cjs').as_posix()+'"',TMP=str(base/'work/temp'),TEMP=str(base/'work/temp'),GEOAI_LOCAL_API_PORT='8003',NEXT_TELEMETRY_DISABLED='1',NPM_CONFIG_USERCONFIG=str(base/'work/gate1c/empty-user.npmrc'),NPM_CONFIG_GLOBALCONFIG=str(base/'work/gate1c/empty-global.npmrc'),NPM_CONFIG_CACHE=str(base/'work/gate1c/npm-cache'),NPM_CONFIG_UPDATE_NOTIFIER='false',STRUVOCIVIL_GATE1C_BUILD_DIR=str(base/'work/gate1b/frontend'),STRUVOCIVIL_GATE1C_CAPTURE=str(out/'launcher-build-runtime.json'))
start=time.monotonic();samples=[];timeout=False
with (out/'build.log').open('wb') as log:
 p=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(base/'work/gate1c/launch-capture/start-copilot-review.ps1')],env=env,stdout=log,stderr=subprocess.STDOUT);parent=psutil.Process(p.pid)
 while p.poll() is None:
  try:tree=[parent]+parent.children(recursive=True)
  except psutil.Error:tree=[]
  rss=cpu=0
  for q in tree:
   try:rss+=q.memory_info().rss;t=q.cpu_times();cpu+=t.user+t.system
   except psutil.Error:pass
  elapsed=time.monotonic()-start;samples.append(dict(elapsed=round(elapsed,2),processes=len(tree),rss=rss,cpu_seconds=round(cpu,2)));(out/'build-resources.json').write_text(json.dumps(samples,indent=2))
  if elapsed>=180:
   timeout=True
   for q in reversed(tree):
    try:q.kill()
    except psutil.Error:pass
   break
  time.sleep(5)
 code=p.wait(timeout=10)
result=dict(exit_code=code,timeout=timeout,elapsed_seconds=round(time.monotonic()-start,2),standard_npm_build=True,environment_from_copied_transitioned_launcher=True,normal_ports_untouched=True);(out/'build-result.json').write_text(json.dumps(result,indent=2));print(result)
