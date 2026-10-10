"""Opt-in real workspace acceptance server with isolated SQLite/private storage.

Never opens the ordinary development database or creates live AI/cloud clients.
Run from backend; point the existing frontend at http://127.0.0.1:8001.
"""
import os
from pathlib import Path
import sys
import argparse
import re
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root = Path(__file__).resolve().parents[1] / ".cad-proof-output" / "workspace-acceptance"
root.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument("--run-id", default="workspace")
run_id = parser.parse_args().run_id
if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", run_id):
    raise ValueError("Invalid isolated acceptance run identity")
os.environ.update(DATABASE_URL="sqlite:///" + str(root / (run_id + ".db")), LOCAL_STORAGE_DIR=str(root / "public"),
    GEOAI_EXPERIMENTAL_CAD="true", GEOAI_CAD_TEST_USER_IDS="1", GEOAI_CAD_TEST_PROJECT_IDS="9001",
    CORS_ALLOWED_ORIGINS="http://localhost:3001,http://127.0.0.1:3001", AUTH_REQUIRE_JWT="false")

import httpx
sync_send, async_send = httpx.Client.send, httpx.AsyncClient.send


def guarded_sync(self, request, *args, **kwargs):
    if "nebius" in request.url.host.lower():
        raise RuntimeError("LIVE_NEBIUS_FORBIDDEN")
    return sync_send(self, request, *args, **kwargs)


async def guarded_async(self, request, *args, **kwargs):
    if "nebius" in request.url.host.lower():
        raise RuntimeError("LIVE_NEBIUS_FORBIDDEN")
    return await async_send(self, request, *args, **kwargs)


httpx.Client.send, httpx.AsyncClient.send = guarded_sync, guarded_async
from app.services import storage
storage._get_s3 = lambda: None
storage._s3_configured = lambda: False
from app.db.init_db import init_db
from app.db.models import Base
from app.db.session import engine
Base.metadata.create_all(engine)  # Isolated acceptance database only.
init_db()
from app.db.session import SessionLocal
from app.db.models import Project, DesignScenario, User
from app.api.routes.model_revisions import persist_revision, RevisionCreate
from app.services.design.editable_model import geometry_spec_to_document
from app.domain.site_workspace import SelectionInput
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService
from app.services.site_profiles.evidence import WGS84
with SessionLocal() as db:
    area = {"type":"Polygon", "coordinates":[[[77,12],[77.002,12],[77.002,12.001],[77,12.001],[77,12]]]}
    if not db.get(Project,9001):
        area = {"type":"Polygon", "coordinates":[[[77,12],[77.002,12],[77.002,12.001],[77,12.001],[77,12]]]}
        project = Project(id=9001,user_id=1,name="CAD isolated workspace acceptance",project_type="building",boundary_geojson=area,center_lat=12,center_lng=77,origin_lat=12,origin_lng=77)
        scenario = DesignScenario(id=9001,project_id=9001,name="Experimental SUPPORT_FRAME",status="completed")
        db.add(project); db.flush(); db.add(scenario); db.flush()
        document = geometry_spec_to_document(project,scenario,{"objects":[{"kind":"box","name":"retained-existing-object","layer":"wall","center":[15,15,1],"size":[1,1,2]}]})
        document["origin"]["elevation_m"] = None
        persist_revision(9001,9001,RevisionCreate(document=document),db,db.get(User,1))
    from app.services.assistant.storage import rows
    if not rows(db,"site_profiles",9001):
        selection = save_selection(db,9001,1,SelectionInput(selection={"kind":"AREA","geometry":area},original_crs=WGS84))
        service = SiteProfileService()
        prepared,_ = service.prepare(db,9001,1,selection["id"])
        service.build(db,9001,prepared["id"],prepared["jobId"])

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    uvicorn.run(app,host="127.0.0.1",port=8001)
