"""Offline CAD integration foundation: native tests opt in independently."""
from copy import deepcopy
import hashlib
import json
import sys
import pytest
from fastapi import HTTPException
from app.experimental.cad_contract import Definition, Geometry, Recipe, Source, digest, encode, from_bim, review_changes
from app.experimental.cad_worker import compile_batch, WorkerFailure
from app.experimental.cad_artifacts import publish, retrieve, PrivateStore, owned_source
from app.experimental.cad_adapter import preview_document, object_id


def source():
    return Source(project_id=101, revision_id=301, revision_document_hash=digest({}), design_id="cad-proof", design_version=1, source_model_revision_id=None)


def geometry():
    d = Definition(component_id="beam", asset_id="frame", assembly_id="assembly", component_type="BEAM",
        material=dict(id="steel", name="Steel", category="STEEL"), recipe=dict(operation="PROFILE_EXTRUSION", profile="I", orientation="HORIZONTAL",
        parameters=dict(width=.3, depth=.5, web=.02, flange=.03, length=5)), placement=dict(origin=[0,0,3]), assembly_placement={},
        dependency_ids=[], relationship_ids=[], provenance=dict(design_id="cad-proof", design_version=1, source_kind="PREVIEW_ASSUMPTION"))
    return Geometry(source=source(), definitions=[d])


def seed(db):
    from app.db.models import User, Project, DesignScenario, ModelRevision
    db.add_all([User(id=1, name="Owner", email="cad@example.test"), User(id=2, name="Other", email="other@example.test"),
                Project(id=101, user_id=1, name="CAD", project_type="bridge"), DesignScenario(id=201, project_id=101, name="Preview"),
                ModelRevision(id=301, project_id=101, design_scenario_id=201, revision_number=1, document_json={}, source="manual_edit")])
    db.commit()


class MemoryStore:
    def __init__(self, fail=False):
        self.data = {}
        self.fail = fail
    def put(self, project, sha, data):
        if self.fail:
            raise OSError("storage offline")
        assert hashlib.sha256(data).hexdigest() == sha
        self.data[project, sha] = data
    def get(self, project, sha):
        return self.data[project, sha]


def fake_result(g):
    from app.experimental.cad_contract import Result
    a = b"test fixture brep"
    b = encode(dict(positions=[[0,0,0],[1,0,0],[0,1,0]], triangles=[[0,1,2]], units="m"))
    sha_a, sha_b = hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest()
    r = Result(component_id="beam", definition_hash=digest(g.definitions[0]),
        brep=dict(sha256=sha_a, byte_length=len(a), kind="BREP"), mesh=dict(sha256=sha_b, byte_length=len(b), kind="MESH"),
        dimensions_m=[5,.3,.5], bounds_m=[0,0,0,5,.3,.5], volume_m3=.134)
    return [r], {sha_a:a, sha_b:b}


def test_contract_roundtrip_no_box_and_hash():
    g = geometry()
    assert Geometry.model_validate_json(encode(g)) == g
    assert b"BOX" not in encode(g)
    assert digest(g) == digest(json.loads(encode(g)))
    assert object_id(101,"frame","beam") == object_id(101,"frame","beam")
    assert object_id(102,"frame","beam") != object_id(101,"frame","beam")
    assert object_id(101,"a:b","c") != object_id(101,"a","b:c")


@pytest.mark.parametrize("patch", [{"code":"import os"}, {"filePath":"../../x"}, {"units":"mm"}, {"version":"cad-recipe/2"}, {"parameters":{"length":float("nan")}}, {"parameters":{"width":.3,"depth":.5,"web":.4,"flange":.03,"length":5}}, {"parameters":{"width":.3,"depth":.5,"web":.02,"flange":.03,"length":501}}])
def test_invalid_recipe(patch):
    raw = geometry().definitions[0].recipe.model_dump()
    raw.update(patch)
    with pytest.raises(ValueError):
        Recipe.model_validate(raw)


def test_source_spoof_and_duplicate():
    raw = geometry().model_dump()
    raw["source"]["design_version"] = 2
    with pytest.raises(ValueError, match="SOURCE_BINDING"):
        Geometry.model_validate(raw)
    raw = geometry().model_dump()
    raw["definitions"] *= 2
    with pytest.raises(ValueError, match="DUPLICATE"):
        Geometry.model_validate(raw)


