"""Finalize scoped source/package/row preservation; never imports app settings."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'.local-tooling/node-24.22.1-validation'
WORK=BASE/'work/gate1b/frontend'
prior=json.loads((OUT.parent/'gate-2c/input-hashes-after.json').read_text())
expected={'frontend/lib/firebase-auth.ts','frontend/lib/firebase-session.test.tsx',
 'frontend/app/login/LoginPageInner.tsx','frontend/components/auth/SessionBoundary.tsx','frontend/components/auth/SessionBoundary.test.tsx'}
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in prior}
assert {name for name in prior if prior[name]!=hashes[name]}==expected
sources=json.loads((OUT/'verified-source-hashes.json').read_text())
for name,digest in sources.items():
 assert hashlib.sha256((ROOT/'frontend'/name).read_bytes()).hexdigest()==digest
 assert (ROOT/'frontend'/name).read_bytes()==(WORK/name).read_bytes()
for name,digest in json.loads((ROOT/'docs/gpu-performance/changed-source-hashes.json').read_text()).items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
before=json.loads((OUT/'preservation-before.json').read_text());after=json.loads((OUT/'preservation-after.json').read_text())
for name in ('dev.db','assistant-history.db'): assert before[name]==after[name] and after[name]['baseline_match']
for name,digest in before['hashes'].items(): assert after['hashes'][name]==digest
packages={d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions()}
old={k.lower().replace('_','-'):v for k,v in json.loads((OUT.parent/'gate-1d/packages-after.json').read_text()).items()}
assert packages==old
for port in (3017,8003):
 with socket.socket() as probe: assert probe.connect_ex(('127.0.0.1',port))!=0
# Remove the test-only alias configuration from the retained test copy by
# restoring its already-qualified disabled build configuration, retaining all evidence.
source=(ROOT/'frontend/next.config.ts').read_text()
(WORK/'next.config.ts').write_text('\n'.join('  distDir: ".next-gate2f",' if line.strip().startswith('distDir:') else line for line in source.splitlines())+'\n')
result=dict(phase='Gate 2F',frontend_tests=63,backend_tests=71,typescript=True,scoped_eslint=True,
 default_turbopack_build=True,additional_offline_sdk_fixture_build=True,browser_widths=[1280,1600,390],
 firebase_disabled_by_default=True,backend_adc_unchanged=True,real_auth_tests=False,owner_configuration_live_verified=False,
 changed_prior_inputs=sorted(expected),unchanged_prior_inputs=len(prior)-len(expected),verified_frontend_sources=len(sources),
 package_distributions_unchanged=len(packages),application_rows=after['dev.db']['rows'],assistant_history_rows=after['assistant-history.db']['rows'],
 isolated_ports_stopped=True,test_alias_config_restored=True,public_launch='BLOCKED')
(OUT/'input-hashes-after.json').write_text(json.dumps(hashes,indent=2))
(OUT/'status.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
