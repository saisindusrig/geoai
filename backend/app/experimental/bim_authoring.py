"""Deterministic offline assembly authoring. No model clients, routes or builders."""
from dataclasses import dataclass
from copy import deepcopy
import math
from app.domain.bim_authoring import AuthoringBundle, AuthoringIntent, AssemblyPlan, AssemblyExpansion, AssemblyRelationships
from app.domain.bim import BIMProject, Placement
from app.experimental.bim_cad import CADMapping
from app.experimental.cad_contract import Source, Geometry, digest, encode, from_bim
from app.services.assistant.bim_foundation import validate_foundation

OPERATIONS = {
    "BEAM": ("PROFILE_EXTRUSION", "RECTANGULAR_LOFT"),
    "GIRDER": ("PROFILE_EXTRUSION", "RECTANGULAR_LOFT"),
    "COLUMN": ("CIRCULAR_COLUMN", "PROFILE_EXTRUSION", "RECTANGULAR_LOFT"),
    "PIER": ("CIRCULAR_COLUMN", "PROFILE_EXTRUSION", "RECTANGULAR_LOFT"),
    "SLAB": ("RECTANGULAR_OPENING", "PROFILE_EXTRUSION"),
    "DECK": ("RECTANGULAR_OPENING", "PROFILE_EXTRUSION"),
    "BRACING": ("PROFILE_EXTRUSION",),
    "PLATE": ("CIRCULAR_HOLE", "PROFILE_EXTRUSION"),
    "BEARING": ("PROFILE_EXTRUSION",),
}
FEATURES = ("I_SECTION", "CIRCULAR_COLUMN", "SLAB_OPENING", "PLATE_HOLE", "RECTANGULAR_MEMBER", "TAPERED_MEMBER")
COST = {"PROFILE_EXTRUSION":3, "CIRCULAR_COLUMN":2, "RECTANGULAR_OPENING":4, "CIRCULAR_HOLE":4, "RECTANGULAR_LOFT":5}
MANDATORY_UNKNOWNS = ("terrain", "soil", "loads", "foundations", "clearances", "codeCompliance", "verticalDatum", "engineeringApproval")
PLANNING_SELECTIONS = {"BRIDGE":("CROSSING","ENDPOINTS","AREA"),"INDUSTRIAL_PLATFORM":("AREA",)}


class AuthoringError(ValueError):
    def __init__(self, code, references=()):
        self.code, self.references = code, tuple(sorted(references))
        super().__init__(code)


def require(condition, code, references=()):
    if not condition:
        raise AuthoringError(code, references)


def capabilities():
    # Deliberately separate from production asset/executor registration.
    return {"version":"bim-authoring-capabilities/1", "mode":"OFFLINE_ONLY",
        "componentOperations":deepcopy(OPERATIONS), "profiles":["RECTANGLE","I","CIRCLE"],
        "recipes":{
            "PROFILE_EXTRUSION":{"componentParameters":["length"],"sectionParameters":{"RECTANGLE":["width","depth"],"I":["width","depth","web","flange"]}},
            "CIRCULAR_COLUMN":{"componentParameters":["length"],"sectionParameters":{"CIRCLE":["radius"]}},
            "RECTANGULAR_OPENING":{"componentParameters":["width","depth","thickness","hole_width","hole_depth"],"sectionParameters":None},
            "CIRCULAR_HOLE":{"componentParameters":["width","depth","thickness","hole_radius"],"sectionParameters":None},
            "RECTANGULAR_LOFT":{"componentParameters":["width","depth","end_width","end_depth","length"],"sectionParameters":None}},
        "rectangularExtrusionOnly":["SLAB","DECK","BEARING","PLATE"],
        "dimensionRules":["Metres only; every CAD dimension is positive and <=500 m.","I-section web < width; 2*flange < depth.","Opening dimensions must lie inside the host face."],
        "features":list(FEATURES), "dependencies":["COPY"], "connections":"UNRESOLVED_INTENT_ONLY",
        "constraints":["PARAMETER_RANGE","REQUIRED_SUPPORT_PATH","UNRESOLVED_CLEARANCE"],
        "maxAssemblies":16,"maxComponentsPerAssembly":8,"maxComponents":64,"maxCompileCost":128,
        "placement":"ASSEMBLY_LOCAL_ORIGIN_AND_HEADING_ONLY", "legacyPrimitivePolicy":"NOT_EXECUTED",
        "selectionPolicy":"AREA/POINT for unregistered compositions; BRIDGE AREA is conceptual with crossing conditions unresolved",
        "productionCadBuild":False, "engineeringStatus":"UNVERIFIED"}


