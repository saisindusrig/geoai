"""Catalogue extension must preserve legacy creation and prevent false generator support."""
from unittest.mock import patch
import pytest
from app.core.project_catalog import ASSET_DEFINITIONS, LEGACY_PROJECT_TYPES, asset_supports_generation
from app.core.security import get_current_user, get_current_user_id
from app.db.models import User
from app.main import app

@pytest.fixture()
def authenticated_client(client, db_session):
    user = User(id=55555, name="Catalogue QA", email="catalogue-qa@example.test")
    db_session.add(user)
    db_session.commit()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    with patch("app.api.routes.projects.enforce_usage_limit"), patch("app.api.routes.projects.record_usage_event"):
        yield client

@pytest.mark.parametrize("asset_id", sorted(LEGACY_PROJECT_TYPES) + ["custom_asset", "offshore_platform_reference", "highway_bridge"])
def test_catalogue_assets_create_and_roundtrip(authenticated_client, asset_id):
    response = authenticated_client.post("/api/projects", json={"name": "Catalogue project", "project_type": asset_id, "units": "metric"})
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["project_type"] == asset_id
    assert authenticated_client.get(f'/api/projects/{project["id"]}').json()["project_type"] == asset_id
    if asset_id not in LEGACY_PROJECT_TYPES:
        response = authenticated_client.post(f'/api/projects/{project["id"]}/design/generate', json={"parameters": {}})
        assert response.status_code == 422
        assert "site reference" in response.json()["detail"]["message"]

@pytest.mark.parametrize("units", ["metric", "metric_mt", "si", "imperial", "ft_in", "us_customary", "indian"])
def test_existing_unit_values_remain_accepted(authenticated_client, units):
    response = authenticated_client.post("/api/projects", json={"name": "Units", "project_type": "road", "units": units})
    assert response.status_code == 201
    assert response.json()["units"] == units

def test_unknown_identifiers_still_rejected(authenticated_client):
    response = authenticated_client.post("/api/projects", json={"name": "Invalid", "project_type": "not_in_catalogue"})
    assert response.status_code == 422

def test_legacy_generator_support_and_reference_limits():
    assert all(asset_supports_generation(asset_id) for asset_id in LEGACY_PROJECT_TYPES)
    for asset in ASSET_DEFINITIONS.values():
        if asset["maturity"] == "REFERENCE":
            assert not asset_supports_generation(asset["id"])
            assert not any(asset["capabilities"].values())
