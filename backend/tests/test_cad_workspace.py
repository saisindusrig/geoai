"""Approved CAD → real ModelRevision acceptance, isolated project/storage."""
import copy
import pytest
from fastapi import HTTPException
from test_site_workspace import site_db
from test_assistant_runtime import message, approval
from app.db.models import Project, ModelRevision, DesignScenario
from app.services.design.editable_model import geometry_spec_to_document
from app.services.assistant.proposals import ProposalService
from app.experimental.cad_fixtures import support_frame
from app.experimental.cad_workspace import create_review, execute_review
from app.experimental.cad_capability import require_cad


@pytest.fixture
def cad_db(site_db, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.services import storage
    monkeypatch.setenv("GEOAI_EXPERIMENTAL_CAD", "true")
    monkeypatch.setenv("GEOAI_CAD_TEST_USER_IDS", "1")
    monkeypatch.setenv("GEOAI_CAD_TEST_PROJECT_IDS", "1")
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path / "public"))
    monkeypatch.setattr(storage, "_s3_configured", lambda: False)
    base = site_db.get(ModelRevision, 1)
    base.document_json = geometry_spec_to_document(site_db.get(Project,1), site_db.get(DesignScenario,1),
        {"objects":[{"kind":"box","name":"retained","layer":"wall","center":[40,40,1],"size":[1,1,2]}]})
    base.document_json["origin"]["elevation_m"] = None
    site_db.commit()
    return site_db


def review(db, key="cad-first"):
    msg, _ = message(db, "Create an experimental CAD support frame concept.")
    bim, mapping = support_frame()
    return create_review(db, project_id=1, user_id=1, request_id=key, message_id=msg["id"], bim=bim, mapping=mapping)


def test_default_off_and_ownership(cad_db, monkeypatch):
    monkeypatch.delenv("GEOAI_EXPERIMENTAL_CAD")
    with pytest.raises(HTTPException) as blocked:
        require_cad(cad_db, 1, 1)
    assert blocked.value.status_code == 403
    with pytest.raises(HTTPException):
        require_cad(cad_db, 1, 2)


def test_approval_required(cad_db):
    result = review(cad_db)
    with pytest.raises(HTTPException):
        execute_review(cad_db, project_id=1, user_id=1, version_id=result["proposal"]["id"])
    assert cad_db.query(ModelRevision).count() == 1


def test_native_revision_and_idempotency(cad_db):
    result = review(cad_db)
    view = result["proposal"]
    assert len(result["components"]) == 10
    assert next(c for c in result["components"] if c["id"] == "primary-0")["parameters"]["length"] == 5
    previous = copy.deepcopy(cad_db.get(ModelRevision,1).document_json)
    ProposalService().approve(cad_db,1,1,approval(view))
    built = execute_review(cad_db, project_id=1, user_id=1, version_id=view["id"])
    revision = cad_db.get(ModelRevision,built["modelRevisionId"])
    assert len(revision.document_json["components"]) == 11
    assert revision.document_json["components"][0] == previous["components"][0]
    assert len(built["regeneratedComponentIds"]) == 10
    assert execute_review(cad_db, project_id=1, user_id=1, version_id=view["id"]) == built
    assert cad_db.query(ModelRevision).count() == 2
    from app.experimental.cad_artifacts import local_orphans
    assert local_orphans(cad_db,user_id=1,project_id=1)["orphanHashes"] == []


def build(db):
    result = review(db)
    ProposalService().approve(db,1,1,approval(result["proposal"]))
    return execute_review(db, project_id=1, user_id=1, version_id=result["proposal"]["id"])


def test_parameter_regeneration_and_rigid_save(cad_db):
    from app.api.routes.cad_experimental import fixture_review, FixtureInput
    from app.api.routes.model_revisions import persist_revision, RevisionCreate
    from app.db.models import User
    from app.services.assistant.storage import rows
    first = build(cad_db)
    source = cad_db.get(ModelRevision, first["modelRevisionId"])
    document = copy.deepcopy(source.document_json)
    document["components"][1]["transform"]["position"] = [1,2,0]
    document["components"][2]["visible"] = False
    document["components"][5]["transform"]["rotation_deg"] = [0,0,90]
    saved = persist_revision(1,1,RevisionCreate(base_revision_id=source.id,document=document),cad_db,cad_db.get(User,1))
    from test_site_workspace import profile
    profile(cad_db)  # Site dependencies include the saved model; refresh explicitly.
    next_review = fixture_review(1,FixtureInput(request_id="regenerate",scenario_id=1,expected_revision_id=saved["id"],beam_length=6),cad_db,1)
    command = approval(next_review["proposal"]).model_copy(update={"expected_model_revision_id":str(saved["id"])})
    ProposalService().approve(cad_db,1,1,command)
    result = execute_review(cad_db,project_id=1,user_id=1,version_id=next_review["proposal"]["id"])
    assert result["regeneratedComponentIds"] == ["primary-0","primary-1"]
    final = cad_db.get(ModelRevision,result["modelRevisionId"]).document_json
    assert final["components"][1]["transform"] == document["components"][1]["transform"]
    assert final["components"][2]["visible"] is False
    assert final["components"][5]["transform"]["position"] == pytest.approx([2.5,.5,3])
    old = {c["id"]:c for c in document["components"]}
    for component in final["components"][1:]:
        previous = old[component["id"]]
        if component["metadata"]["componentId"] not in result["regeneratedComponentIds"]:
            assert component["geometry"]["mesh_hash"] == previous["geometry"]["mesh_hash"]
            assert component["geometry"]["brep_hash"] == previous["geometry"]["brep_hash"]
    assert len(rows(cad_db,"model_object_lineage",1)) == 30


