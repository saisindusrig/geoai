import pytest
from app.core.project_catalog import ASSET_DEFINITIONS, asset_supports_generation
from app.db.models import Base, Project
from app.services.assistant.decomposition import decompose
from test_asset_catalogue import authenticated_client


def test_name_only_creation_opens_empty_neutral_workspace(authenticated_client,db_session):
    response=authenticated_client.post("/api/projects",json={"name":"  River junction  "})
    assert response.status_code==201,response.text
    project=response.json();pid=project["id"]
    assert project["name"]=="River junction" and project["project_type"]=="unclassified"
    assert project["boundary_geojson"] is None and project["alignment_geojson"] is None
    assert authenticated_client.get(f"/api/projects/{pid}").status_code==200
    assert authenticated_client.get(f"/api/projects/{pid}/workspace-state").json()=={"isEmpty":True}
    assert authenticated_client.get(f"/api/projects/{pid}/scenarios").json()=={"scenarios":[],"summaries":[]}
    assert authenticated_client.get(f"/api/projects/{pid}/composition").json()=={"assets":[],"relationships":[]}
    assert not asset_supports_generation("unclassified")
    assert authenticated_client.post(f"/api/projects/{pid}/design/generate",json={"parameters":{}}).status_code==422


@pytest.mark.parametrize("name",["","   ","x"*256])
def test_invalid_project_names(authenticated_client,name):
    assert authenticated_client.post("/api/projects",json={"name":name}).status_code==422


@pytest.mark.parametrize("kind",["site","asset","scenario"])
def test_starter_disappears_after_project_work(authenticated_client,db_session,kind):
    pid=authenticated_client.post("/api/projects",json={"name":"Empty"}).json()["id"]
    if kind=="site":
        assert authenticated_client.put(f"/api/projects/{pid}",json={"center_lat":0,"center_lng":0}).status_code==200
    else:
        table=Base.metadata.tables["asset_instances" if kind=="asset" else "design_scenarios"]
        values={"id":"a","project_id":pid,"name":"Road","asset_type":"road"} if kind=="asset" else {"project_id":pid,"name":"Existing work"}
        db_session.execute(table.insert().values(**values));db_session.commit()
    assert authenticated_client.get(f"/api/projects/{pid}/workspace-state").json()=={"isEmpty":False}


def test_legacy_project_and_catalogue_remain_intact(authenticated_client,db_session):
    legacy=authenticated_client.post("/api/projects",json={"name":"Existing bridge","project_type":"bridge"}).json()
    authenticated_client.post("/api/projects",json={"name":"New neutral project"})
    assert db_session.get(Project,legacy["id"]).project_type=="bridge"
    assert authenticated_client.get(f"/api/projects/{legacy['id']}").json()["name"]=="Existing bridge"
    assert len(ASSET_DEFINITIONS)==197
    entries=decompose("I need a flyover across this junction with two approach roads and drainage.")
    assert [a["assetFamily"] for a in entries]==["BRIDGE","ROAD","ROAD","DRAINAGE"]


def test_workspace_state_is_owned(authenticated_client,db_session):
    db_session.add(Project(id=999,user_id=1,name="Other",project_type="road"));db_session.commit()
    assert authenticated_client.get("/api/projects/999/workspace-state").status_code==404
