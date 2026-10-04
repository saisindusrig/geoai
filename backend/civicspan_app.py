"""Lean GeoAI API entry point for the hackathon demo.

It deliberately avoids the legacy survey, raster, and PostGIS application
modules so the construction-concept demo can run with a small dependency footprint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, civicspan as geoai, project_folders, projects
from app.core.config import settings
from app.core.cors import build_cors_origin_regex, build_cors_origins
from app.db.init_db import _migrate_sqlite_schema
from app.db.models import Base, User
from app.db.session import SessionLocal, engine


def _init_geoai_storage() -> None:
    """Create only the saved-concept tables needed by the hackathon demo.

    The full legacy initializer also seeds a GLB demo asset, which is not part
    of this lean renderer and adds avoidable optional dependencies.
    """
    _migrate_sqlite_schema()
    Base.metadata.create_all(bind=engine)
    if settings.AUTH_REQUIRE_JWT:
        return
    db = SessionLocal()
    try:
        if db.get(User, 1) is None:
            db.add(
                User(
                    id=1,
                    name="Dev User",
                    email="dev@example.com",
                    role="admin",
                    plan="admin",
                )
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Keep the hackathon demo lean while still persisting saved concepts/folders.
    _init_geoai_storage()
    yield

app = FastAPI(
    title="GeoAI API",
    description="Site-aware construction concept planning powered by NVIDIA Nemotron on Nebius.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_origin_regex=build_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "geoai", "disclaimer": "Conceptual visualization only; not engineering advice."}


app.include_router(auth.router)
app.include_router(geoai.router)
app.include_router(projects.router)
app.include_router(project_folders.router)
