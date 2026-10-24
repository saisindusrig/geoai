"""Append-only assistant UI outcomes; separate from engineering data and billing."""
import json,threading,time
from pathlib import Path
from app.core.config import settings
_lock=threading.Lock()
def path():return Path(settings.ASSISTANT_HISTORY_DB).with_suffix('.workspace.jsonl')
def history(owner):
    if not path().exists():return []
    with _lock:
        return [v for line in path().read_text(encoding='utf-8').splitlines() if (v:=json.loads(line))['owner']==owner][-200:]
def append(owner,task_id,action_id,ok,message):
    with _lock:
        previous=[json.loads(line) for line in path().read_text(encoding='utf-8').splitlines()] if path().exists() else []
        old=next((v for v in previous if v['owner']==owner and v['taskId']==task_id and v['actionId']==action_id),None)
        if old:return old
        value=dict(owner=owner,taskId=task_id,actionId=action_id,ok=ok,message=message,confirmedBy='authenticated frontend acknowledgment',created=time.time())
        with path().open('a',encoding='utf-8') as f:f.write(json.dumps(value,separators=(',',':'))+'\n')
        return value
