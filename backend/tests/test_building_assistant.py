import asyncio
import copy
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.db.models import BuildingPlan, DesignScenario, ModelRevision, Project, User, ModelPlacement
from app.services.ai import building_plan, nebius, providers
from app.services.design.planned_building import generate


def specification():
    return {
        "summary": "A single-floor two-room concept with a concrete frame.", "floors": 1, "floor_height": 3,
        "footprint": {"x": -5, "y": -4, "width": 10, "depth": 8},
        "rooms": [{"id": "a", "name": "Living", "floor": 0, "x": -5, "y": -4, "width": 5, "depth": 8},
                  {"id": "b", "name": "Bedroom", "floor": 0, "x": 0, "y": -4, "width": 5, "depth": 8}],
        "walls": [{"id": str(i), "floor": 0, "start": a, "end": b, "thickness": .15} for i, (a,b) in enumerate([
            ([-5,-4],[5,-4]), ([5,-4],[5,4]), ([5,4],[-5,4]), ([-5,4],[-5,-4]), ([0,-4],[0,4])])],
        "openings": [{"id": "door", "wall_id": "0", "kind": "door", "offset": 1, "width": 1, "height": 2.1, "sill": 0},
                     {"id": "window", "wall_id": "2", "kind": "window", "offset": 1, "width": 1.5, "height": 1.2, "sill": 1}],
        "columns": [{"x": x, "y": y, "size": .3} for x,y in [(-4,-3),(4,-3),(4,3),(-4,3)]],
        "beams": [{"start": [-4,-3], "end": [4,-3], "width": .25, "depth": .35},
                  {"start": [-4,3], "end": [4,3], "width": .25, "depth": .35}],
        "assumptions": ["Flat visual reference; no verified survey or structural calculations."],
    }


@pytest.fixture
def building(db_session, sample_boundary, monkeypatch):
    user = User(id=1, name="Builder", email="builder@example.com", role="admin", plan="admin")
    project = Project(id=801, user_id=1, name="AI house", project_type="building", center_lng=77.595, center_lat=12.972,
                      boundary_geojson=sample_boundary)
    db_session.add_all([user, project]); db_session.commit()
    monkeypatch.setattr(building_plan, "propose", AsyncMock(return_value=building_plan.BuildingSpec.model_validate(specification())))
    from app.api.routes import building_plans
    monkeypatch.setattr(building_plans, "enforce_rate_limit", lambda *a, **kw: None)
    return project


def create(client, building):
    url = f"/api/projects/{building.id}/ai/building-plans"
    response = client.post(url, json={"prompt": "Build a one floor house"})
    assert response.status_code == 200, response.text
    return url, response.json()


def test_geometry_validation_and_opening_cutouts(db_session, building):
    spec = building_plan.BuildingSpec.model_validate(specification())
    assert building_plan.validate_spec(spec, building_plan.context(db_session, building)) == []
    result = generate(spec.model_dump())
    objects = result["geometry_spec"]["objects"]
    assert {o["layer"] for o in objects} == {"room", "wall", "door", "window", "column", "beam", "slab", "foundation"}
    assert all(min(o["size"]) > 0 for o in objects)
    # Door removes the full wall segment at floor level, but leaves its lintel.
    door_wall = [o for o in objects if o["name"].startswith("wall-0-")]
    assert len(door_wall) == 3
    assert any("lintel" in o["name"] and o["center"][2] > 2.1 for o in door_wall)
    assert result == generate(spec.model_dump())
    raw = specification(); raw["rooms"][1]["x"] = -1
    assert any("overlap" in e for e in building_plan.validate_spec(building_plan.BuildingSpec.model_validate(raw), building_plan.context(db_session, building)))
    raw = specification(); raw["footprint"]["x"] = 999
    assert building_plan.validate_spec(building_plan.BuildingSpec.model_validate(raw), building_plan.context(db_session, building))
    raw = specification(); raw["floor_height"] = float("nan")
    with pytest.raises(ValidationError): building_plan.BuildingSpec.model_validate(raw)


