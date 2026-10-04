"""Build a conceptual GLB model from a geometry spec using trimesh."""

from __future__ import annotations

import numpy as np
import trimesh

from app.services.design.geometry_utils import LAYER_COLORS

_Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])

PREVIEW_SKIP_LAYERS = {"barrier", "barriers", "drains", "drainage", "facade", "manholes"}


def _make_box(obj: dict) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=obj["size"])
    rot = obj.get("rotation_z_deg", 0.0)
    if rot:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rot), [0, 0, 1]))
    mesh.apply_translation(obj["center"])
    return mesh


def _make_cylinder(obj: dict, *, sections: int) -> trimesh.Trimesh:
    start = np.array(obj["start"], dtype=float)
    end = np.array(obj["end"], dtype=float)
    return trimesh.creation.cylinder(radius=obj["radius_m"], segment=np.vstack([start, end]), sections=sections)


def _filter_objects(objects: list[dict], quality: str) -> list[dict]:
    if quality != "preview":
        return objects
    filtered = []
    for obj in objects:
        layer = str(obj.get("layer", "")).lower()
        if layer in PREVIEW_SKIP_LAYERS:
            continue
        filtered.append(obj)
    return filtered or objects[: min(8, len(objects))]


def _merge_boxes(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh | None:
    if len(meshes) < 2:
        return None
    try:
        return trimesh.util.concatenate(meshes)
    except Exception:
        return None


def generate_glb(geometry_spec: dict, *, quality: str = "final") -> bytes:
    """Export GLB. quality='preview' uses fewer segments and skips decorative layers."""
    sections = 8 if quality == "preview" else 24
    objects = _filter_objects(list(geometry_spec.get("objects", [])), quality)
    scene = trimesh.Scene()
    pier_meshes: list[trimesh.Trimesh] = []

    for obj in objects:
        try:
            if obj["kind"] == "box":
                mesh = _make_box(obj)
            else:
                mesh = _make_cylinder(obj, sections=sections)
        except Exception:
            continue
        mesh.apply_transform(_Z_UP_TO_Y_UP)
        color = LAYER_COLORS.get(obj.get("layer", ""), (128, 128, 128, 255))
        if quality == "preview":
            color = (*color[:3], min(color[3], 180))
        # Vertex colors avoid trimesh's optional scipy dependency used when
        # converting face colors during GLB export.
        mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=np.tile(color, (len(mesh.vertices), 1)))
        layer = obj.get("layer", "misc")
        if quality == "preview" and layer == "piers":
            pier_meshes.append(mesh)
            continue
        scene.add_geometry(mesh, node_name=f"{layer}/{obj['name']}", geom_name=f"{layer}/{obj['name']}")

    if quality == "preview" and pier_meshes:
        merged = _merge_boxes(pier_meshes)
        if merged is not None:
            merged.visual = trimesh.visual.ColorVisuals(
                merged,
                vertex_colors=np.tile(LAYER_COLORS.get("piers", (100, 149, 237, 180)), (len(merged.vertices), 1)),
            )
            scene.add_geometry(merged, node_name="piers/merged", geom_name="piers/merged")

    if len(scene.geometry) == 0:
        fallback = trimesh.creation.box(extents=[1, 1, 1])
        fallback.apply_transform(_Z_UP_TO_Y_UP)
        scene.add_geometry(fallback)
    return scene.export(file_type="glb")
