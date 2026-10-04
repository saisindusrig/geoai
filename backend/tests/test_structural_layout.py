from copy import deepcopy

from app.db.models import AuditLog, DesignScenario, ModelRevision, Project, User
from app.services.design.editable_model import geometry_spec_to_document
from app.services.design.structural_layout import alternative_summaries, validate_layout


def document():
    project = Project(id=901, user_id=1, name="Layout", project_type="building", center_lng=77, center_lat=13)
    scenario = DesignScenario(id=902, project_id=901, name="Baseline", status="completed")
    result = geometry_spec_to_document(project, scenario, {"objects": [
        {"kind": "box", "name": "Column", "layer": "columns", "size": [.4, .4, 3], "center": [0, 0, 1.5]},
    ]})
    return project, scenario, result


def test_scaled_dimensions_and_invalid_presets():
    _, _, doc = document()
    doc["components"][0]["transform"]["scale"] = [2000, 1, 1]
    assert validate_layout(doc)["violations"][0]["rule"] == "max_dimension"
    doc["structural_layout"]["rule_preset"]["min_member_spacing_m"] = -1
    assert validate_layout(doc)["violations"][0]["rule"] == "invalid_preset"


def test_support_spacing_uses_plural_categories_and_levels():
    _, _, doc = document()
    other = deepcopy(doc["components"][0])
    other["id"] = "column-2"
    doc["components"].append(other)
    assert not validate_layout(doc)["passed"]
    other["transform"]["position"][2] = 5
    assert validate_layout(doc)["passed"]


def test_baseline_does_not_invent_alternative_savings():
    _, _, doc = document()
    options = alternative_summaries(doc)
    assert len(options) == 1
    assert options[0]["score"] is None
    assert options[0]["cost_delta_percent"] == 0
    assert options[0]["estimated_cost"] > 0


def test_approval_preserves_snapshot_and_export_requires_revision_approval(client, db_session):
    project, scenario, doc = document()
    db_session.add_all([User(id=1, name="Engineer", email="layout@example.com", role="engineer"), project, scenario])
    db_session.flush()
    revision = ModelRevision(project_id=901, design_scenario_id=902, revision_number=1, document_json=doc, source="manual_edit", user_id=1)
    db_session.add(revision)
    db_session.commit()
    base = f"/api/projects/901/scenarios/902/structural-layout/{revision.id}"
    assert client.get(base + "/analysis-package").status_code == 409
    before = deepcopy(revision.document_json)
    assert client.post(base + "/approve").status_code == 200
    db_session.refresh(revision)
    assert revision.document_json == before
    result = client.get(base + "/analysis-package")
    assert result.status_code == 200
    assert result.json()["approval"]["approved_by"] == 1
    imported = {
        "format": "sitegeoai.structural-analysis-result/v1", "revision_id": revision.id,
        "document_sha256": result.json()["document_sha256"], "solver": "Test solver",
        "summary": "Review completed", "findings": [{"component_id": doc["components"][0]["id"], "status": "warning", "message": "Review connection detail"}],
    }
    assert client.post(base + "/analysis-results", json=imported).status_code == 200
    assert client.get(base + "/analysis-results").json()["results"][0]["summary"] == "Review completed"
    bad_hash = {**imported, "document_sha256": "0" * 64}
    assert client.post(base + "/analysis-results", json=bad_hash).status_code == 409
    unknown = {**imported, "findings": [{"component_id": "missing", "status": "fail", "message": "Unknown"}]}
    assert client.post(base + "/analysis-results", json=unknown).status_code == 422
    db_session.refresh(revision)
    assert revision.document_json == before
    assert db_session.query(AuditLog).filter(AuditLog.action == "layout.approved").count() == 1
    second = ModelRevision(project_id=901, design_scenario_id=902, revision_number=2, document_json=doc, source="manual_edit", user_id=1)
    db_session.add(second)
    db_session.commit()
    assert client.get(f"/api/projects/901/scenarios/902/structural-layout/{second.id}/analysis-package").status_code == 409


def test_non_engineer_cannot_approve(client, db_session):
    project, scenario, doc = document()
    db_session.add_all([User(id=1, name="Owner", email="owner@example.com", role="user"), project, scenario])
    db_session.flush()
    revision = ModelRevision(project_id=901, design_scenario_id=902, revision_number=1, document_json=doc)
    db_session.add(revision)
    db_session.commit()
    assert client.post(f"/api/projects/901/scenarios/902/structural-layout/{revision.id}/approve").status_code == 403


def test_draft_validation_does_not_save_and_handles_invalid_values(client, db_session):
    project, scenario, doc = document()
    db_session.add_all([User(id=1, name="Owner", email="draft@example.com", role="user"), project, scenario])
    db_session.commit()
    base = "/api/projects/901/scenarios/902/structural-layout/validate"
    assert client.post(base, json={"document": doc}).json()["passed"]
    doc["structural_layout"]["rule_preset"]["max_dimension_m"] = 2
    assert not client.post(base, json={"document": doc}).json()["passed"]
    assert db_session.query(ModelRevision).count() == 0
    doc["components"][0]["geometry"]["size"] = ["bad", 1, 1]
    assert client.post(base, json={"document": doc}).status_code == 422
    assert client.post("/api/projects/901/scenarios/999/structural-layout/validate", json={"document": doc}).status_code == 404
