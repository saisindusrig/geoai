from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.cors import build_cors_origin_regex, build_cors_origins
from app.core.disclaimer import DISCLAIMER
from app.core.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.production import log_startup_warnings, production_readiness
from app.core.sentry import init_sentry
from app.db.init_db import init_db
from app.middleware.request_logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_sentry()
    init_db()
    log_startup_warnings()
    readiness = production_readiness()
    logger.info(
        "Startup readiness: deployment_ready=%s production_ready=%s critical=%s",
        readiness.get("deployment_ready"),
        readiness.get("production_ready"),
        readiness.get("critical_count"),
    )
    yield


app = FastAPI(
    title="sitegeoai API",
    description=f"Preliminary construction planning API. {DISCLAIMER}",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(RequestLoggingMiddleware)

_cors_origin_regex = build_cors_origin_regex()
app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(
    "CORS origins=%s netlify_regex=%s",
    build_cors_origins(),
    bool(_cors_origin_regex),
)

# Local storage files are served via authenticated route (see app.api.routes.files)
Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}


from app.api.routes import (  # noqa: E402
    engineering,
    admin_usage,
    ai,
    building_plans,
    audit,
    civicspan as geoai,
    auth,
    design_generate,
    estimates,
    exports,
    files,
    geocode,
    jobs,
    model_revisions,
    project_folders,
    projects,
    rates,
    site_analysis,
    site_suggestions,
    structural_layout,
    survey,
    system,
    templates,
    tiles,
    usage,
)

app.include_router(projects.router)
app.include_router(engineering.router)
app.include_router(project_folders.router)
app.include_router(files.router)
app.include_router(system.router)
app.include_router(survey.router)
app.include_router(auth.router)
app.include_router(geocode.router)
app.include_router(tiles.router)
app.include_router(site_analysis.router)
app.include_router(site_suggestions.router)
app.include_router(design_generate.router)
app.include_router(jobs.router)
app.include_router(model_revisions.router)
app.include_router(structural_layout.router)
app.include_router(estimates.router)
app.include_router(exports.router)
app.include_router(rates.router)
app.include_router(templates.router)
app.include_router(templates.public_router)
app.include_router(audit.router)
app.include_router(usage.router)
app.include_router(admin_usage.router)
app.include_router(ai.router)
app.include_router(building_plans.router)
app.include_router(geoai.router)
