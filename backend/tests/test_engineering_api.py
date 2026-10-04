from app.db.models import (User, Project, DesignScenario, ModelRevision, TerrainDataset, TerrainDatasetVersion,
    ActiveTerrainConfiguration, GroundSample, ModelPlacement, EngineeringAnalysis)
from app.services.survey.terrain_activation import activate_terrain


def seed(db):
    db.add_all([User(id=1, name="Owner", email="owner@test.com"), User(id=2, name="Other", email="other@test.com"),
        Project(id=10, user_id=1, name="Site", project_type="bridge"),
        Project(id=20, user_id=2, name="Other", project_type="bridge"),
        DesignScenario(id=11, project_id=10, name="Design"),
        ModelRevision(id=12, project_id=10, design_scenario_id=11, revision_number=1, document_json={}),
        TerrainDataset(id=13, project_id=10, name="Survey")])
    db.flush()
    for id, number in [(14, 1), (15, 2)]:
        db.add(TerrainDatasetVersion(id=id, project_id=10, terrain_dataset_id=13, version=number, processing_state="READY",
            horizontal_crs_type="PROJECTED", horizontal_crs_code="EPSG:32643", source_unit="METRE", vertical_resolution_state="RESOLVED",
            vertical_reference_json={"type": "ELLIPSOIDAL"}, coverage_geojson={"type": "Polygon", "coordinates": [[[77,12],[78,12],[78,13],[77,12]]]}, cesium_ion_asset_id=123))
    db.commit()


def test_checkpoints_independent_and_owned(client, db_session):
    seed(db_session)
    base = "/api/projects/10/engineering"
    ids = []
    for i in range(3):
        response = client.post(base + "/control-points", json={"name": str(i), "role": "VALIDATION_CHECKPOINT", "coordinates": [0,0,100], "horizontal_crs": "EPSG:32643", "vertical_reference": "WGS84"})
        assert response.status_code == 200, response.text
        ids.append(response.json()["id"])
    observations = [{"checkpoint_id": id, "observed": [.01,.02,100.03], "horizontal_crs": "EPSG:32643", "vertical_reference": "WGS84"} for id in ids]
    response = client.post(base + "/validation-runs", json={"terrain_version_id": 14, "checkpoints": observations})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "VALID"
    assert client.get(base + "/evidence", headers={"X-Mock-User-Id": "2"}).status_code == 404
    observations[0]["vertical_reference"] = "ORTHOMETRIC"
    response = client.post(base + "/validation-runs", json={"terrain_version_id": 14, "checkpoints": observations})
    assert response.json()["status"] == "WARNING"
    assert response.json()["invalid_count"] == 1


def test_terrain_change_preserves_absolute_and_ground_coordinates(db_session):
    seed(db_session)
    db_session.add(ActiveTerrainConfiguration(project_id=10, terrain_dataset_id=13, terrain_version_id=14, revision=1))
    db_session.add(ModelPlacement(id=30, project_id=10, model_revision_id=12, placement_mode="ABSOLUTE", placement_state="VALID", anchor_longitude=77, anchor_latitude=12, anchor_elevation=150, terrain_dataset_id=13, terrain_version_id=14))
    db_session.add(GroundSample(id=31, project_id=10, placement_id=30, longitude=77, latitude=12, elevation=100, status="VALID", source="SURVEY_TERRAIN", terrain_dataset_id=13, terrain_version_id=14))
    db_session.add(EngineeringAnalysis(project_id=10, terrain_version_id=14, analysis_type="CLEARANCE", algorithm_version="1", status="VALID", result_json={"clearance": 50}, actor_user_id=1))
    db_session.commit()
    activate_terrain(db_session, project_id=10, dataset_id=13, version_id=15, actor_user_id=1)
    placement = db_session.get(ModelPlacement, 30)
    assert placement.anchor_elevation == 150 and placement.placement_state == "VALID"
    db_session.expire_all()
    assert db_session.get(GroundSample, 31).status == "STALE"
    assert db_session.query(EngineeringAnalysis).first().status == "STALE"
    placement.placement_mode = "GROUND_RELATIVE"
    activate_terrain(db_session, project_id=10, dataset_id=13, version_id=14, actor_user_id=1)
    assert placement.anchor_elevation == 150 and placement.placement_state == "REVIEW_REQUIRED"