@dataclass(frozen=True)
class FrozenAuthoringContext:
    """Only server code constructs this; never accepted in the authoring JSON."""
    source: Source
    selection_version_id: str
    selection_kind: str
    object_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    enabled: bool = False


@dataclass(frozen=True)
class ReviewCandidate:
    bundle: AuthoringBundle
    model: BIMProject
    mapping: CADMapping
    geometry: Geometry
    context: FrozenAuthoringContext
    candidate_hash: str


def unique(values, code="DUPLICATE_IDENTIFIER"):
    require(len(values) == len(set(values)), code, values)


def validate_plan(intent, plan):
    intent, plan = AuthoringIntent.model_validate(intent), AssemblyPlan.model_validate(plan)
    require(plan.intent_hash == digest(intent), "STALE_INTENT_HASH")
    unique([s.id for s in intent.systems])
    unique(intent.requested_features)
    unique([u.id for u in intent.unknowns])
    for system in intent.systems:unique(system.compatible_selection_kinds)
    unique([a.id for a in plan.assets]+[a.id for a in plan.assemblies]+[g.id for a in plan.assemblies for g in a.groups])
    systems = {s.id:s for s in intent.systems}
    unique([a.system_request_id for a in plan.assets])
    require({a.system_request_id for a in plan.assets} == set(systems), "SYSTEM_MEMBERSHIP_MISMATCH")
    assets={a.id:a for a in plan.assets}
    assemblies={a.id:a for a in plan.assemblies}
    require(all(a.asset_type == systems[a.system_request_id].asset_type for a in plan.assets), "ASSET_TYPE_MISMATCH")
    require(all(a.asset_id in assets for a in plan.assemblies), "UNRESOLVED_ASSET")
    require({a.asset_id for a in plan.assemblies} == set(assets), "EMPTY_ASSET")
    require(sum(g.count for a in plan.assemblies for g in a.groups) <= 64, "COMPONENT_BUDGET")
    require(all(sum(g.count for g in a.groups) <= 8 for a in plan.assemblies), "ASSEMBLY_BUDGET")
    for a in plan.assemblies:
        require(all(g.component_type in OPERATIONS for g in a.groups), "UNSUPPORTED_COMPONENT", [g.component_type for g in a.groups if g.component_type not in OPERATIONS])
        path, node = set(), a
        while node.parent_id:
            require(node.parent_id in assemblies, "UNRESOLVED_PARENT")
            require(node.id not in path, "ASSEMBLY_CYCLE")
            path.add(node.id)
            parent=assemblies[node.parent_id]
            require(parent.asset_id == a.asset_id, "CROSS_ASSET_PARENT")
            node=parent
    return intent, plan


def expansion_for(plan, expansion):
    """One immutable plan -> one bounded expansion. No random IDs or NLP."""
    expansion = AssemblyExpansion.model_validate(expansion)
    require(expansion.plan_hash == digest(plan), "STALE_PLAN_HASH")
    assembly=next((a for a in plan.assemblies if a.id == expansion.assembly_id), None)
    require(assembly is not None, "UNRESOLVED_ASSEMBLY")
    unique([c.id for c in expansion.components])
    groups={g.id:g for g in assembly.groups}
    require(all(c.group_id in groups for c in expansion.components), "UNRESOLVED_GROUP")
    for group in groups.values():
        members=[c for c in expansion.components if c.group_id == group.id]
        require(len(members) == group.count, "GROUP_COUNT_MISMATCH")
        require(all(c.component_type == group.component_type and c.role == group.role for c in members), "GROUP_ROLE_MISMATCH")
    return expansion


