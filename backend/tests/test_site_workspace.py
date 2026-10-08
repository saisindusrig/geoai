"""Focused step 4/5 services and authorization tests on isolated storage."""
import copy
import pytest
import sqlalchemy as sa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.db.models import User, Project, DesignScenario, ModelRevision, ModelPlacement, TerrainDataset, TerrainDatasetVersion, ActiveTerrainConfiguration
from app.domain.site_workspace import SelectionInput, ConversationInput, MessageInput, MemoryInput, MemoryRevisionInput
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService
from app.services.site_profiles.retrieval import SiteRetrievalService
from app.services.site_profiles.evidence import WGS84
from app.services.assistant.conversations import ConversationService
from app.services.assistant.memory import MemoryService
from app.services.assistant.storage import table, rows, owned_row

P1={"type":"Point","coordinates":[77,12]}
P2={"type":"Point","coordinates":[77.001,12.001]}
LINE={"type":"LineString","coordinates":[P1["coordinates"],P2["coordinates"]]}
AREA={"type":"Polygon","coordinates":[[[77,12],[77.002,12],[77.002,12.001],[77,12.001],[77,12]]]}
KINDS=[{"kind":"AREA","geometry":AREA},{"kind":"ROUTE","geometry":LINE},
       {"kind":"CROSSING","geometry":LINE,"endpointA":P1,"endpointB":P2},
       {"kind":"POINT","geometry":P1},{"kind":"ENDPOINTS","endpointA":P1,"endpointB":P2}]


@pytest.fixture
def site_db(db_session):
    db=db_session
    db.add_all([User(id=1,name="One",email="one@site.test"),User(id=2,name="Two",email="two@site.test")]);db.flush()
    db.add_all([Project(id=1,user_id=1,name="Site",project_type="bridge",boundary_geojson=AREA),Project(id=2,user_id=2,name="Other",project_type="road")]);db.flush()
    db.add(DesignScenario(id=1,project_id=1,name="Existing"));db.flush()
    db.add(ModelRevision(id=1,project_id=1,design_scenario_id=1,revision_number=1,document_json={"components":[{"id":"pier-a","name":"Pier A","geometry":{"kind":"box"}}]}));db.flush()
    db.add(ModelPlacement(id=1,project_id=1,model_revision_id=1,anchor_longitude=77,anchor_latitude=12,anchor_elevation=None,local_transform_json={"preserve":True}));db.commit()
    return db


def selection(db,kind=0,project=1):
    return save_selection(db,project,project,SelectionInput(selection=KINDS[kind],original_crs=WGS84))


def profile(db,kind=0,service=None):
    svc=service or SiteProfileService();s=selection(db,kind)
    prepared,_=svc.prepare(db,1,1,s["id"])
    result=svc.build(db,1,prepared["id"],prepared["jobId"])
    return svc,prepared,result,svc.read(db,1,prepared["id"])


@pytest.mark.parametrize("kind,dimension",[(0,"area"),(1,"routeLength"),(2,"crossingSpan"),(3,None),(4,"endpointDistance")])
def test_selection_profiles(site_db,kind,dimension):
    _,_,_,response=profile(site_db,kind)
    data=response["version"]
    assert response["current"]
    if dimension:
        assert data["dimensions"][dimension]["fact"]["value"]["value"]>0
    assert data["terrain"]["sampleSummary"]["valid"]==0
    assert data["relief"]["minElevation"]["value"] is None
    if kind==4:
        assert data["dimensions"]["routeLength"]["applicability"]=="NOT_APPLICABLE"
        samples=owned_row(site_db,"site_sample_sets",1,data["terrain"]["sampleSetId"])["payload"]["samples"]
        assert len(samples)==2 and all(s["chainageM"] is None for s in samples)


