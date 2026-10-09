import asyncio
import copy
import pytest
from fastapi import HTTPException
from app.domain.assistant_runtime import ProposalRequest
from app.domain.building_specialist import BuildingSpec
from app.services.assistant.building_specialist import BuildingAdapter,BuildingSpecValidator
from app.services.assistant.proposals import ProposalService
from app.services.assistant.runtime import process,queue_run
from app.services.assistant.storage import rows,owned_row
from app.services.assistant.foundation import capability
from app.db.models import ModelRevision,Project,ModelPlacement,DesignScenario
from app.services.design.editable_model import geometry_spec_to_document,validate_document,document_to_geometry_spec
from test_assistant_runtime import message,approval,FixtureProvider
from test_site_workspace import site_db


def specification():
    walls=[]
    corners=[(5,5),(17,5),(17,15),(5,15)]
    for floor in range(2):
        for i in range(4):walls.append({"id":f"w{floor}-{i}","floor":floor,"start":corners[i],"end":corners[(i+1)%4],"thickness":.15})
    return {"buildingId":"office-01","name":"Office","footprint":[*corners,corners[0]],"floors":2,"floorHeight":3,"slabThickness":.15,
        "spaces":[{"id":f"room-{i}","name":"Office zone","floor":i,"x":5,"y":5,"width":12,"depth":10} for i in range(2)],
        "walls":walls,"openings":[{"id":"entry","wall_id":"w0-0","kind":"door","offset":2,"width":1,"height":2,"sill":0},
            {"id":"window","wall_id":"w1-0","kind":"window","offset":4,"width":2,"height":1,"sill":1}],
        "columns":[{"id":f"c{i}","x":x,"y":y,"size":.3} for i,(x,y) in enumerate(corners)],
        "beams":[{"id":"b0","start":corners[0],"end":corners[1],"width":.25,"depth":.35}],"inputSource":"USER_PROVIDED"}


def setup(site_db):
    project=site_db.get(Project,1);project.project_type="building"
    base=site_db.get(ModelRevision,1)
    base.document_json=geometry_spec_to_document(project,site_db.get(DesignScenario,1),{"objects":[{"name":"existing","layer":"wall","kind":"box","center":[30,30,1],"size":[1,1,2]}]})
    base.document_json["origin"].update(lng=77,lat=12,elevation_m=None)
    site_db.commit()
    return message(site_db,"Create a simple two-storey rectangular office building.")


