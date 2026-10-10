"""Private CAD publication through existing ownership, GeneratedFile and storage.

No routes registered. Caller runs worker outside request handlers and explicitly
opts into this experimental service. All bytes validate before catalog visibility.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from fastapi import HTTPException
from app.experimental.cad_contract import Geometry, Result, Source, Manifest, digest, encode


class PrivateStore:
    def _target(self, project_id, sha):
        from app.core.config import settings
        from app.services import storage
        # Validate even internal keys; never accept a path from the authored data.
        if type(project_id) is not int or project_id <= 0 or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("INVALID_PRIVATE_KEY")
        key = f"cad-private/v1/{project_id}/{sha}"
        if storage._s3_configured():
            client = storage._get_s3()
            if client is None:
                raise RuntimeError("PRIVATE_S3_UNAVAILABLE")
            return client, key
        public = Path(settings.LOCAL_STORAGE_DIR).resolve()
        private = public.parent / (public.name + "-cad-private")
        return None, private / key

    def put(self, project_id, sha, data):
        if hashlib.sha256(data).hexdigest() != sha:
            raise ValueError("HASH_MISMATCH")
        client, target = self._target(project_id, sha)
        if client:
            from app.core.config import settings
            client.put_object(Bucket=settings.S3_BUCKET, Key=target, Body=data, ContentType="application/octet-stream")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.read_bytes() != data:
                    raise ValueError("IMMUTABLE_ARTIFACT_CONFLICT")
                return
            name = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as staged:
                    name = staged.name
                    staged.write(data)
                    staged.flush()
                    os.fsync(staged.fileno())
                os.replace(name, target)
            finally:
                if name:
                    Path(name).unlink(missing_ok=True)

    def get(self, project_id, sha):
        client, target = self._target(project_id, sha)
        if client:
            from app.core.config import settings
            body = client.get_object(Bucket=settings.S3_BUCKET, Key=target)["Body"]
            try:
                data = body.read(32_000_001)
            finally:
                body.close()
        else:
            if target.stat().st_size > 32_000_000:
                raise ValueError("ARTIFACT_LIMIT")
            data = target.read_bytes()
        if len(data) > 32_000_000 or hashlib.sha256(data).hexdigest() != sha:
            raise ValueError("ARTIFACT_INTEGRITY_FAILURE")
        return data


def owned_source(db, *, user_id, project_id, revision_id, design_id, design_version, source_model_revision_id):
    from app.api.routes.projects import get_owned_project
    from app.db.models import ModelRevision
    get_owned_project(project_id, db, user_id)
    revision = db.query(ModelRevision).filter_by(id=revision_id, project_id=project_id).first()
    if revision is None:
        raise HTTPException(404, "Revision not found")
    return Source(project_id=project_id, revision_id=revision_id, revision_document_hash=digest(revision.document_json),
                  design_id=design_id, design_version=design_version, source_model_revision_id=source_model_revision_id)


def publish(db, *, user_id, geometry, results, blobs, trusted_source, enabled=False, store=None):
    if not enabled:
        raise ValueError("CAD_EXPERIMENT_DISABLED")
    from app.api.routes.projects import get_owned_project
    from app.db.models import ModelRevision, GeneratedFile
    request = Geometry.model_validate(geometry)
    # Trusted context originates in server BIM/proposal lifecycle, never payload.
    if request.source != trusted_source:
        raise ValueError("UNTRUSTED_SOURCE")
    get_owned_project(request.source.project_id, db, user_id)
    revision = db.query(ModelRevision).filter_by(id=request.source.revision_id, project_id=request.source.project_id).first()
    if revision is None or digest(revision.document_json) != request.source.revision_document_hash:
        raise ValueError("STALE_SOURCE_REVISION")
    results = [Result.model_validate(r) for r in results]
    expected = {d.component_id: digest(d) for d in request.definitions}
    if len(results) != len(expected) or {r.component_id: r.definition_hash for r in results} != expected:
        raise ValueError("RESULT_BINDING_MISMATCH")
    artifacts = {a.sha256: a for r in results for a in (r.brep, r.mesh)}
    if set(blobs) != set(artifacts) or sum(len(b) for b in blobs.values()) > 32_000_000:
        raise ValueError("BLOB_MEMBERSHIP_MISMATCH")
    for sha, a in artifacts.items():
        if len(blobs[sha]) != a.byte_length or hashlib.sha256(blobs[sha]).hexdigest() != sha:
            raise ValueError("ARTIFACT_INTEGRITY_FAILURE")
    manifest = Manifest(geometry=request, results=results)
    data = encode(manifest)
    manifest_sha = hashlib.sha256(data).hexdigest()
    store = store or PrivateStore()
    # Storage failure never creates a visible catalog row. Unreferenced blobs can
    # remain; future GC must use committed manifests, not public storage listing.
    for sha, blob in blobs.items():
        store.put(request.source.project_id, sha, blob)
    store.put(request.source.project_id, manifest_sha, data)
    row = GeneratedFile(project_id=request.source.project_id, model_revision_id=request.source.revision_id,
        file_type="cad_manifest_v1", file_url="cad-private:" + manifest_sha,
        metadata_json={"manifestHash": manifest_sha, "sourceHash": digest(request), "schemaVersion": "cad-geometry/1"})
    db.add(row)
    db.flush()  # Publication belongs to caller's existing approval transaction.
    return row


def retrieve(db, *, user_id, project_id, catalog_id, artifact_hash=None, store=None):
    from app.api.routes.projects import get_owned_project
    from app.db.models import GeneratedFile
    get_owned_project(project_id, db, user_id)
    row = db.query(GeneratedFile).filter_by(id=catalog_id, project_id=project_id, file_type="cad_manifest_v1").first()
    if row is None:
        raise HTTPException(404, "CAD artifact not found")
    store = store or PrivateStore()
    raw = store.get(project_id, row.metadata_json["manifestHash"])
    if artifact_hash is None:
        return raw
    manifest = Manifest.model_validate_json(raw)
    allowed = {a.sha256 for r in manifest.results for a in (r.brep, r.mesh)}
    if artifact_hash not in allowed:
        raise HTTPException(404, "CAD artifact not found")
    return store.get(project_id, artifact_hash)


def local_orphans(db, *, user_id, project_id, store=None):
    """Authorized dry-run only. Use a fresh committed session while jobs are idle.

    No automatic deletion: active uploads/retention grace must be accounted for.
    Corrupt/missing committed manifests abort the scan instead of mislabeling data.
    """
    from app.api.routes.projects import get_owned_project
    from app.db.models import GeneratedFile
    get_owned_project(project_id, db, user_id)
    store = store or PrivateStore()
    client, path = store._target(project_id, "0"*64)
    if client is not None:
        raise ValueError("REMOTE_ORPHAN_SCAN_REQUIRES_TESTED_INVENTORY")
    live = set()
    for row in db.query(GeneratedFile).filter(GeneratedFile.project_id == project_id,
            GeneratedFile.file_type.in_(["cad_review_v1", "bim_authoring_review_v1", "bim_authoring_run_v1"])).all():
        sha = row.metadata_json["snapshotHash"]
        store.get(project_id, sha)  # Corruption aborts conservative inventory.
        live.add(sha)
    for row in db.query(GeneratedFile).filter_by(project_id=project_id, file_type="cad_manifest_v1").all():
        sha = row.metadata_json["manifestHash"]
        manifest = Manifest.model_validate_json(store.get(project_id, sha))
        live.add(sha)
        live.update(a.sha256 for r in manifest.results for a in (r.brep, r.mesh))
    files = {p.name for p in path.parent.glob("*") if p.is_file() and len(p.name) == 64 and all(c in "0123456789abcdef" for c in p.name)}
    return {"projectId":project_id, "orphanHashes":sorted(files-live), "deletionEnabled":False}
