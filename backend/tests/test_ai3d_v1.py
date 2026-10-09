import asyncio
import copy
import json
import pytest
from fastapi import HTTPException
from app.domain.ai3d import AI3DDesign
from app.domain.assistant_runtime import ProposalRequest
from app.services.assistant.ai3d_geometry import compile_geometry
from app.services.assistant.ai3d_validation import AI3DDesignValidator, site_summary
from app.services.assistant.ai3d_executor import Generic3DExecutor
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import owned_row, rows
from app.db.models import Project, ModelRevision, DesignScenario, ModelPlacement
from app.services.design.editable_model import geometry_spec_to_document, validate_document
from test_site_workspace import site_db
from test_assistant_runtime import message, approval, FixtureProvider


def object_(id, primitive, semantic="SLAB", system="main", **parameters):
    return {"objectId":id,"systemId":system,"semanticType":semantic,"role":semantic,"parameters":{"primitiveType":primitive,**parameters}}


def fixture(kind="bridge", selection=None, source="1"):
    systems=[{"id":"main","assetType":"BRIDGE","semanticType":"STRUCTURE","role":"PEDESTRIAN_BRIDGE"}]
    path=object_("path","PATH","ALIGNMENT",points=[[5,30,3],[25,30,3],[45,30,3]])
    template=object_("template","BOX","COLUMN",center=[0,0,-1.5],size=[.4,.4,3]);template["templateOnly"]=True
    if kind in {"bridge","unusual"}:
        objects=[path,object_("deck","SWEEP","DECK",pathRef="path",widthM=4,thicknessM=.3),template,
            object_("supports","ARRAY_ALONG_PATH","COLUMN",pathRef="path",templateRef="template",spacingM=10,count=5)]
        if kind=="unusual":systems[0].update(assetType="UNREGISTERED_CIVIL_ASSET",role="ELEVATED_BICYCLE_WALKWAY")
    elif kind=="road":
        path["parameters"]["points"]=[[5,30,0],[25,30,0],[45,30,0]]
        systems[0].update(assetType="ROAD",role="ACCESS_ROAD");objects=[path,object_("surface","SWEEP","SURFACE",pathRef="path",widthM=7,thicknessM=.15)]
    elif kind=="pipe":systems[0].update(assetType="PIPELINE",role="PIPELINE");objects=[path,object_("pipe","PIPE","PIPE",pathRef="path",radiusM=.3)]
    elif kind=="drain":systems[0].update(assetType="DRAINAGE",role="DRAINAGE");objects=[path,object_("channel","CHANNEL","CHANNEL",pathRef="path",widthM=1,depthM=.6,thicknessM=.1)]
    else:
        objects=[];systems=[]
        for index in range(2 if kind=="mixed" else 1):
            system=f"warehouse-{index}";systems.append({"id":system,"assetType":"WAREHOUSE","semanticType":"STRUCTURE","role":"WAREHOUSE"})
            x=(25 if kind=="mixed" else 5)+20*index
            objects.extend([object_(f"footprint-{index}","POLYGON","ZONE",system,points=[[x,5,0],[x+10,5,0],[x+10,15,0],[x,15,0],[x,5,0]]),
                object_(f"slab-{index}","EXTRUDE","SLAB",system,polygonRef=f"footprint-{index}",heightM=.15),
                object_(f"roof-{index}","BOX","SLAB",system,center=[x+5,10,3],size=[10,10,.15])])
            for wall,(center,size) in enumerate([([x+5,5,1.5],[10,.15,3]),([x+5,15,1.5],[10,.15,3]),([x,10,1.5],[.15,10,3]),([x+10,10,1.5],[.15,10,3])]):objects.append(object_(f"wall-{index}-{wall}","BOX","WALL",system,center=center,size=size))
            t=object_(f"column-template-{index}","BOX","COLUMN",system,center=[0,0,1.5],size=[.3,.3,3]);t["templateOnly"]=True;objects.append(t)
            objects.append(object_(f"columns-{index}","ARRAY_ON_GRID","COLUMN",system,templateRef=t["objectId"],origin=[x,5,0],rows=2,columns=2,spacingXM=10,spacingYM=10))
        if kind=="mixed":
            for sub in ["road","drain"]:
                child=fixture(sub);system=sub;systems.append({**child["systems"][0],"id":system})
                for obj in child["objects"]:
                    obj=copy.deepcopy(obj);obj["objectId"]=f"{sub}-{obj['objectId']}";obj["systemId"]=system
                    if "pathRef" in obj["parameters"]:obj["parameters"]["pathRef"]=f"{sub}-path"
                    if sub=="drain":
                        if obj["parameters"]["primitiveType"]=="PATH":obj["parameters"]["points"]=[[5,40,0],[45,40,0]]
                    objects.append(obj)
            systems.extend([{"id":"parking","assetType":"PARKING","semanticType":"SITE","role":"PARKING"},{"id":"tank","assetType":"WATER_TANK","semanticType":"UTILITY","role":"WATER_TANK"}])
            objects.extend([object_("parking-pad","BOX","PAD","parking",center=[15,22,0],size=[15,8,.1]),object_("water-tank","CYLINDER","PIPE","tank",start=[40,20,0],end=[40,20,4],radiusM=2)])
    return {"designId":"design-01","sourceModelRevisionId":source,"siteSelection":selection or {"id":"site","version":1,"contentHash":"a"*64},
        "systems":systems,"objects":objects,"inputSource":"PREVIEW_ASSUMPTION","assumptions":[{"field":"visual dimensions","value":"fixture dimensions in metres","reason":"Concept-only preview; not engineering values."}]}


