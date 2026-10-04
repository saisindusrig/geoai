"""AI design orchestration pipeline with staged progress and fast preview modes."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.project_catalog import project_type_family, asset_supports_generation
from app.db.models import DesignScenario, GeneratedFile, ModelRevision, Project, QuantityEstimate, SiteAnalysis, User
from app.services import jobs
from app.services.ai import design_planner, providers, safety_guardrails
from app.services.ai.schemas import DesignOutput
from app.services.calculations import boq, timeline
from app.services.usage import enforce_usage_limit, record_usage_event
from app.services.design import (
    building_generator,
    flyover_generator,
    pipeline_generator,
    road_generator,
)
from app.services.design.design_review import build_design_review
from app.services.design.scenario_summary import format_scenario_name
from app.services.design.design_validator import validate_design
from app.services.design.generation_cache import get_cached, scenario_input_hash, set_cached
from app.services.design.alignment_geometry import resolve_alignment_context
from app.services.design.elevation_profile import build_elevation_profile
from app.services.design.geometry_simplify import approximate_boq_from_inputs, simplify_geometry_spec
from app.services.design.editable_model import geometry_spec_to_document
from app.services.exports.gltf_export import generate_glb
from app.services.generation_telemetry import build_generation_diagnostics
from app.services.storage import save_file

logger = logging.getLogger(__name__)


def _audit_scenario_generated(
    db: Session,
    *,
    job_id: str | None,
    project_id: int,
    scenario_id: int,
    mode: str,
    status: str,
) -> None:
    from app.services.audit import log_audit_event

    user_id = None
    if job_id:
        job = jobs.get_status(job_id)
        if job:
            user_id = job.get("user_id")
    log_audit_event(
        db,
        user_id=user_id,
        action="scenario.generated",
        entity_type="scenario",
        entity_id=scenario_id,
        project_id=project_id,
        metadata={"mode": mode, "status": status},
    )

GENERATORS = {
    "flyover": flyover_generator.generate,
    "building": building_generator.generate,
    "pipeline": pipeline_generator.generate,
    "road": road_generator.generate,
}

GenerationMode = str  # fast_preview | balanced | high_detail


class StepTimer:
    def __init__(self) -> None:
        self.timings: dict[str, float] = {}
        self._starts: dict[str, float] = {}

    def start(self, name: str) -> None:
        self._starts[name] = time.perf_counter()

    def stop(self, name: str) -> None:
        started = self._starts.pop(name, None)
        if started is None:
            return
        self.timings[name] = round((time.perf_counter() - started) * 1000, 1)

    def log(self) -> None:
        parts = ", ".join(f"{k}={v}ms" for k, v in self.timings.items())
        logger.info("Design generation timings: %s", parts)


def _site_context(db: Session, project: Project) -> dict | None:
    analysis = (
        db.query(SiteAnalysis)
        .filter(SiteAnalysis.project_id == project.id)
        .order_by(SiteAnalysis.created_at.desc())
        .first()
    )
    if analysis is None:
        return None
    return {
        "area_sqm": analysis.area_sqm,
        "perimeter_m": analysis.perimeter_m,
        "elevation_min_m": analysis.elevation_min_m,
        "elevation_max_m": analysis.elevation_max_m,
        "slope_percent_estimate": analysis.slope_percent_estimate,
        "risks": analysis.risks_json,
    }


async def _resolve_design(
    db: Session,
    project: Project,
    params: dict,
    mode: str,
    timer: StepTimer,
    cache_key: str,
    *,
    site_ctx: dict | None = None,
    alignment_length_m: float | None = None,
    elevation_meta: dict | None = None,
    user_id: int | None = None,
) -> tuple[dict, str, dict, dict]:
    """Returns (design, provider, planning_metadata, merged_params)."""
    cached = get_cached(f"design:{cache_key}")
    if cached:
        logger.info("Using cached design layout for project %s", project.id)
        return (
            cached["design"],
            cached["provider"],
            cached.get("planning", {}),
            cached.get("merged_params", params),
        )

    timer.start("llm_planning")
    project_type = project.project_type

    if user_id is not None:
        user = db.get(User, user_id)
        if user is not None:
            enforce_usage_limit(db, user, "llm.plan", project_id=project.id)

    planner_result = await design_planner.plan_design(
        project_type=project_type,
        params=params,
        site_ctx=site_ctx,
        alignment_length_m=alignment_length_m,
        elevation_meta=elevation_meta,
    )
    merged_params = dict(planner_result.parameters)
    planning_meta = planner_result.to_metadata()

    if user_id is not None and planner_result.planning_mode == "llm":
        record_usage_event(
            db,
            user_id=user_id,
            event_type="llm.plan",
            project_id=project.id,
            metadata={"planning_mode": planner_result.planning_mode},
        )

    design_raw = providers._mock_generate(project_type, merged_params)
    if planner_result.planning_mode == "llm":
        provider = planner_result.llm_provider or "llm"
    elif planner_result.planning_mode == "fallback":
        provider = "template-fallback"
    else:
        provider = "template"
    timer.stop("llm_planning")

    try:
        design = DesignOutput.model_validate(design_raw).model_dump()
    except ValidationError:
        logger.warning("Template design failed schema validation, using raw mock")
        design_raw = providers._mock_generate(project_type, params)
        design = DesignOutput.model_validate(design_raw).model_dump()
        provider = "template-fallback"
        merged_params = dict(params)
        planning_meta["planning_mode"] = "fallback"
        planning_meta.setdefault("design_warnings", []).append("Template validation failed")

    design = safety_guardrails.enforce(design)
    for assumption in planner_result.assumptions:
        if assumption not in design["assumptions"]:
            design["assumptions"].append(assumption)
    for warning in planner_result.warnings:
        if warning not in design.get("risks", []):
            design.setdefault("risks", []).append(warning)

    design["ai_provider"] = provider
    design["planning"] = planning_meta

    set_cached(
        f"design:{cache_key}",
        {
            "design": design,
            "provider": provider,
            "planning": planning_meta,
            "merged_params": merged_params,
        },
    )
    return design, provider, planning_meta, merged_params


def _apply_scenario_name(
    scenario: DesignScenario,
    project: Project,
    params: dict,
    mode: str,
) -> None:
    scenario.name = format_scenario_name(
        project.project_type,
        params,
        mode,
        scenario.created_at,
    )


def _attach_validation_and_review(
    design: dict,
    *,
    project_type: str,
    params: dict,
    geometry_spec: dict,
    planning_meta: dict,
    quantities: dict,
    cost_summary: dict | None,
    preview_mode: bool,
    boq_approximate: bool,
    timer: StepTimer | None = None,
) -> dict:
    """Run deterministic validator and attach results to design + return review dict."""
    if timer is not None:
        timer.start("validation")
    validation = validate_design(
        project_type=project_type,
        params=params,
        geometry_spec=geometry_spec,
        planning_meta=planning_meta,
        preview_mode=preview_mode,
        boq_approximate=boq_approximate,
        design_assumptions=design.get("assumptions"),
    )
    review = build_design_review(
        project_type=project_type,
        params=params,
        geometry_spec=geometry_spec,
        planning_meta=planning_meta,
        validation=validation,
        cost_summary=cost_summary,
        quantities=quantities,
        preview_mode=preview_mode or boq_approximate,
    )
    design["validation"] = validation.to_dict()
    design["design_review"] = review
    if timer is not None:
        timer.stop("validation")
    return review


def _publish_job_diagnostics(
    job_id: str | None,
    timer: StepTimer,
    *,
    mode: str,
    provider: str,
    error_type: str | None = None,
    failed_stage: str | None = None,
) -> None:
    if not job_id:
        return
    current = jobs.get_status(job_id) or {}
    jobs.update_job(
        job_id,
        timings=timer.timings,
        diagnostics=build_generation_diagnostics(
            timer.timings,
            mode=mode,
            provider=provider,
            duration_ms=current.get("duration_ms"),
            error_type=error_type,
            failed_stage=failed_stage,
            cancel_requested=bool(current.get("cancel_requested")),
        ),
    )


def _stage(job_id: str | None, stage: str, *, message: str | None = None, **extra: Any) -> None:
    if not job_id:
        return
    jobs.ensure_not_cancelled(job_id)
    jobs.update_job(job_id, stage=stage, message=message, **extra)


def _persist_preview_file(
    db: Session,
    project: Project,
    scenario: DesignScenario,
    preview_url: str,
    provider: str,
) -> None:
    existing = (
        db.query(GeneratedFile)
        .filter(
            GeneratedFile.project_id == project.id,
            GeneratedFile.design_scenario_id == scenario.id,
            GeneratedFile.file_type == "glb-preview",
        )
        .first()
    )
    if existing:
        existing.file_url = preview_url
        existing.metadata_json = {"frame": "local_meters", "provider": provider, "quality": "preview"}
    else:
        db.add(
            GeneratedFile(
                project_id=project.id,
                design_scenario_id=scenario.id,
                file_type="glb-preview",
                file_url=preview_url,
                metadata_json={"frame": "local_meters", "provider": provider, "quality": "preview"},
            )
        )
    db.commit()


async def run_design_generation(
    db: Session,
    project: Project,
    scenario: DesignScenario,
    *,
    job_id: str | None = None,
    mode: GenerationMode = "balanced",
) -> dict:
    timer = StepTimer()
    params = dict(scenario.input_parameters_json or {})
    project_type = project.project_type
    if not asset_supports_generation(project_type):
        raise ValueError("Engineering generation is unavailable for this reference asset.")
    family = project_type_family(project_type)
    job_user_id = None
    if job_id:
        job = jobs.get_status(job_id)
        if job:
            job_user_id = job.get("user_id")
    cache_key = scenario_input_hash(
        project.id,
        project.boundary_geojson,
        project.alignment_geojson,
        params,
    )

    _stage(job_id, "queued", message="Preparing generation")
    _stage(job_id, "analyzing_site", message="Reading site geometry")

    timer.start("site_geometry")
    site_ctx = get_cached(f"site:{cache_key}")
    if site_ctx is None:
        site_ctx = _site_context(db, project)
        set_cached(f"site:{cache_key}", site_ctx)
    alignment_ctx = resolve_alignment_context(
        project.alignment_geojson,
        project.center_lng,
        project.center_lat,
    )
    if alignment_ctx is not None:
        params["length_m"] = round(alignment_ctx.length_m, 2)
        logger.info(
            "Using alignment-derived length_m=%.1f for project %s",
            alignment_ctx.length_m,
            project.id,
        )
    elif family in ("flyover", "road"):
        logger.info(
            "No valid alignment for project %s; using form length_m=%s",
            project.id,
            params.get("length_m"),
        )
    timer.stop("site_geometry")

    timer.start("terrain_elevation")
    elevation_profile = None
    if family in ("flyover", "road"):
        elev_cache_key = f"elevation:{cache_key}"
        elevation_profile = get_cached(elev_cache_key)
        if elevation_profile is None:
            elevation_profile = await build_elevation_profile(
                project.alignment_geojson,
                alignment_ctx,
                site_ctx,
            )
            set_cached(elev_cache_key, elevation_profile)
    timer.stop("terrain_elevation")

    _stage(job_id, "generating_layout", message="Generating layout")
    elevation_meta = elevation_profile.to_spec_metadata() if elevation_profile else None
    design, provider, planning_meta, params = await _resolve_design(
        db,
        project,
        params,
        mode,
        timer,
        cache_key,
        site_ctx=site_ctx,
        alignment_length_m=alignment_ctx.length_m if alignment_ctx else None,
        elevation_meta=elevation_meta,
        user_id=job_user_id,
    )
    if alignment_ctx is not None:
        design.setdefault("geometry", {})["length_m"] = round(alignment_ctx.length_m, 2)

    timer.start("geometry_3d")
    geom_cache_key = f"geometry:{cache_key}:{family}"
    if elevation_profile is not None:
        geom_cache_key = f"{geom_cache_key}:{elevation_profile.cache_signature()}"
    gen_result = get_cached(geom_cache_key)
    if gen_result is None:
        if family in ("flyover", "road"):
            gen_result = GENERATORS[family](
                params,
                design,
                alignment_ctx=alignment_ctx,
                elevation_profile=elevation_profile,
            )
        else:
            gen_result = GENERATORS[family](params, design)
        set_cached(geom_cache_key, gen_result)
    timer.stop("geometry_3d")

    quantities = gen_result["quantities"]
    spec = gen_result["geometry_spec"]
    preview_spec = simplify_geometry_spec(spec)
    prefix = f"projects/{project.id}/scenario_{scenario.id}"
    preview_url: str | None = None

    export_preview = mode in ("fast_preview", "balanced")
    export_final = mode in ("balanced", "high_detail")

    if export_preview:
        _stage(job_id, "generating_3d_preview", message="Generating 3D preview")
        jobs.ensure_not_cancelled(job_id)
        timer.start("glb_preview")
        preview_bytes = generate_glb(preview_spec, quality="preview")
        preview_url = save_file(f"{prefix}/preview.glb", preview_bytes, "model/gltf-binary")
        timer.stop("glb_preview")
        _persist_preview_file(db, project, scenario, preview_url, provider)

        if mode == "fast_preview":
            _stage(job_id, "calculating_boq", message="Estimating quantities")
            timer.start("boq_calculation")
            boq_result = approximate_boq_from_inputs(gen_result["boq_inputs"])
            timer.stop("boq_calculation")

            design["calculated"] = {
                "quantities": quantities,
                "derived": gen_result["derived"],
                "timeline": timeline.estimate_months(family, gen_result["timeline_driver"][1]),
                "cost_summary": boq_result["cost_summary"],
            }
            design["geometry_spec"] = preview_spec
            design["preview_mode"] = True

            design_review = _attach_validation_and_review(
                design,
                project_type=project_type,
                params=params,
                geometry_spec=preview_spec,
                planning_meta=planning_meta,
                quantities=quantities,
                cost_summary=boq_result["cost_summary"],
                preview_mode=True,
                boq_approximate=True,
                timer=timer,
            )

            _stage(job_id, "saving_result", message="Saving preview result")
            jobs.ensure_not_cancelled(job_id)
            timer.start("database_save")
            _apply_scenario_name(scenario, project, params, mode)
            scenario.design_output_json = design
            scenario.assumptions_json = design["assumptions"]
            scenario.status = "preview"
            db.commit()
            timer.stop("database_save")
            timer.log()

            result = {
                "scenario_id": scenario.id,
                "design": design,
                "quantities": quantities,
                "line_items": boq_result["line_items"],
                "cost_summary": boq_result["cost_summary"],
                "preview_glb_url": preview_url,
                "glb_url": preview_url,
                "mode": mode,
                "timings_ms": timer.timings,
                "planning": planning_meta,
                "validation": design["validation"],
                "design_review": design_review,
            }
            _stage(
                job_id,
                "completed",
                message="Fast preview ready",
                preview_ready=True,
                preview_glb_url=preview_url,
                timings=timer.timings,
            )
            _publish_job_diagnostics(job_id, timer, mode=mode, provider=provider)
            _audit_scenario_generated(
                db,
                job_id=job_id,
                project_id=project.id,
                scenario_id=scenario.id,
                mode=mode,
                status="preview",
            )
            return result

        _stage(
            job_id,
            "generating_3d_preview",
            message="Preview ready — final model generating",
            preview_ready=True,
            preview_glb_url=preview_url,
            progress=55,
        )

    if export_final:
        jobs.ensure_not_cancelled(job_id)
        _stage(job_id, "calculating_boq", message="Calculating BOQ")
        timer.start("boq_calculation")
        boq_result = boq.build_boq(db, gen_result["boq_inputs"])
        driver_name, driver_value = gen_result["timeline_driver"]
        schedule = timeline.estimate_months(family, driver_value)
        timer.stop("boq_calculation")

        design["calculated"] = {
            "quantities": quantities,
            "derived": gen_result["derived"],
            "timeline": schedule,
            "cost_summary": boq_result["cost_summary"],
        }
        design["geometry_spec"] = spec

        design_review = _attach_validation_and_review(
            design,
            project_type=project_type,
            params=params,
            geometry_spec=spec,
            planning_meta=planning_meta,
            quantities=quantities,
            cost_summary=boq_result["cost_summary"],
            preview_mode=False,
            boq_approximate=False,
            timer=timer,
        )

        _stage(job_id, "exporting_model", message="Exporting final model")
        jobs.ensure_not_cancelled(job_id)
        timer.start("glb_export")
        main_spec = {**spec, "objects": [o for o in spec["objects"] if o.get("layer") != "excavation"]}
        exc_spec = {**spec, "objects": [o for o in spec["objects"] if o.get("layer") == "excavation"]}
        quality = "final" if mode == "high_detail" else "final"
        glb_url = save_file(f"{prefix}/model.glb", generate_glb(main_spec, quality=quality), "model/gltf-binary")
        excavation_glb_url = None
        if exc_spec["objects"]:
            excavation_glb_url = save_file(
                f"{prefix}/excavation.glb",
                generate_glb(exc_spec, quality=quality),
                "model/gltf-binary",
            )
        timer.stop("glb_export")

        _stage(job_id, "saving_result", message="Saving result")
        jobs.ensure_not_cancelled(job_id)
        timer.start("database_save")
        _apply_scenario_name(scenario, project, params, mode)
        scenario.design_output_json = design
        scenario.assumptions_json = design["assumptions"]
        scenario.status = "completed"
        model_document = geometry_spec_to_document(project, scenario, spec)
        revision = ModelRevision(
            project_id=project.id,
            design_scenario_id=scenario.id,
            revision_number=1,
            document_json=model_document,
            source="ai_generate",
            user_id=job_user_id,
        )
        db.add(revision)
        db.flush()
        design["editable_model_revision_id"] = revision.id
        design["editable_model_revision_number"] = 1
        scenario.design_output_json = design
        estimate = QuantityEstimate(
            design_scenario_id=scenario.id,
            model_revision_id=revision.id,
            **quantities,
            total_cost_estimate=boq_result["cost_summary"]["total_medium"],
            line_items_json=boq_result["line_items"],
        )
        db.add(estimate)
        db.add(
            GeneratedFile(
                project_id=project.id,
                design_scenario_id=scenario.id,
                model_revision_id=revision.id,
                file_type="glb",
                file_url=glb_url,
                metadata_json={"frame": "local_meters", "provider": provider},
            )
        )
        if excavation_glb_url:
            db.add(
                GeneratedFile(
                    project_id=project.id,
                    design_scenario_id=scenario.id,
                    model_revision_id=revision.id,
                    file_type="glb-excavation",
                    file_url=excavation_glb_url,
                    metadata_json={"frame": "local_meters"},
                )
            )
        project.status = "designed"
        db.commit()
        db.refresh(estimate)
        timer.stop("database_save")
        timer.log()

        result = {
            "scenario_id": scenario.id,
            "design": design,
            "quantities": quantities,
            "line_items": boq_result["line_items"],
            "cost_summary": boq_result["cost_summary"],
            "timeline": schedule,
            "glb_url": glb_url,
            "preview_glb_url": preview_url,
            "excavation_glb_url": excavation_glb_url,
            "mode": mode,
            "timings_ms": timer.timings,
            "planning": planning_meta,
            "validation": design["validation"],
            "design_review": design_review,
        }
        _stage(
            job_id,
            "completed",
            message="Design generation completed",
            preview_ready=True,
            preview_glb_url=preview_url or glb_url,
            timings=timer.timings,
        )
        _publish_job_diagnostics(job_id, timer, mode=mode, provider=provider)
        _audit_scenario_generated(
            db,
            job_id=job_id,
            project_id=project.id,
            scenario_id=scenario.id,
            mode=mode,
            status="completed",
        )
        if job_user_id is not None:
            record_usage_event(
                db,
                user_id=job_user_id,
                event_type="generation.completed",
                project_id=project.id,
                metadata={"scenario_id": scenario.id, "mode": mode},
            )
        return result

    raise RuntimeError(f"Unsupported generation mode: {mode}")
