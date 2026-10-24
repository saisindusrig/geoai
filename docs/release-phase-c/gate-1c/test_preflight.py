from pathlib import Path
import os,json,shutil,subprocess,hashlib
root=Path.cwd();base=root/'.local-tooling/node-24.22.1-validation';out=root/'docs/release-phase-c/gate-1c';fixtures=base/'work/gate1c/preflight-fixtures';fixtures.mkdir(parents=True,exist_ok=True);runtime=base/'runtime/node-v24.22.1-win-x64';env=os.environ.copy();env.pop('NODE_OPTIONS',None)
for k in ('GOOGLE_APPLICATION_CREDENTIALS','FIREBASE_AUTH_CREDENTIALS_FILE','NEBIUS_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY'):env.pop(k,None)
rows=[]
for case in ('missing','node22','tampered-npm'):
 p=fixtures/case;(p/'scripts').mkdir(parents=True,exist_ok=True)
 for n in ('run-website.bat','start-copilot-review.ps1'):shutil.copyfile(root/n,p/n)
 shutil.copyfile(root/'scripts/verify-local-node.cjs',p/'scripts/verify-local-node.cjs')
 target=p/'.local-tooling/node-24.22.1-validation/runtime/node-v24.22.1-win-x64'
 if case!='missing':
  for name in json.loads((out/'runtime-verification.json').read_text())['critical_files']:
   dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(runtime/name,dst)
  if case=='node22':shutil.copyfile('C:/Program Files/nodejs/node.exe',target/'node.exe')
  else:
   with (target/'node_modules/npm/bin/npm-cli.js').open('a') as f:f.write('\n// synthetic altered-file fixture\n')
 for kind,args in [('batch',['cmd.exe','/d','/c',str(p/'run-website.bat'),'--check-runtime']),('powershell',['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(p/'start-copilot-review.ps1'),'-CheckRuntime'])]:
  result=subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20);assert result.returncode!=0,(case,kind);(out/(case+'-'+kind+'.log')).write_text(result.stdout);rows.append(dict(case=case,launcher=kind,rejected=True,exit_code=result.returncode))
# Actual launcher must restore the caller's PATH; no startup happens in check mode.
script=f"$before=$env:PATH; & '{root/'start-copilot-review.ps1'}' -CheckRuntime; if ($LASTEXITCODE -ne 0) {{ exit 1 }}; if ($before -cne $env:PATH) {{ throw 'PATH leaked' }}; node -p 'process.version'"
r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',script],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20);assert r.returncode==0,r.stdout;assert 'v22.18.0' in r.stdout;(out/'path-restoration.log').write_text(r.stdout)
# Demonstrate the exact byte rollback in a separate fixture, never against original data.
p=fixtures/'rollback';p.mkdir(exist_ok=True);hashes={}
for n in ('run-website.bat','start-copilot-review.ps1'):
 shutil.copyfile(root/n,p/n);shutil.copyfile(out/'rollback'/n,p/n);h=hashlib.sha256((p/n).read_bytes()).hexdigest();assert h==json.loads((out/'before.json').read_text())['launcher_sha256'][n];hashes[n]=h
old_node=subprocess.check_output(['node','-p','process.version'],env=env,cwd=p,text=True).strip();assert old_node=='v22.18.0'
(out/'rollback-demonstration.json').write_text(json.dumps(dict(restored_bytes_match=True,launcher_sha256=hashes,inherited_node_after_restore=old_node,original_files_not_restored_during_test=True),indent=2))
(out/'preflight-tests.json').write_text(json.dumps(dict(negative_cases=rows,actual_powershell_path_restored=True,batch_setlocal_present='setlocal' in (root/'run-website.bat').read_text().lower(),normal_parent_node_unchanged=old_node),indent=2));print('6 negative launcher cases rejected; PATH restoration and exact-byte rollback passed')
