"""3D tiles / imagery provider configuration exposed to the frontend.

Only restricted browser read keys are delivered through runtime config.
Cesium upload/write credentials stay on the backend.
"""

from app.core.config import settings

ESRI_WORLD_IMAGERY_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
ESRI_WORLD_TOPO_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
)
SATELLITE_MAX_ZOOM = 22
# Esri World Topo cached tiles typically stop around z17 outside select urban LODs.
# Requesting higher levels returns "Map data not yet available" placeholders.
TERRAIN_MAX_ZOOM = 17
ESRI_SATELLITE_MAX_ZOOM = 19


def get_satellite_tile_config() -> dict:
    """Return satellite imagery config for MapLibre / Cesium clients."""
    if settings.MAPBOX_TOKEN:
        return {
            "provider": "mapbox",
            "max_zoom": SATELLITE_MAX_ZOOM,
            "tile_size": 512,
            "url_template": "/api/tiles/satellite/{z}/{x}/{y}.png",
            "attribution": "© Mapbox © OpenStreetMap",
        }
    return {
        "provider": "esri",
        "max_zoom": ESRI_SATELLITE_MAX_ZOOM,
        "tile_size": 256,
        "url_template": ESRI_WORLD_IMAGERY_URL,
        "attribution": "Esri World Imagery",
    }


def get_terrain_tile_config() -> dict:
    """Return terrain / topo imagery config (Esri World Topo — sharper than OpenTopoMap)."""
    return {
        "provider": "esri",
        "max_zoom": TERRAIN_MAX_ZOOM,
        "tile_size": 256,
        "url_template": ESRI_WORLD_TOPO_URL,
        "attribution": "Esri World Topo",
    }


def get_tile_providers() -> dict:
    return {
        "cesium_ion_available": bool(settings.CESIUM_ION_READ_TOKEN),
        "google_3d_tiles_available": bool(settings.GOOGLE_MAPS_API_KEY),
        "mapbox_available": bool(settings.MAPBOX_TOKEN),
        "fallback_imagery": "osm-raster",
        "satellite_config": get_satellite_tile_config(),
        "terrain_config": get_terrain_tile_config(),
    }


def get_map_runtime_config() -> dict:
    """Browser-only map keys for Cesium Ion / Google 3D Tiles (never AI or storage secrets).

    Restrict these keys by HTTP referrer / domain in Google Cloud and Cesium Ion dashboards.
    Mapbox satellite is proxied via /api/tiles and is not returned here.
    """
    return {
        "cesium_ion_token": settings.CESIUM_ION_READ_TOKEN or None,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY or None,
    }


def mapbox_satellite_tile_url(z: int, x: int, y: int) -> str:
    return (
        f"https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png"
        f"?access_token={settings.MAPBOX_TOKEN}"
    )


def esri_satellite_tile_url(z: int, x: int, y: int) -> str:
    return ESRI_WORLD_IMAGERY_URL.format(z=z, x=x, y=y)
