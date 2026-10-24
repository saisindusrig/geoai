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
from app.core.production import enforce_production_security, log_startup_warnings, production_readiness
from app.core.sentry import init_sentry
from app.db.init_db import init_db
from app.middleware.request_logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    enforce_production_security()
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
    title="StruvoCivil API",
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
    expose_headers=["Content-Disposition", "X-Request-ID"],
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
from app.api.routes import site_workspace
app.include_router(site_workspace.router)
app.include_router(geoai.router)
from app.api.routes import cad_experimental
app.include_router(cad_experimental.router)
from app.api.routes import opensees
app.include_router(opensees.router)
from app.api.routes import physical_columns
app.include_router(physical_columns.router)
from app.api.routes import column_agent
app.include_router(column_agent.router)
from app.api.routes import elastic_frames
app.include_router(elastic_frames.router)

from app.api.routes import physical_frames
app.include_router(physical_frames.router)

from app.api.routes import slab_transfers
app.include_router(slab_transfers.router)

from app.api.routes import foundation_interfaces
app.include_router(foundation_interfaces.router)

from app.api.routes import anchor_contacts
app.include_router(anchor_contacts.router)

from app.api.routes import anchor_contacts_3d
app.include_router(anchor_contacts_3d.router)
from app.api.routes import connection_inputs
app.include_router(connection_inputs.router)
from app.api.routes import engineering_study
app.include_router(engineering_study.router)
from app.api.routes import drawing_cad
app.include_router(drawing_cad.router)
from app.api.routes import cad_frames
app.include_router(cad_frames.router)

from app.api.routes import cad_soil
app.include_router(cad_soil.router)

from app.api.routes import footing_transport
app.include_router(footing_transport.router)

from app.api.routes import soil_contact
app.include_router(soil_contact.router)

from app.api.routes import soil_profile
app.include_router(soil_profile.router)

from app.api.routes import bearing_capacity
app.include_router(bearing_capacity.router)

from app.api.routes import footing_flexure
app.include_router(footing_flexure.router)

from app.api.routes import rc_flexure
app.include_router(rc_flexure.router)
from app.api.routes import foundation_system
app.include_router(foundation_system.router)

from app.api.routes import spatial_frames
app.include_router(spatial_frames.router)
from app.api.routes import coupled_floors
app.include_router(coupled_floors.router)
from app.api.routes import analysis_capabilities
app.include_router(analysis_capabilities.router)

from app.api.routes import runtime_diagnostics
app.include_router(runtime_diagnostics.router)
from app.api.routes import site_assistant
app.include_router(site_assistant.router)