def test_proposal_revision_approval_and_duplicate_build(client, db_session, building, monkeypatch):
    from app.services import jobs
    submitted = []
    monkeypatch.setattr(jobs, "submit_design_generation", lambda **kw: submitted.append(kw) or kw["job_id"])
    url, first = create(client, building)
    assert db_session.query(ModelRevision).count() == 0
    assert db_session.query(DesignScenario).count() == 0
    second = client.post(f"{url}/{first['id']}/revisions", json={"prompt": "Make the rooms brighter"}).json()
    assert second["parent_id"] == first["id"]
    assert client.get(f"{url}/{first['id']}").json()["spec"] == first["spec"]
    build_url = f"{url}/{second['id']}/build"
    assert client.post(build_url, json={"approve": False}).status_code == 422
    first_build = client.post(build_url, json={"approve": True})
    assert first_build.status_code == 200, first_build.text
    repeat = client.post(build_url, json={"approve": True})
    assert repeat.json()["job_id"] == first_build.json()["job_id"]
    assert len(submitted) == 1
    assert db_session.query(DesignScenario).count() == 1
    assert db_session.query(BuildingPlan).count() == 2


def test_stale_plot_and_unauthorized_access(client, db_session, building):
    url, plan = create(client, building)
    boundary = copy.deepcopy(building.boundary_geojson)
    boundary["coordinates"][0][1][0] += .001
    building.boundary_geojson = boundary; db_session.commit()
    assert client.get(f"{url}/{plan['id']}").json()["stale"]
    assert client.post(f"{url}/{plan['id']}/build", json={"approve": True}).status_code == 409
    assert db_session.query(DesignScenario).count() == 0
    db_session.add(User(id=2, name="Other", email="other@example.com")); db_session.commit()
    building.user_id = 2; db_session.commit()
    assert client.get(url).status_code in (403, 404)
    assert client.post(f"{url}/{plan['id']}/build", json={"approve": True}).status_code in (403, 404)


def test_new_revision_invalidates_plan(client, db_session, building):
    url, plan = create(client, building)
    scenario = DesignScenario(project_id=building.id, name="Other model", status="completed")
    db_session.add(scenario); db_session.flush()
    db_session.add(ModelRevision(project_id=building.id, design_scenario_id=scenario.id, revision_number=1,
                                document_json={"origin": {"lng": building.center_lng, "lat": building.center_lat, "elevation_m": 0}}, source="manual_edit"))
    db_session.commit()
    assert client.post(f"{url}/{plan['id']}/build", json={"approve": True}).status_code == 409


def test_provider_errors_and_invalid_plan_are_visible(client, db_session, building, monkeypatch):
    url = f"/api/projects/{building.id}/ai/building-plans"
    monkeypatch.setattr(building_plan, "propose", AsyncMock(side_effect=nebius.NebiusError("Nebius timed out")))
    response = client.post(url, json={"prompt": "Build a house"})
    assert response.status_code == 503 and "timed out" in response.text
    monkeypatch.setattr(building_plan, "propose", AsyncMock(side_effect=ValueError("invalid")))
    assert client.post(url, json={"prompt": "Build a house"}).status_code == 422
    assert db_session.query(BuildingPlan).count() == 0


def test_nebius_missing_key_timeout_and_invalid_json(monkeypatch):
    monkeypatch.setattr(settings, "NEBIUS_API_KEY", "")
    with pytest.raises(nebius.NebiusError, match="Configure"):
        asyncio.run(nebius.completion("system", "request"))
    monkeypatch.setattr(settings, "NEBIUS_API_KEY", "test-only")
    monkeypatch.setattr(httpx.AsyncClient, "post", AsyncMock(side_effect=httpx.ReadTimeout("timeout")))
    with pytest.raises(nebius.NebiusError, match="timed out"):
        asyncio.run(nebius.completion("system", "request"))
    monkeypatch.setattr(nebius, "completion", AsyncMock(return_value="not json"))
    with pytest.raises(nebius.NebiusError, match="invalid JSON"):
        asyncio.run(nebius.generate_json("system", "request"))


