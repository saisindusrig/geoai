"""Non-destructive calculations; unknown/stale inputs never imply clearance."""
import math


def clearance_check(*, ground: dict, foundation_bottom_m: float | None, deck_bottom_m: float | None, required_clearance_m: float = 0) -> dict:
    height = ground.get("elevation")
    status = "STALE" if ground.get("status") == "STALE" else "UNKNOWN"
    clearance = None
    if ground.get("status") == "VALID" and height is not None and deck_bottom_m is not None:
        clearance = deck_bottom_m - height
        status = "OK" if clearance >= required_clearance_m else "POTENTIAL CONFLICT"
    return {"status": status, "ground_elevation_m": height, "foundation_bottom_m": foundation_bottom_m,
        "deck_bottom_m": deck_bottom_m, "clearance_m": clearance, "required_clearance_m": required_clearance_m,
        "source": ground.get("source", "NONE"), "terrain_version_id": ground.get("terrain_version_id"),
        "uncertainty": "UNKNOWN", "sample_id": ground.get("id")}


def terrain_difference(before: list[float | None], after: list[float | None], cell_area_m2: float) -> dict:
    if len(before) != len(after) or not math.isfinite(cell_area_m2) or cell_area_m2 <= 0:
        raise ValueError("Equal grids and positive cell area are required")
    differences, missing, changed_coverage = [], 0, 0
    for a, b in zip(before, after):
        valid_a = a is not None and math.isfinite(a)
        valid_b = b is not None and math.isfinite(b)
        if not valid_a or not valid_b:
            differences.append(None)
            missing += 1
            changed_coverage += valid_a != valid_b
        else:
            differences.append(b - a)
    values = [v for v in differences if v is not None]
    return {"differences_m": differences, "min_m": min(values, default=None), "max_m": max(values, default=None),
        "mean_m": sum(values) / len(values) if values else None, "max_absolute_difference_m": max((abs(v) for v in values), default=None),
        "changed_area_m2": sum(v != 0 for v in values) * cell_area_m2, "missing_area_m2": missing * cell_area_m2,
        "changed_coverage_area_m2": changed_coverage * cell_area_m2}


def seam_check(samples: list[dict], threshold_m: float) -> dict:
    if not math.isfinite(threshold_m) or threshold_m < 0:
        raise ValueError("Seam threshold must be non-negative")
    issues = []
    for item in samples:
        a, b = item.get("survey_elevation_m"), item.get("context_elevation_m")
        if a is None or b is None:
            issues.append({**item, "status": "UNKNOWN", "reason": "NoData or missing boundary sample", "difference_m": None})
        elif item.get("survey_vertical_reference") != item.get("context_vertical_reference"):
            issues.append({**item, "status": "WARNING", "reason": "Vertical reference mismatch", "difference_m": None})
        else:
            difference = a - b
            issues.append({**item, "status": "WARNING" if abs(difference) > threshold_m else "VALID", "reason": "Elevation discontinuity" if abs(difference) > threshold_m else None, "difference_m": difference})
    return {"samples": issues, "status": "WARNING" if any(r["status"] == "WARNING" for r in issues) else "UNKNOWN" if any(r["status"] == "UNKNOWN" for r in issues) else "VALID", "survey_geometry_modified": False}


def alignment_profile(stations: list[dict]) -> list[dict]:
    result = []
    previous = None
    for station in stations:
        current = dict(station)
        chainage, proposed, ground = current["chainage_m"], current.get("proposed_elevation_m"), current.get("ground_elevation_m")
        if previous and chainage <= previous["chainage_m"]:
            raise ValueError("Chainage must increase")
        delta = proposed - ground if proposed is not None and ground is not None else None
        current["cut_depth_m"] = max(-delta, 0) if delta is not None else None
        current["fill_depth_m"] = max(delta, 0) if delta is not None else None
        current["grade_percent"] = (proposed - previous["proposed_elevation_m"]) / (chainage - previous["chainage_m"]) * 100 if previous and proposed is not None and previous.get("proposed_elevation_m") is not None else None
        current["uncertainty"] = "UNKNOWN"
        result.append(current)
        previous = current
    return result
