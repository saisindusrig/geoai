"""Personal project folders for the creative dashboard.

Revision ID: 004
Revises: 003
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("project_folders"):
        op.create_table(
            "project_folders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("color", sa.String(20), nullable=False, server_default="sage"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("user_id", "name", name="uq_project_folders_user_name"),
        )
        op.create_index("ix_project_folders_user_id", "project_folders", ["user_id"])

    project_columns = {column["name"] for column in inspect(bind).get_columns("projects")}
    if "folder_id" not in project_columns:
        with op.batch_alter_table("projects") as batch_op:
            batch_op.add_column(sa.Column("folder_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_projects_folder_id_project_folders",
                "project_folders",
                ["folder_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_projects_folder_id", ["folder_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("projects"):
        columns = {column["name"] for column in inspect(bind).get_columns("projects")}
        if "folder_id" in columns:
            with op.batch_alter_table("projects") as batch_op:
                batch_op.drop_column("folder_id")
    if inspect(bind).has_table("project_folders"):
        op.drop_table("project_folders")
