import json
import sqlalchemy as sa
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform
from app.domain.stage1 import SelectionVersion
from app.services.assistant.storage import digest, identity, insert, lock_project, now, owned_row, table, error
from app.services.site_profiles.evidence import EvidenceCollector, WGS84


def save_selection(db, project_id, actor_id, request, selection_id=None):
    if request.original_crs.status != "RESOLVED":
        error(422, "REFERENCE_UNRESOLVED", "Resolve the horizontal CRS before saving a canonical selection.")
    lock_project(db, project_id)
    original = request.selection.model_dump(mode="json", by_alias=True)
    geometry = ({"type": "MultiPoint", "coordinates": [original["endpointA"]["coordinates"], original["endpointB"]["coordinates"]]}
                if original["kind"] == "ENDPOINTS" else original["geometry"])
    try:
        transformer = Transformer.from_crs(request.original_crs.definition, "EPSG:4326", always_xy=True)
        def project(x, y):
            return transformer.transform(x, y, errcheck=True)
        canonical = json.loads(json.dumps(mapping(transform(project, shape(geometry)))))
        payload = dict(original)
        for key in ("geometry", "endpointA", "endpointB", "studyArea"):
            if payload.get(key):
                payload[key] = json.loads(json.dumps(mapping(transform(project, shape(payload[key])))))
        lo, la, hi, ha = shape(canonical).bounds
        if not (-180 <= lo <= hi <= 180 and -90 <= la <= ha <= 90):
            raise ValueError("Invalid geographic extent")
    except Exception:
        error(422, "CRS_TRANSFORMATION_FAILED", "Selection cannot be transformed into valid longitude/latitude coordinates.")
    content_hash = digest({"selection": payload, "original": geometry, "crs": request.original_crs.model_dump(mode="json")})
    sid = selection_id or identity("selection", project_id, content_hash)
    t = table("site_selection_versions")
    existing = db.execute(sa.select(t.c.selection_payload).where(t.c.selection_id == sid, t.c.project_id == project_id).order_by(t.c.version.desc())).scalar()
    if existing and existing["contentHash"] == content_hash:
        db.commit()
        return existing
    if selection_id:
        owned_row(db, "site_selections", project_id, sid)
        if not existing or request.expected_version != existing["version"]:
            error(409, "STALE_SELECTION", "Selection changed. Reload before revising it.")
        if existing["selection"]["kind"] != payload["kind"]:
            error(422, "SELECTION_KIND", "Create a new selection when changing its kind.")
    else:
        insert(db, "site_selections", id=sid, project_id=project_id, kind=payload["kind"])
    number = existing["version"] + 1 if existing else 1
    vid = identity(sid, number, content_hash)
    collector = EvidenceCollector(project_id)
    source = collector.add({"kind": "USER_PROVIDED", "sourceRecordId": vid, "actorId": str(actor_id)},
                           {"geometry": geometry}, crs=request.original_crs.model_dump(mode="json", by_alias=True))
    transformed = collector.derived([source], canonical, "crs-transform", {"source": request.original_crs.definition, "target": "EPSG:4326", "alwaysXY": True})
    result = SelectionVersion.model_validate({"id": vid, "selectionId": sid, "projectId": str(project_id), "version": number,
        "selection": payload, "originalCrs": request.original_crs.model_dump(mode="json", by_alias=True), "originalGeometry": geometry,
        "canonicalCrs": "EPSG:4326", "canonicalGeometry": canonical, "transformationEvidenceId": transformed,
        "contentHash": content_hash, "createdBy": str(actor_id), "createdAt": now()}).model_dump(mode="json", by_alias=True)
    collector.persist(db)
    spatial = sa.func.ST_SetSRID(sa.func.ST_GeomFromGeoJSON(json.dumps(canonical)), 4326) if db.get_bind().dialect.name == "postgresql" else canonical
    insert(db, "site_selection_versions", id=vid, project_id=project_id, selection_id=sid, version=number,
           kind=payload["kind"], original_geometry=geometry, original_crs=result["originalCrs"], canonical_geometry=spatial,
           transformation_provenance={"evidenceId": transformed}, selection_payload=result, content_hash=content_hash)
    db.commit()
    return result
