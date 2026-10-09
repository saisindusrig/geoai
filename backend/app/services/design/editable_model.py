"""Editable semantic model documents and deterministic revision calculations."""

from __future__ import annotations

from copy import deepcopy
from math import prod, cos, sin, radians
import re
from typing import Any
from uuid import uuid4

SUPPORTED_KINDS = {"box", "cylinder", "extrusion", "sweep", "asset_instance"}
SUPPORTED_PROJECT_TYPES = {"bridge", "flyover", "building", "road", "pipeline", "dam"}

LAYER_MATERIALS: dict[str, dict[str, Any]] = {
    "wall": {"name": "Architectural wall", "color": "#E7DFD1", "roughness": 0.8, "metalness": 0.0},
    "door": {"name": "Door", "color": "#93613E", "roughness": 0.7, "metalness": 0.0},
    "window": {"name": "Window", "color": "#78BDCF", "roughness": 0.2, "metalness": 0.15},
    "room": {"name": "Room floor finish", "color": "#CCC3AE", "roughness": 0.8, "metalness": 0.0},
    "beam": {"name": "Concept beam", "color": "#8EACC7", "roughness": 0.8, "metalness": 0.0},
    "deck": {"name": "Structural concrete", "color": "#B8C0CC", "roughness": 0.78, "metalness": 0.0},
    "road": {"name": "Asphalt", "color": "#28313F", "roughness": 0.94, "metalness": 0.0},
    "asphalt": {"name": "Asphalt", "color": "#28313F", "roughness": 0.94, "metalness": 0.0},
    "piers": {"name": "Reinforced concrete", "color": "#AFC4DD", "roughness": 0.72, "metalness": 0.0},
    "foundations": {"name": "Foundation concrete", "color": "#8D96A4", "roughness": 0.85, "metalness": 0.0},
    "barriers": {"name": "Concrete barrier", "color": "#E0E5EA", "roughness": 0.7, "metalness": 0.0},
    "excavation": {"name": "Excavation", "color": "#C7823D", "roughness": 1.0, "metalness": 0.0},
    "pipe": {"name": "Pipeline", "color": "#38BDF8", "roughness": 0.48, "metalness": 0.2},
}


class ModelDocumentError(ValueError):
    pass


def _vec3(value: Any, default: list[float]) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return list(default)
    return [float(value[0]), float(value[1]), float(value[2])]


def geometry_spec_to_document(project: Any, scenario: Any, geometry_spec: dict[str, Any]) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for index, raw in enumerate(geometry_spec.get("objects") or []):
        obj = deepcopy(raw)
        layer = str(obj.get("layer") or "misc")
        name = str(obj.get("name") or f"Component {index + 1}")
        base_id = re.sub(r"[^a-z0-9]+", "-", f"{layer}-{name}".lower()).strip("-") or f"component-{index + 1}"
        component_id = base_id
        suffix = 2
        while component_id in used_ids:
            component_id = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(component_id)

        kind = obj.get("kind", "box")
        if kind == "box":
            geometry = {"kind": "box", "size": _vec3(obj.get("size"), [1, 1, 1])}
            position = _vec3(obj.get("center"), [0, 0, 0])
            rotation = [0.0, 0.0, float(obj.get("rotation_z_deg") or 0)]
        else:
            start = _vec3(obj.get("start"), [0, 0, 0])
            end = _vec3(obj.get("end"), [0, 0, 1])
            geometry = {
                "kind": "cylinder",
                "start": start,
                "end": end,
                "radius_m": float(obj.get("radius_m") or 0.5),
            }
            position = [0.0, 0.0, 0.0]
            rotation = [0.0, 0.0, 0.0]
        components.append(
            {
                "id": component_id,
                "parent_id": None,
                "name": name,
                "category": layer,
                "visible": True,
                "locked": False,
                "geometry": geometry,
                "transform": {"position": position, "rotation_deg": rotation, "scale": [1.0, 1.0, 1.0]},
                "material": deepcopy(LAYER_MATERIALS.get(layer.lower(), {
                    "name": "Generated material", "color": "#94A3B8", "roughness": 0.75, "metalness": 0.0,
                })),
                "quantity": {"included": kind in {"box", "cylinder"} and layer not in {"room", "wall", "door", "window"}},
            }
        )

    return {
        "schema_version": 1,
        "project_id": project.id,
        "scenario_id": scenario.id,
        "project_type": project.project_type,
        "units": "metric",
        "origin": {
            "lng": float(project.origin_lng if project.origin_lng is not None else project.center_lng or 0),
            "lat": float(project.origin_lat if project.origin_lat is not None else project.center_lat or 0),
            "elevation_m": float(project.offset_h_m or 0),
            "heading_deg": 0.0,
        },
        "generator_parameters": deepcopy(scenario.input_parameters_json or {}),
        "components": components,
        "metadata": {"source": "ai_generate", "frame": "local_enu_meters"},
        "structural_layout": {"rule_preset": {"min_member_spacing_m": 1.0, "max_slope_percent": 12.0, "min_clearance_m": 3.0, "max_dimension_m": 500.0}, "assumptions": ["Conceptual layout generated from available site and project data."]},
    }


