"""Bounded isolated build; stop only this invocation's captured process tree."""
import os,sys,json,time,subprocess,psutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/release-phase-c/gate-1b';BASE=ROOT/'.local-tooling/node-24.22.1-validation';WORK=BASE/'work/gate1b/frontend';NODE=BASE/'runtime/node-v24.22.1-win-x64/node.exe'
mode=sys.argv[1] if len(sys.argv)>1 else 'turbopack';limit=int(sys.argv[2]) if len(sys.argv)>2 else 180;name=sys.argv[3] if len(sys.argv)>3 else mode
assert mode in ('turbopack','webpack');assert 30<=limit<=300
WORK=BASE/'work/gate1b/probe' if os.environ.get('GATE1B_PROBE')=='1' else WORK
assert WORK.resolve().is_relative_to(BASE/'work');env=os.environ.copy()
for k in ('GOOGLE_APPLICATION_CREDENTIALS','FIREBASE_AUTH_CREDENTIALS_FILE','NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY'):env.pop(k,None)
env.update(NODE_OPTIONS='--require="'+(BASE/'gate1b-guard.cjs').as_posix()+'"',TMP=str(BASE/'work/temp'),TEMP=str(BASE/'work/temp'),NEXT_TELEMETRY_DISABLED='1',GEOAI_LOCAL_REVIEW='true',GEOAI_LOCAL_API_PORT='8003',FIREBASE_AUTH_ENABLED='false')
if os.environ.get('GATE1B_PIN_WORKER_PATH')=='1':
 old_path=next((v for k,v in env.items() if k.lower()=='path'),'')
 for k in list(env):
  if k.lower()=='path':del env[k]
 env['PATH']=str(NODE.parent)+os.pathsep+old_path
if os.environ.get('GATE1B_DIST_BETA')=='1':env['GEOAI_BETA_VALIDATION']='true'
with (OUT/(name+'-node-selection.log')).open('wb') as log:
 subprocess.run([str(NODE),'-e',"console.log('parent',process.version,process.execPath);const c=require('node:child_process').spawnSync('node',['-p','process.version+\" \"+process.execPath'],{encoding:'utf8'});console.log('PATH child',c.stdout,c.stderr);process.exitCode=c.status"],cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=20)
with (OUT/(name+'-prebuild.log')).open('wb') as log:
 for script in (() if os.environ.get('GATE1B_PROBE')=='1' else ('scripts/sync-asset-catalogue.js','scripts/copy-cesium.js')):
  subprocess.run([str(NODE),script],cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
args=[str(NODE),'node_modules/next/dist/bin/next','build']+(['--webpack'] if mode=='webpack' else [])
start=time.monotonic();samples=[];timed_out=False
with (OUT/(name+'.log')).open('wb') as log:
 p=subprocess.Popen(args,cwd=WORK,env=env,stdout=log,stderr=subprocess.STDOUT);parent=psutil.Process(p.pid)
 while p.poll() is None:
  elapsed=time.monotonic()-start;rss=cpu=read=write=0;procs=[]
  try:procs=[parent]+parent.children(recursive=True)
  except psutil.Error:pass
  for q in procs:
   try:
    rss+=q.memory_info().rss;t=q.cpu_times();cpu+=t.user+t.system;io=q.io_counters();read+=io.read_bytes;write+=io.write_bytes
   except psutil.Error:pass
  build=WORK/('.next-beta' if os.environ.get('GATE1B_DIST_BETA')=='1' else '.next-phase1');files=bytes_=0
  for folder,_,names in os.walk(build):
   for n in names:
    try:files+=1;bytes_+=(Path(folder)/n).stat().st_size
    except OSError:pass
  sample=dict(elapsed_seconds=round(elapsed,2),visible_processes=len(procs),tree_rss_bytes=rss,visible_tree_cpu_seconds=round(cpu,2),tree_read_bytes=read,tree_write_bytes=write,output_files=files,output_bytes=bytes_);samples.append(sample)
  (OUT/(name+'-resources.json')).write_text(json.dumps(samples,indent=2))
  if len(samples)%4==1:print(json.dumps(sample),flush=True)
  if elapsed>=limit:
   timed_out=True
   for q in reversed(procs):
    try:q.kill()
    except psutil.Error:pass
   break
  time.sleep(5)
 try:code=p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.kill();code=p.wait(timeout=10)
result=dict(mode=mode,limit_seconds=limit,elapsed_seconds=round(time.monotonic()-start,2),timed_out=timed_out,exit_code=code,peak_sampled_tree_rss_bytes=max((r['tree_rss_bytes'] for r in samples),default=0),normal_next_config_exact=None if os.environ.get('GATE1B_PROBE')=='1' else (ROOT/'frontend/next.config.ts').read_bytes()==(WORK/'next.config.ts').read_bytes(),physical_dependencies=True,worker_path_pinned_process_only=os.environ.get('GATE1B_PIN_WORKER_PATH')=='1',environment='isolated local review API port 8003; no credential files; inference/auth disabled')
(OUT/(name+'-result.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);sys.exit(124 if timed_out else code)