def _world_placements(plan):
    assemblies={a.id:a for a in plan.assemblies}
    result={}
    def resolve(a):
        if a.id in result:return result[a.id]
        local=a.placement
        if a.parent_id:
            parent=resolve(assemblies[a.parent_id])
            angle=math.radians(parent.heading_deg)
            x,y,z=local.origin
            local=Placement(origin=(parent.origin[0]+x*math.cos(angle)-y*math.sin(angle),
                parent.origin[1]+x*math.sin(angle)+y*math.cos(angle),parent.origin[2]+z),
                heading_deg=(parent.heading_deg+local.heading_deg+180)%360-180)
        result[a.id]=local
        return local
    for assembly in plan.assemblies:resolve(assembly)
    return result


def prepare_candidate(data, context):
    require(isinstance(context,FrozenAuthoringContext) and context.enabled, "AUTHORING_CAPABILITY_DISABLED")
    bundle=AuthoringBundle.model_validate(data)
    require(len(encode(bundle)) <= 250000, "AUTHORING_BYTE_BUDGET")
    intent,plan=validate_plan(bundle.intent,bundle.plan)
    require(set(intent.requested_features).issubset(FEATURES), "UNSUPPORTED_FEATURE", set(intent.requested_features)-set(FEATURES))
    require(all(context.selection_kind in s.compatible_selection_kinds for s in intent.systems), "SELECTION_INCOMPATIBLE")
    require(all(context.selection_kind in PLANNING_SELECTIONS.get(s.asset_type,("AREA","POINT")) for s in intent.systems),"SELECTION_CAPABILITY_MISMATCH")
    require(intent.requested_selection_ref in (None,context.selection_version_id), "UNAUTHORIZED_SELECTION_REFERENCE")
    unique(intent.requested_object_refs)
    require(set(intent.requested_object_refs).issubset(context.object_ids), "UNAUTHORIZED_OBJECT_REFERENCE")
    require(bundle.relationships.plan_hash == digest(plan), "STALE_RELATIONSHIP_PLAN")
    unique([e.assembly_id for e in bundle.expansions])
    require({e.assembly_id for e in bundle.expansions} == {a.id for a in plan.assemblies}, "EXPANSION_MEMBERSHIP_MISMATCH")
    expansions={e.assembly_id:expansion_for(plan,e) for e in bundle.expansions}
    placements=_world_placements(plan)
    components,recipes=[],[]
    for assembly in plan.assemblies:
        for c in sorted(expansions[assembly.id].components,key=lambda c:c.id):
            require(c.recipe.component_id == c.id, "RECIPE_IDENTITY_MISMATCH")
            require(c.recipe.operation in OPERATIONS[c.component_type], "UNSUPPORTED_COMPONENT_MAPPING",[c.id,c.component_type,c.recipe.operation])
            components.append(dict(id=c.id,asset_id=assembly.asset_id,assembly_id=assembly.id,component_type=c.component_type,
                parameters=c.parameters,placement=c.placement,material_id=c.material_id,
                geometry=dict(primitive=dict(primitive_type="BOX",center=[0,0,0],size=[1,1,1]),cross_section_id=c.cross_section_id),
                provenance=dict(design_id=context.source.design_id,design_version=context.source.design_version,
                    source_model_revision_id=context.source.source_model_revision_id,source_kind="PREVIEW_ASSUMPTION")))
            recipes.append(c.recipe)
    ids={c["id"] for c in components}
    unique([c["id"] for c in components])
    relations=bundle.relationships
    unique([a.id for a in plan.assets]+[a.id for a in plan.assemblies]+[g.id for a in plan.assemblies for g in a.groups]
        +[m.id for m in plan.materials]+[s.id for s in plan.cross_sections]+list(ids)
        +[r.id for r in relations.connections]+[r.id for r in relations.clearances]
        +[r.id for r in relations.dependencies]+[r.id for r in relations.constraints])
    unique([c.id for c in relations.connections]+[c.id for c in relations.clearances])
    internal=[]
    for r in relations.connections:
        require(r.from_component_id in ids and (r.to_component_id is None or r.to_component_id in ids), "UNRESOLVED_CONNECTION_REFERENCE")
        require(r.from_component_id != r.to_component_id, "SELF_CONNECTION")
        if r.to_component_id:
            internal.append(dict(id=r.id,from_component_id=r.from_component_id,to_component_id=r.to_component_id,kind=r.kind))
    support={c["id"]:[] for c in components}
    for r in relations.connections:
        if r.kind == "SUPPORTED_BY":support[r.from_component_id].append(r.to_component_id)
    def acyclic(node,path,done):
        require(node not in path,"SUPPORT_CYCLE")
        if node in done:return
        for target in support[node]:
            if target is not None:acyclic(target,path|{node},done)
        done.add(node)
    done=set()
    for node in support:acyclic(node,set(),done)
    for c in components:
        if c["component_type"] in {"SLAB","DECK","BEAM","GIRDER","COLUMN","PIER","BEARING"}:
            require(support[c["id"]], "REQUIRED_SUPPORT_INTENT_MISSING", [c["id"]])
            def reaches_ground(node,path):
                require(node not in path, "SUPPORT_CYCLE")
                return any(target is None or reaches_ground(target,path|{node}) for target in support[node])
            require(reaches_ground(c["id"],set()), "SUPPORT_PATH_UNRESOLVED", [c["id"]])
        else:
            require(any(r.from_component_id == c["id"] or r.to_component_id == c["id"] for r in relations.connections if r.kind != "ADJACENT_TO"), "REQUIRED_CONNECTION_INTENT_MISSING", [c["id"]])
    covered=set()
    for clearance in relations.clearances:
        unique(clearance.component_ids)
        require(set(clearance.component_ids).issubset(ids), "UNRESOLVED_CLEARANCE_REFERENCE")
        covered.update(clearance.component_ids)
    require(ids.issubset(covered), "REQUIRED_CLEARANCE_INTENT_MISSING", ids-covered)
    for c in components:
        c["relationship_ids"]=[r["id"] for r in internal if c["id"] in (r["from_component_id"],r["to_component_id"])]
        c["dependency_ids"]=[d.id for d in relations.dependencies if c["id"] in (d.source_component_id,d.target_component_id)]
    require(all(d.operation == "COPY" for d in relations.dependencies), "UNSUPPORTED_DEPENDENCY")
    model,_=validate_foundation(dict(assets=[dict(id=a.id,asset_type=a.asset_type,assembly_ids=[s.id for s in plan.assemblies if s.asset_id == a.id]) for a in plan.assets],
        assemblies=[dict(id=a.id,asset_id=a.asset_id,role=a.role,component_ids=[c["id"] for c in components if c["assembly_id"] == a.id],placement=placements[a.id]) for a in plan.assemblies],
        components=components,materials=plan.materials,cross_sections=plan.cross_sections,connections=internal,
        dependencies=relations.dependencies,constraints=relations.constraints,
        unknowns=list(MANDATORY_UNKNOWNS)+(["crossingConditions"] if context.selection_kind == "AREA" and any(s.asset_type == "BRIDGE" for s in intent.systems) else [])
            +[u.id for u in intent.unknowns if u.id not in MANDATORY_UNKNOWNS]))
    mapping=CADMapping(recipes=recipes)
    geometry=from_bim(model,mapping,source=context.source)
    require(all(d.recipe.profile == "RECTANGLE" for d in geometry.definitions
        if d.component_type in {"SLAB","DECK","BEARING","PLATE"} and d.recipe.operation == "PROFILE_EXTRUSION"),"UNSUPPORTED_COMPONENT_PROFILE")
    # Explicit shared operations only; bounds/units/I sections/holes validate here.
    require(sum(COST[d.recipe.operation] for d in geometry.definitions) <= 128, "COMPILATION_BUDGET")
    binding=dict(authoring=bundle.model_dump(mode="json",by_alias=True),geometry=geometry.model_dump(mode="json",by_alias=True),
        selection=context.selection_version_id,selectionKind=context.selection_kind,objects=context.object_ids,evidence=context.evidence_ids,
        capabilities=digest(capabilities()))
    return ReviewCandidate(bundle,model,mapping,geometry,context,digest(binding))


