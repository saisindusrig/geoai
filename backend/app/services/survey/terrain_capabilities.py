"""Database capability boundary for authoritative terrain operations."""
from dataclasses import dataclass
from app.db.session import IS_POSTGRES

@dataclass(frozen=True)
class TerrainDatabaseCapabilities:
    supports_postgis: bool
    supports_authoritative_survey_terrain: bool
    supports_spatial_coverage_queries: bool

def terrain_database_capabilities() -> TerrainDatabaseCapabilities:
    return TerrainDatabaseCapabilities(IS_POSTGRES, IS_POSTGRES, IS_POSTGRES)
