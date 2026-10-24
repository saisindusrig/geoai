"""Strict allowlisted adapters. No arbitrary URL, code, file write or solver tool."""
import copy
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.api.routes.projects import get_owned_project
from app.db.models import Project, ModelRevision
from app.services.assistant.engineering_guidance import saved_context
from app.services.design.opensees_benchmark import digest


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Empty(Strict):
    pass


class Destination(Strict):
    destination: Literal['dashboard','projects','editor','cad','analysis','results','quantities','exports','diagnostics','settings','inspect']
    project_id: int | None = Field(default=None,gt=0)


class Transform(Strict):
    component_id: str = Field(min_length=1, max_length=255)
    position: list[float] = Field(min_length=3, max_length=3)


REGISTRY = {
    'read_context': (Empty, 'Read saved project, selected objects, CAD sources and engineering evidence. Never executes analyses.'),
    'list_projects': (Empty, 'List up to 50 projects owned by the authenticated user.'),
    'read_quantities': (Empty, 'Read existing saved quantities and cost estimates; no recalculation.'),
    'read_capabilities': (Empty, 'Read authoritative supported-method and current/stale saved-result gates. Does not run analyses.'),
    'read_diagnostics': (Empty, 'Read existing runtime diagnostics with a bounded solver version-only probe; no numerical analysis or inference.'),
    'navigate': (Destination, 'Prepare a link to an existing website tool. Analysis, imports, exports and saving require manual review in that tool.'),
    'prepare_position_preview': (Transform, 'Prepare a visual position preview for one selected editable component, in East/North/Up metres. Does not apply or save. User must review Preview, Apply, then Save model in the existing editor.'),
}


from app.services.assistant.workspace_tools import TOOLS as WORKSPACE_TOOLS
REGISTRY.update(WORKSPACE_TOOLS)


def definitions():
    return [{'type':'function','function':{'name':name,'description':desc,'parameters':schema.model_json_schema()}} for name,(schema,desc) in REGISTRY.items()]


def context(db, owner, request):
    result = {'page':request.page, 'clientContextUntrusted':True, 'project':None,
              'contextBounds':'Existing evidence adapter: latest 100 engineering records, up to 30 returned analyses, 100 selected objects and 100 CAD references. This is not a complete project inventory or a method validation.',
              'capabilities':{name:desc for name,(_,desc) in REGISTRY.items()},
              'limits':'Only bounded read tools, position previews and supervised independent-column/beam previews. Column dimensions, centre, units and yaw must be explicit; beams require numeric ENU endpoints plus explicit width, depth and units. Apply and Save require separate user clicks in the existing editor. CAD/file operations and numerical analyses retain existing review and authorization. Never claim execution from navigation or preparation.'}
    if request.project_id is None:
        return result
    project = get_owned_project(request.project_id, db, owner)
    result['projectFacts']={'id':project.id,'name':project.name,'type':project.project_type,'units':project.units,
                            'status':project.status,'location':project.location_name,'hasBoundary':project.boundary_geojson is not None,
                            'hasAlignment':project.alignment_geojson is not None}
    revision = request.revision_id
    if revision is None:
        latest = db.query(ModelRevision).filter_by(project_id=project.id).order_by(ModelRevision.id.desc()).first()
        revision = latest.id if latest else None
    result['project'] = saved_context(db,project.id,revision,request.selected_ids,request.dirty)
    return result


def execute(name, arguments, db, owner, request):
    if name not in REGISTRY:
        raise ValueError('Tool is not allowlisted')
    if name in WORKSPACE_TOOLS:
        from app.services.assistant.workspace_tools import execute as workspace_execute
        return workspace_execute(name,arguments,db,owner,request)
    args = REGISTRY[name][0].model_validate(arguments)
    current = context(db,owner,request)  # Re-check ownership and saved identities each time.
    project = current['project']
    if name == 'read_context':
        return current
    if name == 'list_projects':
        query=db.query(Project).filter_by(user_id=owner)
        return {'totalOwnedProjects':query.count(),'limit':50,'projects':[{'id':p.id,'name':p.name,'status':p.status} for p in query.order_by(Project.id.desc()).limit(50)]}
    if name == 'read_diagnostics':
        from fastapi import Response
        from app.api.routes.runtime_diagnostics import diagnostics
        return diagnostics(Response(),request.project_id if project and project['revisionId'] else None,project['revisionId'] if project else None,db,owner)
    if name == 'read_capabilities':
        if not project or not project['revisionId']:
            raise ValueError('Open a saved project first')
        from app.api.routes.analysis_capabilities import capabilities
        return capabilities(request.project_id,project['revisionId'],','.join(request.selected_ids),db,owner,saved_only=True)
    if name == 'read_quantities':
        if project is None:
            raise ValueError('Open a project first')
        from app.services.ai.copilot import build_copilot_context
        p = get_owned_project(request.project_id,db,owner)
        data = build_copilot_context(db,p)
        return {k:data.get(k) for k in ('latest_estimate','calculated_summary')}
    if name == 'navigate':
        dest = args.destination
        paths = {'dashboard':'/dashboard','projects':'/dashboard','settings':'/settings','diagnostics':'/diagnostics'}
        if dest in paths:
            return {'kind':'navigation','href':paths[dest], 'destination':dest, 'executed':False}
        target_id=args.project_id or request.project_id
        if target_id is None:
            raise ValueError('Open a project first')
        get_owned_project(target_id,db,owner)
        if target_id != request.project_id:
            target_revision=db.query(ModelRevision).filter_by(project_id=target_id).order_by(ModelRevision.id.desc()).first()
            project={'revisionId':target_revision.id if target_revision else None,'selected':[]}
        suffix = {'editor':'workspace','inspect':'workspace','cad':'workspace','analysis':'workspace','results':'workspace','quantities':'estimate','exports':'report'}[dest]
        return {'kind':'navigation','href':f'/projects/{target_id}/{suffix}', 'destination':dest,'projectId':target_id,'revisionId':project['revisionId'],'componentIds':[c['id'] for c in project['selected']], 'executed':False}
    if project is None or project['stale'] or request.dirty or request.revision_id != project['revisionId']:
        raise ValueError('A current saved editor revision is required for previews')
    from math import isfinite
    if any(not isfinite(v) or abs(v)>100000 for v in args.position):
        raise ValueError('Position must contain finite bounded metre values')
    component = next((c for c in project['selected'] if c['id']==args.component_id), None)
    revision = db.get(ModelRevision,project['revisionId'])
    original = next((c for c in revision.document_json['components'] if c['id']==args.component_id), None)
    if component is None or original is None or original.get('locked') or original.get('metadata',{}).get('parametric_attachment') or original.get('metadata',{}).get('parametric_platform'):
        raise ValueError('Select an unlocked independent component; assembly edits require existing assembly tools')
    candidate = copy.deepcopy(original)
    candidate['transform']['position'] = args.position
    return {'kind':'position_preview','projectId':request.project_id,'revisionId':project['revisionId'],
            'documentHash':project['documentHash'],'componentHash':digest(original),'componentId':args.component_id,
            'before':original['transform']['position'],'after':args.position,'candidate':candidate,
            'requiresApproval':True,'saved':False,'notice':'Visual geometry proposal only; saved results become stale after saving. Use Preview, Apply, Save model. No engineering approval.'}
