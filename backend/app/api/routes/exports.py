import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.routes.estimates import latest_estimate
from app.api.routes.projects import get_owned_project
from app.core.disclaimer import DISCLAIMER
from app.core.security import get_current_user, get_current_user_id
from app.db.models import DesignScenario, GeneratedFile, ModelRevision, SiteAnalysis, User
from app.db.session import get_db
from app.services.exports.csv_export import build_boq_csv
from app.services.exports.geojson_export import build_geojson
from app.services.exports.pdf_report import build_pdf
from app.services.design.editable_model import document_to_geometry_spec
from app.services.exports.gltf_export import generate_glb
from app.services.storage import normalize_file_url
from app.services.usage import enforce_usage_limit, record_usage_event

router = APIRouter(prefix="/api/projects/{project_id}/exports", tags=["exports"])


def _enforce_export(
    db: Session,
    user: User,
    project_id: int,
    event_type: str,
    request: Request | None = None,
) -> None:
    enforce_usage_limit(db, user, event_type, project_id=project_id, request=request)
    record_usage_event(db, user_id=user.id, event_type=event_type, project_id=project_id)


def _latest_scenario(db: Session, project_id: int) -> DesignScenario | None:
    return (
        db.query(DesignScenario)
        .filter(DesignScenario.project_id == project_id, DesignScenario.status == "completed")
        .order_by(DesignScenario.created_at.desc())
        .first()
    )


def _latest_analysis(db: Session, project_id: int) -> SiteAnalysis | None:
    return (
        db.query(SiteAnalysis)
        .filter(SiteAnalysis.project_id == project_id)
        .order_by(SiteAnalysis.created_at.desc())
        .first()
    )