def proposal_summary(candidate, native_results=None):
    """Display data for existing review. Never a validation/approval assertion."""
    b=candidate.bundle
    native_ids={r.component_id for r in (native_results or [])}
    if native_results is not None:
        unique([r.component_id for r in native_results])
        require(native_ids == {d.component_id for d in candidate.geometry.definitions}, "NATIVE_RESULT_MEMBERSHIP")
        for d,r in zip(candidate.geometry.definitions,sorted(native_results,key=lambda r:next(i for i,x in enumerate(candidate.geometry.definitions) if x.component_id == r.component_id))):
            require(r.definition_hash == digest(d) and r.geometry_valid, "NATIVE_RESULT_BINDING")
    return dict(schemaVersion="bim-authoring-review/1",candidateHash=candidate.candidate_hash,
        requestedStructure=b.intent.requested_structure,sourceRevision=candidate.context.source.revision_id,
        assets=[dict(id=a.id,name=a.name,assetType=a.asset_type) for a in b.plan.assets],
        assemblies=[dict(id=a.id,parentId=a.parent_id,role=a.role,groups=[g.model_dump(mode="json",by_alias=True) for g in a.groups]) for a in b.plan.assemblies],
        components=[dict(id=d.component_id,assetId=d.asset_id,assemblyId=d.assembly_id,
            role=next(c.role for e in b.expansions for c in e.components if c.id == d.component_id),
            parameters=d.recipe.parameters,material=d.material.name,recipe=d.recipe.operation,profile=d.recipe.profile) for d in candidate.geometry.definitions],
        assumptions=list(b.intent.assumptions)+["Geometry preview only; dimensions are not structural sizing."],
        missingSiteInformation=list(candidate.model.unknowns),unsupportedPortions=[],
        unresolvedConnections=[c.model_dump(mode="json",by_alias=True) for c in b.relationships.connections],
        unresolvedClearances=[c.model_dump(mode="json",by_alias=True) for c in b.relationships.clearances],
        geometryStatus="NATIVE_GEOMETRY_VERIFIED" if native_results is not None else "CONTRACT_VALID_NATIVE_NOT_RUN",
        engineeringStatus="UNVERIFIED",finalizationBlocked=True,productionCadBuild=False)


