"""Local syntax, package and preserved source checks; no application imports."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
baseline = json.loads((OUT.parent / 'gate-2b/inputs-before.json').read_text())
allowed = {'backend/app/core/firebase_auth.py', 'backend/app/core/config.py'}
actual = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in baseline}
changed = {name for name in baseline if baseline[name] != actual[name]}
assert changed == allowed, changed
graphics = json.loads((ROOT / 'docs/gpu-performance/changed-source-hashes.json').read_text())
for name, digest in graphics.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
packages = {d.metadata['Name'].lower().replace('_', '-'): d.version for d in importlib.metadata.distributions()}
previous = json.loads((OUT.parent / 'gate-1d/packages-after.json').read_text())
previous = {k.lower().replace('_', '-'): v for k, v in previous.items()}
assert packages == previous, 'Installed packages changed since Gate 1D'
files = sorted(allowed | {'backend/tests/test_firebase_keyless_gate.py'})
files += [str(p.relative_to(ROOT)).replace('\\', '/') for p in OUT.glob('*.py')]
for name in files:
    source = (ROOT / name).read_text(encoding='utf-8')
    ast.parse(source, filename=name)
    assert all(line == line.rstrip() for line in source.splitlines()), name
    assert '\t' not in source, name
result = dict(approved_changed_application_inputs=sorted(changed),
              unchanged_prior_inputs=len(baseline) - len(changed),
              graphics_sources_unchanged=len(graphics),
              installed_distributions_unchanged=len(packages),
              firebase_admin_version=packages['firebase-admin'],
              syntax_and_whitespace_checked=files,
              frontend_changed=False, frontend_checks_rerun=False,
              real_credentials_or_firebase_access=False)
(OUT / 'scope-verification.json').write_text(json.dumps(result, indent=2))
(OUT / 'input-hashes-after.json').write_text(json.dumps(actual, indent=2))
print(json.dumps(result, indent=2))