def test_profile_dedup_dimensions_and_no_placement_movement(site_db):
    before=copy.deepcopy(site_db.get(ModelPlacement,1).local_transform_json)
    svc,p,first,response=profile(site_db)
    result=svc.build(site_db,1,p["id"],p["jobId"])
    assert result["deduplicated"] and result["versionId"]==first["versionId"]
    assert len(rows(site_db,"site_profile_versions",1))==1
    assert 23000<response["version"]["dimensions"]["area"]["fact"]["value"]["value"]<25000
    assert site_db.get(ModelPlacement,1).local_transform_json==before
    assert site_db.get(ModelPlacement,1).anchor_elevation is None


def test_unknown_crs_rejected_before_canonical_storage(site_db):
    with pytest.raises(HTTPException) as e:
        save_selection(site_db,1,1,SelectionInput(selection=KINDS[0],original_crs={"status":"UNKNOWN"}))
    assert e.value.detail["code"]=="REFERENCE_UNRESOLVED"
    assert not rows(site_db,"site_selection_versions",1)


def terrain(db):
    db.add(TerrainDataset(id=1,project_id=1,name="Survey"));db.flush()
    v=TerrainDatasetVersion(id=1,project_id=1,terrain_dataset_id=1,processing_state="READY",horizontal_crs_type="WGS84_GEOGRAPHIC",
        horizontal_crs_code="EPSG:4326",source_unit="METRE",vertical_resolution_state="RESOLVED",
        vertical_reference_json={"type":"ELLIPSOIDAL","unit":"METRE"},coverage_geojson={"type":"Polygon","coordinates":[[[77,12],[77.001,12],[77.001,12.001],[77,12.001],[77,12]]]})
    db.add(v);db.flush();db.add(ActiveTerrainConfiguration(project_id=1,terrain_dataset_id=1,terrain_version_id=1));db.commit()


def test_partial_coverage(site_db):
    terrain(site_db)
    data=profile(site_db)[3]["version"]
    assert data["terrain"]["coverage"]["status"]=="PARTIAL"
    assert data["terrain"]["coverage"]["coveredFraction"]==pytest.approx(.5,abs=.002)


def test_sampling_failure_is_unknown(site_db,monkeypatch):
    terrain(site_db)
    def fail(*a):raise RuntimeError("provider credential details must not leak")
    monkeypatch.setattr("app.services.site_profiles.retrieval.resolve_ground",fail)
    data=profile(site_db)[3]["version"]
    assert data["relief"]["minElevation"]["value"] is None
    evidence=[r["payload"] for r in rows(site_db,"site_evidence",1)]
    assert any(e["evidence"]["source"].get("reason")=="RETRIEVAL_FAILED" for e in evidence)
    assert "credential" not in str(evidence)


def test_context_retrieval_failure_preserves_measured_dimensions(site_db):
    class FailedContext(SiteRetrievalService):
        def context(self,*args):
            raise RuntimeError("external context unavailable")
    data=profile(site_db,service=SiteProfileService(retrieval=FailedContext()))[3]["version"]
    assert data["nearby"]["roads"]["retrieval"]=="FAILED"
    assert data["dimensions"]["area"]["fact"]["value"]["value"]>0


def test_known_zero_profile_and_nodata_intervals(site_db,monkeypatch):
    terrain(site_db)
    calls=[]
    def sample(db,pid,lng,lat):
        calls.append(lng)
        return {"status":"VALID" if len(calls)!=2 else "FAILED","elevation":0,"source":"SURVEY_TERRAIN","terrain_version_id":1,
            "vertical_reference":{"type":"ELLIPSOIDAL","unit":"METRE"}}
    monkeypatch.setattr("app.services.site_profiles.retrieval.resolve_ground",sample)
    data=profile(site_db,1)[3]["version"]
    assert data["relief"]["minElevation"]["value"]["value"]==0
    samples=owned_row(site_db,"site_sample_sets",1,data["terrain"]["sampleSetId"])["payload"]
    assert samples["samples"][1]["elevation"]["value"] is None
    assert samples["nodataPolicy"]=="NO_INTERPOLATION"