@pytest.mark.parametrize("kind",["warehouse","road","pipe","bridge","drain","mixed","unusual"])
def test_compositions(kind):
    design=AI3DDesign.model_validate(fixture(kind));executor=Generic3DExecutor()
    first=executor.generate(design);assert first==executor.generate(design)
    assert not executor.validate_geometry(first,design)["issues"]
    assert len({o["semantic"]["id"] for o in first["objects"]})==len(first["objects"])
    if kind=="bridge":assert len(first["objects"])==7
    if kind=="mixed":assert len({o["semantic"]["systemId"] for o in first["objects"]})==6


@pytest.mark.parametrize("change,code",[
    ({"schemaVersion":"ai3d/2"},"SCHEMA_VALIDATION_FAILED"),
    ({"objects":[]},"SCHEMA_VALIDATION_FAILED"),({"coordinateFrame":"CESIUM"},"SCHEMA_VALIDATION_FAILED"),
    ({"inputSource":"ENGINEERING_RESULT"},"SCHEMA_VALIDATION_FAILED"),({"assumptions":[]},"PREVIEW_ASSUMPTION_REQUIRED"),
    ({"terrainDependencies":[{"id":"terrain","version":1,"contentHash":"a"*64}]},"TERRAIN_PLACEMENT_UNSUPPORTED")])
def test_invalid_contract(change,code):
    assert code in {i["code"] for i in AI3DDesignValidator().validate(fixture()|change)["issues"]}


@pytest.mark.parametrize("mutation,code",[
    (lambda d:d["objects"][1]["parameters"].update(pathRef="missing"),"UNRESOLVED_REFERENCE"),
    (lambda d:d["objects"][0].update(parentId="deck"),"CIRCULAR_DEPENDENCY"),
    (lambda d:d["objects"][0]["parameters"].update(points=[[1,1,0],[1,1,0]]),"ZERO_LENGTH_PATH"),
    (lambda d:d["objects"][1]["parameters"].update(widthM=0),"SCHEMA_VALIDATION_FAILED"),
    (lambda d:d["objects"][1]["parameters"].update(widthM=float("nan")),"SCHEMA_VALIDATION_FAILED"),
    (lambda d:d["objects"][3]["parameters"].update(count=100),"ARRAY_EXCEEDS_PATH"),
    (lambda d:d["objects"][1]["parameters"].update(primitiveType="PYTHON",code="print(1)"),"SCHEMA_VALIDATION_FAILED"),
    (lambda d:d["objects"][1].update(objectId="path"),"DUPLICATE_OBJECT_ID"),
    (lambda d:d["objects"][1].update(systemId="missing"),"UNRESOLVED_SYSTEM")])
