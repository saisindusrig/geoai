"""Shared geometry helpers for conceptual model generation.

All generated models use a local ENU-like frame in meters centered on the
project center; the frontend places the GLB at (center_lat, center_lng).
"""

import math

from pyproj import Geod

GEOD = Geod(ellps="WGS84")

# Layer color conventions (RGBA 0-255) per the product spec
LAYER_COLORS = {
    "terrain": (139, 119, 101, 255),
    "excavation": (180, 60, 40, 110),     # transparent red/brown
    "foundation": (100, 100, 110, 255),
    "concrete": (160, 160, 165, 255),
    "piers": (150, 150, 158, 255),
    "pier_caps": (140, 140, 150, 255),
    "deck": (170, 170, 175, 255),
    "steel": (60, 60, 70, 255),
    "asphalt": (45, 45, 48, 255),
    "road_marking": (240, 240, 235, 255),
    "barrier": (230, 200, 40, 255),
    "pipe_water": (40, 110, 220, 255),
    "pipe_drain": (230, 130, 40, 255),
    "bedding": (210, 190, 140, 255),
    "backfill": (150, 130, 100, 140),
    "slab": (175, 175, 180, 255),
    "column": (150, 150, 158, 255),
    "core": (120, 120, 128, 255),
    "facade": (180, 200, 220, 90),
    "manhole": (90, 90, 95, 255),
    "shoulder": (120, 110, 95, 255),
}


def line_to_local_xy(coords_lnglat: list[list[float]], center_lng: float, center_lat: float) -> list[tuple[float, float]]:
    """Project lng/lat coords to local meters (equirectangular, fine for sites)."""
    k = math.pi / 180.0
    lat0 = center_lat * k
    r = 6371000.0
    out = []
    for lng, lat in coords_lnglat:
        x = (lng - center_lng) * k * r * math.cos(lat0)
        y = (lat - center_lat) * k * r
        out.append((x, y))
    return out


def line_length_lnglat(coords_lnglat: list[list[float]]) -> float:
    lons = [c[0] for c in coords_lnglat]
    lats = [c[1] for c in coords_lnglat]
    return GEOD.line_length(lons, lats)


def box(name: str, layer: str, center: tuple[float, float, float],
        size: tuple[float, float, float], rotation_z_deg: float = 0.0) -> dict:
    return {"kind": "box", "name": name, "layer": layer, "center": center,
            "size": size, "rotation_z_deg": rotation_z_deg}


def cylinder(name: str, layer: str, start: tuple[float, float, float],
             end: tuple[float, float, float], radius_m: float) -> dict:
    return {"kind": "cylinder", "name": name, "layer": layer,
            "start": start, "end": end, "radius_m": radius_m}