def test_terrain_change_race_leaves_snapshot_stale(site_db):
    terrain(site_db)
    class Race(SiteRetrievalService):
        def context(self,snapshot,extent,evidence):
            active=site_db.get(ActiveTerrainConfiguration,1);active.revision+=1;site_db.commit()
            return super().context(snapshot,extent,evidence)
    svc,p,_,data=profile(site_db,service=SiteProfileService(retrieval=Race()))
    assert not data["current"] and data["errorCode"]=="STALE_DEPENDENCIES"
    assert data["version"]["terrain"]["activeConfigurationRevision"]==1
    assert site_db.get(ModelPlacement,1).local_transform_json=={"preserve":True}


def test_evidence_lineage_missing_and_readiness(site_db):
    data=profile(site_db)[3]["version"]
    evidence={r["id"]:r["payload"]["evidence"] for r in rows(site_db,"site_evidence",1)}
    for e in evidence.values():
        if e["sourceType"]=="DERIVED":
            assert set(e["source"]["inputEvidenceIds"])<=set(evidence)
            assert e["source"]["algorithmVersion"]
    missing=[r["payload"] for r in rows(site_db,"site_missing_information",1)]
    soil=next(r for r in missing if r["type"]=="SOIL_BEARING_CAPACITY")
    assert "CONCEPT_LAYOUT" not in soil["requiredFor"] and "FOUNDATION_ANALYSIS" in soil["requiredFor"]
    assessment=owned_row(site_db,"engineering_analyses",1,data["readinessAssessmentId"])["result_json"]
    assert assessment["siteDataState"]=="UNCONFIGURED"
    assert next(o for o in assessment["operations"] if o["operation"]=="CONCEPT_LAYOUT")["eligible"]


def conversation(db):
    return ConversationService().create(db,1,1,ConversationInput(client_request_id="conversation"))


def message(key="one",objects=None,**context):
    return MessageInput(client_request_id=key,parts=[{"kind":"TEXT","text":"Could the road move west?"}],
        context={"selectedObjectIds":objects or [],"modelRevisionId":"1",**context})


def test_conversation_persistence_idempotence_and_order(site_db):
    c=conversation(site_db);svc=ConversationService()
    first=svc.submit(site_db,1,1,c["id"],message())
    assert svc.submit(site_db,1,1,c["id"],message())==first
    svc.submit(site_db,1,1,c["id"],message("two"))
    site_db.expire_all()
    result=ConversationService().messages(site_db,1,c["id"])
    assert [m["sequence"] for m in result["messages"]]==[1,2]
    assert result["messages"][0]["run"]["status"]=="WAITING_FOR_INPUT"
    assert result["messages"][0]["run"]["errorCode"]=="ORCHESTRATION_NOT_ENABLED"
    assert not rows(site_db,"project_memory_versions",1)


def test_selection_and_model_do_not_drift(site_db):
    c=conversation(site_db);svc=ConversationService()
    svc.submit(site_db,1,1,c["id"],message(objects=["pier-a"],editorDirty=True))
    site_db.add(ModelRevision(id=2,project_id=1,design_scenario_id=1,revision_number=2,document_json={"components":[]}));site_db.commit()
    captured=svc.messages(site_db,1,c["id"])["messages"][0]["context"]
    assert captured["modelRevisionId"]=="1" and captured["selection"][0]["objectId"]=="pier-a"
    assert captured["editorDirty"] and len(captured["selection"][0]["geometryHash"])==64


def test_reused_message_key_different_context_rejected(site_db):
    c=conversation(site_db);svc=ConversationService();svc.submit(site_db,1,1,c["id"],message())
    with pytest.raises(HTTPException) as e:svc.submit(site_db,1,1,c["id"],message(objects=["pier-a"]))
    assert e.value.status_code==409


@pytest.mark.parametrize("field,table_name",[("siteSelectionVersionId","site_selection_versions"),("siteProfileVersionId","site_profile_versions"),("proposalVersionId","design_proposal_versions"),("scenarioId","design_scenarios")])
def test_nested_context_references_rejected(site_db,field,table_name):
    c=conversation(site_db)
    with pytest.raises(HTTPException) as e:ConversationService().submit(site_db,1,1,c["id"],message(**{field:"foreign"}))
    assert e.value.status_code==404