def test_invalid_geometry(mutation,code):
    design=fixture();mutation(design)
    assert code in {i["code"] for i in AI3DDesignValidator().validate(design)["issues"]}


def test_reference_primitives_and_constraints():
    design=fixture("road")
    design["objects"]+=[object_("start","POINT","ALIGNMENT",position=[5,30,0]),object_("offset","OFFSET","ALIGNMENT",pathRef="path",distanceM=2)]
    # OFFSET deliberately requires a straight two-point input.
    design["objects"][0]["parameters"]["points"]=[[5,30,0],[45,30,0]]
    design["constraints"]=[{"id":"endpoint","kind":"START_AT","targetId":"path","referenceId":"start"}]
    assert AI3DDesignValidator().validate(design)["constraintChecks"][0]["status"]=="SATISFIED"
    design["relationships"]=[{"id":"follows","kind":"FOLLOWS","fromId":"surface","toId":"path"}]
    assert not AI3DDesignValidator().validate(design)["issues"]
    design["relationships"][0]["toId"]="missing"
    assert AI3DDesignValidator().validate(design)["issues"][0]["code"]=="UNRESOLVED_RELATIONSHIP"
    design["relationships"]=[];design["constraints"][0]["kind"]="MIN_CLEARANCE"
    assert AI3DDesignValidator().validate(design)["constraintChecks"][0]["status"]=="UNSUPPORTED"


def setup(site_db):
    project=site_db.get(Project,1);project.project_type="building"
    base=site_db.get(ModelRevision,1);base.document_json=geometry_spec_to_document(project,site_db.get(DesignScenario,1),{"objects":[{"kind":"box","name":"existing","layer":"wall","center":[60,60,1],"size":[1,1,2]}]})
    base.document_json["origin"].update(lng=77,lat=12,elevation_m=None);base.document_json["structural_layout"]={"rule_preset":{}}
    site_db.commit();return message(site_db,"Create a pedestrian bridge concept.")


def proposal(site_db,kind="bridge"):
    msg,_=setup(site_db);summary=site_summary(site_db,1,msg["context"])
    design=fixture(kind,summary["selectionReference"])
    return ProposalService().create(site_db,1,1,ProposalRequest(client_request_id="generic",message_id=msg["id"],title="Generic concept",rationale="Fixture composition",
        assets=[{"assetType":"AI3D_DESIGN","name":"Generic systems","ai3dDesign":design}]))


def test_approved_generation_preserves_revision_and_lineage(site_db):
    view=proposal(site_db,"mixed");service=ProposalService();before=copy.deepcopy(site_db.get(ModelRevision,1).document_json)
    with pytest.raises(HTTPException):service.build(site_db,1,view["id"])
    service.approve(site_db,1,1,approval(view));result=service.build(site_db,1,view["id"])
    assert service.build(site_db,1,view["id"])==result
    revision=site_db.get(ModelRevision,int(result["modelRevisionId"]));document=revision.document_json
    assert document["components"][0]==before["components"][0] and site_db.get(ModelRevision,1).document_json==before
    assert not validate_document(document,project_id=1,scenario_id=1,project_type="building")
    assert len(rows(site_db,"model_object_lineage",1))==len(document["components"])-1
    assert document["origin"]["elevation_m"] is None
    assert all(r["payload"]["generationModelRevisionId"]==revision.id for r in rows(site_db,"model_object_lineage",1))


