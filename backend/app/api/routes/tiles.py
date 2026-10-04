import httpx
from fastapi import APIRouter, HTTPException, Response

from app.core.config import settings
from app.services.geospatial.tiles import esri_satellite_tile_url, mapbox_satellite_tile_url

router = APIRouter(prefix="/api/tiles", tags=["geospatial"])

TILE_CACHE = "public, max-age=86400"


@router.get("/satellite/{z}/{x}/{y}.png")
async def satellite_tile(z: int, x: int, y: int):
    if z < 0 or z > 22 or x < 0 or y < 0:
        raise HTTPException(status_code=400, detail="Invalid tile coordinates")

    if settings.MAPBOX_TOKEN:
        upstream = mapbox_satellite_tile_url(z, x, y)
    else:
        upstream = esri_satellite_tile_url(z, x, y)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(upstream)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Tile upstream failed: {exc}") from exc

    content_type = resp.headers.get("content-type", "image/png")
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Cache-Control": TILE_CACHE},
    )
