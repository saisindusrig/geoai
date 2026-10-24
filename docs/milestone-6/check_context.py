"""Read-only actual-project context sizing; no provider or database writes."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.db.session import SessionLocal
from app.db.models import Project
from app.api.routes.site_assistant import Context,provider_context
from app.services.assistant.site_tools import context

rows=[]
with SessionLocal() as db:
    for pid,rid in ((793,103),(794,105),(804,145)):
        owner=db.get(Project,pid).user_id
        raw=context(db,owner,Context(project_id=pid,page=f'/projects/{pid}/workspace'))
        rid=raw['project']['revisionId']
        sources=raw['project']['drawingReferences']
        selected=[sources[0]['componentId']] if sources else []
        raw=context(db,owner,Context(project_id=pid,revision_id=rid,selected_ids=selected,page=f'/projects/{pid}/workspace'))
        for maximum in (12000,24000):
            packed=provider_context(raw,maximum)
            size=len(json.dumps(packed,ensure_ascii=False,default=str).encode())
            assert size<=maximum,(pid,maximum,size)
            assert packed['project']['documentHash']==raw['project']['documentHash']
            if selected:assert packed['project']['selected'][0]['id']==selected[0]
            rows.append(dict(project_id=pid,revision_id=rid,maximum_bytes=maximum,actual_bytes=size,
                             selected_ids=selected,selected_identity_preserved=True,document_hash_preserved=True,
                             analysis_records_returned=len(packed['project']['analyses']),truncated=packed['project'].get('truncated',False)))
Path(__file__).with_name('context-boundaries.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
