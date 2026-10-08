"""Shared project-scoped persistence helpers. All commands own their transaction."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from fastapi import HTTPException
from app.db.models import Base, Project


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False).encode()).hexdigest()


def identity(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, ":".join(map(str, parts))))


def now():
    return datetime.now(timezone.utc).isoformat()


def utc_timestamp(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def table(name):
    return Base.metadata.tables[name]


def error(status, code, message):
    raise HTTPException(status, {"code": code, "message": message})


def lock_project(db, project_id):
    # An actual write serializes commands on SQLite too; FOR UPDATE alone does not.
    db.execute(sa.update(Project).where(Project.id == project_id).values(id=Project.id))


def owned_row(db, name, project_id, row_id):
    t = table(name)
    if isinstance(t.c.id.type, sa.Integer):
        try:
            row_id = int(row_id)
        except (ValueError, TypeError):
            error(404, "NOT_FOUND", "Referenced resource not found")
    row = db.execute(sa.select(t).where(t.c.id == row_id, t.c.project_id == project_id)).mappings().first()
    if not row:
        error(404, "NOT_FOUND", "Referenced resource not found")
    return dict(row)


def rows(db, name, project_id):
    t = table(name)
    return [dict(r) for r in db.execute(sa.select(t).where(t.c.project_id == project_id)).mappings()]


def insert(db, table_name, **values):
    db.execute(table(table_name).insert().values(**values))


def update(db, name, project_id, row_id, **values):
    t = table(name)
    db.execute(t.update().where(t.c.id == row_id, t.c.project_id == project_id).values(**values))
