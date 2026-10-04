"""Versioned editable 3D model documents.

Revision ID: 005
Revises: 004
Create Date: 2026-09-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("model_revisions"):
        op.create_table(
            "model_revisions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("design_scenario_id", sa.Integer(), sa.ForeignKey("design_scenarios.id"), nullable=False),
            sa.Column("revision_number", sa.Integer(), nullable=False),
            sa.Column("document_json", sa.JSON(), nullable=False),
            sa.Column("source", sa.String(32), nullable=False, server_default="manual_edit"),
            sa.Column("prompt", sa.Text(), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("design_scenario_id", "revision_number", name="uq_model_revision_number"),
        )
        op.create_index("ix_model_revisions_project_id", "model_revisions", ["project_id"])
        op.create_index("ix_model_revisions_design_scenario_id", "model_revisions", ["design_scenario_id"])
        op.create_index("ix_model_revisions_user_id", "model_revisions", ["user_id"])
        op.create_index("ix_model_revisions_created_at", "model_revisions", ["created_at"])

    for table in ("quantity_estimates", "generated_files"):
        columns = {column["name"] for column in inspect(bind).get_columns(table)}
        if "model_revision_id" not in columns:
            with op.batch_alter_table(table) as batch_op:
                batch_op.add_column(sa.Column("model_revision_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    f"fk_{table}_model_revision_id",
                    "model_revisions",
                    ["model_revision_id"],
                    ["id"],
                )
                batch_op.create_index(f"ix_{table}_model_revision_id", ["model_revision_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in ("quantity_estimates", "generated_files"):
        if inspector.has_table(table):
            columns = {column["name"] for column in inspect(bind).get_columns(table)}
            if "model_revision_id" in columns:
                with op.batch_alter_table(table) as batch_op:
                    batch_op.drop_column("model_revision_id")
    if inspector.has_table("model_revisions"):
        op.drop_table("model_revisions")
