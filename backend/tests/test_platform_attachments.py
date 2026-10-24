import json
from copy import deepcopy
from pathlib import Path

import pytest

from app.db.models import DesignScenario, Project, User
from app.services.design.editable_model import validate_document, document_to_geometry_spec
from app.services.design.platform_attachments import validate_platform_attachments


def document():
    return json.loads((Path(__file__).parent / "fixtures/platform_attachments.json").read_text(encoding="utf-8"))


def test_actual_generator_fixture_has_connected_solids_and_unverified_scope():
    doc = document()
    before = deepcopy(doc)
    assert validate_platform_attachments(doc) == []
    assert validate_document(doc, project_id=1, scenario_id=1, project_type=doc["project_type"]) == []
    assert len(doc["components"]) == 42
    assert len(document_to_geometry_spec(doc)["objects"]) == 42
    assert doc == before


@pytest.mark.parametrize("field,value", [("width", 0), ("depth", -1), ("thickness", float("nan")), ("width", float("inf")), ("width", 501)])
def test_invalid_dimensions_are_rejected(field, value):
    doc = document()
    doc["generator_parameters"]["platform_attachments"]["items"][0]["parameters"][field] = value
    assert validate_platform_attachments(doc)


@pytest.mark.parametrize("change", ["missing_ref", "missing_core", "duplicate_ref", "disconnected", "missing_tread", "orphan", "unverified", "quantity", "wrong_category", "extra_part", "altered_radius", "unknown_kind", "unsupported_version", "plate_footprint"])
def test_tampered_geometry_and_references_are_rejected(change):
    doc = document()
    items = doc["generator_parameters"]["platform_attachments"]["items"]
    managed = next(c for c in doc["components"] if c.get("metadata", {}).get("parametric_attachment"))
    if change == "missing_ref":
        items[0]["refs"] = ["missing"]
    elif change == "missing_core":
        doc["components"] = [c for c in doc["components"] if c["id"] != "industrial-platform-5x3:beam-west"]
    elif change == "duplicate_ref":
        brace = next(a for a in items if a["kind"] == "brace")
        brace["refs"][1] = brace["refs"][0]
    elif change == "disconnected":
        managed["transform"]["position"][0] += 1
    elif change == "missing_tread":
        doc["components"] = [c for c in doc["components"] if c["id"] != "platform-addon:stairs-south:tread-2"]
    elif change == "orphan":
        doc["generator_parameters"]["platform_attachments"]["items"] = []
    elif change == "unverified":
        managed["metadata"]["engineering_status"] = "approved"
    elif change == "quantity":
        managed["quantity"]["included"] = True
    elif change == "wrong_category":
        managed["category"] = "decoration"
    elif change == "extra_part":
        extra = deepcopy(managed)
        extra["id"] += "-duplicate"
        doc["components"].append(extra)
    elif change == "altered_radius":
        brace = next(c for c in doc["components"] if c["category"] == "bracing")
        brace["geometry"]["radius_m"] *= 2
    elif change == "unknown_kind":
        items[0]["kind"] = "imaginary"
    elif change == "unsupported_version":
        doc["generator_parameters"]["platform_attachments"]["version"] = 2
    else:
        next(a for a in items if a["kind"] == "base_plate")["parameters"]["width"] = 2
    assert validate_platform_attachments(doc)


def test_unmanaged_documents_keep_existing_validation_behavior():
    assert validate_platform_attachments({"components": [], "generator_parameters": {}}) == []


def test_saved_revision_roundtrip_rejects_disconnected_draft_without_changing_history(client, db_session, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "S3_ACCESS_KEY", "")
    monkeypatch.setattr(settings, "S3_SECRET_KEY", "")
    doc = document()
    doc["project_id"], doc["scenario_id"] = 101, 201
    doc["project_type"] = "building"
    db_session.add(User(id=1, name="Local reviewer", email="reviewer@example.test", role="admin", plan="admin"))
    db_session.add(Project(id=101, user_id=1, name="Attachment review", project_type="building", center_lat=13, center_lng=77))
    db_session.add(DesignScenario(id=201, project_id=101, name="Platform", status="completed"))
    db_session.commit()
    url = "/api/projects/101/scenarios/201/model-revisions"
    first = client.post(url, json={"base_revision_id": None, "document": doc, "source": "manual_edit"})
    assert first.status_code == 200, first.text
    revision = first.json()["id"]
    saved = client.get(f"{url}/{revision}")
    assert saved.json()["document"] == doc
    bad = deepcopy(doc)
    next(c for c in bad["components"] if c["category"] == "bracing")["geometry"]["end"][2] += 1
    rejected = client.post(url, json={"base_revision_id": revision, "document": bad, "source": "manual_edit"})
    assert rejected.status_code == 422, rejected.text
    assert len(client.get(url).json()["revisions"]) == 1
    assert client.get(f"{url}/{revision}").json()["document"] == doc
