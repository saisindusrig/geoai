"""Offline audit and explicitly authorized approval/build. No provider calls."""
import json
from pathlib import Path
from live_ai3d_acceptance import safe, save
from app.db.session import SessionLocal
from app.db.models import Project, ModelRevision
from app.domain.ai3d import AI3DDesign
from app.domain.assistant_runtime import ApplicationApproval
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import owned_row, rows
from app.services.assistant.ai3d_validation import site_summary, AI3DDesignValidator
from app.services.ai.building_plan import local_plot
from app.services.assistant.preview_parameters import preview_parameters

OUT=Path('live-results/universal-v2')

def main():
    if (OUT/'offline-review-and-build.json').exists():
        raise RuntimeError('AUDIT_ALREADY_EXISTS: preserve the original review and approval evidence')
    audit={'providerCalls':0,'cases':[]}
    with SessionLocal() as db:
        for case in 'ABC':
            path=OUT/f'case-{case}.json'; result=json.loads(path.read_text(encoding='utf-8'))
            pid=result['projectId']; context=result['runContext']['context']
            proposals=set()
            designs=[]; tools=[]
            for completion in result['completions']:
                for item in completion.get('toolResultsSeen',[]):
                    data=item.get('result',{}).get('data') or {}
                    if data.get('proposalVersionId'):proposals.add(data['proposalVersionId'])
                visible=completion.get('visibleStructuredResponse') or {}
                arguments=[visible] if completion.get('nestedRepair') else []
                for call in visible.get('toolCalls',[]):
                    record={'name':call['name'],'allowed':call['name'] in result['runContext'].get('policy',{}).get('understanding',{}).get('requiredTools',[])}
                    try:
                        args=json.loads(call['arguments']); record['jsonParses']=True
                        from app.services.assistant.tool_contracts import SCHEMAS
                        SCHEMAS[call['name']].model_validate(args); record['schemaValid']=True
                        arguments.append(args)
                    except Exception as exc:record.update(schemaValid=False,errorCategory=type(exc).__name__)
                    tools.append(record)
                for args in arguments:
                    for asset in args.get('assets',[]):
                        if asset.get('ai3dDesign') and asset['ai3dDesign'] not in designs:designs.append(asset['ai3dDesign'])
            views=[ProposalService().read(db,pid,vid) for vid in proposals]
            result['proposals']=safe(views)
            save(path,result)
            summary=site_summary(db,pid,context)
            project=db.get(Project,pid)
            boundary=local_plot({'origin':summary['origin'],'boundary':project.boundary_geojson}) if project.boundary_geojson else None
            reviews=[]
            for design in designs:
                try: validation=AI3DDesignValidator().validate(AI3DDesign.model_validate(design),summary,boundary)
                except Exception as exc:validation={'status':'SCHEMA_INVALID','errorCategory':type(exc).__name__}
                reviews.append({'design':safe(design),'validation':validation,'derivedPreviewParameters':preview_parameters(design)})
            item={'case':case,'projectId':pid,'runStatus':result['runStatus'],'errorCode':result['errorCode'],
                'classification':result['completions'][0].get('visibleStructuredResponse'),
                'diagnostics':result['runContext'].get('modelRoutingDiagnostics',[]),'tools':tools,'designReviews':reviews,
                'savedProposalReviews':safe(views),'builds':[]}
            audit['cases'].append(item)
            # Durable complete review before any approval, using the unchanged application gate.
            save(OUT/'offline-review-and-build.json',audit)
            for view in views:
                if view['status']!='READY_FOR_REVIEW' or not view['current'] or view['validation']['status']!='PASSED':continue
                command=ApplicationApproval(client_request_id='acceptance-v2-controlled-approval',proposal_version_id=view['id'],
                    proposal_hash=view['contentHash'],dependency_hash=view['dependencyHash'],validation_hash=view['validationHash'],
                    alternative_id=view['alternatives'][0]['id'] if view['alternatives'] else None,
                    acknowledged_assumption_version_ids=view['content']['contract']['assumptionVersionIds'],
                    expected_model_revision_id=view['content']['context'].get('modelRevisionId'))
                approved=ProposalService().approve(db,pid,project.user_id,command)
                entry={'proposalVersionId':view['id'],'approval':approved};item['builds'].append(entry)
                save(OUT/'offline-review-and-build.json',audit)
                try:
                    entry['execution']=ProposalService().build(db,pid,view['id'])
                    revision=db.get(ModelRevision,int(entry['execution']['modelRevisionId']))
                    entry['document']=safe(revision.document_json)
                except Exception as exc:
                    db.rollback();entry['failure']=safe(getattr(exc,'detail',{'type':type(exc).__name__}))
                save(OUT/'offline-review-and-build.json',audit)
            print(json.dumps({'case':case,'savedProposals':len(views),'builds':[{k:v for k,v in b.items() if k!='document'} for b in item['builds']]}),flush=True)
        source=db.get(ModelRevision,30);latest=db.query(ModelRevision).filter_by(project_id=576).order_by(ModelRevision.id.desc()).first()
        audit['existingPreservation']={'sourceRevision':30,'latestRevision':latest.id,'sourceComponents':len(source.document_json['components']),
            'latestComponents':len(latest.document_json['components']),'allOriginalObjectsUnchanged':source.document_json['components']==latest.document_json['components'],
            'lineageCount':len([r for r in rows(db,'model_object_lineage',576) if r['model_revision_id']==latest.id])}
        save(OUT/'offline-review-and-build.json',audit)

if __name__=='__main__':main()
