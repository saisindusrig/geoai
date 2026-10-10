"""One authorized authenticated retry of each original frozen live case."""
import asyncio
import json
from pathlib import Path
from live_ai3d_acceptance import CapturedProvider, MODEL, safe, save
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import Project
from app.services.assistant.runtime import retry_run, process
from app.services.assistant.storage import owned_row, rows
from app.services.assistant.proposals import ProposalService
import time

async def main():
    if (settings.NEBIUS_PRIMARY_MODEL.strip() or settings.NEBIUS_CHAT_MODEL)!=MODEL or settings.NEBIUS_FAST_MODEL.strip():raise RuntimeError('CONFIGURATION_GUARD')
    out=Path('live-results/universal-v1-authenticated')
    originals=[json.loads((Path('live-results/universal-v1')/f'case-{case}.json').read_text(encoding='utf-8')) for case in 'ABC']
    out.mkdir(parents=True,exist_ok=False)
    for original in originals:
        path=out/f"case-{original['case']}.json"
        result={k:original[k] for k in ('case','selectionType','userRequest','model','projectId','scenarioId','conversationId','messageId','sourceRevisionId')}
        result.update(originalRunId=original['runId'],completions=[],approval='NOT_APPROVED')
        save(path,result)
        with SessionLocal() as db:
            pid=original['projectId'];project=db.get(Project,pid)
            run_id,_=retry_run(db,pid,project.user_id,original['runId'],'auth-restored-v1')
            result['runId']=run_id;save(path,result)
            started=time.monotonic()
            await process(db,pid,run_id,CapturedProvider(result,path))
            run=owned_row(db,'assistant_runs',pid,run_id)
            result.update(runStatus=run['status'],errorCode=run['error_code'],latencySeconds=round(time.monotonic()-started,3),runContext=safe(run['context_snapshot']))
            messages=[m for m in rows(db,'conversation_messages',pid) if m['conversation_id']==original['conversationId']]
            result['visibleMessages']=safe([{k:m[k] for k in ('id','role','parts')} for m in messages])
            versions=[r for r in rows(db,'design_proposal_versions',pid) if original['messageId'] in r['payload'].get('sourceMessageIds',[])]
            result['proposals']=safe([ProposalService().read(db,pid,r['id']) for r in versions])
            save(path,result)
            print(json.dumps({'case':result['case'],'status':run['status'],'errorCode':run['error_code'],'requests':len(result['completions']),'proposals':len(result['proposals']),'path':str(path)}),flush=True)
    print('STOP: three frozen live flows attempted; no further provider calls authorized.',flush=True)

if __name__=='__main__':asyncio.run(main())
