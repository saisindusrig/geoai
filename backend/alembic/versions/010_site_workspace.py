"""Profile current state and immutable sample artifacts; preserve foundation history."""
import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    from app.db.models import Base, STAGE1_TABLES
    from app.db.stage1_schema_v1 import install_guards
    bind = op.get_bind()
    present = {c["name"] for c in sa.inspect(bind).get_columns("site_profiles")}
    for name in ("latest_version_id", "refresh_context", "refresh_job_id", "refresh_error"):
        if name not in present:
            source = Base.metadata.tables["site_profiles"].c[name]
            op.add_column("site_profiles", sa.Column(name, source.type, nullable=True))
    Base.metadata.tables["site_sample_sets"].create(bind, checkfirst=True)
    install_guards(bind, STAGE1_TABLES)


def downgrade():
    raise RuntimeError("Profile/sample history must be retained. Restore a verified pre-010 backup.")
