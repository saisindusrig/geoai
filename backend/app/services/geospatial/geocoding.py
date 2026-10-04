"""Geocoding provider adapters.

Order of preference: Mapbox (if token) -> Nominatim (public, no key) ->
mock. Each provider returns the same plain-dict shape so they are drop-in
replacements.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "sitegeoai/0.1 (dev)"


async def _nominatim_geocode(query: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 5},
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        return [
            {
                "name": item["display_name"],
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
                "provider": "nominatim",
            }
            for item in resp.json()
        ]


async def _mapbox_geocode(query: str) -> list[dict]:
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"access_token": settings.MAPBOX_TOKEN, "limit": 5})
        resp.raise_for_status()
        return [
            {
                "name": f["place_name"],
                "lat": f["center"][1],
                "lng": f["center"][0],
                "provider": "mapbox",
            }
            for f in resp.json().get("features", [])
        ]


def _mock_geocode(query: str) -> list[dict]:
    return [
        {
            "name": f"Mock result for '{query}' (Bengaluru city center)",
            "lat": 12.9716,
            "lng": 77.5946,
            "provider": "mock",
        }
    ]


async def geocode(query: str) -> list[dict]:
    if settings.MAPBOX_TOKEN:
        try:
            return await _mapbox_geocode(query)
        except Exception:
            logger.warning("Mapbox geocoding failed, trying Nominatim")
    try:
        return await _nominatim_geocode(query)
    except Exception:
        logger.warning("Nominatim unavailable, using mock geocoder")
        return _mock_geocode(query)
