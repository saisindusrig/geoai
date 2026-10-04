"""Versioned engineering evidence; preserves legacy survey tables."""
from alembic import op
from sqlalchemy import text
from app.db.models import Base

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

TABLES = ["terrain_datasets", "terrain_dataset_versions", "active_terrain_configuration", "model_placements", "ground_samples",
          "terrain_source_files", "survey_control_points", "survey_validation_runs", "survey_checkpoint_residuals",
          "engineering_analyses", "structure_ground_checks", "constraint_datasets", "engineering_audit_events", "saved_camera_views", "project_map_preferences"]


def upgrade():
    bind = op.get_bind()
    for name in TABLES:
        Base.metadata.tables[name].create(bind, checkfirst=True)
    if bind.dialect.name == "postgresql":
        bind.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_raster"))
        bind.execute(text("""CREATE TABLE IF NOT EXISTS engineering_terrain_rasters (
            id BIGSERIAL PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id),
            terrain_version_id INTEGER NOT NULL REFERENCES terrain_dataset_versions(id), rast raster NOT NULL)"""))
        bind.execute(text("CREATE INDEX IF NOT EXISTS ix_engineering_terrain_raster_coverage ON engineering_terrain_rasters USING gist(ST_ConvexHull(rast))"))


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TABLE IF EXISTS engineering_terrain_rasters")
    for name in reversed(TABLES):
        Base.metadata.tables[name].drop(op.get_bind(), checkfirst=True)
