"""Immutable concept proposals. Approval is an application command, never an LLM tool."""
import sqlalchemy as sa
from app.db.models import EngineeringAnalysis, ModelRevision, ModelPlacement, Project, ActiveTerrainConfiguration
from app.domain.stage1 import DependencyManifest, ProposalPayload, ValidationResult
from app.services.assistant.storage import digest, identity, insert, lock_project, owned_row, rows, table, update, error, now
from app.services.assistant.conversations import reject_secrets
from app.services.assistant.memory import MemoryService
from app.services.site_profiles.retrieval import record

TRANSITIONS = {"DRAFT": {"GENERATING"}, "GENERATING": {"READY_FOR_REVIEW", "HAS_ISSUES"},
    "READY_FOR_REVIEW": {"APPROVED", "REJECTED", "STALE"}, "HAS_ISSUES": {"REJECTED", "STALE"},
    "APPROVED": {"BUILT", "STALE"}, "STALE": set(), "REJECTED": set(), "BUILT": set()}


def asset_proposals(db, project_id, payload):
    """Read compatibility view; legacy immutable payloads and hashes stay intact."""
    from app.domain.composition import AssetProposal
    from app.services.assistant.foundation import capability
    from app.services.assistant.composition import project_composition
    edges = project_composition(db, project_id)["relationships"]
    constraints = [r["id"] for r in rows(db, "constraint_datasets", project_id)]
    result = []
    for i, sid in enumerate(payload["contract"]["assetSpecificationVersionIds"]):
        spec = owned_row(db, "asset_specification_versions", project_id, sid)
        asset = payload["request"]["assets"][i]
        cap = capability(asset["assetType"])
        result.append(AssetProposal(asset_request_id=asset.get("assetRequestId") or f"A{i+1:02d}", asset_id=spec["asset_id"],
            asset_type=asset["assetType"], asset_family=cap.asset_family, display_name=asset["name"],
            requirements=asset.get("requirements", []), assumptions=payload["request"].get("assumptions", []), constraint_ids=constraints,
            specification_ref={"id":sid,"version":spec["version"],"contentHash":spec["content_hash"]}, capabilities=cap,
            warnings=payload["request"].get("warnings", []), blockers=[] if asset.get("buildingSpec") or asset.get("ai3dDesign") or asset.get("buildingPatch") else ["A supported typed specialist specification is required before generation."],
            dependency_refs=[r["id"] for r in edges if spec["asset_id"] in (r["from_asset_id"],r["to_asset_id"])],
            generation_eligible=bool(asset.get("buildingSpec") or asset.get("ai3dDesign") or asset.get("buildingPatch")) and "GENERATE" in cap.supported_operations).model_dump(mode="json", by_alias=True))
    return result


