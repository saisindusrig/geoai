"""Read-only warm loopback measurements; no load-generation claims."""
import json
import statistics
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
targets={
 'health':'http://127.0.0.1:8011/api/health',
 'project_list':'http://127.0.0.1:8011/api/projects',
 'saved_frame_compact':'http://127.0.0.1:8011/api/projects/781/engineering/assembly?compact=true',
 'engineering_context':'http://127.0.0.1:8011/api/projects/781/assistant/engineering-context',
 'production_dashboard':'http://localhost:3011/dashboard',
}
results={}
for name,url in targets.items():
 rows=[]
 for i in range(11):
  started=time.perf_counter()
  with urllib.request.urlopen(url,timeout=30) as response:
   content=response.read();status=response.status
  if i:rows.append((time.perf_counter()-started)*1000)
 results[name]={'samples':10,'status':status,'median_ms':round(statistics.median(rows),2),
                'p95_nearest_rank_ms':round(sorted(rows)[9],2),'response_bytes':len(content)}
out={'method':'Sequential warm loopback GETs, first sample discarded; no concurrency/load or field performance claim.',
     'results':results}
(ROOT/'docs/production-beta/performance.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
