"""Read-only live-row comparison; never opens credentials or changes databases."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
baseline = json.loads((ROOT / 'docs/milestone-12/database-baseline.json').read_text())
result = {}
for name in ('dev.db', 'assistant-history.db'):
    with sqlite3.connect((ROOT / 'backend' / name).as_uri() + '?mode=ro', uri=True) as db:
        schema = json.loads(json.dumps(db.execute('select type,name,tbl_name,sql from sqlite_master order by type,name').fetchall()))
        tables = {}
        for (table,) in db.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
            tables[table] = sorted(hashlib.sha256(repr(tuple(row)).encode()).hexdigest() for row in db.execute('select * from "' + table.replace('"', '""') + '"'))
    result[name] = {'baseline_match': baseline[name] == dict(schema=schema, tables=tables), 'rows': sum(map(len, tables.values()))}
files = ['backend/requirements.txt', 'frontend/package.json', 'frontend/package-lock.json', 'run-website.bat', 'start-copilot-review.ps1', 'scripts/verify-local-node.cjs', 'backend/app/core/firebase_auth.py', 'backend/app/core/config.py']
result['hashes'] = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
(OUT / ('preservation-' + sys.argv[1] + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
assert all(result[name]['baseline_match'] for name in ('dev.db', 'assistant-history.db'))