def requirement(key="r1",value=7,asset=None):
    return MemoryInput(client_request_id=key,asset_id=asset,content={"kind":"REQUIREMENT","key":"carriageway.width","constraint":{"operator":"EQ","value":value,"unit":"m"},"hardness":"HARD"})


def test_memory_explicit_accept_reject_supersede(site_db):
    svc=MemoryService();r=svc.create(site_db,1,1,requirement())
    assert r["status"]=="PROPOSED"
    svc.transition(site_db,1,1,r["id"],1,"accept","PROPOSED")
    rev=MemoryRevisionInput(**requirement("r2",8).model_dump(),expected_version=1)
    new=svc.create(site_db,1,1,rev,r["id"])
    assert next(i for i in svc.list(site_db,1) if i["version"]==1)["status"]=="ACCEPTED"
    svc.transition(site_db,1,1,r["id"],2,"accept","PROPOSED")
    assert [i["status"] for i in svc.list(site_db,1)]==["SUPERSEDED","ACCEPTED"]
    other=svc.create(site_db,1,1,requirement("reject",9))
    assert svc.transition(site_db,1,1,other["id"],1,"reject","PROPOSED")["status"]=="REJECTED"


def test_conflicting_requirements_not_silently_accepted(site_db):
    svc=MemoryService();a=svc.create(site_db,1,1,requirement());svc.transition(site_db,1,1,a["id"],1,"accept","PROPOSED")
    b=svc.create(site_db,1,1,requirement("other",8))
    with pytest.raises(HTTPException) as e:svc.transition(site_db,1,1,b["id"],1,"accept","PROPOSED")
    assert e.value.detail["code"]=="MEMORY_CONFLICT"
    assert svc.list(site_db,1)[-1]["status"]=="PROPOSED"


def test_asset_scoped_memory_and_frozen_accepted_versions(site_db):
    c=conversation(site_db);conv=ConversationService();conv.submit(site_db,1,1,c["id"],message(objects=["pier-a"]))
    asset=conv.messages(site_db,1,c["id"])["messages"][0]["context"]["selection"][0]["assetId"]
    svc=MemoryService();a=svc.create(site_db,1,1,requirement(asset=asset));svc.transition(site_db,1,1,a["id"],1,"accept","PROPOSED")
    conv.submit(site_db,1,1,c["id"],message("selected",["pier-a"]))
    conv.submit(site_db,1,1,c["id"],message("unselected"))
    msgs=conv.messages(site_db,1,c["id"])["messages"]
    assert msgs[1]["context"]["memoryVersionIds"]==[a["versionId"]]
    assert msgs[2]["context"]["memoryVersionIds"]==[]
    assert msgs[0]["context"]["memoryVersionIds"]==[]


@pytest.fixture
def api_client(site_db,monkeypatch):
    from app.main import app
    from app.db.session import get_db
    from app.core.security import get_current_user_id
    async def unavailable(*args):
        from app.services.ai.nebius import AssistantProviderError
        raise AssistantProviderError("MISSING_KEY")
    monkeypatch.setattr("app.services.assistant.runtime.assistant_json",unavailable)
    app.dependency_overrides[get_db]=lambda:site_db
    app.dependency_overrides[get_current_user_id]=lambda:1
    client=TestClient(app)
    yield client
    client.close();app.dependency_overrides.clear()


@pytest.mark.parametrize("path",["conversations","memory","site-profiles","site-evidence/foreign","assistant/runs/foreign"])
def test_project_authorization(api_client,path):
    assert api_client.get(f"/api/projects/2/{path}").status_code==404