def review_offline(data,context):
    """Human-readable rejection without partial BIM or native execution."""
    from pydantic import ValidationError
    try:return proposal_summary(prepare_candidate(data,context))
    except ValidationError as error:
        issues=[dict(code="SCHEMA_INVALID",path=".".join(str(p) for p in e["loc"]),type=e["type"]) for e in error.errors(include_input=False)[:20]]
    except AuthoringError as error:
        issues=[dict(code=error.code,references=list(error.references))]
    except ValueError as error:
        issues=[dict(code=str(error).split("\n",1)[0][:128])]
    return dict(schemaVersion="bim-authoring-review/1",geometryStatus="REJECTED",engineeringStatus="UNVERIFIED",
        finalizationBlocked=True,productionCadBuild=False,validationIssues=issues,
        unsupportedPortions=[i for i in issues if "UNSUPPORTED" in i["code"]],missingSiteInformation=list(MANDATORY_UNKNOWNS))


def compile_offline_proof(candidate):
    """Explicit offline test proof only. No artifacts, proposal approval or revisions."""
    require(candidate.context.enabled, "AUTHORING_CAPABILITY_DISABLED")
    checked=prepare_candidate(candidate.bundle,candidate.context)
    require(checked.candidate_hash == candidate.candidate_hash and checked.geometry == candidate.geometry
        and checked.model == candidate.model and checked.mapping == candidate.mapping,"CANDIDATE_MUTATED")
    from app.experimental.cad_worker import compile_batch
    results,blobs=compile_batch(candidate.geometry)
    from app.experimental.cad_contract import Manifest
    Manifest(geometry=candidate.geometry,results=results)
    import hashlib
    for result in results:
        for artifact in (result.brep,result.mesh):
            require(artifact.sha256 in blobs and len(blobs[artifact.sha256]) == artifact.byte_length
                and hashlib.sha256(blobs[artifact.sha256]).hexdigest() == artifact.sha256,"NATIVE_ARTIFACT_INTEGRITY")
    return results,blobs