def validate_document(document: dict[str, Any], *, project_id: int, scenario_id: int, project_type: str) -> list[str]:
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if int(document.get("project_id") or 0) != project_id:
        errors.append("document project_id does not match the route")
    if int(document.get("scenario_id") or 0) != scenario_id:
        errors.append("document scenario_id does not match the route")
    if document.get("project_type") != project_type:
        errors.append("document project_type does not match the project")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty list")
        return errors
    ids: set[str] = set()
    for index, component in enumerate(components):
        label = f"components[{index}]"
        component_id = str(component.get("id") or "")
        if not component_id:
            errors.append(f"{label}.id is required")
        elif component_id in ids:
            errors.append(f"duplicate component id: {component_id}")
        ids.add(component_id)
        geometry = component.get("geometry") or {}
        kind = geometry.get("kind")
        if kind not in SUPPORTED_KINDS:
            errors.append(f"{label}.geometry.kind is unsupported")
        if kind == "box":
            size = geometry.get("size")
            if not isinstance(size, list) or len(size) != 3 or any(float(v) <= 0 for v in size):
                errors.append(f"{label}.geometry.size must contain three positive values")
        if kind == "cylinder" and float(geometry.get("radius_m") or 0) <= 0:
            errors.append(f"{label}.geometry.radius_m must be positive")
        transform = component.get("transform") or {}
        scale = transform.get("scale", [1, 1, 1])
        if not isinstance(scale, list) or len(scale) != 3 or any(float(v) <= 0 or float(v) > 100 for v in scale):
            errors.append(f"{label}.transform.scale must contain values in (0, 100]")
        color = str((component.get("material") or {}).get("color") or "")
        if color and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            errors.append(f"{label}.material.color must be a six-digit hex color")
    for component in components:
        parent_id = component.get("parent_id")
        if parent_id and parent_id not in ids:
            errors.append(f"component {component.get('id')} references an unknown parent")
    return errors


def document_to_geometry_spec(document: dict[str, Any]) -> dict[str, Any]:
    objects: list[dict[str, Any]] = []
    for component in document.get("components") or []:
        if not component.get("visible", True):
            continue
        geometry = component.get("geometry") or {}
        transform = component.get("transform") or {}
        position = _vec3(transform.get("position"), [0, 0, 0])
        rotation = _vec3(transform.get("rotation_deg"), [0, 0, 0])
        scale = _vec3(transform.get("scale"), [1, 1, 1])
        kind = geometry.get("kind")
        common = {"name": component["id"], "layer": component.get("category") or "misc"}
        if kind in {"box", "extrusion"}:
            base_size = geometry.get("size") or geometry.get("dimensions") or [1, 1, 1]
            size = [float(base_size[i]) * scale[i] for i in range(3)]
            objects.append({**common, "kind": "box", "size": size, "center": position, "rotation_z_deg": rotation[2]})
        elif kind in {"cylinder", "sweep"}:
            start = _vec3(geometry.get("start"), [0, 0, 0])
            end = _vec3(geometry.get("end"), [0, 0, 1])
            def endpoint(point):
                # Match the editor's XYZ Euler transform (Rx * Ry * Rz).
                x,y,z = [point[i] * scale[i] for i in range(3)]
                rx,ry,rz = [radians(v) for v in rotation]
                x,y = x*cos(rz)-y*sin(rz), x*sin(rz)+y*cos(rz)
                x,z = x*cos(ry)+z*sin(ry), -x*sin(ry)+z*cos(ry)
                y,z = y*cos(rx)-z*sin(rx), y*sin(rx)+z*cos(rx)
                return [x+position[0],y+position[1],z+position[2]]
            objects.append({
                **common,
                "kind": "cylinder",
                "start": endpoint(start),
                "end": endpoint(end),
                "radius_m": float(geometry.get("radius_m") or 0.5) * max(scale[0], scale[1]),
            })
        # asset_instance is intentionally reference-only and is not included in calculated quantities.
    return {"frame": "local_meters", "objects": objects}


