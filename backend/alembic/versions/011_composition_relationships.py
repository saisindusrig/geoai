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
        triggers=[]
        if bind.dialect.name=="sqlite":
            # SQLite validates other tables' triggers while renaming the batch
            # replacement. Retention guards on assets also refer to this table.
            # Keep the whole replacement/guard restoration in a real SQLite
            # transaction (legacy sqlite3 SELECT/DDL does not start one).
            raw=bind.connection.driver_connection
            if not raw.in_transaction:
                bind.exec_driver_sql("BEGIN IMMEDIATE")
            triggers=bind.exec_driver_sql("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%asset_relationships%'").all()
            for name,_ in triggers:
                quoted=name.replace('"','""')
                bind.exec_driver_sql(f'DROP TRIGGER "{quoted}"')
        with op.batch_alter_table("asset_relationships") as batch:
            batch.drop_constraint(kind["name"],type_="check")
            batch.create_check_constraint("ck_asset_relationships_1",KIND_CHECK)
        # Restore custom triggers too; install_guards refreshes Stage 1 guards.
        for _,sql in triggers:
            bind.exec_driver_sql(sql)
    install_guards(bind,STAGE1_TABLES)


def downgrade():
    raise RuntimeError("Composition history must be preserved. Restore a verified pre-011 backup.")