def dependencies(db, project_id, context, proposal_asset_ids=(), include_relationships=True):
    """Scope model comparisons to attached objects; never include viewport/UI state."""
    db.expire_all()
    project = db.get(Project, project_id)
    selection = owned_row(db, "site_selection_versions", project_id, context["siteSelectionVersionId"])
    t = table("site_selection_versions")
    latest = db.execute(sa.select(t.c.content_hash).where(t.c.project_id == project_id,
        t.c.selection_id == selection["selection_id"]).order_by(t.c.version.desc()).limit(1)).scalar_one()
    profile = owned_row(db, "site_profile_versions", project_id, context["siteProfileVersionId"])
    head = owned_row(db, "site_profiles", project_id, profile["profile_id"])
    facts = owned_row(db, "site_profile_versions", project_id, head["latest_version_id"])["payload"]
    # Model references and assessment IDs are not site facts.
    facts = {k: v for k, v in facts.items() if k not in {"id", "version", "contentHash", "createdAt", "onSiteObjects", "readinessAssessmentId", "dependencyManifestId"}}
    selected = context["selection"]
    assets = {r["assetId"] for r in selected} | set(proposal_asset_ids)
    model = db.query(ModelRevision).filter_by(project_id=project_id)
    if context.get("scenarioId"):
        model = model.filter_by(design_scenario_id=int(context["scenarioId"]))
    model = model.order_by(ModelRevision.id.desc()).first()
    if selected:
        components = {str(c["id"]): c for c in (model.document_json.get("components", []) if model else [])}
        model_value = {r["objectId"]: components.get(r["objectId"]) for r in selected}
    else:
        model_value = model.id if model else None
    placement = db.query(ModelPlacement).filter_by(project_id=project_id, model_revision_id=model.id).first() if model else None
    placement_value = record(placement)
    if placement_value:
        placement_value = {k: v for k, v in placement_value.items() if k not in {"id", "model_revision_id"}}
    memory = [{"id": m["versionId"], "hash": m["contentHash"]} for m in MemoryService().list(db, project_id, status="ACCEPTED")
        if m["assetId"] is None or m["assetId"] in assets]
    data = [("SELECTION", "selection", latest), ("BOUNDARY", "boundary", project.boundary_geojson),
        ("TERRAIN", "active-terrain", record(db.get(ActiveTerrainConfiguration, project_id))),
        ("SURVEY_EVIDENCE", "site-facts", facts), ("MODEL", "model", model_value),
        ("PLACEMENT", "placement", placement_value), ("MEMORY", "memory", sorted(memory, key=lambda m:m["id"])),
        ("CONSTRAINT", "constraints", rows(db, "constraint_datasets", project_id))]
    if include_relationships:
        from app.services.assistant.composition import project_composition
        edges = [r for r in project_composition(db, project_id)["relationships"] if r["from_asset_id"] in assets or r["to_asset_id"] in assets]
        data.append(("RELATIONSHIP", "composition", sorted(edges, key=lambda r: r["relationship_id"])))
    entries = [{"kind": kind, "id": key, "version": digest(value), "contentHash": digest(value),
        "policy": "MUST_MATCH_CURRENT", "scope": "PROJECT" if not assets else ",".join(sorted(assets))[:128]} for kind,key,value in data]
    return DependencyManifest(schema_version="dependencies/1", entries=entries, hash=digest(entries)).model_dump(mode="json", by_alias=True)


