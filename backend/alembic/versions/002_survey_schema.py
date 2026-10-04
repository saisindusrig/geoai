"""Survey-grade schema: project CRS fields + survey tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

Idempotent on PostgreSQL: safe when revision 001 already ran ``create_all`` with
current models (survey tables + project columns). Uses ``IF NOT EXISTS`` DDL and
``information_schema`` / ``to_regclass`` instead of a stale inspector snapshot.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

_PROJECT_SURVEY_COLUMN_NAMES = (
    "engineering_crs_epsg",
    "accuracy_tier",
    "origin_lat",
    "origin_lng",
    "offset_e_m",
    "offset_n_m",
    "offset_h_m",
    "survey_mode_enabled",
)

# PostgreSQL ADD COLUMN IF NOT EXISTS fragments (boolean uses DEFAULT false, not 'false').
_PG_PROJECT_COLUMN_DDLS = (
    ("engineering_crs_epsg", "INTEGER"),
    ("accuracy_tier", "VARCHAR(32) DEFAULT 'visual' NOT NULL"),
    ("origin_lat", "DOUBLE PRECISION"),
    ("origin_lng", "DOUBLE PRECISION"),
    ("offset_e_m", "DOUBLE PRECISION"),
    ("offset_n_m", "DOUBLE PRECISION"),
    ("offset_h_m", "DOUBLE PRECISION"),
    ("survey_mode_enabled", "BOOLEAN DEFAULT false NOT NULL"),
)

_SQLITE_PROJECT_COLUMNS = (
    ("engineering_crs_epsg", sa.Column("engineering_crs_epsg", sa.Integer(), nullable=True)),
    (
        "accuracy_tier",
        sa.Column("accuracy_tier", sa.String(32), server_default="visual", nullable=False),
    ),
    ("origin_lat", sa.Column("origin_lat", sa.Float(), nullable=True)),
    ("origin_lng", sa.Column("origin_lng", sa.Float(), nullable=True)),
    ("offset_e_m", sa.Column("offset_e_m", sa.Float(), nullable=True)),
    ("offset_n_m", sa.Column("offset_n_m", sa.Float(), nullable=True)),
    ("offset_h_m", sa.Column("offset_h_m", sa.Float(), nullable=True)),
    (
        "survey_mode_enabled",
        sa.Column("survey_mode_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    ),
)


def _ensure_postgis() -> None:
    with op.get_context().autocommit_block():
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def _pg_table_exists(bind, table_name: str) -> bool:
    return bool(
        bind.execute(
            text("SELECT to_regclass(:qualified) IS NOT NULL"),
            {"qualified": f"public.{table_name}"},
        ).scalar()
    )


def _pg_column_exists(bind, table_name: str, column_name: str) -> bool:
    return bool(
        bind.execute(
            text(
                "SELECT EXISTS ("
                " SELECT 1 FROM information_schema.columns"
                " WHERE table_schema = 'public'"
                " AND table_name = :table_name"
                " AND column_name = :column_name"
                ")"
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def _table_exists(bind, table_name: str, is_pg: bool) -> bool:
    if is_pg:
        return _pg_table_exists(bind, table_name)
    return inspect(bind).has_table(table_name)


def _survey_schema_complete(bind, is_pg: bool) -> bool:
    if not (
        _table_exists(bind, "survey_datasets", is_pg)
        and _table_exists(bind, "engineering_layers", is_pg)
    ):
        return False
    if is_pg:
        return all(
            _pg_column_exists(bind, "projects", col) for col in _PROJECT_SURVEY_COLUMN_NAMES
        )
    project_cols = {c["name"] for c in inspect(bind).get_columns("projects")}
    return all(col in project_cols for col in _PROJECT_SURVEY_COLUMN_NAMES)


def _pg_create_index(index_name: str, table_name: str, columns: list[str]) -> None:
    cols = ", ".join(columns)
    op.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({cols})")


def _add_pg_project_columns() -> None:
    for name, ddl in _PG_PROJECT_COLUMN_DDLS:
        op.execute(f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {name} {ddl}")


def _add_sqlite_project_columns(bind) -> None:
    inspector = inspect(bind)
    project_cols = {c["name"] for c in inspector.get_columns("projects")}
    with op.batch_alter_table("projects") as batch_op:
        for name, col in _SQLITE_PROJECT_COLUMNS:
            if name not in project_cols:
                batch_op.add_column(col)


def _ensure_geom_column(bind, is_pg: bool) -> None:
    if not is_pg or not _pg_table_exists(bind, "engineering_layers"):
        return
    _ensure_postgis()
    if not _pg_column_exists(bind, "engineering_layers", "geom"):
        op.execute(
            "ALTER TABLE engineering_layers "
            "ADD COLUMN IF NOT EXISTS geom geometry(Geometry, 0)"
        )


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        _ensure_postgis()

    if _survey_schema_complete(bind, is_pg):
        _ensure_geom_column(bind, is_pg)
        return

    if is_pg:
        _add_pg_project_columns()
    else:
        _add_sqlite_project_columns(bind)

    # Revision 001 create_all may already have created survey tables; skip if present.
    if _table_exists(bind, "survey_datasets", is_pg) and _table_exists(bind, "engineering_layers", is_pg):
        _ensure_geom_column(bind, is_pg)
        return

    if not _table_exists(bind, "survey_datasets", is_pg):
        op.create_table(
            "survey_datasets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("storage_key", sa.String(512), nullable=True),
            sa.Column("source", sa.String(255), nullable=True),
            sa.Column("capture_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("crs_epsg", sa.Integer(), nullable=True),
            sa.Column("pixel_size_m", sa.Float(), nullable=True),
            sa.Column("rmse_h_m", sa.Float(), nullable=True),
            sa.Column("rmse_v_m", sa.Float(), nullable=True),
            sa.Column("accuracy_tier", sa.String(32), server_default="gis_grade", nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        if is_pg:
            _pg_create_index("ix_survey_datasets_project_id", "survey_datasets", ["project_id"])
            _pg_create_index("ix_survey_datasets_kind", "survey_datasets", ["kind"])
        else:
            op.create_index("ix_survey_datasets_project_id", "survey_datasets", ["project_id"])
            op.create_index("ix_survey_datasets_kind", "survey_datasets", ["kind"])

    if not _table_exists(bind, "engineering_layers", is_pg):
        op.create_table(
            "engineering_layers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column(
                "survey_dataset_id",
                sa.Integer(),
                sa.ForeignKey("survey_datasets.id"),
                nullable=True,
            ),
            sa.Column("layer_type", sa.String(64), nullable=False),
            sa.Column("name", sa.String(255), server_default="", nullable=False),
            sa.Column("width_m", sa.Float(), nullable=True),
            sa.Column("properties_json", sa.JSON(), nullable=True),
            sa.Column("accuracy_tier", sa.String(32), server_default="gis_grade", nullable=False),
            sa.Column("source", sa.String(255), nullable=True),
            sa.Column("capture_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("crs_epsg", sa.Integer(), nullable=True),
            sa.Column("pixel_size_m", sa.Float(), nullable=True),
            sa.Column("rmse_h_m", sa.Float(), nullable=True),
            sa.Column("rmse_v_m", sa.Float(), nullable=True),
            sa.Column("geom_geojson", sa.JSON(), nullable=True),
            sa.Column("geom_wgs84_geojson", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        if is_pg:
            _pg_create_index(
                "ix_engineering_layers_project_id", "engineering_layers", ["project_id"]
            )
            _pg_create_index(
                "ix_engineering_layers_layer_type", "engineering_layers", ["layer_type"]
            )
        else:
            op.create_index("ix_engineering_layers_project_id", "engineering_layers", ["project_id"])
            op.create_index("ix_engineering_layers_layer_type", "engineering_layers", ["layer_type"])

    _ensure_geom_column(bind, is_pg)

    if not _table_exists(bind, "ground_control_points", is_pg):
        op.create_table(
            "ground_control_points",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("source", sa.String(32), server_default="manual", nullable=False),
            sa.Column("lng", sa.Float(), nullable=False),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("ellipsoid_h_m", sa.Float(), nullable=True),
            sa.Column("easting_m", sa.Float(), nullable=True),
            sa.Column("northing_m", sa.Float(), nullable=True),
            sa.Column("orthometric_h_m", sa.Float(), nullable=True),
            sa.Column("horizontal_accuracy_m", sa.Float(), nullable=True),
            sa.Column("vertical_accuracy_m", sa.Float(), nullable=True),
            sa.Column("map_derived_e_m", sa.Float(), nullable=True),
            sa.Column("map_derived_n_m", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        if is_pg:
            _pg_create_index(
                "ix_ground_control_points_project_id",
                "ground_control_points",
                ["project_id"],
            )
        else:
            op.create_index(
                "ix_ground_control_points_project_id",
                "ground_control_points",
                ["project_id"],
            )

    if not _table_exists(bind, "accuracy_reports", is_pg):
        op.create_table(
            "accuracy_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("tier_result", sa.String(32), nullable=False),
            sa.Column("passed", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("report_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        if is_pg:
            _pg_create_index("ix_accuracy_reports_project_id", "accuracy_reports", ["project_id"])
        else:
            op.create_index("ix_accuracy_reports_project_id", "accuracy_reports", ["project_id"])


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if _table_exists(bind, "accuracy_reports", is_pg):
        op.drop_table("accuracy_reports")
    if _table_exists(bind, "ground_control_points", is_pg):
        op.drop_table("ground_control_points")
    if _table_exists(bind, "engineering_layers", is_pg):
        op.drop_table("engineering_layers")
    if _table_exists(bind, "survey_datasets", is_pg):
        op.drop_table("survey_datasets")

    if is_pg:
        for col in reversed(_PROJECT_SURVEY_COLUMN_NAMES):
            op.execute(f"ALTER TABLE projects DROP COLUMN IF EXISTS {col}")
    else:
        inspector = inspect(bind)
        project_cols = {c["name"] for c in inspector.get_columns("projects")}
        with op.batch_alter_table("projects") as batch_op:
            for col in reversed(_PROJECT_SURVEY_COLUMN_NAMES):
                if col in project_cols:
                    batch_op.drop_column(col)