def test_nebius_provider_is_supported_without_fallback(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "nebius")
    monkeypatch.setattr(nebius, "generate_json", AsyncMock(side_effect=nebius.NebiusError("unavailable")))
    assert providers.normalize_ai_provider() == "nebius"
    with pytest.raises(nebius.NebiusError): asyncio.run(providers.generate_plan_json("system", "request"))


def test_generation_uses_approved_spec_and_saves_editable_revision(client, db_session, building, monkeypatch, tmp_path):
    from app.services import jobs
    from app.services.ai import orchestrator
    from app.services.ai import design_planner
    monkeypatch.setattr(jobs, "submit_design_generation", lambda **kw: kw["job_id"])
    monkeypatch.setattr(jobs, "_get_redis", lambda: None)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(design_planner, "plan_design", AsyncMock(side_effect=AssertionError("Must not re-plan")))
    url, plan = create(client, building)
    response = client.post(f"{url}/{plan['id']}/build", json={"approve": True})
    assert response.status_code == 200, response.text
    scenario = db_session.get(DesignScenario, response.json()["scenario_id"])
    result = asyncio.run(orchestrator.run_design_generation(db_session, building, scenario, job_id=response.json()["job_id"], mode="high_detail"))
    revision = db_session.query(ModelRevision).filter_by(design_scenario_id=scenario.id).one()
    assert revision.document_json["metadata"]["building_plan_id"] == plan["id"]
    assert revision.document_json["metadata"]["elevation_known"] is False
    assert result["planning"]["planning_mode"] == "approved_plan"
    assert scenario.status == "completed"
    assert "wall" in {c["category"] for c in revision.document_json["components"]}


def test_legacy_generation_rejects_injected_plan(client, building):
    response = client.post(f"/api/projects/{building.id}/design/generate", json={"parameters": {"approved_building_plan_id": 1}})
    assert response.status_code == 422


def test_openings_and_missing_boundary_are_rejected(client, db_session, building):
    raw = specification()
    raw["openings"][0]["offset"] = 100
    errors = building_plan.validate_spec(building_plan.BuildingSpec.model_validate(raw), building_plan.context(db_session, building))
    assert any("does not fit" in e for e in errors)
    building.boundary_geojson = None; db_session.commit()
    response = client.post(f"/api/projects/{building.id}/ai/building-plans", json={"prompt": "Build a house"})
    assert response.status_code == 422 and "boundary" in response.text


def test_plan_changed_during_provider_request_is_not_saved(client, db_session, building, monkeypatch):
    async def change_context(*args, **kwargs):
        building.offset_h_m = 12
        db_session.commit()
        return building_plan.BuildingSpec.model_validate(specification())
    monkeypatch.setattr(building_plan, "propose", change_context)
    response = client.post(f"/api/projects/{building.id}/ai/building-plans", json={"prompt": "Build a house"})
    assert response.status_code == 409
    assert db_session.query(BuildingPlan).count() == 0


def test_one_bounded_repair_of_provider_geometry(db_session, sample_boundary, monkeypatch):
    project = Project(id=900, center_lng=77.595, center_lat=12.972, project_type="building", boundary_geojson=sample_boundary)
    ctx = building_plan.context(db_session, project)
    invalid = specification(); invalid["rooms"][1]["x"] = -1
    response = AsyncMock(side_effect=[invalid, specification()])
    monkeypatch.setattr(nebius, "generate_json", response)
    result = asyncio.run(building_plan.propose("Build a house", ctx))
    assert result.rooms[1].x == 0
    assert response.await_count == 2
    assert "validation_errors" in response.call_args.args[1]
    response = AsyncMock(return_value=invalid)
    monkeypatch.setattr(nebius, "generate_json", response)
    with pytest.raises(building_plan.PlanValidationError): asyncio.run(building_plan.propose("Build a house", ctx))
    assert response.await_count == 2


