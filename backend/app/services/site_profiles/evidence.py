from app.domain.stage1 import Evidence
from app.services.assistant.storage import digest, identity, insert, now, table

UNKNOWN_CRS = {"status": "UNKNOWN"}
WGS84 = {"status": "RESOLVED", "definition": "EPSG:4326", "axisOrder": "XY", "unit": "DEGREE", "transformId": None}
UNKNOWN_VERTICAL = {"status": "UNKNOWN"}


def vertical_reference(version):
    raw = version.get("vertical_reference_json") if version else None
    if not raw or version.get("vertical_resolution_state") != "RESOLVED" or raw.get("unit") != "METRE":
        return UNKNOWN_VERTICAL
    kind = raw.get("type")
    name = raw.get("datumName") or ("WGS84 ellipsoid" if kind == "ELLIPSOIDAL" else None)
    if kind not in {"ORTHOMETRIC", "ELLIPSOIDAL", "LOCAL_DATUM"} or not name:
        return UNKNOWN_VERTICAL
    return {"status": "RESOLVED", "kind": kind, "identifier": name, "unit": "METRE", "geoidModelVersion": raw.get("geoidModelVersion")}


class EvidenceCollector:
    def __init__(self, project_id):
        self.project_id = project_id
        self.records = {}

    def add(self, source, observation, *, crs=None, vertical=None, status="UNVERIFIED", accuracy=None, dataset_id=None, version_id=None):
        content = {"source": source, "observation": observation, "crs": crs or WGS84,
                   "vertical": vertical or UNKNOWN_VERTICAL, "status": status, "accuracy": accuracy or {},
                   "datasetId": dataset_id, "versionId": version_id}
        content_hash = digest(content)
        eid = identity("evidence", self.project_id, content_hash)
        contract = Evidence.model_validate({"id": eid, "projectId": str(self.project_id), "sourceType": source["kind"],
            "retrievedAt": now(), "horizontalCrs": content["crs"], "verticalReference": content["vertical"],
            "status": status, "accuracy": content["accuracy"], "source": source, "contentHash": content_hash,
            "datasetId": dataset_id, "datasetVersionId": version_id})
        self.records[eid] = {"evidence": contract.model_dump(mode="json", by_alias=True), "observation": observation}
        return eid

    def derived(self, inputs, observation, algorithm="site-derivation", parameters=None):
        return self.add({"kind": "DERIVED", "inputEvidenceIds": inputs, "algorithmId": algorithm,
            "algorithmVersion": "1", "parametersHash": digest(parameters or {}), "outputArtifactId": None}, observation)

    def persist(self, db):
        t = table("site_evidence")
        for eid, payload in self.records.items():
            if not db.execute(t.select().where(t.c.id == eid)).first():
                e = payload["evidence"]
                insert(db, "site_evidence", id=eid, project_id=self.project_id, source_type=e["sourceType"],
                       content_hash=e["contentHash"], payload=payload)


def unknown(fid, reason="NOT_COLLECTED", evidence=(), missing=()):
    return {"id": fid, "sourceKind": "UNKNOWN", "value": None, "reason": reason,
            "evidenceIds": list(evidence), "missingInformationIds": list(missing)}


def known(fid, value, evidence, source="DERIVED", use="CONCEPT"):
    return {"id": fid, "sourceKind": source, "value": value, "evidenceIds": list(evidence),
            "use": use, "verification": "UNVERIFIED"}
