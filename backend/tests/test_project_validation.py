"""Tests for project validation service."""

from app.services.project_validation import validate_project
from app.db.models import Project


def test_validation_missing_boundary(db_session):
    project = Project(
        user_id=1,
        name="Incomplete",
        project_type="flyover",
        center_lat=12.97,
        center_lng=77.59,
        location_name="Test",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    result = validate_project(db_session, project)
    assert result["ready_for_design"] is False
    boundary_check = next(c for c in result["checks"] if c["id"] == "boundary")
    assert boundary_check["passed"] is False
    assert "boundary" in boundary_check["detail"].lower()


def test_validation_complete_flyover(db_session, sample_boundary, sample_alignment):
    project = Project(
        user_id=1,
        name="Complete Flyover",
        project_type="flyover",
        center_lat=12.9716,
        center_lng=77.5946,
        location_name="Bengaluru",
        boundary_geojson=sample_boundary,
        alignment_geojson=sample_alignment,
        accuracy_tier="visual",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    result = validate_project(db_session, project)
    assert result["ready_for_design"] is True
    assert result["boundary_area_sqm"] and result["boundary_area_sqm"] > 0
    assert result["alignment_length_m"] and result["alignment_length_m"] > 0
    assert result["engineering_crs_epsg"] is not None