def test_api_full_site_and_persistent_message_flow(api_client):
    c=api_client
    selection=c.post("/api/projects/1/site-selections/from-project").json()
    created=c.post("/api/projects/1/site-profiles",json={"selectionVersionId":selection["id"]})
    assert created.status_code==202,created.text
    pid=created.json()["id"]
    profile=c.get(f"/api/projects/1/site-profiles/{pid}").json()
    assert profile["version"],profile
    assert c.get(f"/api/projects/1/site-profiles/{pid}/readiness").json()["databaseMode"]=="DEMO"
    convo=c.post("/api/projects/1/conversations",json={"clientRequestId":"api"}).json()
    msg=message(siteSelectionVersionId=selection["id"],siteProfileVersionId=profile["version"]["id"])
    sent=c.post(f"/api/projects/1/conversations/{convo['id']}/messages",json=msg.model_dump(mode="json",by_alias=True))
    assert sent.status_code==202,sent.text
    assert len(c.get(f"/api/projects/1/conversations/{convo['id']}/messages").json()["messages"])==1


def test_profile_refresh_reuses_equivalent_version(site_db):
    svc,p,first,_=profile(site_db)
    prepared,start=svc.prepare(site_db,1,1,selection(site_db)["id"],p["id"])
    assert start
    second=svc.build(site_db,1,p["id"],prepared["jobId"])
    assert second["versionId"]==first["versionId"] and second["deduplicated"]


def test_old_profile_read_reports_boundary_change(site_db):
    svc,p,_,_=profile(site_db)
    site_db.get(Project,1).boundary_geojson=copy.deepcopy(KINDS[0]["geometry"] | {"coordinates":[[[77,12],[77.003,12],[77.003,12.002],[77,12]]]})
    site_db.commit()
    assert not svc.read(site_db,1,p["id"])["current"]


def test_unsupported_extent_is_explicit(site_db):
    from app.services.site_profiles.service import run_profile_job
    s=save_selection(site_db,1,1,SelectionInput(selection={"kind":"ENDPOINTS","endpointA":P1,"endpointB":{"type":"Point","coordinates":[80,12]}},original_crs=WGS84))
    svc=SiteProfileService();p,_=svc.prepare(site_db,1,1,s["id"])
    run_profile_job(site_db.get_bind(),1,p["id"],p["jobId"])
    result=svc.read(site_db,1,p["id"])
    assert result["errorCode"]=="UNSUPPORTED_EXTENT" and result["version"] is None


@pytest.mark.parametrize("mock",[True,False])
def test_retained_public_context_is_context_only(site_db,mock):
    from app.db.models import SiteAnalysis
    site_db.add(SiteAnalysis(project_id=1,raw_geojson={"mock":mock,"type":"FeatureCollection","features":[{"type":"Feature","geometry":LINE,"properties":{"category":"road","osm_id":10,"name":"Local road","highway":"residential"}}]}));site_db.commit()
    data=profile(site_db)[3]["version"]
    roads=data["nearby"]["roads"]
    assert roads["retrieval"]==("FAILED" if mock else "PARTIAL")
    if not mock:
        assert roads["features"][0]["geometry"]["use"]=="CONTEXT_ONLY"
        assert roads["features"][0]["attributes"]["width"]["value"] is None
    assert data["nearby"]["utilities"]["retrieval"]=="NOT_REQUESTED"


def test_foreign_existing_selection_cannot_be_bound_to_profile(site_db):
    s=selection(site_db,project=2)
    with pytest.raises(HTTPException) as e:SiteProfileService().prepare(site_db,1,1,s["id"])
    assert e.value.status_code==404


def test_waiting_or_interrupted_run_survives_reload(site_db):
    c=conversation(site_db);svc=ConversationService();result=svc.submit(site_db,1,1,c["id"],message())
    t=table("assistant_runs")
    site_db.execute(t.update().where(t.c.id==result["runId"]).values(status="FAILED",error_code="INTERRUPTED"));site_db.commit();site_db.expire_all()
    assert svc.messages(site_db,1,c["id"])["messages"][0]["run"]["errorCode"]=="INTERRUPTED"