def proposal_request(candidate, *, request_id, message_id):
    from app.domain.assistant_runtime import ProposalRequest
    summary=proposal_summary(candidate)
    return ProposalRequest(client_request_id=request_id,message_id=message_id,
        title=candidate.bundle.intent.requested_structure[:255],rationale="Offline BIM candidate; explicit human review required. Engineering and all connection/clearance conditions remain unverified.",
        assets=[dict(asset_type="CUSTOM",name=a.name,requirements=["bim-authoring-sha256:"+candidate.candidate_hash,
            "Requested civil asset: "+a.asset_type,"Geometry: CONTRACT_VALID_NATIVE_NOT_RUN",
            "Missing: "+", ".join(summary["missingSiteInformation"]),
            "Materials: "+", ".join(sorted({d.material.name for d in candidate.geometry.definitions if d.asset_id == a.id})),
            "Dimensions (m): "+", ".join(f"{key} {min(values):g}..{max(values):g}" for key in ("length","width","depth","thickness")
                if (values:=[d.recipe.parameters[key] for d in candidate.geometry.definitions if d.asset_id == a.id and key in d.recipe.parameters])),
            *["Assembly "+s.id+": "+", ".join(f"{g.count} {g.role}" for g in s.groups) for s in candidate.bundle.plan.assemblies if s.asset_id == a.id],
            "Connections and clearances UNRESOLVED; no CAD finalization."] ) for a in candidate.bundle.plan.assets],
        assumptions=summary["assumptions"],warnings=["OFFLINE_ONLY: no native Build from AI responses.","Unresolved connections/clearances block finalization; valid geometry is not safe engineering."])


def compact_schema(value):
    """Drop presentation-only titles; retain every schema validation keyword."""
    if isinstance(value,dict):return {k:compact_schema(v) for k,v in value.items() if not (k == "title" and isinstance(v,str))}
    if isinstance(value,list):return [compact_schema(v) for v in value]
    return value


def stage_capabilities(stage):
    full=capabilities()
    common={k:full[k] for k in ("version","productionCadBuild","engineeringStatus")}
    common["componentTypes"]=list(OPERATIONS)
    common["unsupported"]=["REINFORCEMENT","STRUCTURAL_ANALYSIS","COMPLEX_FOUNDATIONS","ARBITRARY_3D_BRACING"]
    if stage == "UNDERSTAND":return {**common,"features":full["features"]}
    if stage == "PLAN":return {**common,**{k:full[k] for k in ("profiles","maxAssemblies","maxComponentsPerAssembly","maxComponents","placement")},
        "sectionParameters":{**full["recipes"]["PROFILE_EXTRUSION"]["sectionParameters"],**full["recipes"]["CIRCULAR_COLUMN"]["sectionParameters"]}}
    if stage == "EXPAND":return full
    return {**common,**{k:full[k] for k in ("dependencies","connections","constraints","maxComponents")}}


