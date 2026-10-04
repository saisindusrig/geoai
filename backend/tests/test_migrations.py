"""Alembic migration smoke tests."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_head_sqlite(tmp_path):
    db_path = tmp_path / "migration_test.db"
    url = f"sqlite:///{db_path.as_posix()}"

    env = os.environ.copy()
    env["DATABASE_URL"] = url

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
    )

    engine = create_engine(url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert version == "006"
        for table in ("terrain_dataset_versions", "model_placements", "ground_samples", "survey_validation_runs", "engineering_analyses", "engineering_audit_events"):
            assert conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"), {"name": table}).scalar() == table

        inspector = inspect(conn)
        for table in (
            "users",
            "projects",
            "project_folders",
            "survey_datasets",
            "engineering_layers",
            "audit_logs",
            "usage_events",
            "model_revisions",
        ):
            assert inspector.has_table(table), f"missing table {table}"

        user_cols = {c["name"] for c in inspector.get_columns("users")}
        assert {"password_hash", "role", "plan"}.issubset(user_cols)
        project_cols = {c["name"] for c in inspector.get_columns("projects")}
        assert "folder_id" in project_cols
        estimate_cols = {c["name"] for c in inspector.get_columns("quantity_estimates")}
        file_cols = {c["name"] for c in inspector.get_columns("generated_files")}
        assert "model_revision_id" in estimate_cols
        assert "model_revision_id" in file_cols
