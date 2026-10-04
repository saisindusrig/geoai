"""Simplify geometry specs for fast preview exports."""

from __future__ import annotations

PREVIEW_KEEP_LAYERS = {
    "deck",
    "asphalt",
    "road_surface",
    "piers",
    "pier_caps",
    "foundation",
    "formation",
    "pavement",
    "base_course",
    "columns",
    "slabs",
    "core",
    "pipe",
    "trench",
    "excavation",
}

SKIP_PREVIEW_LAYERS = {"barrier", "barriers", "drains", "drainage", "facade", "manholes", "backfill", "bedding"}


def simplify_geometry_spec(spec: dict, *, max_piers: int = 4) -> dict:
    """Return a low-polygon preview geometry spec derived from the full spec."""
    objects = []
    pier_count = 0
    for obj in spec.get("objects", []):
        layer = str(obj.get("layer", "")).lower()
        if layer in SKIP_PREVIEW_LAYERS:
            continue
        if layer == "piers":
            if pier_count >= max_piers:
                continue
            pier_count += 1
        if layer and layer not in PREVIEW_KEEP_LAYERS and "pier" not in obj.get("name", ""):
            # Keep unknown structural objects but skip decorative extras.
            if layer in {"shoulders", "markings", "utilities"}:
                continue
        objects.append(obj)
    if not objects:
        objects = spec.get("objects", [])[: min(8, len(spec.get("objects", [])))]
    return {**spec, "objects": objects}


def approximate_boq_from_inputs(boq_inputs: list[dict]) -> dict:
    """Lightweight BOQ summary without DB rate lookups."""
    line_items = []
    total = 0.0
    for row in boq_inputs:
        qty = float(row.get("quantity") or 0)
        rate = float(row.get("rate") or 1.0)
        amount = round(qty * rate, 2)
        total += amount
        line_items.append({**row, "rate": rate, "amount": amount, "currency": "INR"})
    return {
        "line_items": line_items,
        "cost_summary": {
            "direct_cost": round(total, 2),
            "contingency_percent": 10,
            "contingency": round(total * 0.1, 2),
            "design_survey_approval": round(total * 0.05, 2),
            "total_low": round(total * 0.92, 2),
            "total_medium": round(total * 1.08, 2),
            "total_high": round(total * 1.18, 2),
            "currency": "INR",
        },
    }