def stage_packet(stage, *, intent=None, plan=None, assembly_id=None, expansions=None, request_text=None):
    """Schema/prompt packets for a future PRIMARY caller. Never calls a provider."""
    contracts={"UNDERSTAND":AuthoringIntent,"PLAN":AssemblyPlan,"EXPAND":AssemblyExpansion,"RELATE":AssemblyRelationships}
    require(stage in contracts, "UNKNOWN_AUTHORING_STAGE")
    inputs={}
    if stage == "UNDERSTAND":
        request_text=request_text or (AuthoringIntent.model_validate(intent).requested_structure if intent is not None else None)
        require(isinstance(request_text,str) and 0 < len(request_text) <= 4000,"HUMAN_REQUEST_REQUIRED")
        inputs["humanRequest"]=request_text
    if stage != "UNDERSTAND":
        intent=AuthoringIntent.model_validate(intent)
        inputs={"intent":intent.model_dump(mode="json",by_alias=True),"intentHash":digest(intent)}
    if stage in ("EXPAND","RELATE"):
        _,plan=validate_plan(intent,plan)
        inputs.update(planHash=digest(plan))
        if stage == "EXPAND":
            assembly=next((a for a in plan.assemblies if a.id == assembly_id),None)
            require(assembly is not None,"UNRESOLVED_ASSEMBLY")
            inputs["assembly"]=assembly.model_dump(mode="json",by_alias=True)
            inputs["asset"]=next(a.model_dump(mode="json",by_alias=True) for a in plan.assets if a.id==assembly.asset_id)
            # The plan does not bind groups to materials/sections. All shared
            # definitions remain relevant choices; do not invent a subset.
            inputs["materials"]=[m.model_dump(mode="json",by_alias=True) for m in plan.materials]
            inputs["crossSections"]=[s.model_dump(mode="json",by_alias=True) for s in plan.cross_sections]
        else:
            require(expansions is not None,"EXPANSIONS_REQUIRED")
            checked=[expansion_for(plan,e) for e in expansions]
            unique([e.assembly_id for e in checked])
            require({e.assembly_id for e in checked} == {a.id for a in plan.assemblies},"EXPANSION_MEMBERSHIP_MISMATCH")
            inputs["assemblies"]=[a.model_dump(mode="json",by_alias=True) for a in plan.assemblies]
            inputs["components"]=[dict(id=c.id,assemblyId=e.assembly_id,componentType=c.component_type,
                parameters=[p.model_dump(mode="json",by_alias=True) for p in c.parameters]) for e in checked for c in e.components]
    scope={"UNDERSTAND":"Identify systems and user-supplied requirements only. No assembly, material catalog, recipe or component design. Preserve explicit dimensions/preferences in requestedStructure or purpose; do not invent dimensions. Mark unsupported requested features explicitly for rejection.",
        "PLAN":"Plan hierarchical assemblies and shared definitions only; no component expansion.",
        "EXPAND":"Expand only this assembly. Reuse exact shared IDs; do not duplicate definitions.",
        "RELATE":"Use exact component IDs. Required support paths and clearance unknowns must remain explicit unresolved intent; never omit them to bypass validation."}[stage]
    packet=dict(stage=stage,capabilities=stage_capabilities(stage),input=inputs,outputSchema=compact_schema(contracts[stage].model_json_schema(by_alias=True)),
        instruction="Return one concise JSON object matching outputSchema. No prose, scripts, approval or Build. Preserve source references and unknown terrain/soil/loads/elevation; engineering remains UNVERIFIED. "+scope)
    if stage == "EXPAND":
        kinds={g.component_type for g in assembly.groups}
        ops={op for kind in kinds for op in OPERATIONS[kind]}
        packet["capabilities"]["componentOperations"]={k:v for k,v in packet["capabilities"]["componentOperations"].items() if k in kinds}
        packet["capabilities"]["recipes"]={k:v for k,v in packet["capabilities"]["recipes"].items() if k in ops}
    require(len(encode(packet)) <= 24000,"STAGE_CONTEXT_BUDGET")
    return packet


def stage_context(stage, snapshot, frozen_hash):
    """Verified projection only; full authoritative snapshot stays server-owned."""
    profile=snapshot["siteProfile"]
    projected=dict(frozenContextHash=frozen_hash,selectionVersionId=snapshot["selectionVersionId"],selectionKind=snapshot["selectionKind"],
        objectIds=snapshot["objectIds"],evidenceIds=snapshot["evidenceIds"],acceptedRequirements=snapshot["acceptedRequirements"],
        explicitUnknowns=snapshot["explicitUnknowns"],engineeringStatus="UNVERIFIED")
    if stage != "UNDERSTAND":
        # Normalized intent can omit an explicit preference/dimension. Keep
        # the short authoritative user requirements available downstream.
        projected["userRequirementsText"]=snapshot["userRequest"]
    if stage in {"UNDERSTAND","PLAN"}:
        projected["siteSummary"]={k:profile[k] for k in ("dimensions","relief","verticalReference","planningFacts","constraints","limitations") if k in profile}
        projected["terrainSummary"]=profile.get("terrain",{}).get("sampleSummary",{})
        if stage == "UNDERSTAND":
            projected["siteEvidenceIds"]=profile.get("evidenceIds",[])
            if "dimensions" in projected["siteSummary"]:
                projected["siteSummary"]["dimensions"]={k:v for k,v in profile["dimensions"].items() if v.get("applicability")!="NOT_APPLICABLE"}
            relief=profile.get("relief",{})
            relief_facts={k:v for k,v in relief.items() if isinstance(v,dict)}
            # Unknown relief carries repeated evidence lists. Preserve each
            # unknown value/reason and one exact union of evidence references.
            if relief_facts and all(v.get("value") is None for v in relief_facts.values()):
                projected["siteSummary"]["relief"]={k:{x:v[x] for x in ("sourceKind","value","reason") if x in v} for k,v in relief_facts.items()}
                projected["siteEvidenceIds"]=sorted(set(projected["siteEvidenceIds"])|{e for v in relief_facts.values() for e in v.get("evidenceIds",[])})
    return deepcopy(projected)


