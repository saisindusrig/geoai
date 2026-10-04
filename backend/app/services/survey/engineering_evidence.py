"""Evidence-based readiness. Imagery resolution is never accuracy evidence."""
from __future__ import annotations

import math
from datetime import datetime, timezone


def checkpoint_statistics(points: list[dict]) -> dict:
    """Independent, same-reference XYZ observations only; preserve bad records."""
    residuals = []
    for point in points:
        row = {"checkpoint_id": point.get("id"), "status": "INVALID", "reason": None}
        if point.get("role") != "VALIDATION_CHECKPOINT":
            row.update(status="EXCLUDED", reason="ADJUSTMENT_CONTROL")
        elif point.get("excluded"):
            row.update(status="EXCLUDED", reason=point.get("exclusion_reason") or "Explicit exclusion")
        elif not point.get("same_reference"):
            row["reason"] = "CRS_OR_VERTICAL_REFERENCE_UNRESOLVED"
        else:
            observed, reference = point.get("observed", []), point.get("reference", [])
            if len(observed) != 3 or len(reference) != 3 or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in [*observed, *reference]):
                row["reason"] = "MISSING_OR_INVALID_XYZ"
            else:
                de, dn, dz = [observed[i] - reference[i] for i in range(3)]
                row.update(status="VALID", delta_e_m=de, delta_n_m=dn, delta_z_m=dz, horizontal_residual_m=math.hypot(de, dn))
        residuals.append(row)
    valid = [r for r in residuals if r["status"] == "VALID"]
    count = len(valid)
    return {
        "total_count": len(points), "valid_count": count,
        "invalid_count": sum(r["status"] == "INVALID" for r in residuals),
        "excluded_count": sum(r["status"] == "EXCLUDED" for r in residuals),
        "horizontal_rmse_m": math.sqrt(sum(r["delta_e_m"] ** 2 + r["delta_n_m"] ** 2 for r in valid) / count) if count else None,
        "vertical_rmse_m": math.sqrt(sum(r["delta_z_m"] ** 2 for r in valid) / count) if count else None,
        "max_horizontal_error_m": max((r["horizontal_residual_m"] for r in valid), default=None),
        "max_vertical_error_m": max((abs(r["delta_z_m"]) for r in valid), default=None),
        "residuals": residuals,
    }


def readiness(evidence: dict) -> str:
    if evidence.get("blocked"):
        return "BLOCKED"
    if not evidence.get("terrain_available"):
        return "VISUAL_REFERENCE" if evidence.get("imagery_available") else "UNCONFIGURED"
    if not all(evidence.get(k) for k in ("horizontal_crs_resolved", "vertical_reference_resolved", "units_resolved", "coverage_verified")):
        return "VISUAL_REFERENCE"
    if not evidence.get("survey_authoritative") or evidence.get("validation_status") != "VALID":
        return "SPATIAL_READY"
    stats = evidence.get("checkpoint_statistics", {})
    if stats.get("valid_count", 0) < 3 or stats.get("invalid_count", 0) or stats.get("horizontal_rmse_m") is None or stats.get("vertical_rmse_m") is None:
        return "SPATIAL_READY"
    if stats["horizontal_rmse_m"] > evidence.get("horizontal_limit_m", 0.05) or stats["vertical_rmse_m"] > evidence.get("vertical_limit_m", 0.1):
        return "SPATIAL_READY"
    return "ENGINEERING_READY" if evidence.get("engineering_checks_valid") else "SURVEY_READY"


def sample_result(*, longitude: float, latitude: float, height: float | None, source="NONE", dataset_id=None, version_id=None, vertical_reference=None, failure_reason=None) -> dict:
    if not math.isfinite(longitude) or not -180 <= longitude <= 180 or not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Invalid geographic coordinates")
    known = height is not None and math.isfinite(height) and source != "NONE" and vertical_reference is not None
    return {"longitude": longitude, "latitude": latitude, "elevation": height if known else None,
            "source": source if known else "NONE", "status": "VALID" if known else "FAILED",
            "terrain_dataset_id": dataset_id, "terrain_version_id": version_id,
            "vertical_reference": vertical_reference, "horizontal_crs": "EPSG:4326", "unit": "METRE",
            "sampled_at": datetime.now(timezone.utc).isoformat(), "calculation_version": "ground-sample/1",
            "failure_reason": None if known else failure_reason or "Terrain elevation unavailable"}