def test_owned_source_and_private_publication(db_session):
    seed(db_session)
    context = owned_source(db_session, user_id=1, project_id=101, revision_id=301, design_id="cad-proof", design_version=1, source_model_revision_id=None)
    assert context == source()
    with pytest.raises(HTTPException):
        owned_source(db_session, user_id=2, project_id=101, revision_id=301, design_id="cad-proof", design_version=1, source_model_revision_id=None)
    g, store = geometry(), MemoryStore()
    results, blobs = fake_result(g)
    row = publish(db_session,user_id=1,geometry=g,results=results,blobs=blobs,trusted_source=context,enabled=True,store=store)
    db_session.commit()
    assert json.loads(retrieve(db_session,user_id=1,project_id=101,catalog_id=row.id,store=store))["geometry"]["source"]["revisionId"] == 301
    assert retrieve(db_session,user_id=1,project_id=101,catalog_id=row.id,artifact_hash=results[0].brep.sha256,store=store) == next(iter(blobs.values()))
    with pytest.raises(HTTPException):
        retrieve(db_session,user_id=2,project_id=101,catalog_id=row.id,store=store)
    with pytest.raises(HTTPException):
        retrieve(db_session,user_id=1,project_id=101,catalog_id=row.id,artifact_hash="../private",store=store)


@pytest.mark.parametrize("failure", ["gate", "trust", "hash", "storage", "stale"])
def test_atomic_publication_failures(db_session, failure):
    from app.db.models import GeneratedFile
    seed(db_session)
    g = geometry()
    r,b = fake_result(g)
    trusted = source()
    if failure == "trust":
        trusted = trusted.model_copy(update={"project_id":999})
    if failure == "hash":
        b[next(iter(b))] = b"tampered"
    if failure == "stale":
        from app.db.models import ModelRevision
        db_session.get(ModelRevision,301).document_json = {"changed":True}
    with pytest.raises((ValueError,OSError)):
        publish(db_session,user_id=1,geometry=g,results=r,blobs=b,trusted_source=trusted,enabled=failure!="gate",store=MemoryStore(failure=="storage"))
    assert db_session.query(GeneratedFile).count() == 0


def test_private_files_not_public_and_integrity(tmp_path, monkeypatch):
    from app.core.config import settings
    from app.services import storage
    monkeypatch.setattr(settings,"LOCAL_STORAGE_DIR",str(tmp_path/"public"))
    monkeypatch.setattr(storage,"_s3_configured",lambda:False)
    s = PrivateStore()
    data = b"solid"
    sha = hashlib.sha256(data).hexdigest()
    s.put(101,sha,data)
    s.put(101,sha,data)
    assert s.get(101,sha) == data and not (tmp_path/"public").exists()
    with pytest.raises(ValueError):
        s.get(101,"../../secret")
    target = s._target(101,sha)[1]
    target.write_bytes(b"bad")
    with pytest.raises(ValueError,match="INTEGRITY"):
        s.get(101,sha)


@pytest.mark.parametrize("mode", ["timeout", "crash", "cancel", "output"])
def test_worker_failures(mode, monkeypatch):
    from app.experimental import cad_worker
    codes = {"timeout":"import sys,time; sys.stdin.buffer.read(); time.sleep(2)", "crash":"import sys; sys.stdin.buffer.read(); sys.exit(7)", "cancel":"import time; time.sleep(2)", "output":"import sys; sys.stdin.buffer.read(); print('{}')"}
    monkeypatch.setattr(cad_worker,"_command",lambda root:[sys.executable,"-c",codes[mode]])
    with pytest.raises(WorkerFailure):
        compile_batch(geometry(),timeout_s=.2,cancelled=lambda:mode=="cancel")


def test_adapter_preserves_unrelated_and_source():
    g = geometry()
    r,_ = fake_result(g)
    original = {"components":[{"id":"unrelated","geometry":{"kind":"box"}}]}
    candidate = preview_document(original,g,r,catalog_id=7)
    assert original == {"components":[{"id":"unrelated","geometry":{"kind":"box"}}]}
    assert candidate["components"][0] == original["components"][0]
    item = candidate["components"][1]
    sha = item["source"]["definitionHash"]
    item["transform"]["position"] = [1,2,3]
    assert item["source"]["definitionHash"] == sha
    assert "positions" not in encode(candidate).decode()
    assert json.loads(encode(candidate))["components"][1]["componentId"] == "beam"
    reloaded = preview_document(candidate,g,r,catalog_id=8)
    assert reloaded["components"][1]["transform"]["position"] == [1,2,3]


