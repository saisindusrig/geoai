"""Personal folder ownership and project assignment tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import project_folders, projects
from app.db.models import User
from app.db.session import get_db


def _headers(user_id: int) -> dict[str, str]:
    return {"X-Mock-User-Id": str(user_id)}


@pytest.fixture()
def folder_client(db_session):
    """A small API app avoids unrelated demo-asset startup work in this unit suite."""
    test_app = FastAPI()
    test_app.include_router(projects.router)
    test_app.include_router(project_folders.router)

    def _override_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_db
    with TestClient(test_app) as client:
        yield client


def _seed_users(db_session) -> None:
    db_session.add_all(
        [
            User(id=1, name="One", email="one@example.com"),
            User(id=2, name="Two", email="two@example.com"),
        ]
    )
    db_session.commit()


def _create_folder(client, name: str = "Water studies") -> int:
    response = client.post("/api/project-folders", json={"name": name}, headers=_headers(1))
    assert response.status_code == 201
    return response.json()["id"]


def _create_project(client, folder_id: int | None) -> dict:
    response = client.post(
        "/api/projects",
        json={
            "name": "River concept",
            "project_type": "dam",
            "location_name": "River valley",
            "folder_id": folder_id,
        },
        headers=_headers(1),
    )
    assert response.status_code == 201
    return response.json()


def test_folders_are_private_to_their_owner(folder_client, db_session):
    _seed_users(db_session)
    folder_id = _create_folder(folder_client)

    other_list = folder_client.get("/api/project-folders", headers=_headers(2))
    assert other_list.status_code == 200
    assert other_list.json() == []

    other_update = folder_client.put(
        f"/api/project-folders/{folder_id}",
        json={"name": "Not allowed"},
        headers=_headers(2),
    )
    assert other_update.status_code == 404


def test_project_can_be_assigned_and_unassigned_from_a_personal_folder(folder_client, db_session):
    _seed_users(db_session)
    folder_id = _create_folder(folder_client)

    project = _create_project(folder_client, folder_id)
    assert project["folder_id"] == folder_id

    unfiled = folder_client.put(
        f"/api/projects/{project['id']}",
        json={"folder_id": None},
        headers=_headers(1),
    )
    assert unfiled.status_code == 200
    assert unfiled.json()["folder_id"] is None

    foreign_assignment = folder_client.put(
        f"/api/projects/{project['id']}",
        json={"folder_id": folder_id},
        headers=_headers(2),
    )
    assert foreign_assignment.status_code == 404


def test_deleting_folder_leaves_its_projects_unfiled(folder_client, db_session):
    _seed_users(db_session)
    folder_id = _create_folder(folder_client)
    project = _create_project(folder_client, folder_id)

    deleted = folder_client.delete(f"/api/project-folders/{folder_id}", headers=_headers(1))
    assert deleted.status_code == 204

    saved = folder_client.get(f"/api/projects/{project['id']}", headers=_headers(1))
    assert saved.status_code == 200
    assert saved.json()["folder_id"] is None