@pytest.mark.parametrize("failure",["stale","storage","generator"])
def test_no_revision_on_failure(site_db,monkeypatch,failure):
    view=proposal(site_db);service=ProposalService();service.approve(site_db,1,1,approval(view))
    if failure=="stale":site_db.get(Project,1).boundary_geojson=None;site_db.commit()
    if failure=="storage":
        import app.api.routes.model_revisions as revisions
        monkeypatch.setattr(revisions,"save_file",lambda *args:(_ for _ in ()).throw(RuntimeError("fixture storage failure")))
    if failure=="generator":monkeypatch.setattr(Generic3DExecutor,"generate",lambda *args:(_ for _ in ()).throw(ValueError("fixture generation failure")))
    with pytest.raises(Exception):service.build(site_db,1,view["id"])
    assert len(rows(site_db,"model_revisions",1))==1


def test_building_translation():
    from app.domain.building_specialist import BuildingSpec
    from app.services.assistant.building_specialist import BuildingAdapter
    from app.services.assistant.ai3d_building_translation import translate_building
    from test_building_specialist_v1 import specification
    raw=specification()
    raw["spaces"]=[{"id":f"room-{floor}-{side}","name":"Office zone","floor":floor,"x":5+6*side,"y":5,"width":6,"depth":10} for floor in range(2) for side in range(2)]
    raw["walls"]+=[{"id":f"partition-{floor}","floor":floor,"start":[11,5],"end":[11,15],"thickness":.15} for floor in range(2)]
    spec=BuildingSpec.model_validate(raw);original=BuildingAdapter().generate(spec)
    assert len(original["objects"])==34
    translated=translate_building(spec,fixture()["siteSelection"])
    generic=Generic3DExecutor().generate(translated)
    assert {o["semantic"]["id"] for o in original["objects"]}=={o["semantic"]["id"] for o in generic["objects"]}
    by_id={o["semantic"]["id"]:o for o in original["objects"]}
    assert all(list(o["size"])==list(by_id[o["semantic"]["id"]]["size"]) and list(o["center"])==list(by_id[o["semantic"]["id"]]["center"]) for o in generic["objects"])


def test_assistant_fixture_no_direct_mutation(site_db):
    from app.services.assistant.runtime import process,queue_run
    from app.services.assistant.policy import evaluate
    msg,run=setup(site_db);summary=site_summary(site_db,1,msg["context"])
    args={"title":"Bridge concept","rationale":"Composed primitives","assets":[{"assetType":"AI3D_DESIGN","name":"Bridge","ai3dDesign":fixture("bridge",summary["selectionReference"])}]}
    args["assets"][0]["ai3dDesign"]["systems"][0]["assetType"]=evaluate(msg)["intent"]["assets"][0]["assetType"]
    queue_run(site_db,1,1,run)
    asyncio.run(process(site_db,1,run,FixtureProvider([evaluate(msg)["intent"],{"toolCalls":[{"name":"create_proposal","arguments":json.dumps(args)}]},{"text":"Review the preliminary bridge layout and assumptions."}])))
    assert owned_row(site_db,"assistant_runs",1,run)["status"]=="COMPLETE", owned_row(site_db,"assistant_runs",1,run)["error_code"]
    assert len(rows(site_db,"model_revisions",1))==1


def test_surface_grid_and_array_positions():
    design=fixture("warehouse")
    design["objects"][1]["parameters"]["primitiveType"]="SURFACE"
    geometry,_=compile_geometry(design)
    columns=[o for o in geometry["objects"] if o["semantic"]["sourceObjectId"]=="columns-0"]
    assert [o["center"] for o in columns]==[[5,5,1.5],[15,5,1.5],[5,15,1.5],[15,15,1.5]]
    geometry,_=compile_geometry(fixture())
    supports=[o for o in geometry["objects"] if o["semantic"]["sourceObjectId"]=="supports"]
    assert [o["center"] for o in supports]==[[5,30,1.5],[15,30,1.5],[25,30,1.5],[35,30,1.5],[45,30,1.5]]


