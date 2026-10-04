"""Project readiness validation before design, BOQ, and exports."""

from __future__ import annotations

from typing import Any, Literal

from shapely.geometry import shape
from shapely.ops import unary_union
from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.core.project_catalog import ALIGNMENT_TYPES
from app.db.models import DesignScenario, GroundControlPoint, Project, QuantityEstimate, SurveyDataset
from app.db.session import IS_POSTGRES
from app.services.geospatial.crs import estimate_utm_epsg
from app.services.geospatial.spatial_analysis import line_length_m, polygon_metrics

Severity = Literal["error", "warning", "info"]


def _check(
    id_: str,
    label: str,
    passed: bool,
    detail: str,
    *,
    severity: Severity = "warning",
    action: str | None = None,
) -> dict[str, Any]:
    effective = severity if passed else ("error" if severity == "error" else severity)
    return {
        "id": id_,
        "label": label,
        "passed": passed,
        "severity": effective,
        "detail": detail,
        "action": action,
    }


def _polygon_valid(boundary: dict | None) -> tuple[bool, str, float]:
    if not boundary:
        return False, "Boundary is missing", 0.0
    if boundary.get("type") != "Polygon":
        return False, f"Expected Polygon, got {boundary.get('type')}", 0.0
    try:
        coords = boundary.get("coordinates") or []
        if not coords or not coords[0]:
            return False, "Boundary has no coordinates", 0.0
        ring = coords[0]
        if len(ring) < 4:
            return False, "Boundary polygon needs at least 4 ring points (closed)", 0.0
        if ring[0] != ring[-1]:
            return False, "Boundary polygon ring is not closed", 0.0
        geom = shape(boundary)
        if geom.is_empty or not geom.is_valid:
            return False, "Boundary geometry is empty or invalid", 0.0
        metrics = polygon_metrics(boundary)
        area = metrics["area_sqm"]
        if area <= 0:
            return False, "Boundary area is zero", 0.0
        return True, f"Area ≈ {area:,.0f} m²", area
    except Exception as exc:
        return False, f"Invalid boundary: {exc}", 0.0


def _alignment_valid(alignment: dict | None) -> tuple[bool, str, float]:
    if not alignment:
        return False, "Alignment is missing", 0.0
    if alignment.get("type") != "LineString":
        return False, f"Expected LineString, got {alignment.get('type')}", 0.0
    try:
        coords = alignment.get("coordinates") or []
        if len(coords) < 2:
            return False, "Alignment needs at least two points", 0.0
        length = line_length_m(alignment)
        if length <= 0:
            return False, "Alignment length is zero", 0.0
        return True, f"Length ≈ {length:,.0f} m", length
    except Exception as exc:
        return False, f"Invalid alignment: {exc}", 0.0


def _alignment_near_boundary(boundary: dict, alignment: dict, buffer_m: float = 50.0) -> tuple[bool, str]:
    try:
        b = shape(boundary)
        a = shape(alignment)
        # Approximate buffer in degrees (~111km per degree lat)
        buf_deg = buffer_m / 111_000.0
        region = unary_union([b, b.buffer(buf_deg)])
        if region.contains(a) or region.intersects(a.buffer(buf_deg)):
            return True, "Alignment is inside or near the project boundary"
        return False, "Alignment is outside project boundary — adjust site or alignment"
    except Exception as exc:
        return False, f"Could not verify alignment placement: {exc}"


