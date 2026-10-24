"""Read-only original row fingerprints; new rows allowed, old rows immutable."""
import hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).with_name('original-rows.json')
def snapshot():
 c=sqlite3.connect((ROOT/'backend/dev.db').as_uri()+'?mode=ro',uri=True)
 result={}
 for (name,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
  quoted='"'+name.replace('"','""')+'"'
  result[name]=[hashlib.sha256(repr(tuple(r)).encode()).hexdigest() for r in c.execute('select * from '+quoted)]
 c.close();return result
if __name__=='__main__':
 current=snapshot()
 if sys.argv[-1]=='baseline':
  assert not OUT.exists(),'Never replace original baseline'
  OUT.write_text(json.dumps(current))
 else:
  from collections import Counter
  old=json.loads(OUT.read_text());missing={t:sum((Counter(rows)-Counter(current.get(t,[]))).values()) for t,rows in old.items()}
  result={'unchanged_original_rows':not any(missing.values()),'original_rows':sum(map(len,old.values())),'missing_or_modified':{t:n for t,n in missing.items() if n}}
  Path(__file__).with_name('preservation-result.json').write_text(json.dumps(result,indent=2));print(result)
  assert result['unchanged_original_rows']
