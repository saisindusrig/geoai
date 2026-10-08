"""Expand relationship semantics without replacing existing assets or edge history."""
import sqlalchemy as sa
from alembic import op

revision="011"
down_revision="010"
branch_labels=None
depends_on=None


def upgrade():
    from app.db.stage1_composition_schema import KIND_CHECK
    from app.db.models import STAGE1_TABLES
    from app.db.stage1_schema_v1 import install_guards
    bind=op.get_bind()
    checks=sa.inspect(bind).get_check_constraints("asset_relationships")
    if not any("HOSTED_BY" in c["sqltext"] for c in checks):
        kind=next(c for c in checks if "kind IN" in c["sqltext"])
        with op.batch_alter_table("asset_relationships") as batch:
            batch.drop_constraint(kind["name"],type_="check")
            batch.create_check_constraint("ck_asset_relationships_1",KIND_CHECK)
    install_guards(bind,STAGE1_TABLES)


def downgrade():
    raise RuntimeError("Composition history must be preserved; restore a verified pre-011 backup.")