def test_placement_requires_valid_sample_and_preserves_model_geometry(client, db_session):
    seed(db_session)
    base = "/api/projects/10/engineering/placements/12"
    payload = dict(placement_mode="GROUND_RELATIVE", longitude=77, latitude=12, elevation=100, vertical_reference={"type": "ELLIPSOIDAL"})
    assert client.put(base, json=payload).status_code == 422
    payload["placement_mode"] = "ABSOLUTE"
    assert client.put(base, json=payload).status_code == 200
    assert db_session.get(ModelRevision, 12).document_json == {}
    assert client.get(base, headers={"X-Mock-User-Id": "2"}).status_code == 404


def test_sqlite_sample_is_unknown_and_provenance_owned(client, db_session):
    seed(db_session)
    base = "/api/projects/10/engineering"
    response = client.post(base + "/ground-samples", json={"longitude": 77, "latitude": 12})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["elevation"] is None and result["source"] == "NONE"
    assert "PostGIS" in result["failure_reason"]
    assert client.get(base + f'/ground-samples/{result["id"]}').json()["elevation"] is None
    assert client.get(base + f'/ground-samples/{result["id"]}', headers={"X-Mock-User-Id": "2"}).status_code == 404


def test_version_creation_does_not_overwrite_earlier_evidence(client, db_session):
    seed(db_session)
    payload = dict(horizontal_crs_code="EPSG:4326", vertical_reference="ORTHOMETRIC", datum_name="Local survey datum", unit="METRE",
        coverage_geojson={"type": "Polygon", "coordinates": [[[77,12],[78,12],[78,13],[77,12]]]}, cesium_ion_asset_id=123, source="Licensed survey", capture_date="2026-10-01")
    response = client.post("/api/projects/10/engineering/terrain-datasets/13/versions", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "METADATA_REQUIRED"
    assert db_session.get(TerrainDatasetVersion, 14).version == 1
    assert db_session.get(TerrainDatasetVersion, 14).vertical_reference_json == {"type": "ELLIPSOIDAL"}
    payload["coverage_geojson"]["coordinates"][0][-1] = [0,0]
    assert client.post("/api/projects/10/engineering/terrain-datasets/13/versions", json=payload).status_code == 422


def test_preferences_utc_timezone_camera_and_exports_are_owned(client, db_session):
    seed(db_session)
    base = "/api/projects/10/engineering"
    preferences = {"preset":"SUN_STUDY","quality":"BALANCED","shadows":"HIGH","utc":"2026-06-21T12:00:00+05:30","timeZone":"Asia/Kolkata"}
    response = client.put(base + "/map-preferences", json=preferences)
    assert response.status_code == 200, response.text
    saved = client.get(base + "/map-preferences").json()["preferences"]
    assert saved["utc"] == "2026-06-21T06:30:00+00:00"
    assert saved["timeZone"] == "Asia/Kolkata"
    preferences["timeZone"] = "Invalid/Zone"
    assert client.put(base + "/map-preferences", json=preferences).status_code == 422
    camera = dict(name="SITE", position=[1,2,3], heading=0,pitch=-1,roll=0,projection="PERSPECTIVE")
    assert client.post(base + "/camera-views", json=camera).status_code == 200
    assert client.get(base + "/camera-views").json()[0]["position"] == [1,2,3]
    manifest = client.get(base + "/revisions/12/spatial-manifest")
    assert manifest.status_code == 200 and manifest.json()["local_axis_convention"] == "EAST_NORTH_UP"
    assert manifest.json()["placement"] is None
    assert client.get(base + "/revisions/12/spatial-manifest", headers={"X-Mock-User-Id":"2"}).status_code == 404
    assert client.get(base + "/log").json()[0]["action"] == "export.spatial_manifest"


def test_sqlite_profile_does_not_masquerade_as_authoritative(client, db_session):
    seed(db_session)
    response = client.post("/api/projects/10/engineering/analyses/profile", json={"model_revision_id":12})
    assert response.status_code == 503
    assert "PostGIS" in response.text


def test_project_delete_preserves_engineering_evidence(client, db_session):
    seed(db_session)
    response = client.delete("/api/projects/10")
    assert response.status_code == 409
    assert db_session.get(Project, 10) is not None
    assert db_session.get(TerrainDatasetVersion, 14) is not None