def calculate_revision_impact(document: dict[str, Any]) -> dict[str, Any]:
    spec = document_to_geometry_spec(document)
    concrete = asphalt = excavation = steel = pipe_length = 0.0
    for obj in spec["objects"]:
        layer = str(obj.get("layer") or "").lower()
        if layer in {"room", "wall", "door", "window"}:
            continue
        if obj["kind"] == "box":
            volume = prod(float(v) for v in obj["size"])
        else:
            start, end = obj["start"], obj["end"]
            length = sum((float(end[i]) - float(start[i])) ** 2 for i in range(3)) ** 0.5
            volume = 3.141592653589793 * float(obj["radius_m"]) ** 2 * length
            if "pipe" in layer:
                pipe_length += length
        if "excav" in layer or "trench" in layer:
            excavation += volume
        elif "road" in layer or "asphalt" in layer or "pavement" in layer:
            asphalt += volume
        elif "steel" in layer or "truss" in layer or "arch" in layer:
            steel += volume * 7850
        else:
            concrete += volume
    rebar = concrete * 110
    cement_bags = concrete * 7.2
    total = concrete * 8500 + asphalt * 11000 + excavation * 250 + (steel + rebar) * 75 + pipe_length * 2200
    return {
        "quantities": {
            "concrete_m3": round(concrete, 3), "cement_bags": round(cement_bags, 1),
            "steel_kg": round(steel, 1), "rebar_kg": round(rebar, 1),
            "excavation_m3": round(excavation, 3), "backfill_m3": 0.0,
            "formwork_sqm": round(concrete ** (2 / 3) * 6 if concrete else 0, 2),
            "asphalt_m3": round(asphalt, 3), "pipe_length_m": round(pipe_length, 2),
            "pipe_diameter_mm": 0.0,
        },
        "total_cost_estimate": round(total, 2),
        "currency": "INR",
    }


def build_ai_edit_preview(document: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Return a safe deterministic patch preview; never executes model-supplied code."""
    prompt_l = prompt.lower().strip()
    components = document.get("components") or []
    targets = [c for c in components if str(c.get("category", "")).lower() in prompt_l or str(c.get("name", "")).lower() in prompt_l]
    if not targets:
        targets = components[:1]
    patch: list[dict[str, Any]] = []
    warnings: list[str] = []
    number_match = re.search(r"(-?\d+(?:\.\d+)?)", prompt_l)
    value = float(number_match.group(1)) if number_match else None
    for component in targets:
        cid = component["id"]
        if component.get("locked") and not ("hide" in prompt_l or "show" in prompt_l):
            warnings.append(f"{component.get('name', cid)} is locked. Unlock it before editing.")
            continue
        if "hide" in prompt_l:
            patch.append({"component_id": cid, "changes": {"visible": False}})
        elif "show" in prompt_l:
            patch.append({"component_id": cid, "changes": {"visible": True}})
        elif "move" in prompt_l or "raise" in prompt_l or "lower" in prompt_l:
            pos = list((component.get("transform") or {}).get("position", [0, 0, 0]))
            amount = value if value is not None else 1.0
            pos[2] += -abs(amount) if "lower" in prompt_l else amount
            patch.append({"component_id": cid, "changes": {"transform": {**component["transform"], "position": pos}}})
        elif "scale" in prompt_l or "larger" in prompt_l or "smaller" in prompt_l:
            factor = (value / 100.0 if value and value > 10 else value) or (0.9 if "smaller" in prompt_l else 1.1)
            scale = [round(float(v) * factor, 4) for v in component["transform"]["scale"]]
            patch.append({"component_id": cid, "changes": {"transform": {**component["transform"], "scale": scale}}})
        else:
            warnings.append("Describe a move, raise, lower, scale, hide, or show operation with a component name or category.")
    return {"patch": patch, "warnings": warnings, "preview_id": str(uuid4())}


def apply_component_patch(document: dict[str, Any], patch: list[dict[str, Any]]) -> dict[str, Any]:
    result = deepcopy(document)
    by_id = {c["id"]: c for c in result.get("components") or []}
    for operation in patch:
        component = by_id.get(operation.get("component_id"))
        if not component:
            raise ModelDocumentError(f"Unknown component: {operation.get('component_id')}")
        changes = operation.get("changes") or {}
        if component.get("locked") and any(key not in ("visible", "locked") for key in changes):
            raise ModelDocumentError(f"Locked component cannot be edited: {component['id']}")
        for key in ("visible", "locked", "transform", "material", "geometry", "name", "category"):
            if key in changes:
                component[key] = deepcopy(changes[key])
    return result