@pytest.mark.parametrize("kind,parameters,code",[
    ("CYLINDER",{"start":[0,0,0],"end":[0,0,0],"radiusM":1},"ZERO_LENGTH_CYLINDER"),
    ("CYLINDER",{"start":[0,0,0],"end":[0,0,3],"radiusM":-1},"SCHEMA_VALIDATION_FAILED"),
    ("POLYGON",{"points":[[0,0,0],[1,1,0],[1,0,0],[0,1,0],[0,0,0]]},"INVALID_POLYGON"),
    ("BOX",{"center":[float("inf"),0,0],"size":[1,1,1]},"SCHEMA_VALIDATION_FAILED"),
    ("ARRAY_ALONG_PATH",{"pathRef":"path","templateRef":"template","spacingM":10,"count":0},"SCHEMA_VALIDATION_FAILED"),
    ("SWEEP",{"pathRef":"template","widthM":1,"thicknessM":.1},"PATH_REFERENCE_REQUIRED"),
    ("CHANNEL",{"pathRef":"path","widthM":1,"depthM":.5,"thicknessM":.6},"INVALID_CHANNEL_SECTION")])
def test_more_invalid_primitives(kind,parameters,code):
    design=fixture();design["objects"].append(object_("invalid",kind,**parameters))
    assert code in {i["code"] for i in AI3DDesignValidator().validate(design)["issues"]}


def test_planar_and_rectangular_limits():
    design=fixture();design["objects"][0]["parameters"]["points"][1][2]=4
    assert AI3DDesignValidator().validate(design)["issues"][0]["code"]=="PLANAR_SWEEP_ONLY"
    design=fixture("warehouse");design["objects"][0]["parameters"]["points"][1]=[10,8,0]
    assert AI3DDesignValidator().validate(design)["issues"][0]["code"]=="RECTANGULAR_EXTRUSION_ONLY"


def test_site_constraints_and_unknown_terrain(site_db):
    msg,_=setup(site_db);summary=site_summary(site_db,1,msg["context"])
    design=fixture("road",summary["selectionReference"])
    design["constraints"]=[{"id":"within","kind":"WITHIN_AREA","targetId":"main"}]
    result=AI3DDesignValidator().validate(design,summary)
    assert not result["issues"] and result["constraintChecks"][0]["status"]=="SATISFIED"
    assert summary["origin"]["elevation_m"] is None and summary["facts"]["relief"]["minElevation"]["value"] is None
    design["objects"][0]["parameters"]["points"][0][0]=-200
    assert "OUTSIDE_SELECTED_AREA" in {i["code"] for i in AI3DDesignValidator().validate(design,summary)["issues"]}


def test_follow_route_endpoint_and_avoid_constraints():
    design=fixture("road");design["objects"][0]["parameters"]["points"]=[[5,30,0],[45,30,0]]
    design["objects"]+=[object_("end","POINT",position=[45,30,0]),object_("avoid","POLYGON",points=[[5,50,0],[10,50,0],[10,55,0],[5,55,0],[5,50,0]])]
    design["constraints"]=[{"id":"follow","kind":"FOLLOW_ROUTE","targetId":"path"},{"id":"end-at","kind":"END_AT","targetId":"path","referenceId":"end"},{"id":"avoid-check","kind":"AVOID_AREA","targetId":"surface","referenceId":"avoid"}]
    summary={"selectionReference":design["siteSelection"],"sourceModelRevisionId":"1","selectionKind":"ROUTE","localGeometry":{"type":"LineString","coordinates":[[5,30],[45,30]]}}
    assert all(c["status"]=="SATISFIED" for c in AI3DDesignValidator().validate(design,summary)["constraintChecks"])
    summary["localGeometry"]["coordinates"][0]=[6,30]
    assert "ROUTE_MISMATCH" in {i["code"] for i in AI3DDesignValidator().validate(design,summary)["issues"]}


