"""Survey import validation tests."""

import pytest

from app.services.survey.import_pipeline import ingest_gcp_csv
from app.db.models import Project


def test_gcp_csv_invalid_coordinates_raises(db_session):
    project = Project(
        user_id=1,
        name="Survey Test",
        project_type="flyover",
        center_lat=12.9716,
        center_lng=77.5946,
        location_name="Bengaluru",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    bad_csv = b"name,lng,lat\nGCP1,not-a-number,12.97\n"
    with pytest.raises((ValueError, TypeError)):
        ingest_gcp_csv(db_session, project, bad_csv)


def test_survey_import_requires_postgis(client):
    """On SQLite dev mode, survey import should fail safely with 503, not crash."""
    r = client.post(
        "/api/projects",
        json={"name": "Survey Gate", "project_type": "flyover", "location_name": "Test"},
    )
    pid = r.json()["id"]
    files = {"file": ("gcp.csv", b"name,lng,lat\nA,77.59,12.97\n", "text/csv")}
    data = {"format": "gcp_csv", "name": "GCPs"}
    sr = client.post(f"/api/projects/{pid}/survey/import", files=files, data=data)
    # SQLite fallback: 503 PostGIS required; PostGIS env: may succeed
    assert sr.status_code in (200, 201, 503)
    client.delete(f"/api/projects/{pid}")