class ProposalService:
    def transition(self, db, project_id, version_id, status):
        state = owned_row(db, "proposal_version_states", project_id, identity(version_id, "state"))
        if state["status"] == status:
            return
        if status not in TRANSITIONS[state["status"]]:
            error(409, "INVALID_TRANSITION", "Proposal cannot enter this state.")
        update(db, "proposal_version_states", project_id, state["id"], status=status)

    def create(self, db, project_id, actor_id, request):
        lock_project(db, project_id)
        # Preview assumptions use the existing visible, acknowledged proposal-memory mechanism.
        assumptions=list(request.assumptions)
        for asset in request.assets:
            if sum(x is not None for x in (asset.building_spec,asset.building_patch,asset.ai3d_design))>1:error(422,"AMBIGUOUS_SPECIFICATION","Use one typed specification per asset.")
            if asset.building_patch:
                for statement in asset.building_patch.assumptions:
                    if statement not in assumptions: assumptions.append(statement)
            if asset.building_spec or asset.ai3d_design:
                for item in (asset.building_spec or asset.ai3d_design).assumptions:
                    statement=f"PREVIEW_ASSUMPTION ({asset.name}): {item.field} = {item.value}. {item.reason}"
                    if statement not in assumptions:assumptions.append(statement)
        if len(assumptions)>20:error(422,"ASSUMPTION_LIMIT","Limit the proposal to twenty explicit assumptions.")
        request=request.model_copy(update={"assumptions":assumptions})
        request_data = request.model_dump(mode="json", by_alias=True)
        for asset in request_data["assets"]:
            if asset.get("assetRequestId") is None: asset.pop("assetRequestId", None)
        reject_secrets(request_data)
        vid = identity("proposal-version", project_id, actor_id, request.client_request_id)
        existing = db.execute(sa.select(table("design_proposal_versions")).where(table("design_proposal_versions").c.id == vid)).mappings().first()
        if existing:
            if existing["payload"]["requestHash"] != digest(request_data):
                error(409, "IDEMPOTENCY_CONFLICT", "Proposal request key was already used.")
            db.commit()
            return self.read(db, project_id, vid)
        message = owned_row(db, "conversation_messages", project_id, request.message_id)
        context = message["context"]
        from app.services.assistant.policy import evaluate
        policy=evaluate(message)
        if message["role"]!="USER" or policy["allowedEffect"]!="PROPOSAL_ONLY":
            error(403,"READ_ONLY_POLICY","Questions and explanations cannot create proposals.")
        if not context.get("siteProfileVersionId") or not context.get("siteSelectionVersionId"):
            error(422, "SITE_PROFILE_REQUIRED", "Refresh the site and send a new message before proposing a concept.")
        if request.translation and not set(request.translation.object_ids) <= {r["objectId"] for r in context["selection"]}:
            error(422, "TARGET_NOT_ATTACHED", "A proposal may target only the objects attached to its source message.")
        expected=policy["understanding"]["proposedTranslation"]
        if expected and not any(a.building_patch for a in request.assets) and (not request.translation or request.translation.object_ids!=expected["objectIds"] or list(request.translation.delta_m)!=expected["deltaM"]):
            error(422,"TRANSLATION_MISMATCH","The proposal must preserve the selected targets and requested distance/direction.")
        attached_profile=owned_row(db,"site_profile_versions",project_id,context["siteProfileVersionId"])
        profile_head=owned_row(db,"site_profiles",project_id,attached_profile["profile_id"])
        if profile_head["latest_version_id"]!=attached_profile["id"]:
            error(409,"STALE_SITE_PROFILE","The message references an older site profile. Send a new request with current facts.")
        scoped_assets={ref["assetId"] for ref in context["selection"]}
        if context.get("proposalVersionId"):
            active_proposal=owned_row(db,"design_proposal_versions",project_id,context["proposalVersionId"])
            scoped_assets.update(owned_row(db,"asset_specification_versions",project_id,sid)["asset_id"] for sid in active_proposal["payload"]["contract"]["assetSpecificationVersionIds"])
        current_memory={m["versionId"] for m in MemoryService().list(db,project_id,status="ACCEPTED") if m["assetId"] is None or m["assetId"] in scoped_assets}
        if current_memory!=set(context["memoryVersionIds"]):
            error(409,"STALE_MEMORY","Accepted requirements changed after the source message. Send a new request.")
        from app.services.site_profiles.service import SiteProfileService
        if not SiteProfileService().read(db,project_id,attached_profile["profile_id"])["current"]:
            error(409,"STALE_SITE_PROFILE","Refresh the site profile before proposing.")
        latest_model=db.query(ModelRevision).filter_by(project_id=project_id)
        if context.get("scenarioId"):latest_model=latest_model.filter_by(design_scenario_id=int(context["scenarioId"]))
        latest_model=latest_model.order_by(ModelRevision.id.desc()).first()
        if context["selection"]:
            current_objects={str(c["id"]):c for c in (latest_model.document_json.get("components",[]) if latest_model else [])}
            if any(digest(current_objects.get(ref["objectId"]))!=ref["geometryHash"] for ref in context["selection"]):
                error(409,"STALE_SELECTION","Attached objects changed after this message was sent.")
        parent = owned_row(db, "design_proposal_versions", project_id, request.parent_version_id) if request.parent_version_id else None
        if parent and parent["payload"]["context"]["siteSelectionVersionId"] != context["siteSelectionVersionId"]:
            error(409, "SELECTION_CHANGED", "Start a new proposal for a different site selection.")
        pid = parent["proposal_id"] if parent else identity(vid, "proposal")
        t = table("design_proposal_versions")
        version = (db.execute(sa.select(sa.func.max(t.c.version)).where(t.c.proposal_id == pid)).scalar() or 0) + 1
        if parent and parent["version"] != version - 1:
            error(409, "REVISION_CONFLICT", "Revise the latest proposal version.")
        if not parent:
            insert(db, "design_proposals", id=pid, project_id=project_id, name=request.title)
        manifest_id = identity(vid, "manifest")
        specification_ids = []
        proposal_asset_ids=[]
        parent_specs=[owned_row(db,"asset_specification_versions",project_id,sid) for sid in parent["payload"]["contract"]["assetSpecificationVersionIds"]] if parent else []
        for i, asset in enumerate(request.assets):
            aid, sid = identity(vid, "asset", i), identity(vid, "spec", i)
            if asset.building_patch:
                if asset.building_spec or len(request.assets) != 1 or context["editorDirty"]:
                    error(422,"INVALID_PATCH_REQUEST","One saved-state patch asset per proposal is supported.")
                patch = asset.building_patch
                if patch.source_model_revision_id != context.get("modelRevisionId") or not context["selection"] or {op.target_component_id for op in patch.operations} != {ref["objectId"] for ref in context["selection"]}:
                    error(422,"TARGET_NOT_ATTACHED","Patch must preserve the exact single attached target and saved revision.")
                from app.services.assistant.building_patch import BuildingPatchValidator
                preview = BuildingPatchValidator().preview(db, project_id, patch)
                if expected:
                    op = patch.operations[0].parameters
                    delta = [float(v)/(1000 if op.unit == "mm" else 1) for v in op.delta] if op.operation_type == "MOVE_COMPONENT" else None
                    if delta != expected["deltaM"]: error(422,"TRANSLATION_MISMATCH","Preserve the user's exact unit-normalized movement.")
                aid = patch.asset_id
                source_asset = owned_row(db,"asset_instances",project_id,aid)
                if source_asset["asset_type"] != asset.asset_type: error(422,"TARGET_BUILDING_MISMATCH","Asset type must match persisted lineage.")
                spec_table = table("asset_specification_versions")
                spec_version = (db.execute(sa.select(sa.func.max(spec_table.c.version)).where(spec_table.c.asset_id==aid)).scalar() or 0)+1
                spec = {"schemaVersion":"building-patch/1",**asset.model_dump(mode="json",by_alias=True),"executable":True,
                    "patchPreview":preview["summary"],"affectedComponentIds":preview["affectedComponentIds"]}
                insert(db,"asset_specification_versions",id=sid,project_id=project_id,asset_id=aid,version=spec_version,
                    schema_id="building-patch",schema_version="1",payload=spec,content_hash=digest(spec))
                specification_ids.append(sid);proposal_asset_ids.append(aid)
                continue
            previous=next((s for s in parent_specs if s["payload"].get("assetType")==asset.asset_type and s["payload"].get("name")==asset.name),None)
            if previous:
                aid=previous["asset_id"]
                spec_table=table("asset_specification_versions")
                spec_version=(db.execute(sa.select(sa.func.max(spec_table.c.version)).where(spec_table.c.asset_id==aid,spec_table.c.project_id==project_id)).scalar() or 0)+1
            else:
                spec_version=1
                insert(db, "asset_instances", id=aid, project_id=project_id, asset_type=asset.asset_type, name=asset.name)
            spec = {"schemaVersion": "civil-concept/1", **asset.model_dump(mode="json", by_alias=True), "executable": False}
            if asset.ai3d_design:
                if len(request.assets)!=1 or asset.asset_type!="AI3D_DESIGN":error(422,"INVALID_GENERIC_DESIGN_REQUEST","Represent all systems in one AI3D_DESIGN asset.")
                from app.services.assistant.ai3d_validation import validate_saved_design
                summary,result=validate_saved_design(db,project_id,context,asset.ai3d_design)
                spec.update(schemaVersion="ai-3d-design/1",executable=True,specialistValidation=result,
                    provenance={"proposalId":pid,"proposalVersionId":vid,"proposalVersion":version,"sourceModelRevisionId":context.get("modelRevisionId"),
                        "siteSelectionVersionId":context["siteSelectionVersionId"],"siteProfileVersionId":context["siteProfileVersionId"]})
            if asset.building_spec:
                from app.services.assistant.specialists import ADAPTERS
                adapter=ADAPTERS.resolve(asset.asset_type)
                if not adapter:error(422,"GENERATION_UNAVAILABLE","No building adapter supports this asset type.")
                result=adapter.validate_specification(asset.building_spec)
                if result["issues"]:error(422,"INVALID_BUILDING_SPEC",result)
                spec.update(schemaVersion="building-concept/1",executable=True,specialistValidation=result,
                    provenance={"proposalId":pid,"proposalVersionId":vid,"proposalVersion":version,"sourceModelRevisionId":context.get("modelRevisionId"),
                        "siteSelectionVersionId":context["siteSelectionVersionId"],"siteProfileVersionId":context["siteProfileVersionId"]})
            insert(db, "asset_specification_versions", id=sid, project_id=project_id, asset_id=aid, version=spec_version,
                schema_id="civil-concept", schema_version="1", payload=spec, content_hash=digest(spec))
            specification_ids.append(sid)
            proposal_asset_ids.append(aid)
        manifest = dependencies(db, project_id, context, proposal_asset_ids)
        insert(db, "dependency_manifests", id=manifest_id, project_id=project_id, payload=manifest, content_hash=manifest["hash"])
        alternative_ids = [identity(vid, "alternative", i) for i in range(len(request.alternatives))]
        assumption_ids=[]
        for i,statement in enumerate(request.assumptions):
            iid,mid=identity(vid,"assumption-item",i),identity(vid,"assumption",i)
            content={"kind":"ASSUMPTION","statement":statement,"impact":"Concept proposal requires explicit review.","requiredVerification":"User or specialist verification","scope":"CONCEPT_ONLY"}
            value={"content":content,"sourceMessageIds":[message["id"]],"evidenceIds":[],"proposedBy":str(actor_id),"createdAt":now(),"requestHash":digest(content)}
            insert(db,"project_memory_items",id=iid,project_id=project_id,kind="ASSUMPTION",asset_id=None)
            insert(db,"project_memory_versions",id=mid,project_id=project_id,item_id=iid,version=1,payload=value,content_hash=digest(value),supersedes_id=None)
            insert(db,"project_memory_states",id=identity(mid,"state"),project_id=project_id,memory_version_id=mid,status="PROPOSED",actor_id=actor_id)
            assumption_ids.append(mid)
        scenario_id = context.get("scenarioId")
        if not scenario_id:
            # Existing contract requires a scenario reference even for a concept-only proposal.
            from app.db.models import DesignScenario
            scenario = DesignScenario(project_id=project_id, name=request.title, status="concept_proposal")
            db.add(scenario); db.flush(); scenario_id = str(scenario.id)
        contract = ProposalPayload(schema_version="proposal/1", site_profile_version_id=context["siteProfileVersionId"],
            input_memory_version_ids=context["memoryVersionIds"], asset_specification_version_ids=specification_ids,
            layout_geometry_refs=[], assumption_version_ids=assumption_ids, alternative_ids=alternative_ids,
            source_scenario_id=scenario_id, source_model_revision_id=context.get("modelRevisionId"),
            dependency_manifest_id=manifest_id, parent_version_id=request.parent_version_id)
        payload = {"contract": contract.model_dump(mode="json", by_alias=True), "context": context, "request": request_data,
            "requestHash": digest(request_data), "preview": request.translation.model_dump(mode="json", by_alias=True) if request.translation else None,
            "previewOnly": True, "validationId": identity(vid, "validation")}
        if any(a.building_patch for a in request.assets):
            payload["patchPreview"] = {**preview["summary"],"affectedComponentIds":preview["affectedComponentIds"]}
        # Concept relationships are versioned with the proposal, never applied to live composition by the LLM.
        payload["planning"]={**policy["understanding"],"proposedAssets":request_data["assets"],
            "assumptions":request_data["assumptions"],"constraints":[r["id"] for r in rows(db,"constraint_datasets",project_id)],
            "acceptedMemoryVersionIds":context["memoryVersionIds"],"dependencyManifest":manifest}
        payload["assetProposals"] = asset_proposals(db, project_id, payload)
        insert(db, "design_proposal_versions", id=vid, project_id=project_id, proposal_id=pid, version=version,
            site_profile_version_id=context["siteProfileVersionId"], dependency_manifest_id=manifest_id, parent_version_id=request.parent_version_id,
            source_model_revision_id=int(context["modelRevisionId"]) if context.get("modelRevisionId") else None, payload=payload, content_hash=digest(payload))
        insert(db, "proposal_version_states", id=identity(vid,"state"), project_id=project_id, proposal_version_id=vid, status="DRAFT")
        for sid in specification_ids:
            insert(db,"proposal_asset_specifications",id=identity(vid,sid),project_id=project_id,proposal_version_id=vid,specification_version_id=sid)
        for aid, alternative in zip(alternative_ids, request.alternatives):
            value=alternative.model_dump(mode="json",by_alias=True)
            insert(db,"proposal_alternatives",id=aid,project_id=project_id,proposal_version_id=vid,name=alternative.name,payload=value,content_hash=digest(value))
        self.transition(db,project_id,vid,"GENERATING")
        issues = [{"code":"CONCEPT_ONLY", "severity":"WARNING", "componentIds":[], "fieldPaths":[], "evidenceIds":[],
            "message":"Concept review only. A typed Building patch may execute after approval; engineering analysis remains unavailable." if any(a.building_patch for a in request.assets) else "Preliminary generic 3D layout; geometry validation only, no engineering approval." if any(a.ai3d_design for a in request.assets) else "Concept review only. Typed Building V1 geometry may be generated after approval; engineering analysis remains unavailable." if any(a.building_spec for a in request.assets) else "Concept review only. A supported typed specialist specification is required for geometry generation; engineering analysis remains unavailable.","remediation":"Use a validated specialist workflow before engineering or construction."}]
        if context["editorDirty"]:
            issues.append({**issues[0],"code":"UNSAVED_MODEL", "severity":"BLOCKER", "message":"The source message captured unsaved editor changes.","remediation":"Save the model and submit a new proposal request."})
        validation=ValidationResult(id=identity(vid,"validation"),level="CONCEPT_VALIDATION",validator_id="civil-concept-contract",validator_version="1",
            input_hash=digest(payload),status="FAILED" if any(i["severity"]=="BLOCKER" for i in issues) else "PASSED",issues=issues).model_dump(mode="json",by_alias=True)
        db.add(EngineeringAnalysis(project_id=project_id,model_revision_id=int(context["modelRevisionId"]) if context.get("modelRevisionId") else None,
            analysis_type="PROPOSAL_CONCEPT",algorithm_version="civil-concept-contract/1",dependency_ids_json=[vid],constraint_versions_json=[],
            status=validation["status"],result_json=validation,actor_user_id=actor_id))
        self.transition(db,project_id,vid,"READY_FOR_REVIEW" if validation["status"]=="PASSED" else "HAS_ISSUES")
        if parent:
            state=owned_row(db,"proposal_version_states",project_id,identity(parent["id"],"state"))
            if state["status"] in {"APPROVED","READY_FOR_REVIEW","HAS_ISSUES"}:
                self.transition(db,project_id,parent["id"],"STALE")
        db.commit()
        return self.read(db,project_id,vid)

    def read(self,db,project_id,version_id):
        row=owned_row(db,"design_proposal_versions",project_id,version_id)
        state=owned_row(db,"proposal_version_states",project_id,identity(version_id,"state"))
        manifest=owned_row(db,"dependency_manifests",project_id,row["dependency_manifest_id"])["payload"]
        assets=[owned_row(db,"asset_specification_versions",project_id,sid)["asset_id"] for sid in row["payload"]["contract"]["assetSpecificationVersionIds"]]
        current=dependencies(db,project_id,row["payload"]["context"],assets,include_relationships=any(e["kind"]=="RELATIONSHIP" for e in manifest["entries"]))["hash"]==manifest["hash"]
        t=table("design_proposal_versions")
        latest=db.execute(sa.select(sa.func.max(t.c.version)).where(t.c.project_id==project_id,t.c.proposal_id==row["proposal_id"])).scalar()
        current=current and row["version"]==latest
        validation=db.query(EngineeringAnalysis).filter_by(project_id=project_id,analysis_type="PROPOSAL_CONCEPT").all()
        validation=next((r.result_json for r in validation if r.result_json.get("id")==row["payload"]["validationId"]),None)
        status="STALE" if not current and state["status"] in {"READY_FOR_REVIEW","APPROVED","HAS_ISSUES"} else state["status"]
        content = dict(row["payload"])
        if "assetProposals" not in content: content["assetProposals"] = asset_proposals(db, project_id, content)
        return {"id":row["id"],"proposalId":row["proposal_id"],"version":row["version"],"status":status,"current":current,
            "contentHash":row["content_hash"],"dependencyHash":manifest["hash"],"validationHash":digest(validation),"validation":validation,
            "content":content,"alternatives":[{k:r[k] for k in ("id","name","payload")} for r in rows(db,"proposal_alternatives",project_id) if r["proposal_version_id"]==version_id]}

    def approve(self,db,project_id,actor_id,command):
        lock_project(db,project_id)
        view=self.read(db,project_id,command.proposal_version_id)
        if not view["current"]:
            if view["status"]=="STALE":self.transition(db,project_id,view["id"],"STALE")
            db.commit();error(409,"STALE_PROPOSAL","Dependencies changed; request a new proposal version.")
        if (command.proposal_hash,command.dependency_hash,command.validation_hash)!=(view["contentHash"],view["dependencyHash"],view["validationHash"]):
            error(409,"APPROVAL_MISMATCH","Review the exact current proposal and validation before approving.")
        if command.expected_model_revision_id!=view["content"]["context"].get("modelRevisionId"):
            error(409,"MODEL_MISMATCH","Approval source model differs.")
        if command.alternative_id and command.alternative_id not in {r["id"] for r in view["alternatives"]}:
            error(422,"INVALID_ALTERNATIVE","Alternative belongs to another proposal version.")
        if view["alternatives"] and not command.alternative_id:
            error(422,"ALTERNATIVE_REQUIRED","Select an alternative explicitly.")
        if set(command.acknowledged_assumption_version_ids)!=set(view["content"]["contract"]["assumptionVersionIds"]):
            error(422,"ASSUMPTION_REVIEW_REQUIRED","Explicitly acknowledge each proposed assumption.")
        if not view["validation"] or view["validation"]["status"]!="PASSED":
            error(409,"VALIDATION_BLOCKED","Resolve validation blockers in a new revision.")
        aid=identity(view["id"],"approval")
        existing=db.execute(sa.select(table("proposal_approvals")).where(table("proposal_approvals").c.id==aid)).mappings().first()
        if existing:
            if existing["alternative_id"]!=command.alternative_id:error(409,"APPROVAL_CONFLICT","This version already has a different approval.")
            db.commit();return {"id":aid,"status":view["status"]}
        self.transition(db,project_id,view["id"],"APPROVED")
        insert(db,"proposal_approvals",id=aid,project_id=project_id,proposal_version_id=view["id"],alternative_id=command.alternative_id,
            proposal_hash=command.proposal_hash,dependency_hash=command.dependency_hash,validation_hash=command.validation_hash,
            approved_by=actor_id,acknowledged_assumptions=command.acknowledged_assumption_version_ids)
        db.commit();return {"id":aid,"status":"APPROVED"}

    def reject(self,db,project_id,version_id):
        lock_project(db,project_id);self.transition(db,project_id,version_id,"REJECTED");db.commit()
        return self.read(db,project_id,version_id)

    def build(self,db,project_id,version_id):
        from app.services.assistant.building_execution import build
        return build(db,project_id,version_id)

    def assert_build_current(self,db,project_id,version_id,expected_model_revision_id=None):
        """Mandatory worker gate for both start and commit; caller holds the project lock.

        Future specialist adapters must call this again inside their revision commit
        transaction. A supplied model revision is a stricter generation-time CAS.
        This gate never writes geometry or creates a job on its own.
        """
        view=self.read(db,project_id,version_id)
        if view["status"]!="APPROVED":error(409,"APPROVAL_REQUIRED","An exact current approval is required.")
        approved=owned_row(db,"proposal_approvals",project_id,identity(version_id,"approval"))
        if (approved["proposal_hash"],approved["dependency_hash"],approved["validation_hash"])!=(view["contentHash"],view["dependencyHash"],view["validationHash"]):
            error(409,"STALE_APPROVAL","The approved payload, dependencies or validation no longer match.")
        if expected_model_revision_id is not None:
            model=db.query(ModelRevision).filter_by(project_id=project_id)
            scenario=view["content"]["context"].get("scenarioId")
            if scenario:model=model.filter_by(design_scenario_id=int(scenario))
            current=model.order_by(ModelRevision.id.desc()).first()
            if (str(current.id) if current else None)!=expected_model_revision_id:
                error(409,"MODEL_COMMIT_CONFLICT","A manual edit occurred during generation; user work must not be overwritten.")
        return view
