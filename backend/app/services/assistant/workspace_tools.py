"""Read-only workspace receipts. All numerical/source gates delegate to existing APIs."""
from typing import Literal,Annotated
from pydantic import Field,BaseModel,ConfigDict
class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
from app.api.routes.projects import get_owned_project
from app.db.models import ModelRevision,EngineeringAnalysis
from app.services.design.opensees_benchmark import digest

class WorkspaceRejected(ValueError):
    pass

class Target(Strict):
    project_id:int=Field(gt=0)
class Components(Target):
    offset:int=Field(default=0,ge=0,le=100000)
class Selection(Target):
    component_ids:list[Annotated[str,Field(min_length=1,max_length=255)]]=Field(min_length=1,max_length=20)
class View(Target):
    view:Literal['model','site']
class SavedResult(Target):
    revision_id:int=Field(gt=0)
    result_id:int=Field(gt=0)
    method:Literal['frame','slab','spatial','coupled','foundation']
    load_case:str=Field(min_length=1,max_length=200)
class Result(SavedResult):
    mode:Literal['loads','forces','deformation','slab']

class Primitive(Target):
    revision_id:int=Field(gt=0)
    primitive:Literal['column']
    name:str=Field(min_length=1,max_length=80)
    units:Literal['m','cm','mm']
    dimensions:list[float]=Field(min_length=3,max_length=3)
    position:list[float]=Field(min_length=3,max_length=3)
    position_reference:Literal['local_enu_center']
    rotation_deg:list[float]=Field(min_length=3,max_length=3)
    parent_id:None
    provenance:Literal['user_dimensions_conceptual']

class Beam(Target):
    revision_id:int=Field(gt=0)
    primitive:Literal['beam']
    name:str=Field(min_length=1,max_length=80)
    units:Literal['m','cm','mm']
    endpoints:list[Annotated[list[float],Field(min_length=3,max_length=3)]]=Field(min_length=2,max_length=2)
    width:float
    depth:float
    position_reference:Literal['local_enu']
    point_source:Literal['user_explicit_enu']
    parent_id:None
    provenance:Literal['user_dimensions_conceptual']

TOOLS={
 'prepare_beam_preview':(Beam,'Prepare one independent straight rectangular conceptual beam from two explicit user-supplied local ENU 3D endpoints, width, depth and m/cm/mm units. Ask for missing values. No verified selected-point endpoint registry exists: reject ambiguous point/object references and ask for numeric endpoints. Length, XYZ orientation and section convention are derived by existing geometry libraries. Preview only; user must click Apply then Save. No connectivity, strengths, loads, supports, reinforcement or analysis.'),
 'prepare_primitive_preview':(Primitive,'Prepare one independent box-shaped column, using explicitly user-supplied width/depth/height, units, local ENU centre, yaw orientation and null parent. Ask for missing dimensions/placement/orientation; never guess. Geometry only, no strengths, loads, supports or connections. Protected CAD/assemblies and beams are unsupported. Frontend must show temporary preview; user must click Apply then Save.'),
 'cancel_primitive_preview':(Target,'Cancel only the current temporary primitive preview in this owned workspace. Never deletes applied or saved geometry. Frontend confirmation required.'),
 'open_project':(Target,'Open an owned project at its current saved revision. Frontend confirmation is required.'),
 'list_components':(Components,'List actual saved components, IDs, names, categories and positions, 50 per page. Resolve ambiguous names before selecting.'),
 'select_components':(Selection,'Select and highlight exact saved component IDs. No geometry mutation. Frontend confirmation required.'),
 'focus_components':(Selection,'Focus the camera on exact visible saved component IDs. Fails if geometry is hidden or not rendered.'),
 'read_component_properties':(Selection,'Read actual saved geometry, transform and declared metadata for exact component IDs. Appearance is not engineering certification.'),
 'switch_workspace_view':(View,'Switch the existing model/site presentation only, with frontend confirmation.'),
 'list_saved_results':(Target,'List current authoritative saved results, exact methods and load cases. Never computes or substitutes an old result.'),
 'read_saved_result':(SavedResult,'Read the exact current verified saved result and named load case, including actual saved reaction/force/displacement evidence. No calculation.'),
 'show_saved_result':(Result,'Show an exact current verified saved result and explicit load case using existing visual controls. Foundation deformation and frame slab contours are unsupported. No calculation.'),
}

