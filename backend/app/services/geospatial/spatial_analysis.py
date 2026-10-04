"""Deterministic spatial analysis using Shapely + pyproj (works on any DB)."""

from pyproj import Geod
from shapely.geometry import shape

GEOD = Geod(ellps="WGS84")


def polygon_metrics(boundary_geojson: dict) -> dict:
    """Geodesic area (sqm) and perimeter (m) of a GeoJSON polygon."""
    geom = shape(boundary_geojson)
    area, perimeter = GEOD.geometry_area_perimeter(geom)
    return {"area_sqm": abs(area), "perimeter_m": perimeter}


def line_length_m(line_geojson: dict) -> float:
    geom = shape(line_geojson)
    return GEOD.geometry_length(geom)


def bbox_with_buffer(geojson: dict, buffer_deg: float = 0.003) -> tuple[float, float, float, float]:
    """(south, west, north, east) bbox expanded by ~300m for context fetch."""
    geom = shape(geojson)
    minx, miny, maxx, maxy = geom.bounds
    return (miny - buffer_deg, minx - buffer_deg, maxy + buffer_deg, maxx + buffer_deg)


def find_intersections(boundary_geojson: dict, features: list[dict]) -> list[dict]:
    """Which OSM features cross/touch the project boundary (clash candidates)."""
    boundary = shape(boundary_geojson)
    clashes = []
    for feature in features:
        try:
            geom = shape(feature["geometry"])
        except Exception:
            continue
        if geom.intersects(boundary):
            props = feature.get("properties", {})
            clashes.append(
                {
                    "category": props.get("category", "unknown"),
                    "name": props.get("name") or "(unnamed)",
                    "osm_id": props.get("osm_id"),
                }
            )
    return clashes


def sample_line_points(line_geojson: dict, num_samples: int = 25) -> list[tuple[float, float]]:
    """Sample (lat, lng) points along a LineString for elevation profiling."""
    if line_geojson.get("type") != "LineString":
        return []
    coords = line_geojson["coordinates"]
    if len(coords) < 2:
        return []
    if num_samples < 2:
        num_samples = 2
    total = line_length_m(line_geojson)
    if total <= 0:
        lng, lat = coords[0]
        return [(lat, lng)]

    targets = [total * i / (num_samples - 1) for i in range(num_samples)]
    points: list[tuple[float, float]] = []
    seg_start = 0.0
    seg_idx = 0
    for target in targets:
        while seg_idx < len(coords) - 1:
            seg_len = line_length_m(
                {"type": "LineString", "coordinates": [coords[seg_idx], coords[seg_idx + 1]]}
            )
            if seg_start + seg_len >= target or seg_idx == len(coords) - 2:
                frac = (target - seg_start) / seg_len if seg_len > 0 else 0
                frac = max(0.0, min(1.0, frac))
                lng = coords[seg_idx][0] + frac * (coords[seg_idx + 1][0] - coords[seg_idx][0])
                lat = coords[seg_idx][1] + frac * (coords[seg_idx + 1][1] - coords[seg_idx][1])
                points.append((lat, lng))
                break
            seg_start += seg_len
            seg_idx += 1
    return points


def slope_percent(elevations_m: list[float], distance_m: float) -> float | None:
    if not elevations_m or distance_m <= 0:
        return None
    rise = max(elevations_m) - min(elevations_m)
    return round(rise / distance_m * 100, 2)
