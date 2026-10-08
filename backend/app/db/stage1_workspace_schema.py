"""Additive storage for profile current-state and bounded sample artifacts (010)."""
import sqlalchemy as sa
from app.db.stage1_schema_v1 import JSON


def extend(metadata):
    profiles = metadata.tables["site_profiles"]
    for column in (sa.Column("latest_version_id", sa.String(128)),
                   sa.Column("refresh_context", JSON), sa.Column("refresh_job_id", sa.String(128)),
                   sa.Column("refresh_error", sa.String(128))):
        if column.name not in profiles.c:
            profiles.append_column(column)
    samples = sa.Table("site_sample_sets", metadata,
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("profile_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("project_id", "id"),
        sa.ForeignKeyConstraint(["project_id", "profile_id"], ["site_profiles.project_id", "site_profiles.id"]),
        info={"stage1": True, "immutable": True})
    return {samples.name: samples}