def execute(name,arguments,db,owner,request):
    args=TOOLS[name][0].model_validate(arguments)
    project=get_owned_project(args.project_id,db,owner)
    revision=db.query(ModelRevision).filter_by(project_id=project.id).order_by(ModelRevision.id.desc()).first()
    if not revision:raise WorkspaceRejected('This project has no saved model revision. Open its existing workspace to review inputs.')
    if request.dirty and name!='cancel_primitive_preview':raise WorkspaceRejected('Resolve the unsaved editor draft before controlling the workspace.')
    if request.project_id==project.id and request.revision_id not in (None,revision.id):raise WorkspaceRejected('Saved editor revision is stale. Open the current saved revision first.')
    doc=revision.document_json;components=doc.get('components',[])
    base={'projectId':project.id,'projectName':project.name,'revisionId':revision.id,'documentHash':digest(doc)}
    if name in ('prepare_primitive_preview','prepare_beam_preview'):
        from math import isfinite
        from copy import deepcopy
        if request.project_id!=project.id or request.revision_id!=revision.id or args.revision_id!=revision.id:
            raise WorkspaceRejected('Open this exact current saved revision before proposing geometry.')
        if doc.get('units')!='metric':raise WorkspaceRejected('This preview supports only the existing metric editor.')
        if any(c.get('locked') or c.get('parent_id') or c.get('geometry',{}).get('kind') not in ('box','cylinder') or any(k.startswith('parametric_') or 'cad' in k for k in c.get('metadata',{})) for c in components) or any('cad' in k or 'drawing' in k or 'parametric' in k for k in doc.get('metadata',{})):
            raise WorkspaceRejected('Protected CAD or assembly model: use its existing reviewed creation workflow. No source object will be changed.')
        factor={'m':1.,'cm':.01,'mm':.001}[args.units]
        beam=None
        if name=='prepare_beam_preview':
            from app.services.assistant.beam_proposal import beam_box
            beam=beam_box(args.endpoints,args.width,args.depth,args.units)
            size=beam['size'];position=beam['position'];rotation=beam['rotation_deg'];category='beam'
        else:
            size=[v*factor for v in args.dimensions];position=[v*factor for v in args.position];rotation=args.rotation_deg;category='column'
        if any(not isfinite(v) or not .01<=v<=100 for v in size) or any(not isfinite(v) or abs(v)>10000 for v in position):
            raise WorkspaceRejected('Explicit dimensions must be 0.01–100 m and centre coordinates within ±10,000 m.')
        if not beam and (any(not isfinite(v) or abs(v)>360 for v in rotation) or rotation[:2]!=[0.,0.]):
            raise WorkspaceRejected('Only an upright column with explicit yaw rotation is supported.')
        component_id='assistant-'+category+':'+digest({**base,'parameters':args.model_dump()})[:24]
        if any(c['id']==component_id for c in components):raise WorkspaceRejected('This proposal is already present; duplicate replay rejected.')
        component=dict(id=component_id,parent_id=None,name=args.name,category=category,visible=True,locked=False,
            geometry={'kind':'box','size':size},transform={'position':position,'rotation_deg':rotation,'scale':[1,1,1]},
            material={'name':'Conceptual geometry only','color':'#E879F9','roughness':.75,'metalness':0},quantity={'included':False},
            metadata={'source':'assistant_supervised_primitive','provenance':args.provenance,'base_revision_id':revision.id,'engineering':'UNVERIFIED_GEOMETRY_ONLY'})
        if beam:component['metadata']['beam']=beam
        candidate=deepcopy(doc);candidate['components'].append(component)
        from app.services.design.editable_model import validate_document
        from app.services.design.structural_layout import validate_layout
        errors=validate_document(candidate,project_id=project.id,scenario_id=revision.design_scenario_id,project_type=project.project_type)
        if errors or not validate_layout(candidate)['passed']:raise WorkspaceRejected('The existing editor validators reject this addition. Use the existing manual creation workflow.')
        base.update(candidate=component,requiresApproval=True,saved=False)
    if name=='list_components':return {**base,'total':len(components),'offset':args.offset,'limit':50,'components':[{k:c.get(k) for k in ('id','name','category','visible','transform')} for c in components[args.offset:args.offset+50]]}
    ids=getattr(args,'component_ids',[])
    if ids:
        if len(set(ids))!=len(ids) or any(i not in {c['id'] for c in components} for i in ids):raise WorkspaceRejected('Component IDs must exactly match this saved model.')
        selected=[c for c in components if c['id'] in ids]
        if name=='read_component_properties':return {**base,'components':selected,'notice':'Saved properties only; material appearance does not establish engineering properties.'}
        if any(not c.get('visible',True) for c in selected):raise WorkspaceRejected('Requested component is hidden. Restore visibility in Layers before focusing or selecting.')
    if name in ('list_saved_results','show_saved_result','read_saved_result'):
        from app.api.routes.analysis_capabilities import capabilities
        caps=capabilities(project.id,revision.id,'',db,owner,saved_only=True)
        if name=='list_saved_results':return {**base,'methods':{k:{'status':v['status'],'reason':v['reason'],'current_results':v['current_results'][:20]} for k,v in caps['methods'].items()},'notice':'Only current_results are eligible. No result is generated by this read.'}
        if args.revision_id!=revision.id:raise WorkspaceRejected('Requested saved result revision is stale.')
        identity=next((r for r in caps['methods'][args.method]['current_results'] if r['id']==args.result_id),None)
        if not identity or identity['model_document_sha256']!=base['documentHash']:raise WorkspaceRejected('Exact result is stale, unavailable or not verified for this project, revision and method. Review existing analysis tools; no replacement was selected.')
        if args.load_case not in identity['load_cases']:raise WorkspaceRejected('Exact load case is not present in this saved result. No case was substituted.')
        record=db.get(EngineeringAnalysis,args.result_id)
        if name=='read_saved_result':
            body=record.result_json
            def exact_case(value):
                if value.get('case_name','Saved case')==args.load_case:return value
                return next((c for c in value.get('load_case_results',[]) if c.get('case_name','Saved case')==args.load_case),None)
            evidence=body.get('computed') if args.method=='foundation' else next((c for c in body.get('cases',[]) if c.get('case',{}).get('name')==args.load_case),None) if 'cases' in body else [c for f in body['frames'] if (c:=exact_case(f['result']))] if 'frames' in body else exact_case(body)
            if evidence is None or evidence==[]:raise WorkspaceRejected('Saved load-case evidence is unavailable. No case was substituted.')
            return {**base,'resultIdentity':identity,'resultHash':digest(body),'loadCase':args.load_case,'savedEvidence':evidence,'notice':'Exact saved numerical evidence only; no safety or design approval.'}
        if (args.method=='foundation' and args.mode=='deformation') or (args.method=='frame' and args.mode=='slab'):raise WorkspaceRejected('This visualization is unsupported by the saved method. Open its existing results workflow.')
        record=db.get(EngineeringAnalysis,args.result_id)
        base.update(resultIdentity=identity,resultHash=digest(record.result_json),loadCase=args.load_case,mode=args.mode)
    command={**base,'kind':'workspace_action','operation':name,'componentIds':ids,'view':getattr(args,'view',None),'validation':{'name':name,'arguments':args.model_dump()},'executed':False}
    command['actionId']=digest(command)
    return command
