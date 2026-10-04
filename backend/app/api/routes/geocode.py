from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.security import get_current_user_id
from app.services.geospatial.geocoding import geocode
from app.services.geospatial.tiles import get_map_runtime_config, get_tile_providers

router = APIRouter(prefix="/api/geocode", tags=["geospatial"])


@router.get("")
async def search(q: str = Query(min_length=2, max_length=200)):
    return {"results": await geocode(q)}


@router.get("/tile-providers")
def tile_providers():
    return get_tile_providers()


@router.get("/map-runtime-config")
def map_runtime_config(_user_id: int = Depends(get_current_user_id)):
    """Map/3D client bootstrap config. JWT required when AUTH_REQUIRE_JWT is enabled."""
    return get_map_runtime_config()