def freeze_owned_context(db, *, project_id, user_id, message_id):
    """Resolve authoritative source and scope from an owned frozen USER message."""
    from app.experimental.cad_capability import require_cad
    from app.services.assistant.storage import owned_row, identity, digest as context_digest
    from app.experimental.cad_artifacts import owned_source
    from app.db.models import ModelRevision
    from app.services.site_profiles.service import SiteProfileService
    require_cad(db,project_id,user_id)
    message=owned_row(db,"conversation_messages",project_id,message_id)
    require(message["role"] == "USER","HUMAN_CONTEXT_REQUIRED")
    context=message["context"]
    require(not context.get("editorDirty"),"DIRTY_SOURCE")
    base=db.query(ModelRevision).filter_by(project_id=project_id,design_scenario_id=int(context.get("scenarioId") or 0)).order_by(ModelRevision.revision_number.desc()).first()
    require(base is not None and str(base.id) == context.get("modelRevisionId"),"STALE_SOURCE_REVISION")
    profile=owned_row(db,"site_profile_versions",project_id,context["siteProfileVersionId"])
    head=owned_row(db,"site_profiles",project_id,profile["profile_id"])
    require(head["latest_version_id"] == profile["id"] and SiteProfileService().read(db,project_id,head["id"])["current"],"STALE_SITE_PROFILE")
    require(profile["selection_version_id"] == context["siteSelectionVersionId"],"SELECTION_CONTEXT_MISMATCH")
    selection=owned_row(db,"site_selection_versions",project_id,context["siteSelectionVersionId"])
    objects={c["id"]:c for c in base.document_json["components"]}
    require(all(ref["objectId"] in objects and context_digest(objects[ref["objectId"]]) == ref["geometryHash"] for ref in context["selection"]),"STALE_OBJECT_SELECTION")
    source=owned_source(db,user_id=user_id,project_id=project_id,revision_id=base.id,
        design_id=identity(project_id,"bim-authoring",message_id),design_version=1,source_model_revision_id=str(base.id))
    return FrozenAuthoringContext(source,selection["id"],selection["kind"],
        tuple(ref["objectId"] for ref in context["selection"]),
        (selection["selection_payload"]["transformationEvidenceId"],),True)


def create_offline_proposal(db, *, project_id, user_id, message_id, request_id, data, store=None):
    """Existing proposal review + private snapshot, with zero approval/native work."""
    from app.services.assistant.proposals import ProposalService
    from app.experimental.cad_artifacts import PrivateStore
    from app.db.models import GeneratedFile
    context=freeze_owned_context(db,project_id=project_id,user_id=user_id,message_id=message_id)
    candidate=prepare_candidate(data,context)
    view=ProposalService().create(db,project_id,user_id,proposal_request(candidate,request_id=request_id,message_id=message_id))
    snapshot=dict(schemaVersion="bim-authoring-snapshot/1",authoring=candidate.bundle.model_dump(mode="json",by_alias=True),
        bim=candidate.model.model_dump(mode="json",by_alias=True),mapping=candidate.mapping.model_dump(mode="json",by_alias=True),
        review=proposal_summary(candidate))
    sha=digest(snapshot)
    existing=db.query(GeneratedFile).filter_by(project_id=project_id,file_type="bim_authoring_review_v1").all()
    saved=next((r for r in existing if r.metadata_json.get("proposalVersionId") == view["id"]),None)
    store=store or PrivateStore()
    if saved:
        require(saved.metadata_json["snapshotHash"] == sha,"AUTHORING_SNAPSHOT_BINDING")
        store.get(project_id,sha)
    else:
        try:
            store.put(project_id,sha,encode(snapshot))
            db.add(GeneratedFile(project_id=project_id,model_revision_id=context.source.revision_id,
                file_type="bim_authoring_review_v1",file_url="cad-private:"+sha,
                metadata_json=dict(snapshotHash=sha,proposalVersionId=view["id"],candidateHash=candidate.candidate_hash)))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return dict(proposal=view,review=proposal_summary(candidate))
