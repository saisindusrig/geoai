"""Project CRS helpers — WGS84 display, UTM/projected storage for meter-accurate work."""

from __future__ import annotations

from functools import lru_cache

from pyproj import CRS, Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

WGS84 = 4326


def estimate_utm_epsg(lng: float, lat: float) -> int:
    """Return EPSG code for UTM zone covering (lng, lat)."""
    zone = int((lng + 180) / 6) + 1
    zone = max(1, min(60, zone))
    return 32600 + zone if lat >= 0 else 32700 + zone


@lru_cache(maxsize=64)
def _transformer(from_epsg: int, to_epsg: int) -> Transformer:
    return Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)


def wgs84_to_project(lng: float, lat: float, project_epsg: int) -> tuple[float, float]:
    e, n = _transformer(WGS84, project_epsg).transform(lng, lat)
    return float(e), float(n)


def project_to_wgs84(easting: float, northing: float, project_epsg: int) -> tuple[float, float]:
    lng, lat = _transformer(project_epsg, WGS84).transform(easting, northing)
    return float(lng), float(lat)


def reproject_geojson(geojson: dict, from_epsg: int, to_epsg: int) -> dict:
    if from_epsg == to_epsg:
        return geojson
    geom = shape(geojson)
    tx = _transformer(from_epsg, to_epsg).transform
    return mapping(transform(tx, geom))


def geodesic_length_m(geojson_wgs84: dict) -> float:
    from app.services.geospatial.spatial_analysis import line_length_m

    return line_length_m(geojson_wgs84)


def projected_length_m(geojson_project: dict, project_epsg: int) -> float:
    geom = shape(geojson_project)
    if geom.is_empty:
        return 0.0
    if geom.geom_type == "LineString":
        return float(geom.length)
    if geom.geom_type == "MultiLineString":
        return float(sum(g.length for g in geom.geoms))
    return 0.0


def projected_area_sqm(geojson_project: dict) -> float:
    geom = shape(geojson_project)
    if geom.is_empty or geom.geom_type not in ("Polygon", "MultiPolygon"):
        return 0.0
    return float(geom.area)


def crs_label(epsg: int) -> str:
    try:
        return CRS.from_epsg(epsg).to_authority()[1]
    except Exception:
        return f"EPSG:{epsg}"
