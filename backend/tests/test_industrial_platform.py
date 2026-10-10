"""Offline platform composition and fail-closed application gates."""
import copy
import pytest
from fastapi import HTTPException
from app.db.models import ModelRevision, Project
from app.domain.assistant_runtime import ProposalRequest
from app.services.assistant.ai3d_executor import Generic3DExecutor
from app.services.assistant.ai3d_validation import AI3DDesignValidator, site_summary
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import rows
from scripts.industrial_platform_design import platform_design
from test_ai3d_v1 import setup
from test_assistant_runtime import approval
from test_site_workspace import site_db


def request(db):
    msg, _ = setup(db)
    selection = site_summary(db, 1, msg["context"])["selectionReference"]
    return ProposalRequest(client_request_id="platform", message_id=msg["id"], title="5 m x 3 m platform",
        rationale="Offline conceptual platform", assets=[{"assetType": "AI3D_DESIGN", "name": "Maintenance platform",
        "ai3dDesign": platform_design(selection, "1", (10, 10))}])


def test_platform_dimensions_and_explicit_assumptions(site_db):
    req = request(site_db)
    spec = req.assets[0].ai3d_design
    summary = site_summary(site_db, 1, {"modelRevisionId": "1", **ProposalService().create(site_db, 1, 1, req)["content"]["context"]})
    result = AI3DDesignValidator().validate(spec, summary)
    assert result["status"] == "DESIGN_VALID" and result["componentCount"] == 9
    assert result["engineeringStatus"] == "UNVALIDATED"
    with pytest.raises(ValueError): Generic3DExecutor().generate(spec)
    generated = Generic3DExecutor().generate(spec, summary)
    assert generated == Generic3DExecutor().generate(spec, summary)
    mismatched = {**summary, "selectionReference": {**summary["selectionReference"], "version": 999}}
    with pytest.raises(ValueError): Generic3DExecutor().generate(spec, mismatched)
    deck = next(o for o in generated["objects"] if o["semantic"]["sourceObjectId"] == "platform-deck")
    assert list(deck["size"]) == [5, 3, .2]
    assert deck["center"][2] + deck["size"][2] / 2 == pytest.approx(3)
    assert [o.semantic_type for o in spec.objects].count("COLUMN") == 4
    assert [o.semantic_type for o in spec.objects].count("BEAM") == 4
    assert summary["origin"]["elevation_m"] is None
    assert "not surveyed" in spec.assumptions[1].reason
    assert {"designLoads", "foundations", "clearances", "structuralAdequacy", "codeCompliance"} <= set(spec.unknowns)


def test_platform_requires_acknowledgment_and_explicit_approval(site_db):
    service = ProposalService(); view = service.create(site_db, 1, 1, request(site_db))
    before = copy.deepcopy(site_db.get(ModelRevision, 1).document_json)
    assert view["status"] == "READY_FOR_REVIEW"
    with pytest.raises(HTTPException): service.build(site_db, 1, view["id"])
    with pytest.raises(HTTPException):
        service.approve(site_db, 1, 1, approval(view).model_copy(update={"acknowledged_assumption_version_ids": []}))
    assert not rows(site_db, "proposal_approvals", 1)
    service.approve(site_db, 1, 1, approval(view))
    result = service.build(site_db, 1, view["id"])
    assert len(site_db.get(ModelRevision, int(result["modelRevisionId"])).document_json["components"]) == 10
    assert site_db.get(ModelRevision, 1).document_json == before
    assert len(rows(site_db, "model_object_lineage", 1)) == 9


@pytest.mark.parametrize("failure", ["missing-site", "stale-site", "stale-selection", "invalid-dimension"])
def test_platform_invalid_context_does_not_generate(site_db, failure):
    req = request(site_db); service = ProposalService()
    if failure == "invalid-dimension":
        raw = req.assets[0].ai3d_design.model_dump(mode="json", by_alias=True)
        raw["objects"][0]["parameters"]["size"][0] = 0
        assert AI3DDesignValidator().validate(raw)["status"] == "INVALID_DESIGN"
        assert len(rows(site_db, "model_revisions", 1)) == 1
        return
    if failure == "missing-site":
        from app.domain.site_workspace import MessageInput
        from app.services.assistant.conversations import ConversationService
        msg = rows(site_db, "conversation_messages", 1)[0]
        posted = ConversationService().submit(site_db, 1, 1, msg["conversation_id"], MessageInput(
            client_request_id="missing-site", parts=[{"kind": "TEXT", "text": "Create a maintenance platform concept."}],
            context={"modelRevisionId": "1", "scenarioId": "1"}))
        req = req.model_copy(update={"message_id": posted["messageId"]})
        with pytest.raises(HTTPException) as exc: service.create(site_db, 1, 1, req)
        assert exc.value.detail["code"] == "SITE_PROFILE_REQUIRED"
    else:
        view = service.create(site_db, 1, 1, req)
        service.approve(site_db, 1, 1, approval(view))
        if failure == "stale-selection":
            from app.domain.site_workspace import SelectionInput
            from app.services.site_profiles.selection import save_selection
            from app.services.assistant.storage import owned_row
            from test_site_workspace import AREA, WGS84
            selected = owned_row(site_db, "site_selection_versions", 1, view["content"]["context"]["siteSelectionVersionId"])
            changed = copy.deepcopy(AREA); changed["coordinates"][0][1][0] += .001
            save_selection(site_db, 1, 1, SelectionInput(selection={"kind": "AREA", "geometry": changed},
                original_crs=WGS84, expected_version=selected["version"]), selection_id=selected["selection_id"])
        else:
            site_db.get(Project, 1).boundary_geojson = None; site_db.commit()
        with pytest.raises(HTTPException): service.build(site_db, 1, view["id"])
        assert service.read(site_db, 1, view["id"])["status"] == "STALE"
    assert len(rows(site_db, "model_revisions", 1)) == 1
