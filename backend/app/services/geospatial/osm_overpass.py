"""OpenStreetMap Overpass adapter: fetch roads and buildings near a bbox.

Falls back to a deterministic mock dataset when Overpass is unreachable, so
site analysis always works offline.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _overpass_query(bbox: tuple[float, float, float, float]) -> str:
    # bbox = (south, west, north, east)
    s, w, n, e = bbox
    return f"""
    [out:json][timeout:25];
    (
      way["highway"]({s},{w},{n},{e});
      way["building"]({s},{w},{n},{e});
      way["waterway"]({s},{w},{n},{e});
    );
    out geom;
    """


def _ways_to_geojson(elements: list[dict]) -> dict:
    """Convert Overpass `out geom` ways into a GeoJSON FeatureCollection."""
    features = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        tags = el.get("tags", {})
        if "building" in tags and len(coords) >= 4 and coords[0] == coords[-1]:
            geometry = {"type": "Polygon", "coordinates": [coords]}
            category = "building"
        elif "highway" in tags:
            geometry = {"type": "LineString", "coordinates": coords}
            category = "road"
        elif "waterway" in tags:
            geometry = {"type": "LineString", "coordinates": coords}
            category = "waterway"
        else:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "category": category,
                    "name": tags.get("name", ""),
                    "highway": tags.get("highway", ""),
                    "building": tags.get("building", ""),
                    "waterway": tags.get("waterway", ""),
                    "osm_id": el.get("id"),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _mock_osm_data(bbox: tuple[float, float, float, float]) -> dict:
    s, w, n, e = bbox
    mid_lat, mid_lng = (s + n) / 2, (w + e) / 2
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[w, mid_lat], [e, mid_lat]]},
                "properties": {"category": "road", "name": "Mock Main Road", "highway": "secondary", "osm_id": -1},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [mid_lng, mid_lat],
                        [mid_lng + 0.0005, mid_lat],
                        [mid_lng + 0.0005, mid_lat + 0.0005],
                        [mid_lng, mid_lat + 0.0005],
                        [mid_lng, mid_lat],
                    ]],
                },
                "properties": {"category": "building", "name": "Mock Building", "building": "yes", "osm_id": -2},
            },
        ],
        "mock": True,
    }


async def fetch_osm_features(bbox: tuple[float, float, float, float]) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(OVERPASS_URL, data={"data": _overpass_query(bbox)})
            resp.raise_for_status()
            return _ways_to_geojson(resp.json().get("elements", []))
    except Exception:
        logger.warning("Overpass unavailable, returning mock OSM data")
        return _mock_osm_data(bbox)
