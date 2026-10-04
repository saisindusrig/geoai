from app.db.models import DesignScenario, Project, User
from app.services.design.editable_model import (
    apply_component_patch,
    build_ai_edit_preview,
    calculate_revision_impact,
    document_to_geometry_spec,
    geometry_spec_to_document,
    validate_document,
)


def _seed(db_session):
    user = User(id=1, name="Editor", email="editor@example.com", role="admin", plan="admin")
    project = Project(
        id=101,
        user_id=1,
        name="Editable bridge",
        project_type="bridge",
        center_lat=12.97,
        center_lng=77.59,
    )
    scenario = DesignScenario(id=201, project_id=101, name="Generated", status="completed")
    db_session.add_all([user, project, scenario])
    db_session.commit()
    return project, scenario


def _spec():
    return {
        "frame": "local_meters",
        "objects": [
            {"kind": "box", "name": "Deck", "layer": "deck", "size": [20, 8, 1], "center": [0, 0, 5]},
            {"kind": "cylinder", "name": "Pier", "layer": "piers", "start": [0, 0, 0], "end": [0, 0, 5], "radius_m": 1},
        ],
    }


def test_document_roundtrip_and_impact(db_session):
    project, scenario = _seed(db_session)
    document = geometry_spec_to_document(project, scenario, _spec())
    assert validate_document(document, project_id=project.id, scenario_id=scenario.id, project_type="bridge") == []
    assert len({item["id"] for item in document["components"]}) == 2
    result = document_to_geometry_spec(document)
    assert result["objects"][0]["name"] == "deck-deck"
    impact = calculate_revision_impact(document)
    assert impact["quantities"]["concrete_m3"] > 160
    assert impact["total_cost_estimate"] > 0


def test_ai_edit_is_preview_only_and_patch_is_explicit(db_session):
    project, scenario = _seed(db_session)
    document = geometry_spec_to_document(project, scenario, _spec())
    preview = build_ai_edit_preview(document, "raise deck 2 metres")
    assert preview["patch"][0]["component_id"] == "deck-deck"
    candidate = apply_component_patch(document, preview["patch"])
    assert document["components"][0]["transform"]["position"][2] == 5
    assert candidate["components"][0]["transform"]["position"][2] == 7


def test_revision_api_conflict_and_immutable_history(client, db_session):
    project, scenario = _seed(db_session)
    document = geometry_spec_to_document(project, scenario, _spec())
    url = f"/api/projects/{project.id}/scenarios/{scenario.id}/model-revisions"
    first = client.post(url, json={"base_revision_id": None, "document": document, "source": "manual_edit"})
    assert first.status_code == 200, first.text
    first_id = first.json()["id"]
    conflict = client.post(url, json={"base_revision_id": None, "document": document, "source": "manual_edit"})
    assert conflict.status_code == 409
    second = client.post(url, json={"base_revision_id": first_id, "document": document, "source": "manual_edit"})
    assert second.status_code == 200, second.text
    assert second.json()["revision_number"] == 2
    listed = client.get(url)
    assert [item["revision_number"] for item in listed.json()["revisions"]] == [2, 1]
    previous = client.get(f"{url}/{first_id}")
    assert previous.status_code == 200
    assert previous.json()["document"] == document
    assert client.get(f"{url}/999999").status_code == 404


def test_ai_preview_and_apply_respect_locked_objects(db_session):
    import pytest
    project, scenario = _seed(db_session)
    document = geometry_spec_to_document(project, scenario, _spec())
    document["components"][0]["locked"] = True
    preview = build_ai_edit_preview(document, "raise deck 2 metres")
    assert preview["patch"] == [] and "locked" in preview["warnings"][0]
    with pytest.raises(ValueError, match="Locked component"):
        apply_component_patch(document, [{"component_id": "deck-deck", "changes": {"name": "Bypass", "locked": False}}])
    assert apply_component_patch(document, [{"component_id": "deck-deck", "changes": {"visible": False}}])["components"][0]["visible"] is False


def test_saved_revision_preserves_accepted_anchor_and_stales_analyses(client, db_session):
    from app.db.models import ModelPlacement, EngineeringAnalysis
    project, scenario = _seed(db_session)
    document = geometry_spec_to_document(project, scenario, _spec())
    url = f"/api/projects/{project.id}/scenarios/{scenario.id}/model-revisions"
    first = client.post(url, json={"base_revision_id": None, "document": document, "source": "manual_edit"})
    assert first.status_code == 200, first.text
    first_id = first.json()["id"]
    db_session.add(ModelPlacement(project_id=project.id, model_revision_id=first_id, placement_mode="ABSOLUTE", placement_state="VALID", anchor_longitude=77.59, anchor_latitude=12.97, anchor_elevation=912, anchor_heading_deg=30))
    db_session.add(EngineeringAnalysis(project_id=project.id, model_revision_id=first_id, analysis_type="CLEARANCE", algorithm_version="1", status="VALID", result_json={"clearance_m": 5}, actor_user_id=1))
    db_session.commit()
    document["components"][0]["material"]["color"] = "#112233"
    second = client.post(url, json={"base_revision_id": first_id, "document": document, "source": "manual_edit"})
    assert second.status_code == 200, second.text
    anchor = db_session.query(ModelPlacement).filter_by(model_revision_id=second.json()["id"]).one()
    assert anchor.anchor_elevation == 912 and anchor.anchor_heading_deg == 30 and anchor.placement_state == "VALID"
    db_session.expire_all()
    analysis = db_session.query(EngineeringAnalysis).one()
    assert analysis.status == "STALE" and analysis.result_json == {"clearance_m": 5}