def test_cross_project_reference_rejected(site_db):
    msg,_=setup(site_db)
    with pytest.raises(HTTPException):site_summary(site_db,2,msg["context"])


def test_building_plus_generic_systems(site_db):
    from test_building_specialist_v1 import create
    from app.domain.site_workspace import MessageInput
    from app.services.assistant.conversations import ConversationService
    from app.services.site_profiles.service import SiteProfileService
    service=ProposalService();building=create(site_db);service.approve(site_db,1,1,approval(building));result=service.build(site_db,1,building["id"])
    base=site_db.get(ModelRevision,int(result["modelRevisionId"]));before=copy.deepcopy(base.document_json)
    context=building["content"]["context"];profiles=SiteProfileService();prepared,_=profiles.prepare(site_db,1,1,context["siteSelectionVersionId"])
    profiles.build(site_db,1,prepared["id"],prepared["jobId"]);profile=profiles.read(site_db,1,prepared["id"])["version"]
    old=owned_row(site_db,"conversation_messages",1,building["content"]["request"]["messageId"])
    posted=ConversationService().submit(site_db,1,1,old["conversation_id"],MessageInput(client_request_id="mixed-next",parts=[{"kind":"TEXT","text":"Create a preliminary mixed infrastructure concept."}],
        context={"modelRevisionId":str(base.id),"scenarioId":"1","siteSelectionVersionId":context["siteSelectionVersionId"],"siteProfileVersionId":profile["id"]}))
    message_=owned_row(site_db,"conversation_messages",1,posted["messageId"]);summary=site_summary(site_db,1,message_["context"])
    view=service.create(site_db,1,1,ProposalRequest(client_request_id="mixed-next",message_id=posted["messageId"],title="Mixed systems",rationale="Preserve office",
        assets=[{"assetType":"AI3D_DESIGN","name":"Mixed systems","ai3dDesign":fixture("mixed",summary["selectionReference"],str(base.id))}]))
    service.approve(site_db,1,1,approval(view).model_copy(update={"expected_model_revision_id":str(base.id)}));result=service.build(site_db,1,view["id"])
    document=site_db.get(ModelRevision,int(result["modelRevisionId"])).document_json
    assert document["components"][:len(before["components"])]==before["components"]
    assert site_db.get(ModelRevision,base.id).document_json==before
    assert {c.get("metadata",{}).get("generatorId") for c in document["components"]}>={"building-concept","generic-3d"}
    old_lineage=[r for r in rows(site_db,"model_object_lineage",1) if r["model_revision_id"]==base.id]
    new_lineage=[r for r in rows(site_db,"model_object_lineage",1) if r["model_revision_id"]==int(result["modelRevisionId"])]
    assert len(new_lineage)==len(document["components"])-1 and len(old_lineage)>0


def test_pipe_export_preserves_saved_transform():
    from app.services.design.editable_model import document_to_geometry_spec
    document={"components":[{"id":"pipe","geometry":{"kind":"cylinder","start":[0,0,0],"end":[10,0,0],"radius_m":.2},
        "transform":{"position":[3,4,5],"rotation_deg":[0,0,90],"scale":[2,2,2]}}]}
    pipe=document_to_geometry_spec(document)["objects"][0]
    assert pipe["start"]==[3,4,5] and pipe["end"]==pytest.approx([3,24,5]) and pipe["radius_m"]==.4


def test_large_generated_extent_rejected_before_persistence():
    design=fixture("road");design["objects"][0]["parameters"]["points"]=[[0,0,0],[1000,0,0]]
    assert AI3DDesignValidator().validate(design)["issues"][0]["code"]=="OUTPUT_DIMENSION_LIMIT"