def test_active_run_prevents_interleaving(site_db):
    c=conversation(site_db);svc=ConversationService();r=svc.submit(site_db,1,1,c["id"],message())
    t=table("assistant_runs");site_db.execute(t.update().where(t.c.id==r["runId"]).values(status="READING_CONTEXT"));site_db.commit()
    with pytest.raises(HTTPException) as e:svc.submit(site_db,1,1,c["id"],message("another"))
    assert e.value.detail["code"]=="RUN_ACTIVE"


@pytest.mark.parametrize("payload",[
    {"kind":"PREFERENCE","key":"material","value":"timber","priority":"NORMAL"},
    {"kind":"DECISION","statement":"Study the east crossing","rationale":"User requested study"},
    {"kind":"ASSUMPTION","statement":"Concept use only","impact":"Requires later verification","scope":"CONCEPT_ONLY"},
])
def test_typed_memory_kinds_and_project_scope(site_db,payload):
    svc=MemoryService();r=svc.create(site_db,1,1,MemoryInput(client_request_id=payload["kind"],content=payload))
    assert r["status"]=="PROPOSED" and r["assetId"] is None
    accepted=svc.transition(site_db,1,1,r["id"],1,"accept","PROPOSED")
    assert accepted["acceptedBy"]=="1" and accepted["acceptedAt"]


def test_memory_idempotence_and_foreign_scope(site_db):
    svc=MemoryService();first=svc.create(site_db,1,1,requirement())
    assert svc.create(site_db,1,1,requirement())["versionId"]==first["versionId"]
    with pytest.raises(HTTPException):svc.create(site_db,1,1,requirement("bad",asset="foreign"))


def test_credential_message_rejected_without_persistence(site_db):
    c=conversation(site_db)
    with pytest.raises(HTTPException) as e:
        ConversationService().submit(site_db,1,1,c["id"],MessageInput(client_request_id="secret",parts=[{"kind":"TEXT","text":"NEBIUS_API_KEY=example-secret-credential"}],context={}))
    assert e.value.detail["code"]=="SENSITIVE_CONTENT"
    assert not rows(site_db,"conversation_messages",1)


def test_typed_message_parts_reject_unowned_references(site_db):
    from pydantic import TypeAdapter
    from app.domain.site_workspace import MessagePart
    parts=[{"kind":"TEXT","text":"Discuss"},{"kind":"QUESTION","questionId":"q1","text":"Which crossing?","options":["East","West"]},
        {"kind":"ATTACHMENT","attachmentId":"missing","mediaType":"application/pdf","contentHash":"a"*64},
        {"kind":"PROPOSAL","proposalVersionId":"missing"},{"kind":"EVIDENCE","evidenceIds":["missing"]},{"kind":"ASSUMPTION","assumptionVersionId":"missing"}]
    c=conversation(site_db)
    for i,part in enumerate(parts):
        assert TypeAdapter(MessagePart).validate_python(part).model_dump(mode="json",by_alias=True)==part
        if i>=2:
            with pytest.raises(HTTPException):ConversationService().submit(site_db,1,1,c["id"],MessageInput(client_request_id=f"part{i}",parts=[part],context={}))


def test_concurrent_messages_are_ordered_and_retry_safe(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy.orm import Session
    from app.db.models import Base
    engine=sa.create_engine(f"sqlite:///{(tmp_path/'concurrent.db').as_posix()}",connect_args={"timeout":20})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(id=1,name="One",email="concurrent@test"));db.flush();db.add(Project(id=1,user_id=1,name="Site",project_type="bridge"));db.commit()
        cid=ConversationService().create(db,1,1,ConversationInput(client_request_id="one"))["id"]
    def submit(key):
        with Session(engine) as db:
            return ConversationService().submit(db,1,1,cid,MessageInput(client_request_id=key,parts=[{"kind":"TEXT","text":key}],context={}))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(submit,["same","same","second"]))
    assert results[0]["messageId"]==results[1]["messageId"]
    with Session(engine) as db:
        assert [m["sequence"] for m in ConversationService().messages(db,1,cid)["messages"]]==[1,2]
    engine.dispose()
