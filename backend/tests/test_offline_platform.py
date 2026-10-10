"""Website orchestration path without inference or premature model writes."""
import asyncio
import pytest
from app.core.config import settings
from app.db.models import ModelRevision, Project
from app.services.assistant.runtime import process, queue_run
from app.services.assistant.offline_platform import EXAMPLE, provider_for_request
from app.services.assistant.storage import rows, owned_row, update
from test_site_workspace import site_db
from test_assistant_runtime import message


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(settings, "GEOAI_OFFLINE_PLATFORM_DEMO", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    async def forbidden(*args, **kwargs):
        pytest.fail("Offline template must not dispatch inference")
    monkeypatch.setattr("app.services.ai.provider.NebiusProvider.complete", forbidden)


def run(db, text=EXAMPLE, change=None):
    msg, rid = message(db, text)
    if change:
        change(msg)
        update(db, "conversation_messages", 1, msg["id"], context=msg["context"])
        db.commit()
    queue_run(db, 1, 1, rid)
    asyncio.run(process(db, 1, rid))
    return rid


def test_website_platform_proposal_without_model_mutation(site_db):
    before = site_db.get(ModelRevision, 1).document_json.copy()
    rid = run(site_db)
    assert owned_row(site_db, "assistant_runs", 1, rid)["status"] == "COMPLETE"
    specs = rows(site_db, "asset_specification_versions", 1)
    assert len(specs) == 1
    from app.services.assistant.proposals import ProposalService
    view = ProposalService().read(site_db, 1, rows(site_db, "design_proposal_versions", 1)[0]["id"])
    assert view["status"] == "READY_FOR_REVIEW"
    assert "Offline demo" in view["content"]["request"]["rationale"]
    assert len(rows(site_db, "model_revisions", 1)) == 1
    assert site_db.get(ModelRevision, 1).document_json == before
    assert not rows(site_db, "proposal_approvals", 1)
    assert not rows(site_db, "generation_requests", 1)
    asyncio.run(process(site_db, 1, rid))
    assert len(rows(site_db, "design_proposal_versions", 1)) == 1


@pytest.mark.parametrize("text", [
    EXAMPLE.replace("5 m", "6 m"), EXAMPLE.replace("3 m high", "4 m high"),
    "Create an industrial maintenance platform", EXAMPLE + " Add stairs.",
    "Create a bridge and platform with a crane", EXAMPLE + " Certified safe for 10 tonnes.",
])
def test_unsupported_request_clarifies_without_substitution(site_db, text):
    rid = run(site_db, text)
    assert owned_row(site_db, "assistant_runs", 1, rid)["status"] == "COMPLETE"
    assert not rows(site_db, "design_proposal_versions", 1)
    assert len(rows(site_db, "model_revisions", 1)) == 1


@pytest.mark.parametrize("text", ["What is a platform?", "Create a bridge", "Move this platform", "Hello"])
def test_other_requests_are_not_hijacked(site_db, text):
    msg, _ = message(site_db, text)
    assert provider_for_request(site_db, 1, msg) is None


@pytest.mark.parametrize("gate,value", [("GEOAI_OFFLINE_PLATFORM_DEMO", False), ("AI_PROVIDER", "nebius"), ("ENVIRONMENT", "production")])
def test_explicit_local_gate(site_db, monkeypatch, gate, value):
    msg, _ = message(site_db, EXAMPLE)
    monkeypatch.setattr(settings, gate, value)
    assert provider_for_request(site_db, 1, msg) is None


def test_missing_profile_fails_closed(site_db):
    from app.domain.site_workspace import ConversationInput, MessageInput
    from app.services.assistant.conversations import ConversationService
    svc = ConversationService()
    convo = svc.create(site_db, 1, 1, ConversationInput(client_request_id="missing"))
    posted = svc.submit(site_db, 1, 1, convo["id"], MessageInput(client_request_id="missing", parts=[{"kind": "TEXT", "text": EXAMPLE}], context={}))
    rid = posted["runId"]
    queue_run(site_db, 1, 1, rid)
    asyncio.run(process(site_db, 1, rid))
    assert owned_row(site_db, "assistant_runs", 1, rid)["error_code"] == "SITE_PROFILE_REQUIRED"
    assert not rows(site_db, "design_proposal_versions", 1)


def test_stale_site_cannot_create_ready_proposal(site_db):
    msg, rid = message(site_db, EXAMPLE)
    site_db.get(Project, 1).boundary_geojson = None
    site_db.commit()
    queue_run(site_db, 1, 1, rid)
    asyncio.run(process(site_db, 1, rid))
    assert not any(r["status"] == "READY_FOR_REVIEW" for r in rows(site_db, "design_proposal_versions", 1))
    assert len(rows(site_db, "model_revisions", 1)) == 1


@pytest.mark.parametrize("small", [False, True])
def test_fresh_project_and_small_boundary(site_db, small):
    from app.domain.site_workspace import SelectionInput, ConversationInput, MessageInput
    from app.services.site_profiles.selection import save_selection
    from app.services.site_profiles.service import SiteProfileService
    from app.services.assistant.conversations import ConversationService
    from test_site_workspace import AREA, WGS84
    from app.services.assistant.proposals import ProposalService
    from app.domain.assistant_runtime import ApplicationApproval
    from fastapi import HTTPException
    boundary = {"type": "Polygon", "coordinates": [[[77,12],[77.00001,12],[77.00001,12.00001],[77,12.00001],[77,12]]]} if small else AREA
    site_db.add(Project(id=3, user_id=1, name="Fresh website", project_type="building", boundary_geojson=boundary))
    site_db.commit()
    selection = save_selection(site_db, 3, 1, SelectionInput(selection={"kind": "AREA", "geometry": boundary}, original_crs=WGS84))
    profiles = SiteProfileService()
    prepared, _ = profiles.prepare(site_db, 3, 1, selection["id"])
    profiles.build(site_db, 3, prepared["id"], prepared["jobId"])
    version = profiles.read(site_db, 3, prepared["id"])["version"]
    svc = ConversationService()
    convo = svc.create(site_db, 3, 1, ConversationInput(client_request_id="fresh"))
    posted = svc.submit(site_db, 3, 1, convo["id"], MessageInput(client_request_id="fresh", parts=[{"kind": "TEXT", "text": EXAMPLE}], context={"siteSelectionVersionId": selection["id"], "siteProfileVersionId": version["id"]}))
    queue_run(site_db, 3, 1, posted["runId"])
    asyncio.run(process(site_db, 3, posted["runId"]))
    assert not rows(site_db, "model_revisions", 3)
    assert not rows(site_db, "proposal_approvals", 3)
    proposals = rows(site_db, "design_proposal_versions", 3)
    if small:
        assert not any(p["status"] == "READY_FOR_REVIEW" for p in proposals)
        return
    view = ProposalService().read(site_db, 3, proposals[0]["id"])
    assert view["status"] == "READY_FOR_REVIEW"
    with pytest.raises(HTTPException):
        ProposalService().build(site_db, 3, view["id"])
    approval = ApplicationApproval(client_request_id="fresh", proposal_version_id=view["id"], proposal_hash=view["contentHash"], dependency_hash=view["dependencyHash"], validation_hash=view["validationHash"], alternative_id=None, acknowledged_assumption_version_ids=view["content"]["contract"]["assumptionVersionIds"], expected_model_revision_id=None)
    ProposalService().approve(site_db, 3, 1, approval)
    built = ProposalService().build(site_db, 3, view["id"])
    revision = site_db.get(ModelRevision, int(built["modelRevisionId"]))
    assert len(revision.document_json["components"]) == 9
    assert revision.document_json["origin"]["elevation_m"] is None
    assert ProposalService().build(site_db, 3, view["id"]) == built