@pytest.mark.parametrize("failure", ["stale", "worker", "storage"])
def test_atomic_failure(cad_db, monkeypatch, failure):
    result = review(cad_db)
    ProposalService().approve(cad_db,1,1,approval(result["proposal"]))
    compiler = None
    if failure == "stale":
        cad_db.get(Project,1).boundary_geojson = None
        cad_db.commit()
    if failure == "worker":
        def compiler(*args):
            raise RuntimeError("native worker failure")
    if failure == "storage":
        from app.experimental.cad_artifacts import PrivateStore
        monkeypatch.setattr(PrivateStore,"put",lambda *args: (_ for _ in ()).throw(OSError("storage failure")))
    with pytest.raises(Exception):
        execute_review(cad_db,project_id=1,user_id=1,version_id=result["proposal"]["id"],compiler=compiler)
    cad_db.rollback()
    assert cad_db.query(ModelRevision).count() == 1


def test_manual_authority_and_mesh_authorization(cad_db, monkeypatch):
    from app.api.routes.model_revisions import persist_revision, RevisionCreate
    from app.api.routes.cad_experimental import mesh
    from app.db.models import User
    built = build(cad_db)
    revision = cad_db.get(ModelRevision,built["modelRevisionId"])
    document = copy.deepcopy(revision.document_json)
    geometry = document["components"][1]["geometry"]
    with pytest.raises(HTTPException):
        mesh(1,built["catalogId"],geometry["mesh_hash"],cad_db,2)
    document["components"][1]["geometry"] = {"kind":"box","size":[1,1,1]}
    with pytest.raises(HTTPException):
        persist_revision(1,1,RevisionCreate(base_revision_id=revision.id,document=document),cad_db,cad_db.get(User,1))
    cad_db.rollback()
    document = copy.deepcopy(revision.document_json)
    document["components"][1]["transform"]["scale"] = [2,1,1]
    with pytest.raises(HTTPException):
        persist_revision(1,1,RevisionCreate(base_revision_id=revision.id,document=document),cad_db,cad_db.get(User,1))
    cad_db.rollback()
    from app.experimental.cad_artifacts import PrivateStore
    _, path = PrivateStore()._target(1,geometry["mesh_hash"])
    path.write_bytes(b"broken")
    with pytest.raises(ValueError,match="INTEGRITY"):
        mesh(1,built["catalogId"],geometry["mesh_hash"],cad_db,1)
    path.unlink()
    with pytest.raises(FileNotFoundError):
        mesh(1,built["catalogId"],geometry["mesh_hash"],cad_db,1)


def test_rollback_after_revision_flush(cad_db, monkeypatch):
    from app.api.routes import model_revisions
    real = model_revisions.persist_revision
    def failed(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError("database publication failure")
    monkeypatch.setattr(model_revisions,"persist_revision",failed)
    result = review(cad_db)
    ProposalService().approve(cad_db,1,1,approval(result["proposal"]))
    with pytest.raises(RuntimeError,match="publication failure"):
        execute_review(cad_db,project_id=1,user_id=1,version_id=result["proposal"]["id"])
    assert cad_db.query(ModelRevision).count() == 1
    from app.db.models import GeneratedFile
    assert not cad_db.query(GeneratedFile).filter_by(file_type="cad_manifest_v1").all()


def test_manual_revision_during_native_work_is_preserved(cad_db):
    from app.experimental.cad_worker import compile_batch
    from app.api.routes.model_revisions import persist_revision, RevisionCreate
    from app.db.models import User
    result = review(cad_db)
    ProposalService().approve(cad_db,1,1,approval(result["proposal"]))
    def changed(geometry):
        output = compile_batch(geometry)
        document = copy.deepcopy(cad_db.get(ModelRevision,1).document_json)
        document["components"][0]["name"] = "Manual user work wins"
        persist_revision(1,1,RevisionCreate(base_revision_id=1,document=document),cad_db,cad_db.get(User,1))
        return output
    with pytest.raises(HTTPException):
        execute_review(cad_db,project_id=1,user_id=1,version_id=result["proposal"]["id"],compiler=changed)
    assert cad_db.query(ModelRevision).count() == 2
    assert cad_db.query(ModelRevision).order_by(ModelRevision.id.desc()).first().document_json["components"][0]["name"] == "Manual user work wins"