def test_native_regeneration_review_cache_and_mesh():
    pytest.importorskip("OCP")
    from app.experimental.cad_fixtures import support_frame
    from app.services.assistant.bim_foundation import propagate_parameters
    model,mapping = support_frame()
    g = from_bim(model,mapping,source=source())
    results,blobs = compile_batch(g)
    assert len(results) == 10
    assert all(r.geometry_valid and r.solid_count == 1 for r in results)
    for r in results:
        assert hashlib.sha256(blobs[r.brep.sha256]).hexdigest() == r.brep.sha256
        assert json.loads(blobs[r.mesh.sha256])["units"] == "m"
    updated,dirty = propagate_parameters(model,{("primary-0","length"):6},expected_design_version=1)
    after = from_bim(updated,mapping,source=source())
    next_results,_ = compile_batch(after)
    assert dirty == ["primary-0","primary-1"]
    assert review_changes(g,after)["status"] == "REVIEW_REQUIRED"
    old = {r.component_id:r for r in results}
    for r in next_results:
        if r.component_id in dirty:
            assert r.definition_hash != old[r.component_id].definition_hash
            assert r.dimensions_m[0] == pytest.approx(6)
            assert r.volume_m3 == pytest.approx(.1608)
        else:
            assert r == old[r.component_id]
    # Legacy BOX changes cannot influence authoritative CAD definitions.
    raw = model.model_dump()
    raw["components"][0]["geometry"]["primitive"]["size"] = [9,9,9]
    from app.domain.bim import BIMProject
    assert from_bim(BIMProject.model_validate(raw),mapping,source=source()) == g


def test_connections_require_review():
    g = geometry()
    support = g.definitions[0].model_copy(update={"component_id":"support","component_type":"COLUMN"})
    raw = g.model_dump()
    raw["definitions"].append(support.model_dump())
    raw["connections"] = [dict(id="joint",from_component_id="beam",to_component_id="support",kind="SUPPORTED_BY")]
    for d in raw["definitions"]:
        d["relationship_ids"] = ["joint"]
    before = Geometry.model_validate(raw)
    raw["definitions"][0]["recipe"]["parameters"]["length"] = 6
    after = Geometry.model_validate(raw)
    report = review_changes(before,after)
    assert any(i.get("connectionId") == "joint" for i in report["issues"])
    assert after.definitions[1] == before.definitions[1]


def test_memory_limit_kills_worker(monkeypatch):
    from app.experimental import cad_worker
    # Exhaust a 64 MiB process limit, not host memory. Child catches no exception.
    code = "import sys; sys.stdin.buffer.read(); blocks=[]\nwhile True: blocks.append(bytearray(16*1024*1024))"
    monkeypatch.setattr(cad_worker,"_command",lambda root:[sys.executable,"-c",code])
    with pytest.raises(WorkerFailure,match="WORKER_CRASH"):
        compile_batch(geometry(),memory_mb=64,timeout_s=5)


def test_cache_revision_binding_and_dependency_cycle():
    from app.experimental.cad_contract import cache_key
    g = geometry()
    raw = g.model_dump()
    raw["source"]["revision_id"] = 302
    assert cache_key(Geometry.model_validate(raw)) != cache_key(g)
    raw = g.model_dump()
    raw["dependencies"] = [dict(id="loop",source_component_id="beam",target_component_id="beam",source_parameter_id="length",target_parameter_id="length",operation="COPY")]
    raw["definitions"][0]["dependency_ids"] = ["loop"]
    with pytest.raises(ValueError,match="CYCLE"):
        Geometry.model_validate(raw)


def test_private_s3_failure_never_falls_back(tmp_path,monkeypatch):
    from app.services import storage
    from app.core.config import settings
    monkeypatch.setattr(settings,"LOCAL_STORAGE_DIR",str(tmp_path/"public"))
    monkeypatch.setattr(storage,"_s3_configured",lambda:True)
    monkeypatch.setattr(storage,"_get_s3",lambda:None)
    with pytest.raises(RuntimeError,match="PRIVATE_S3_UNAVAILABLE"):
        PrivateStore().put(101,hashlib.sha256(b"x").hexdigest(),b"x")
    assert not list(tmp_path.iterdir())
