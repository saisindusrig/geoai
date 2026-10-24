"""Hash original data read-only; compare later without restoring or deleting anything."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/production-beta'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def originals():
    # Include all pre-existing databases, source CAD/model assets, storage and
    # published engineering evidence. Compiler/dependency trees are excluded.
    excluded = {'.git', 'node_modules', '.venv', '.venv-civicspan', '__pycache__',
                '.next', '.next-phase1', '.next-beta', 'production-beta'}
    import os
    for parent, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in excluded]
        for name in files:
            p = Path(parent) / name
            rel = p.relative_to(ROOT)
            if (p.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.dxf', '.dwg', '.glb', '.gltf', '.ifc', '.step', '.stp'}
                or rel.parts[:2] == ('backend', 'storage')
                or rel.parts[0] == 'docs'
                or name in {'.env', '.env.local'}):
                yield p

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['snapshot', 'verify'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / 'data-before.json'
    if args.mode == 'snapshot':
        if manifest.exists():
            raise SystemExit('Refusing to replace original snapshot')
        rows = {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in originals()}
        manifest.write_text(json.dumps(rows, indent=2), encoding='utf-8')
        print(json.dumps({'files': len(rows), 'bytes': sum(r['bytes'] for r in rows.values())}))
    else:
        rows = json.loads(manifest.read_text(encoding='utf-8'))
        changed = [name for name, row in rows.items() if not (ROOT/name).is_file() or digest(ROOT/name) != row['sha256']]
        result = {'original_files': len(rows), 'changed_or_missing': changed, 'unchanged': not changed}
        (OUT/'data-after.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))
        raise SystemExit(bool(changed))
