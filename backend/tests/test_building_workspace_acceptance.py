"""Generated specialist snapshots through the generic manual-save API."""
from copy import deepcopy
from starlette.requests import Request
from app.api.routes.model_revisions import save_revision, RevisionCreate
from app.db.models import ModelRevision, ModelPlacement, User
from app.services.assistant.proposals import ProposalService
from app.services.assistant.storage import rows
from test_building_specialist_v1 import create
from test_assistant_runtime import approval
from test_site_workspace import site_db


def test_generated_manual_save_reload_preserves_lineage(site_db, monkeypatch):
    view = create(site_db)
    service = ProposalService()
    service.approve(site_db, 1, 1, approval(view))
    generated = site_db.get(ModelRevision, int(service.build(site_db, 1, view["id"])["modelRevisionId"]))
    original = deepcopy(generated.document_json)
    document = deepcopy(original)
    column = next(c for c in document["components"] if c.get("metadata", {}).get("componentKind") == "COLUMN")
    column["transform"]["position"][0] += .1
    monkeypatch.setattr("app.api.routes.model_revisions.save_file", lambda *args: "/test/model.glb")
    result = save_revision(1, 1, RevisionCreate(base_revision_id=generated.id, document=document),
                           Request({"type": "http"}), site_db, site_db.get(User, 1))
    site_db.expire_all()
    saved = site_db.get(ModelRevision, result["id"])
    assert saved.source == "manual_edit"
    assert saved.document_json == document
    assert site_db.get(ModelRevision, generated.id).document_json == original
    before = [r for r in rows(site_db, "model_object_lineage", 1) if r["model_revision_id"] == generated.id]
    after = [r for r in rows(site_db, "model_object_lineage", 1) if r["model_revision_id"] == saved.id]
    assert len(before) == len(after)
    for old in before:
        new = next(r for r in after if r["object_id"] == old["object_id"])
        for key in ("asset_id", "component_id", "proposal_version_id", "specification_version_id", "generator_id"):
            assert new[key] == old[key]
        assert new["payload"]["generationModelRevisionId"] == generated.id
    placement = site_db.query(ModelPlacement).filter_by(model_revision_id=saved.id).one()
    assert placement.anchor_elevation is None
    assert placement.placement_state == "REVIEW_REQUIRED"
    # A second manual snapshot still points at the original generation.
    second = save_revision(1, 1, RevisionCreate(base_revision_id=saved.id, document=document),
                           Request({"type": "http"}), site_db, site_db.get(User, 1))
    assert all(r["payload"]["generationModelRevisionId"] == generated.id for r in
               rows(site_db, "model_object_lineage", 1) if r["model_revision_id"] == second["id"])