def validate_project(db: Session, project: Project) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    recommended: list[str] = []

    has_location = bool(
        project.location_name
        or (project.center_lat is not None and project.center_lng is not None)
    )
    checks.append(
        _check(
            "location",
            "Project location",
            has_location,
            project.location_name or f"{project.center_lat}, {project.center_lng}" if has_location else "Location is missing",
            severity="error",
            action="Set a site location in the map or new project wizard",
        )
    )
    if not has_location:
        recommended.append("Search and save a project location on the map")

    b_ok, b_detail, b_area = _polygon_valid(project.boundary_geojson)
    checks.append(
        _check(
            "boundary",
            "Site boundary",
            b_ok,
            b_detail,
            severity="error",
            action="Draw or import a closed site boundary polygon",
        )
    )
    if not b_ok:
        recommended.append("Draw the site boundary on the map")

    needs_alignment = project.project_type in ALIGNMENT_TYPES
    a_ok, a_detail, a_len = _alignment_valid(project.alignment_geojson)
    if needs_alignment:
        checks.append(
            _check(
                "alignment",
                "Alignment / centerline",
                a_ok,
                a_detail if a_ok else "Alignment is missing for this project type",
                severity="error",
                action="Draw the road, pipeline, or flyover alignment on the map",
            )
        )
        if not a_ok:
            recommended.append("Draw the project alignment (centerline) on the map")
        elif b_ok and project.boundary_geojson and project.alignment_geojson:
            near, near_detail = _alignment_near_boundary(project.boundary_geojson, project.alignment_geojson)
            checks.append(
                _check(
                    "alignment_in_boundary",
                    "Alignment within site",
                    near,
                    near_detail,
                    severity="warning",
                    action="Move alignment inside the boundary or expand the site",
                )
            )
    elif project.alignment_geojson:
        checks.append(
            _check(
                "alignment",
                "Alignment (optional)",
                a_ok,
                a_detail,
                severity="info",
            )
        )

    crs_epsg = project.engineering_crs_epsg
    if crs_epsg:
        crs_detail = f"Engineering CRS: EPSG:{crs_epsg}"
        crs_ok = True
    elif project.center_lng is not None and project.center_lat is not None:
        crs_epsg = estimate_utm_epsg(project.center_lng, project.center_lat)
        crs_detail = f"Auto UTM available: EPSG:{crs_epsg} (not yet saved on project)"
        crs_ok = True
    else:
        crs_detail = "CRS is unknown — set location first"
        crs_ok = False
    checks.append(
        _check(
            "crs",
            "Coordinate reference system",
            crs_ok,
            crs_detail,
            severity="warning",
            action="Enable survey mode or set project location to derive UTM CRS",
        )
    )

    checks.append(
        _check(
            "postgis",
            "Database mode",
            IS_POSTGRES,
            "Full survey mode (PostGIS active)" if IS_POSTGRES else "Limited GIS mode (SQLite — survey imports restricted)",
            severity="info" if IS_POSTGRES else "warning",
            action=None if IS_POSTGRES else "Use Docker + PostGIS for full survey-grade workflows",
        )
    )

    dem_count = (
        db.query(SurveyDataset)
        .filter(SurveyDataset.project_id == project.id, SurveyDataset.kind.in_(["dem", "ortho", "geotiff"]))
        .count()
    )
    has_dem = dem_count > 0
    checks.append(
        _check(
            "dem",
            "Terrain / DEM data",
            has_dem,
            f"{dem_count} elevation dataset(s) imported" if has_dem else "DEM is missing — cut/fill and terrain mesh are approximate",
            severity="info" if has_dem else "warning",
            action=None if has_dem else "Import a GeoTIFF DEM in Survey Mode",
        )
    )
    if not has_dem and project.project_type in ALIGNMENT_TYPES:
        recommended.append("Import survey DEM for better cut/fill estimates")

    gcp_count = db.query(GroundControlPoint).filter(GroundControlPoint.project_id == project.id).count()
    checks.append(
        _check(
            "gcp",
            "Ground control points",
            gcp_count >= 3,
            f"{gcp_count} GCP(s) uploaded" if gcp_count else "No GCPs uploaded",
            severity="info" if gcp_count >= 3 else "warning",
            action=None if gcp_count >= 3 else "Upload GCP CSV in Survey Mode for survey-grade accuracy",
        )
    )

    tier = project.accuracy_tier or "visual"
    tier_labels = {
        "visual": "Visual only — not for quantity takeoff",
        "gis_grade": "GIS-grade — suitable for planning, not final construction drawings",
        "survey_grade": "Survey-grade — suitable for preliminary engineering quantities",
        "engineering_ready": "Engineering-ready — highest available tier for this project",
    }
    checks.append(
        _check(
            "accuracy_tier",
            "Accuracy tier",
            tier in tier_labels,
            tier_labels.get(tier, tier),
            severity="info" if tier in ("survey_grade", "engineering_ready") else "warning",
            action="Run survey validation after importing GCPs and DEM" if tier in ("visual", "gis_grade") else None,
        )
    )
    if tier in ("visual", "gis_grade"):
        recommended.append("This project is GIS-level only and not suitable for final construction drawings")

    scenario = (
        db.query(DesignScenario)
        .filter(DesignScenario.project_id == project.id, DesignScenario.status == "completed")
        .order_by(DesignScenario.created_at.desc())
        .first()
    )
    has_design = scenario is not None
    checks.append(
        _check(
            "design_scenario",
            "Completed design scenario",
            has_design,
            scenario.name if scenario else "No completed design — generate one in AI Design Studio",
            severity="warning",
            action="Open AI Design Studio and generate a design scenario",
        )
    )

    has_estimate = False
    if scenario:
        has_estimate = (
            db.query(QuantityEstimate)
            .filter(QuantityEstimate.design_scenario_id == scenario.id)
            .first()
            is not None
        )
    checks.append(
        _check(
            "estimate",
            "BOQ / quantity estimate",
            has_estimate,
            "Estimate available" if has_estimate else "No BOQ yet — generate a design first",
            severity="warning",
            action="Generate design to produce BOQ line items",
        )
    )

    errors = [c for c in checks if not c["passed"] and c["severity"] == "error"]
    warnings = [c for c in checks if not c["passed"] and c["severity"] == "warning"]

    ready_for_design = has_location and b_ok and (a_ok if needs_alignment else True)
    ready_for_boq = ready_for_design and has_design
    ready_for_export = ready_for_boq and has_estimate

    return {
        "project_id": project.id,
        "project_type": project.project_type,
        "accuracy_tier": tier,
        "postgis_available": IS_POSTGRES,
        "survey_mode_available": IS_POSTGRES,
        "database_mode": "postgis" if IS_POSTGRES else "sqlite",
        "ready_for_design": ready_for_design,
        "ready_for_boq": ready_for_boq,
        "ready_for_export": ready_for_export,
        "boundary_area_sqm": b_area if b_ok else None,
        "alignment_length_m": a_len if a_ok else None,
        "engineering_crs_epsg": project.engineering_crs_epsg or (crs_epsg if crs_ok else None),
        "checks": checks,
        "errors": [c["label"] for c in errors],
        "warnings": [c["detail"] for c in warnings],
        "recommended_next_steps": recommended[:6],
        "disclaimer": DISCLAIMER,
    }
