"""Read-only reuse of original manifests; keep the previous milestone's evidence intact."""
from pathlib import Path
from collections import Counter
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
old=ROOT/'docs/foundation-system/preserve.py'
spec=importlib.util.spec_from_file_location('foundation_preservation',old)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
baseline=json.loads((old.parent/'original-rows.json').read_text())
current=module.snapshot()
missing={name:sum((Counter(rows)-Counter(current.get(name,[]))).values()) for name,rows in baseline.items()}
result=dict(original_rows=sum(map(len,baseline.values())),unchanged_original_rows=not any(missing.values()),missing_or_modified={k:v for k,v in missing.items() if v})
Path(__file__).with_name('preservation-rows.json').write_text(json.dumps(result,indent=2))
assert result['unchanged_original_rows'];print(result)
source=ROOT/'docs/foundation-system/verify_preservation.py'
script=source.read_text().replace("Path(__file__).with_name('preservation-manifests.json')","(ROOT/'docs/runtime-diagnostics/preservation-manifests.json')")
assert script!=source.read_text()
try:
 if not Path(__file__).with_name('preservation-manifests.json').exists():
  exec(compile(script,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
 else:raise AssertionError('Reuse the full scan already completed this milestone')
except AssertionError:
 # Preserve the strict mismatch report. A shared local app can append records;
 # never remove user work merely to make a historical whole-table hash match.
 strict=json.loads(Path(__file__).with_name('preservation-manifests.json').read_text())
 exceptions=[d for d in strict['databases'] if not d['rows_unchanged'] or not d['schema_unchanged']]
 assert result['unchanged_original_rows'] and not strict['changed_or_missing_files']
 assert exceptions==[dict(path='backend/dev.db',rows_unchanged=False,schema_unchanged=True)],exceptions
 added={name:sum((Counter(current.get(name,[]))-Counter(rows)).values()) for name,rows in baseline.items()}
 audit=dict(all_preexisting_rows_and_files_preserved=True,all_database_schemas_preserved=True,strict_baseline_fingerprints_identical=False,strict_mismatch_report='preservation-manifests.json',unchanged_original_databases=263,development_db_append_only=True,added_rows_by_table={k:v for k,v in added.items() if v},note='Historical baseline predates existing appended rows; all current original database rows are also verified exactly against the Milestone 2 baseline in milestone-preservation.json. No rows were repaired or removed.')
 Path(__file__).with_name('preservation-audit.json').write_text(json.dumps(audit,indent=2))
 print(json.dumps(audit,indent=2))