@router.get("/model.glb")
def export_model_glb(
    project_id: int,
    request: Request,
    revision_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export an immutable editable-model revision as a semantic GLB."""
    get_owned_project(project_id, db, user.id)
    _enforce_export(db, user, project_id, "export.glb", request=request)
    query = db.query(ModelRevision).filter(ModelRevision.project_id == project_id)
    if revision_id is not None:
        revision = query.filter(ModelRevision.id == revision_id).first()
    else:
        revision = query.order_by(ModelRevision.created_at.desc(), ModelRevision.id.desc()).first()
    if revision is None:
        raise HTTPException(404, "No editable model revision is available")
    if revision.document_json.get("structural_layout"):
        from app.api.routes.structural_layout import require_layout_approval
        require_layout_approval(db, revision)
    data = generate_glb(document_to_geometry_spec(revision.document_json), quality="final")
    return Response(
        data,
        media_type="model/gltf-binary",
        headers={
            "Content-Disposition": (
                f"attachment; filename=project_{project_id}_revision_{revision.revision_number}.glb"
            )
        },
    )


@router.get("/csv")
def export_csv(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_owned_project(project_id, db, user.id)
    _enforce_export(db, user, project_id, "export.csv", request=request)
    estimate = latest_estimate(db, project_id)
    if estimate is None:
        fallback = "item_name,quantity,unit,rate,amount,note\n"
        fallback += f'"No estimate available",0,ea,0,0,"{DISCLAIMER}"\n'
        return Response(fallback, media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=boq_project_{project_id}.csv"})
    data = build_boq_csv(estimate.line_items_json or [], DISCLAIMER)
    return Response(data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=boq_project_{project_id}.csv"})


@router.get("/json")
def export_json(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user.id)
    _enforce_export(db, user, project_id, "export.json", request=request)
    scenario = _latest_scenario(db, project_id)
    analysis = _latest_analysis(db, project_id)
    estimate = latest_estimate(db, project_id)
    files = db.query(GeneratedFile).filter(GeneratedFile.project_id == project_id).all()
    payload = {
        "disclaimer": DISCLAIMER,
        "project": {
            "id": project.id, "name": project.name, "project_type": project.project_type,
            "status": project.status, "units": project.units,
            "location_name": project.location_name,
            "center_lat": project.center_lat, "center_lng": project.center_lng,
            "boundary_geojson": project.boundary_geojson,
            "alignment_geojson": project.alignment_geojson,
        },
        "site_analysis": {
            "area_sqm": analysis.area_sqm, "perimeter_m": analysis.perimeter_m,
            "elevation_min_m": analysis.elevation_min_m, "elevation_max_m": analysis.elevation_max_m,
            "slope_percent_estimate": analysis.slope_percent_estimate,
            "risks": analysis.risks_json,
        } if analysis else None,
        "scenario": {
            "id": scenario.id, "name": scenario.name,
            "input_parameters": scenario.input_parameters_json,
            "assumptions": scenario.assumptions_json,
        } if scenario else None,
        "design_output": scenario.design_output_json if scenario else None,
        "quantity_estimate": {
            "concrete_m3": estimate.concrete_m3, "cement_bags": estimate.cement_bags,
            "steel_kg": estimate.steel_kg, "excavation_m3": estimate.excavation_m3,
            "backfill_m3": estimate.backfill_m3, "formwork_sqm": estimate.formwork_sqm,
            "asphalt_m3": estimate.asphalt_m3, "pipe_length_m": estimate.pipe_length_m,
            "total_cost_estimate": estimate.total_cost_estimate,
            "line_items": estimate.line_items_json,
        } if estimate else None,
        "generated_files": [
            {
                "file_type": f.file_type,
                "file_url": normalize_file_url(f.file_url),
                "metadata": f.metadata_json,
            }
            for f in files
        ],
    }
    return Response(json.dumps(payload, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=project_{project_id}.json"})


@router.get("/geojson")
def export_geojson(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user.id)
    _enforce_export(db, user, project_id, "export.json", request=request)
    data = build_geojson(project, _latest_analysis(db, project_id))
    return Response(data, media_type="application/geo+json",
                    headers={"Content-Disposition": f"attachment; filename=project_{project_id}.geojson"})


@router.get("/pdf")
def export_pdf(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.project_validation import validate_project

    project = get_owned_project(project_id, db, user.id)
    _enforce_export(db, user, project_id, "export.pdf", request=request)
    scenario = _latest_scenario(db, project_id)
    validation = validate_project(db, project)
    data = build_pdf(
        project,
        _latest_analysis(db, project_id),
        scenario,
        latest_estimate(db, project_id),
        validation=validation,
    )
    return Response(data, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=report_project_{project_id}.pdf"})


@router.get("/dxf")
def export_dxf(project_id: int):
    raise HTTPException(501, "DXF export is a planned feature; use GLB/GeoJSON for now")


@router.get("/alpha-map.png")
def export_alpha_map(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    from app.services.survey.alpha_raster import generate_alpha_raster
    from app.services.survey.project_helpers import require_postgis, require_survey_tier

    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    require_survey_tier(project, "gis_grade")
    result = generate_alpha_raster(db, project)
    if not result.get("alpha_png_url"):
        raise HTTPException(503, "PNG preview unavailable; use alpha-map GeoTIFF")
    import httpx

    r = httpx.get(result["alpha_png_url"], follow_redirects=True)
    return Response(r.content, media_type="image/png",
                    headers={"Content-Disposition": f"attachment; filename=alpha_project_{project_id}.png"})


@router.get("/terrain.glb")
def export_terrain_glb(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    from app.services.survey.mesh_export import export_terrain_glb as _export
    from app.services.survey.project_helpers import require_postgis, require_survey_tier

    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    require_survey_tier(project, "survey_grade")
    try:
        url = _export(db, project)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    import httpx

    r = httpx.get(url, follow_redirects=True)
    return Response(r.content, media_type="model/gltf-binary",
                    headers={"Content-Disposition": f"attachment; filename=terrain_project_{project_id}.glb"})


@router.get("/roads.glb")
def export_roads_glb(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    from app.services.survey.mesh_export import export_roads_glb as _export
    from app.services.survey.project_helpers import require_postgis, require_survey_tier

    require_postgis()
    project = get_owned_project(project_id, db, user_id)
    require_survey_tier(project, "gis_grade")
    try:
        url = _export(db, project)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    import httpx

    r = httpx.get(url, follow_redirects=True)
    return Response(r.content, media_type="model/gltf-binary",
                    headers={"Content-Disposition": f"attachment; filename=roads_project_{project_id}.glb"})


@router.get("/accuracy-report.json")
def export_accuracy_report(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    from app.db.models import AccuracyReport

    get_owned_project(project_id, db, user_id)
    report = (
        db.query(AccuracyReport)
        .filter(AccuracyReport.project_id == project_id)
        .order_by(AccuracyReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(404, "No accuracy report; run POST /survey/validate first")
    return Response(json.dumps(report.report_json, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=accuracy_project_{project_id}.json"})


@router.get("/files")
def list_files(project_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    get_owned_project(project_id, db, user_id)
    files = (
        db.query(GeneratedFile)
        .filter(GeneratedFile.project_id == project_id)
        .order_by(GeneratedFile.created_at.desc())
        .all()
    )
    return [
        {
            "id": f.id,
            "file_type": f.file_type,
            "file_url": normalize_file_url(f.file_url),
            "scenario_id": f.design_scenario_id,
            "created_at": f.created_at,
        }
        for f in files
    ]
