"""Explicit elevation resolution; preserve ambiguous legacy numeric values."""
from alembic import op
import sqlalchemy as sa
from app.db.stage1_elevation_v1 import backfill

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {c["name"]: c for c in sa.inspect(bind).get_columns("model_placements")}
    # Add provenance before interpreting any existing elevations.
    if "elevation_resolution" not in columns:
        op.add_column("model_placements", sa.Column("elevation_resolution", sa.String(24), nullable=False, server_default="UNKNOWN"))
    if "elevation_provenance_json" not in columns:
        op.add_column("model_placements", sa.Column("elevation_provenance_json", sa.JSON(), nullable=True))
    if not columns["anchor_elevation"]["nullable"] or columns["anchor_elevation"].get("default") is not None:
        # SQLite's batch copy preserves every row and transform. Back up a live
        # installation first; tests exercise existing FK children as well.
        with op.batch_alter_table("model_placements") as batch:
            batch.alter_column("anchor_elevation", existing_type=sa.Float(), nullable=True, server_default=None)
    backfill(bind)


def downgrade():
    raise RuntimeError("Nullable elevations cannot be converted to zero safely. Restore a verified pre-009 backup.")
