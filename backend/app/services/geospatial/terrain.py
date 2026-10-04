"""Terrain / elevation adapter.

Uses public elevation for visual reference. Unknown samples remain null.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"


async def sample_elevations(points: list[tuple[float, float]]) -> dict:
    """points: list of (lat, lng). Returns elevations + provenance flag."""
    try:
        locations = [{"latitude": lat, "longitude": lng} for lat, lng in points]
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(OPEN_ELEVATION_URL, json={"locations": locations})
            resp.raise_for_status()
            results = resp.json()["results"]
        elevations = [r["elevation"] for r in results]
        return {"elevations_m": elevations, "provider": "open-elevation", "assumed": False}
    except Exception:
        logger.warning("Elevation API unavailable; elevations are unknown")
        return {"elevations_m": [None] * len(points), "provider": "NONE", "assumed": True}
