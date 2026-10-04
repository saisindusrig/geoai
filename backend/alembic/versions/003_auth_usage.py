"""Incremental schema: auth, audit, usage tracking."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _pg_table_exists(bind, table_name: str) -> bool:
    return bool(
        bind.execute(
            text("SELECT to_regclass(:qualified) IS NOT NULL"),
            {"qualified": f"public.{table_name}"},
        ).scalar()
    )


def _table_exists(bind, table_name: str, is_pg: bool) -> bool:
    if is_pg:
        return _pg_table_exists(bind, table_name)
    return inspect(bind).has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)")
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user' NOT NULL")
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(20) DEFAULT 'free' NOT NULL")
    else:
        inspector = inspect(bind)
        user_cols = {c["name"] for c in inspector.get_columns("users")}
        with op.batch_alter_table("users") as batch_op:
            if "password_hash" not in user_cols:
                batch_op.add_column(sa.Column("password_hash", sa.String(255), nullable=True))
            if "role" not in user_cols:
                batch_op.add_column(sa.Column("role", sa.String(20), server_default="user", nullable=False))
            if "plan" not in user_cols:
                batch_op.add_column(sa.Column("plan", sa.String(20), server_default="free", nullable=False))

    # Revision 001 create_all may already include these tables on fresh installs.
    if not _table_exists(bind, "audit_logs", is_pg):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
            sa.Column("action", sa.String(100), nullable=False, index=True),
            sa.Column("entity_type", sa.String(100), nullable=True, index=True),
            sa.Column("entity_id", sa.String(100), nullable=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True, index=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(512), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, index=True),
        )

    if not _table_exists(bind, "usage_events", is_pg):
        op.create_table(
            "usage_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True, index=True),
            sa.Column("event_type", sa.String(64), nullable=False, index=True),
            sa.Column("units", sa.Integer(), server_default="1", nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, index=True),
        )


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("audit_logs")
