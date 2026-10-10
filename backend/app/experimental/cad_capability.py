"""Server-owned, default-off experimental CAD authorization.

No chat-tool registration and no production generator routing.
"""
import os
from fastapi import HTTPException
from app.api.routes.projects import get_owned_project


def _ids(name):
    try:
        return {int(value.strip()) for value in os.environ.get(name, "").split(",") if value.strip()}
    except ValueError:
        # Malformed deployment configuration denies access.
        return set()


def require_cad(db, project_id, user_id):
    project = get_owned_project(project_id, db, user_id)
    if (os.environ.get("GEOAI_EXPERIMENTAL_CAD", "").lower() != "true"
            or user_id not in _ids("GEOAI_CAD_TEST_USER_IDS")
            or project_id not in _ids("GEOAI_CAD_TEST_PROJECT_IDS")):
        raise HTTPException(403, detail={"code": "CAD_EXPERIMENT_DISABLED", "message": "CAD requires an authorized experimental test project and user."})
    return project
