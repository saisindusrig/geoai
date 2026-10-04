"""Tests for scenario summary, detail, and compare APIs (Phase 5)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import DesignScenario, Project, QuantityEstimate
from app.db.session import SessionLocal
from app.main import app
from app.services.design.scenario_summary import build_scenario_summary, compare_scenarios

client = TestClient(app)


def _seed_scenario(
    db: Session,
    project: Project,
    *,
    name: str,
    params: dict,
    design: dict,
    cost: float = 1_000_000,
    status: str = "completed",
) -> DesignScenario:
    scenario = DesignScenario(
        project_id=project.id,
        name=name,
        input_parameters_json=params,
        design_output_json=design,
        assumptions_json=design.get("assumptions", ["Test assumption"]),
        status=status,
        created_at=datetime.now(timezone.utc),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    db.add(
        QuantityEstimate(
            design_scenario_id=scenario.id,
            concrete_m3=100,
            total_cost_estimate=cost,
            line_items_json=[],
        )
    )
    db.commit()
    return scenario


def _make_design(
    *,
    validation_status: str = "warning",
    score: int = 75,
    geometry_mode: str = "alignment",
    elevation_mode: str = "profile",
    max_grade: float = 5.0,
    cost_medium: float = 1_000_000,
) -> dict:
    return {
        "summary": "Test flyover",
        "assumptions": ["Preliminary only"],
        "geometry": {"length_m": 500, "deck_width_m": 16},
        "geometry_spec": {
            "geometry_mode": geometry_mode,
            "elevation_mode": elevation_mode,
            "max_grade_percent": max_grade,
            "length_m": 500,
        },
        "validation": {
            "validation_status": validation_status,
            "score": score,
            "warnings": [{"code": "test", "message": "Test warning"}],
            "errors": [],
            "recommendations": [],
            "assumptions": [],
        },
        "design_review": {
            "validation_status": validation_status,
            "validation_score": score,
            "geometry_mode": geometry_mode,
            "elevation_mode": elevation_mode,
            "max_grade_percent": max_grade,
            "planning_mode": "template",
            "warnings": ["Test warning"],
            "recommendations": ["Review with engineer"],
        },
        "calculated": {
            "quantities": {"concrete_m3": 100, "steel_kg": 5000},
            "cost_summary": {"total_medium": cost_medium, "currency": "INR"},
        },
    }


def test_list_scenarios_returns_summaries():
    r = client.post("/api/projects", json={"name": "Scenario List Test", "project_type": "flyover"})
    pid = r.json()["id"]
    db = SessionLocal()
    try:
        project = db.get(Project, pid)
        _seed_scenario(
            db,
            project,
            name="Flyover A",
            params={"lanes": 4, "generation_mode": "balanced", "length_m": 500, "deck_width_m": 16},
            design=_make_design(cost_medium=900_000),
        )
    finally:
        db.close()

    lr = client.get(f"/api/projects/{pid}/scenarios")
    assert lr.status_code == 200
    body = lr.json()
    assert "summaries" in body
    assert len(body["summaries"]) >= 1
    summary = body["summaries"][0]
    assert summary["scenario_id"]
    assert summary["validation_score"] == 75
    assert summary["geometry_mode"] == "alignment"
    client.delete(f"/api/projects/{pid}")


def test_scenario_detail_includes_validation_and_review():
    r = client.post("/api/projects", json={"name": "Detail Test", "project_type": "road"})
    pid = r.json()["id"]
    db = SessionLocal()
    try:
        project = db.get(Project, pid)
        scenario = _seed_scenario(
            db,
            project,
            name="Road A",
            params={"lanes": 2, "generation_mode": "balanced", "road_width_m": 7.5, "length_m": 800},
            design=_make_design(geometry_mode="straight", elevation_mode="flat"),
        )
        sid = scenario.id
    finally:
        db.close()

    dr = client.get(f"/api/projects/{pid}/scenarios/{sid}")
    assert dr.status_code == 200
    detail = dr.json()
    assert detail["validation"]["validation_status"] == "warning"
    assert detail["design_review"]["validation_score"] == 75
    assert detail["design_output"] is not None
    client.delete(f"/api/projects/{pid}")


def test_compare_two_scenarios():
    r = client.post("/api/projects", json={"name": "Compare Test", "project_type": "flyover"})
    pid = r.json()["id"]
    db = SessionLocal()
    try:
        project = db.get(Project, pid)
        s1 = _seed_scenario(
            db,
            project,
            name="Cheap",
            params={"lanes": 4, "generation_mode": "balanced"},
            design=_make_design(cost_medium=800_000, score=70),
            cost=800_000,
        )
        s2 = _seed_scenario(
            db,
            project,
            name="Premium",
            params={"lanes": 6, "generation_mode": "high_detail"},
            design=_make_design(cost_medium=1_200_000, score=85),
            cost=1_200_000,
        )
        ids = [s1.id, s2.id]
    finally:
        db.close()

    cr = client.post(f"/api/projects/{pid}/scenarios/compare", json={"scenario_ids": ids})
    assert cr.status_code == 200
    comp = cr.json()
    assert len(comp["rows"]) == 2
    assert comp["best_option_by"]["lowest_cost"] == ids[0]
    assert comp["best_option_by"]["highest_validation_score"] == ids[1]
    assert comp["notes"]
    client.delete(f"/api/projects/{pid}")


def test_compare_rejects_invalid_ids():
    r = client.post("/api/projects", json={"name": "Invalid Compare", "project_type": "flyover"})
    pid = r.json()["id"]
    cr = client.post(f"/api/projects/{pid}/scenarios/compare", json={"scenario_ids": [99999, 99998]})
    assert cr.status_code == 404
    client.delete(f"/api/projects/{pid}")


def test_compare_rejects_more_than_four():
    r = client.post("/api/projects", json={"name": "Too Many Compare", "project_type": "flyover"})
    pid = r.json()["id"]
    cr = client.post(
        f"/api/projects/{pid}/scenarios/compare",
        json={"scenario_ids": [1, 2, 3, 4, 5]},
    )
    assert cr.status_code == 422
    client.delete(f"/api/projects/{pid}")


def test_summaries_handle_missing_boq_gracefully():
    r = client.post("/api/projects", json={"name": "No BOQ", "project_type": "pipeline"})
    pid = r.json()["id"]
    db = SessionLocal()
    try:
        project = db.get(Project, pid)
        scenario = DesignScenario(
            project_id=project.id,
            name="Pending",
            input_parameters_json={"generation_mode": "balanced"},
            design_output_json={"summary": "In progress"},
            status="running",
        )
        db.add(scenario)
        db.commit()
        summary = build_scenario_summary(db, scenario, project)
        assert summary["cost_total"] is None
        assert summary["validation_status"] is None
    finally:
        db.close()
    client.delete(f"/api/projects/{pid}")


def test_format_scenario_name():
    from app.services.design.scenario_summary import format_scenario_name

    name = format_scenario_name(
        "flyover",
        {"lanes": 4, "clearance_m": 5.5},
        "balanced",
        datetime(2026, 6, 14, 18, 30, tzinfo=timezone.utc),
    )
    assert "Flyover" in name
    assert "4 lanes" in name
    assert "Balanced" in name
