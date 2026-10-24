import sys,json,sqlite3,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'backend'))
from app.core.config import settings
from app.services.ai.nebius_config import resolve
from app.services.assistant import site_store
from app.api.routes.site_assistant import Context
from app.services.assistant.site_tools import context
from app.db.session import SessionLocal
from app.db.models import Project
out=root/'docs/milestone-6.2'
c=resolve(model='zai-org/GLM-5.3-Flash')
ledger=Path(settings.ASSISTANT_HISTORY_DB)
with sqlite3.connect(ledger.as_uri()+'?mode=ro',uri=True) as db:
 rows=db.execute('SELECT id,owner,status,reserved,tokens,payload FROM tasks').fetchall()
summary=dict(tasks=len(rows),accounted_usd=sum(r[3] for r in rows),accounting_blocked=any(json.loads(r[5]).get('accounting_blocked') for r in rows),running=sum(r[2]=='RUNNING' for r in rows))
with SessionLocal() as db:
 p=db.get(Project,793)
 saved=context(db,p.user_id,Context(project_id=793,revision_id=103,page='/projects/793/workspace'))
 # Save only the authorized test project's evidence, not other project details.
 (out/'saved-context-baseline.json').write_text(json.dumps(saved,default=str,indent=2),encoding='utf-8')
result=dict(inference_requests=0,credentials_resolved=bool(c.api_key),official_endpoint=c.base_url=='https://api.tokenfactory.nebius.com/v1',ledger=summary,project_context_available=saved.get('project') is not None)
(out/'preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
# Strict existing-manifest preservation, output only under the new milestone.
source=(root/'docs/milestone-6.1/preserve.py').read_text()
exec(compile(source,str(out/'preserve.py'),'exec'),{'__file__':str(out/'preserve.py'),'__name__':'__main__'})