def test_revision_build_preserves_anchor_and_previous_model(client, db_session, building, monkeypatch, tmp_path):
    from app.services import jobs
    from app.services.ai import orchestrator
    monkeypatch.setattr(jobs, "submit_design_generation", lambda **kw: kw["job_id"])
    monkeypatch.setattr(jobs, "_get_redis", lambda: None)
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path))
    scenario = DesignScenario(project_id=building.id, name="Original", status="completed")
    db_session.add(scenario); db_session.flush()
    origin = {"lng": building.center_lng, "lat": building.center_lat, "elevation_m": 10, "heading_deg": 25}
    original = ModelRevision(project_id=building.id, design_scenario_id=scenario.id, revision_number=1,
                             document_json={"origin": origin, "components": []}, source="manual_edit")
    db_session.add(original); db_session.flush()
    placement = ModelPlacement(project_id=building.id, model_revision_id=original.id,
                               anchor_longitude=building.center_lng, anchor_latitude=building.center_lat,
                               anchor_elevation=10, anchor_heading_deg=25, placement_mode="ABSOLUTE", placement_state="VALID")
    db_session.add(placement); db_session.commit()
    url = f"/api/projects/{building.id}/ai/building-plans"
    plan = client.post(url, json={"prompt": "Revise this house", "base_revision_id": original.id})
    assert plan.status_code == 200, plan.text
    response = client.post(f"{url}/{plan.json()['id']}/build", json={"approve": True})
    assert response.status_code == 200, response.text
    next_scenario = db_session.get(DesignScenario, response.json()["scenario_id"])
    asyncio.run(orchestrator.run_design_generation(db_session, building, next_scenario, job_id=response.json()["job_id"], mode="high_detail"))
    new_revision = db_session.query(ModelRevision).filter_by(design_scenario_id=next_scenario.id).one()
    new_placement = db_session.query(ModelPlacement).filter_by(model_revision_id=new_revision.id).one()
    assert new_revision.document_json["origin"] == origin
    assert new_placement.anchor_heading_deg == placement.anchor_heading_deg
    assert new_placement.anchor_elevation == placement.anchor_elevation
    assert new_placement.placement_state == "REVIEW_REQUIRED"
    assert original.document_json == {"origin": origin, "components": []}
    assert db_session.query(ModelRevision).count() == 2


def test_plot_projection_inverts_model_heading():
    from shapely.geometry import mapping, box
    from shapely import affinity
    from shapely.ops import transform
    from pyproj import CRS, Transformer
    origin = {"lng": 77.595, "lat": 12.972, "heading_deg": 37, "elevation_m": None}
    crs = CRS.from_proj4("+proj=aeqd +lat_0=12.972 +lon_0=77.595 +datum=WGS84 +units=m")
    to_geo = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
    local = box(10, 1, 30, 8)
    geographic = transform(to_geo, affinity.rotate(local, 37, origin=(0, 0)))
    restored = building_plan.local_plot({"origin": origin, "boundary": mapping(geographic)})
    assert restored.hausdorff_distance(local) < .001


def test_worker_rejects_context_changed_after_approval(client, db_session, building, monkeypatch):
    from app.services import jobs
    monkeypatch.setattr(jobs, "submit_design_generation", lambda **kw: kw["job_id"])
    url, plan = create(client, building)
    result = client.post(f"{url}/{plan['id']}/build", json={"approve": True}).json()
    scenario = db_session.get(DesignScenario, result["scenario_id"])
    building.offset_h_m = 20; db_session.commit()
    with pytest.raises(ValueError, match="changed after approval"):
        building_plan.approved_for_scenario(db_session, building, scenario, result["job_id"])
    assert db_session.query(ModelRevision).count() == 0
