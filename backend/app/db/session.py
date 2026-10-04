"""Database engine selection.

Primary target is PostgreSQL + PostGIS (docker compose). For dev machines
without Docker, we fall back to SQLite: geometry is then stored only as
GeoJSON (JSON column) and spatial math is done in Python with Shapely.
"""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import BACKEND_DIR, settings

logger = logging.getLogger(__name__)

SQLITE_URL = f"sqlite:///{BACKEND_DIR / 'dev.db'}"


def _resolve_engine():
    url = settings.DATABASE_URL
    if url.startswith("postgresql"):
        try:
            engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL")
            return engine, True
        except Exception as exc:  # pragma: no cover - env dependent
            logger.warning("PostgreSQL unavailable (%s); falling back to SQLite", type(exc).__name__)
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    return engine, False


engine, IS_POSTGRES = _resolve_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
