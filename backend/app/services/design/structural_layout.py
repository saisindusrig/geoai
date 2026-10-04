"""Rule checks and decision summaries for georeferenced structural layouts.

These checks are deliberately transparent, project-preset based screening checks.
They are not a substitute for licensed structural design verification.
"""
from __future__ import annotations

from math import hypot, isfinite
from typing import Any

DEFAULT_PRESET = {
    "min_member_spacing_m": 1.0,
    "max_slope_percent": 12.0,
    "min_clearance_m": 3.0,
    "max_dimension_m": 500.0,
}


def _position(component: dict[str, Any]) -> list[float]:
    return list(component.get("transform", {}).get("position", [0, 0, 0]))


def validate_layout(document: dict[str, Any]) -> dict[str, Any]:
    layout = document.get("structural_layout") or {}
    if not isinstance(layout, dict) or not isinstance(layout.get("rule_preset", {}), dict):
        return {"passed": False, "preset": DEFAULT_PRESET, "violations": [{"rule": "invalid_preset", "message": "Rule preset must be an object.", "action": "Restore a valid project preset."}], "disclaimer": "Project rule screening only."}
    preset = {**DEFAULT_PRESET, **layout.get("rule_preset", {})}
    components = document.get("components", [])
    violations: list[dict[str, Any]] = []
    for key, value in preset.items():
        if key not in DEFAULT_PRESET or not isinstance(value, (float, int)) or isinstance(value, bool) or not isfinite(value) or value < 0:
            violations.append({"rule": "invalid_preset", "message": f"Invalid preset value: {key}", "action": "Enter a finite, non-negative rule value."})
    if violations:
        return {"passed": False, "preset": preset, "violations": violations, "disclaimer": "Project rule screening only."}
    for component in components:
        geometry = component.get("geometry", {})
        scale = component.get("transform", {}).get("scale", [1, 1, 1])
        vectors = [scale, component.get("transform", {}).get("position", [0, 0, 0])]
        if geometry.get("kind") in {"box", "extrusion"}:
            vectors.append(geometry.get("size", []))
        if any(not isinstance(vector, list) or len(vector) != 3 or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v) for v in vector) for vector in vectors):
            violations.append({"rule": "invalid_geometry", "component_id": component.get("id"), "message": "Component coordinates and dimensions must be finite numbers.", "action": "Correct the component geometry in Inspect."})
            continue
        size = [abs(v * scale[i]) for i, v in enumerate(geometry.get("size") or [])]
        if size and max(size) > float(preset["max_dimension_m"]):
            violations.append({"rule": "max_dimension", "component_id": component.get("id"), "message": "Component exceeds the project maximum dimension.", "action": "Reduce its dimension or update the approved project preset."})
        slope = component.get("structural", {}).get("slope_percent")
        if slope is not None and (not isinstance(slope, (int, float)) or isinstance(slope, bool) or not isfinite(slope)):
            violations.append({"rule": "invalid_slope", "component_id": component.get("id"), "message": "Slope must be a finite number.", "action": "Correct the component slope."})
        elif slope is not None and abs(slope) > float(preset["max_slope_percent"]):
            violations.append({"rule": "max_slope", "component_id": component.get("id"), "message": "Component slope exceeds the project maximum.", "action": "Reduce the slope or create a stepped transition."})
    invalid_ids = {v.get("component_id") for v in violations if v["rule"] == "invalid_geometry"}
    structural = [c for c in components if c.get("id") not in invalid_ids and c.get("category", "").rstrip("s") in {"column", "foundation", "pier"} and c.get("geometry", {}).get("kind") in {"box", "extrusion"}]
    minimum = float(preset["min_member_spacing_m"])
    for index, first in enumerate(structural):
        for second in structural[index + 1:]:
            if first.get("category") != second.get("category"):
                continue
            a, b = _position(first), _position(second)
            if abs(a[2] - b[2]) > minimum:
                continue
            if hypot(a[0] - b[0], a[1] - b[1]) < minimum:
                violations.append({"rule": "member_spacing", "component_id": first.get("id"), "related_component_id": second.get("id"), "message": f"Structural supports are closer than {minimum:g} m.", "action": "Move, merge, or remove one of the supports."})
    return {"passed": not violations, "preset": preset, "violations": violations, "disclaimer": "Conceptual rule screening only; licensed engineer review is required."}


def alternative_summaries(document: dict[str, Any]) -> list[dict[str, Any]]:
    from app.services.design.editable_model import calculate_revision_impact
    impact = calculate_revision_impact(document)
    validation = validate_layout(document)
    # Only report an evaluated document. Do not invent savings or candidate scores.
    return [
        {"id": "baseline", "name": "Saved layout baseline", "score": None, "cost_delta_percent": 0, "estimated_cost": impact["total_cost_estimate"], "constructability": "not evaluated", "rule_compliant": validation["passed"]},
    ]


def analysis_package(document: dict[str, Any], revision: Any, validation: dict[str, Any]) -> dict[str, Any]:
    return {"format": "sitegeoai.structural-analysis-package/v1", "revision": {"id": revision.id, "number": revision.revision_number}, "origin": document.get("origin"), "components": document.get("components", []), "rule_validation": validation, "assumptions": document.get("structural_layout", {}).get("assumptions", []), "notice": "Conceptual data package — validate loads, connections, codes, and detailing in specialist analysis software."}