def create(site_db):
    msg,_=setup(site_db)
    req=ProposalRequest(client_request_id="building",message_id=msg["id"],title="Office concept",rationale="Requested two-storey office",
        assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":specification()}])
    return ProposalService().create(site_db,1,1,req)


def test_assistant_to_approved_building_revision(site_db):
    import json
    from app.services.assistant.policy import evaluate
    msg,rid=setup(site_db);queue_run(site_db,1,1,rid)
    args={"title":"Office concept","rationale":"Two floors as requested","assets":[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":specification()}]}
    args["assets"][0]["buildingSpec"].update(inputSource="PREVIEW_ASSUMPTION",assumptions=[{"field":"visual layout dimensions","value":"12 x 10 m; floor height 3 m; concept members","reason":"Preview only, requires user review."}])
    # Catalogue resolves the user request to OFFICE_BUILDING; no live model participates.
    asyncio.run(process(site_db,1,rid,FixtureProvider([evaluate(msg)["intent"],{"toolCalls":[{"name":"create_proposal","arguments":json.dumps(args)}]},{"text":"Review this conceptual office."}])))
    assert owned_row(site_db,"assistant_runs",1,rid)["status"]=="COMPLETE"
    vid=next(p["proposalVersionId"] for p in rows(site_db,"conversation_messages",1)[-1]["parts"] if p["kind"]=="PROPOSAL")
    svc=ProposalService();view=svc.read(site_db,1,vid);svc.approve(site_db,1,1,approval(view))
    assert view["content"]["contract"]["assumptionVersionIds"]
    result=svc.build(site_db,1,vid);revision=site_db.get(ModelRevision,int(result["modelRevisionId"]))
    assert svc.build(site_db,1,vid)==result
    assert len(rows(site_db,"model_revisions",1))==2
    doc=revision.document_json
    assert not validate_document(doc,project_id=1,scenario_id=1,project_type="building")
    generated=[c for c in doc["components"] if c.get("metadata",{}).get("buildingId")]
    from app.core.asset_families import COMPONENT_KINDS
    kinds={c["metadata"]["componentKind"] for c in generated}
    assert kinds>={"WALL","SLAB","ROOM","OPENING","COLUMN","BEAM"} and kinds<=COMPONENT_KINDS.keys()
    assert {c["metadata"]["componentRole"] for c in generated}>={"DOOR","WINDOW","ROOF"}
    assert all(c["metadata"]["proposalVersionId"]==vid and c["metadata"]["specificationHash"] for c in generated)
    assert all(c["quantity"]["included"] is False for c in generated)
    assert doc["origin"]["elevation_m"] is None and not doc["metadata"]["elevation_known"]
    placed=site_db.query(ModelPlacement).filter_by(model_revision_id=revision.id).one()
    assert placed.anchor_elevation is None and placed.local_transform_json=={"preserve":True}
    assert placed.placement_state=="REVIEW_REQUIRED"
    assert len(rows(site_db,"model_object_lineage",1))==len(generated)
    assert document_to_geometry_spec(doc)["objects"]


def test_same_spec_same_geometry():
    adapter=BuildingAdapter();spec=BuildingSpec.model_validate(specification())
    assert adapter.generate(spec)==adapter.generate(spec)
    assert adapter.generate(spec)["validation"]["engineeringStatus"]=="UNVALIDATED"
    long=spec.model_copy(update={"building_id":"x"*128})
    assert all(len(o["semantic"]["id"])<=128 for o in adapter.generate(long)["objects"])


@pytest.mark.parametrize("change,code",[
    ({"footprint":[[5,5],[17,15],[17,5],[5,15],[5,5]]},"INVALID_FOOTPRINT"),
    ({"floorHeight":0},"SCHEMA_VALIDATION_FAILED"),({"floorHeight":-1},"SCHEMA_VALIDATION_FAILED"),
    ({"floors":11},"SCHEMA_VALIDATION_FAILED"),({"schemaVersion":"building/2"},"SCHEMA_VALIDATION_FAILED"),
    ({"requestedFeatures":["MEP"]},"SCHEMA_VALIDATION_FAILED"),
    ({"requestedFeatures":["FOUNDATION_DESIGN"]},"SCHEMA_VALIDATION_FAILED"),
    ({"requestedFeatures":["STRUCTURAL_ANALYSIS"]},"SCHEMA_VALIDATION_FAILED"),
    ({"floorHeight":float("nan")},"SCHEMA_VALIDATION_FAILED"),
])
def test_invalid_spec(change,code):
    result=BuildingSpecValidator().validate(specification()|change)
    assert code in {i["code"] for i in result["issues"]}


def test_duplicate_ids_and_invalid_opening():
    raw=specification();raw["columns"][0]["id"]="entry"
    raw["openings"][0]["offset"]=50
    codes={i["code"] for i in BuildingSpecValidator().validate(raw)["issues"]}
    assert {"DUPLICATE_COMPONENT_ID","OPENING_OUTSIDE_WALL"}<=codes


@pytest.mark.parametrize("state",["unapproved","rejected","stale"])
def test_execution_approval_gate(site_db,state):
    view=create(site_db);svc=ProposalService()
    if state=="rejected":svc.reject(site_db,1,view["id"])
    if state=="stale":
        svc.approve(site_db,1,1,approval(view));site_db.get(Project,1).boundary_geojson=None;site_db.commit()
    with pytest.raises(HTTPException):svc.build(site_db,1,view["id"])
    assert len(rows(site_db,"model_revisions",1))==1


def test_invalid_source_revision_rejected(site_db):
    from app.domain.site_workspace import MessageInput
    from app.services.assistant.conversations import ConversationService
    msg,_=setup(site_db)
    with pytest.raises(HTTPException):ConversationService().submit(site_db,1,1,msg["conversation_id"],MessageInput(
        client_request_id="invalid-source",parts=msg["parts"],context={"modelRevisionId":"999999"}))


def test_accurate_capability():
    cap=capability("OFFICE_BUILDING")
    assert cap.generator_id=="building-concept" and cap.engineering_analysis_support=="UNSUPPORTED"
    assert capability("FOUNDATION").generation_support=="UNSUPPORTED"
    assert capability("BRIDGE").generation_support=="UNSUPPORTED"


def test_regeneration_creates_new_revision_and_retains_previous(site_db):
    from app.domain.site_workspace import MessageInput
    from app.services.assistant.conversations import ConversationService
    view=create(site_db);svc=ProposalService();svc.approve(site_db,1,1,approval(view))
    first=svc.build(site_db,1,view["id"]);base=site_db.get(ModelRevision,int(first["modelRevisionId"]))
    before=copy.deepcopy(base.document_json)
    source=owned_row(site_db,"conversation_messages",1,view["content"]["request"]["messageId"])
    ctx=view["content"]["context"]
    from app.services.site_profiles.service import SiteProfileService
    profiles=SiteProfileService();prepared,_=profiles.prepare(site_db,1,1,ctx["siteSelectionVersionId"])
    profiles.build(site_db,1,prepared["id"],prepared["jobId"])
    refreshed=profiles.read(site_db,1,prepared["id"])["version"]
    posted=ConversationService().submit(site_db,1,1,source["conversation_id"],MessageInput(client_request_id="regenerate",parts=[{"kind":"TEXT","text":"Create a revised office building concept."}],
        context={"modelRevisionId":str(base.id),"siteSelectionVersionId":ctx["siteSelectionVersionId"],"siteProfileVersionId":refreshed["id"],"proposalVersionId":view["id"]}))
    raw=specification();raw["floorHeight"]=3.2
    next_view=svc.create(site_db,1,1,ProposalRequest(client_request_id="regenerate",message_id=posted["messageId"],title="Office revision",rationale="Concept height edit",parent_version_id=view["id"],
        assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":raw}]))
    command=approval(next_view).model_copy(update={"expected_model_revision_id":str(base.id)})
    svc.approve(site_db,1,1,command)
    second=svc.build(site_db,1,next_view["id"])
    assert first["modelRevisionId"]!=second["modelRevisionId"]
    assert site_db.get(ModelRevision,base.id).document_json==before
    assert len(rows(site_db,"model_revisions",1))==3


def test_failed_adapter_creates_no_revision(site_db,monkeypatch):
    view=create(site_db);svc=ProposalService();svc.approve(site_db,1,1,approval(view))
    monkeypatch.setattr(BuildingAdapter,"generate",lambda *_: (_ for _ in ()).throw(ValueError("fixture failure")))
    with pytest.raises(HTTPException) as exc:svc.build(site_db,1,view["id"])
    assert exc.value.detail["code"]=="BUILDING_GENERATION_FAILED"
    assert len(rows(site_db,"model_revisions",1))==1


def test_bad_geometry_and_generated_id_collision():
    adapter=BuildingAdapter();spec=BuildingSpec.model_validate(specification());geometry=adapter.generate(spec)
    geometry["objects"][0]["size"]=[0,1,1]
    assert adapter.validate_geometry(geometry,spec)["geometryStatus"]=="GEOMETRY_INVALID"
    raw=specification();raw["spaces"][0]["id"]="slab-0"
    assert "DUPLICATE_GENERATED_ID" in {i["code"] for i in BuildingSpecValidator().validate(raw)["issues"]}


def test_foundation_without_geotechnical_data_cannot_generate(site_db):
    msg,_=setup(site_db);svc=ProposalService()
    view=svc.create(site_db,1,1,ProposalRequest(client_request_id="foundation",message_id=msg["id"],title="Foundation discussion",rationale="Soil is unknown",
        assets=[{"assetType":"FOUNDATION","name":"Foundation"}]))
    svc.approve(site_db,1,1,approval(view))
    with pytest.raises(HTTPException) as exc:svc.build(site_db,1,view["id"])
    assert exc.value.detail["code"]=="GENERATION_UNAVAILABLE"
    assert len(rows(site_db,"model_revisions",1))==1


def test_preview_assumptions_required_and_opening_reference():
    raw=specification();raw["inputSource"]="PREVIEW_ASSUMPTION";raw["openings"][0]["wall_id"]="missing"
    codes={i["code"] for i in BuildingSpecValidator().validate(raw)["issues"]}
    assert {"PREVIEW_ASSUMPTION_REQUIRED","OPENING_OUTSIDE_WALL"}<=codes


def test_invalid_spec_never_creates_geometry(site_db):
    msg,_=setup(site_db);raw=specification();raw["openings"][0]["offset"]=50
    with pytest.raises(HTTPException) as exc:ProposalService().create(site_db,1,1,ProposalRequest(client_request_id="invalid",message_id=msg["id"],title="Invalid",rationale="Bad opening",
        assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":raw}]))
    assert exc.value.detail["code"]=="INVALID_BUILDING_SPEC"
    assert len(rows(site_db,"model_revisions",1))==1


def test_footprint_must_fit_selected_area_not_just_project_boundary(site_db):
    from app.domain.site_workspace import SelectionInput,MessageInput
    from app.services.site_profiles.selection import save_selection
    from app.services.site_profiles.service import SiteProfileService
    from app.services.site_profiles.evidence import WGS84
    from app.services.assistant.conversations import ConversationService
    msg,_=setup(site_db)
    tiny={"type":"Polygon","coordinates":[[[77,12],[77.00002,12],[77.00002,12.00002],[77,12.00002],[77,12]]]}
    selected=save_selection(site_db,1,1,SelectionInput(selection={"kind":"AREA","geometry":tiny},original_crs=WGS84))
    profiles=SiteProfileService();prepared,_=profiles.prepare(site_db,1,1,selected["id"])
    profiles.build(site_db,1,prepared["id"],prepared["jobId"])
    version=profiles.read(site_db,1,prepared["id"])["version"]
    posted=ConversationService().submit(site_db,1,1,msg["conversation_id"],MessageInput(client_request_id="small-site",parts=msg["parts"],
        context={"modelRevisionId":"1","siteSelectionVersionId":selected["id"],"siteProfileVersionId":version["id"]}))
    svc=ProposalService();view=svc.create(site_db,1,1,ProposalRequest(client_request_id="small-site",message_id=posted["messageId"],title="Office",rationale="Concept",
        assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":specification()}]))
    svc.approve(site_db,1,1,approval(view))
    with pytest.raises(HTTPException) as exc:svc.build(site_db,1,view["id"])
    assert exc.value.detail["code"]=="FOOTPRINT_OUTSIDE_SITE"
    assert len(rows(site_db,"model_revisions",1))==1


def test_first_building_revision_uses_selected_area_anchor_without_fake_elevation(site_db):
    from app.domain.site_workspace import SelectionInput,ConversationInput,MessageInput
    from app.services.site_profiles.selection import save_selection
    from app.services.site_profiles.service import SiteProfileService
    from app.services.site_profiles.evidence import WGS84
    from app.services.assistant.conversations import ConversationService
    from test_site_workspace import AREA
    project=site_db.get(Project,2);project.project_type="building";project.boundary_geojson=AREA;site_db.commit()
    selected=save_selection(site_db,2,2,SelectionInput(selection={"kind":"AREA","geometry":AREA},original_crs=WGS84))
    profiles=SiteProfileService();prepared,_=profiles.prepare(site_db,2,2,selected["id"])
    profiles.build(site_db,2,prepared["id"],prepared["jobId"])
    version=profiles.read(site_db,2,prepared["id"])["version"]
    convos=ConversationService();convo=convos.create(site_db,2,2,ConversationInput(client_request_id="first"))
    posted=convos.submit(site_db,2,2,convo["id"],MessageInput(client_request_id="first",parts=[{"kind":"TEXT","text":"Create an office building concept."}],
        context={"siteSelectionVersionId":selected["id"],"siteProfileVersionId":version["id"]}))
    svc=ProposalService();view=svc.create(site_db,2,2,ProposalRequest(client_request_id="first",message_id=posted["messageId"],title="Office",rationale="First concept",
        assets=[{"assetType":"OFFICE_BUILDING","name":"Office","buildingSpec":specification()}]))
    svc.approve(site_db,2,2,approval(view).model_copy(update={"expected_model_revision_id":None}))
    result=svc.build(site_db,2,view["id"])
    revision=site_db.get(ModelRevision,int(result["modelRevisionId"]))
    assert revision.document_json["origin"]["elevation_m"] is None
    assert revision.document_json["metadata"]["sourceModelRevisionId"] is None
    placed=site_db.query(ModelPlacement).filter_by(model_revision_id=revision.id).one()
    assert placed.anchor_longitude==pytest.approx(77.001) and placed.anchor_latitude==pytest.approx(12.0005)
    assert placed.elevation_provenance_json["anchorSource"]=="SELECTED_AREA_CENTROID"
