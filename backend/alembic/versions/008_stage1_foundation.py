"""Stage 1 immutable persistence foundation; no runtime AI behavior."""
from alembic import op
import sqlalchemy as sa
from app.db.stage1_schema_v1 import register, install_guards

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    indexes = sa.inspect(bind).get_indexes("model_revisions")
    constraints = sa.inspect(bind).get_unique_constraints("model_revisions")
    if not any(item.get("column_names") == ["project_id", "id"] for item in indexes + constraints):
        op.create_index("uq_model_revision_project_id", "model_revisions", ["project_id", "id"], unique=True)
    metadata = sa.MetaData()
    # Reflect only referenced legacy identities, not application metadata that
    # may evolve in later releases.
    for name in ("projects", "users", "model_revisions"):
        sa.Table(name, metadata, autoload_with=bind)
    tables = register(metadata)
    metadata.create_all(bind, tables=list(tables.values()), checkfirst=True)
    install_guards(bind, tables)


def downgrade():
    raise RuntimeError("Stage 1 histories cannot be destructively downgraded. Restore a verified pre-008 backup; see docs/STAGE_1_FOUNDATION.md.")
