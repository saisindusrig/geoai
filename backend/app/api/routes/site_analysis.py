import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.core.security import get_current_user, get_current_user_id
from app.api.routes.projects import get_owned_project
from app.db.models import SiteAnalysis, User
from app.db.session import get_db
from app.services.geospatial import spatial_analysis, terrain
from app.services.geospatial.osm_overpass import fetch_osm_features
from app.services.jobs import _get_redis
from app.services.usage import enforce_usage_limit, record_usage_event

router = APIRouter(prefix="/api/projects/{project_id}/site-analysis", tags=["site-analysis"])

CACHE_TTL = 24 * 3600


def _analysis_out(a: SiteAnalysis) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "area_sqm": a.area_sqm,
        "perimeter_m": a.perimeter_m,
        "elevation_min_m": a.elevation_min_m,
        "elevation_max_m": a.elevation_max_m,
        "slope_percent_estimate": a.slope_percent_estimate,
        "nearby_roads_json": a.nearby_roads_json,
        "existing_buildings_json": a.existing_buildings_json,
        "risks_json": a.risks_json,
        "raw_geojson": a.raw_geojson,
        "created_at": a.created_at,
        "disclaimer": DISCLAIMER,
    }


@router.post("")
async def run_site_analysis(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user.id)
    enforce_usage_limit(db, user, "site_analysis.run", project_id=project.id, request=request)
    geojson = project.boundary_geojson or project.alignment_geojson
    if geojson is None:
        raise HTTPException(422, "Project has no boundary polygon or alignment; draw one first")

    if geojson["type"] == "Polygon":
        metrics = spatial_analysis.polygon_metrics(geojson)
    else:
        length = spatial_analysis.line_length_m(geojson)
        metrics = {"area_sqm": 0.0, "perimeter_m": length}

    bbox = spatial_analysis.bbox_with_buffer(geojson)
    cache_key = "osm:" + hashlib.sha1(json.dumps(bbox).encode()).hexdigest()
    redis = _get_redis()
    osm_data = None
    if redis is not None:
        cached = redis.get(cache_key)
        if cached:
            osm_data = json.loads(cached)
    if osm_data is None:
        osm_data = await fetch_osm_features(bbox)
        if redis is not None:
            redis.setex(cache_key, CACHE_TTL, json.dumps(osm_data))

    features = osm_data.get("features", [])
    roads = [f for f in features if f["properties"].get("category") == "road"]
    buildings = [f for f in features if f["properties"].get("category") == "building"]
    waterways = [f for f in features if f["properties"].get("category") == "waterway"]
    clashes = spatial_analysis.find_intersections(geojson, features) if geojson["type"] == "Polygon" else []

    # Sample elevations at bbox corners + center
    s, w, n, e = bbox
    sample_points = [(s, w), (s, e), (n, w), (n, e), ((s + n) / 2, (w + e) / 2)]
    elev = await terrain.sample_elevations(sample_points)
    elevations = [value for value in elev["elevations_m"] if value is not None]
    diag_m = spatial_analysis.line_length_m(
        {"type": "LineString", "coordinates": [[w, s], [e, n]]}
    )
    slope = spatial_analysis.slope_percent(elevations, diag_m)

    risks = [
        "No geotechnical soil data: bearing capacity unknown",
        "Underground utilities not surveyed",
    ]
    if elev["assumed"]:
        risks.append("Elevation data unavailable: terrain and slope are unknown")
    if osm_data.get("mock"):
        risks.append("OSM data unavailable: mock context shown")
    if waterways:
        risks.append(f"Waterway detected nearby ({len(waterways)} feature(s)): flood/hydrology study required")
    for clash in clashes:
        risks.append(
            f"Existing {clash['category']} '{clash['name']}' intersects the project boundary"
        )

    analysis = SiteAnalysis(
        project_id=project.id,
        area_sqm=round(metrics["area_sqm"], 1),
        perimeter_m=round(metrics["perimeter_m"], 1),
        elevation_min_m=min(elevations, default=None),
        elevation_max_m=max(elevations, default=None),
        slope_percent_estimate=slope,
        nearby_roads_json={"type": "FeatureCollection", "features": roads},
        existing_buildings_json={"type": "FeatureCollection", "features": buildings},
        risks_json=risks,
        raw_geojson=osm_data,
    )
    db.add(analysis)
    project.status = "analyzed"
    db.commit()
    db.refresh(analysis)
    record_usage_event(
        db,
        user_id=user.id,
        event_type="site_analysis.run",
        project_id=project.id,
        metadata={"analysis_id": analysis.id},
    )
    return _analysis_out(analysis)


@router.get("/elevation-profile")
async def elevation_profile(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    project = get_owned_project(project_id, db, user_id)
    alignment = project.alignment_geojson
    if alignment is None or alignment.get("type") != "LineString":
        raise HTTPException(422, "Draw an alignment line first for elevation profile")

    coords = alignment["coordinates"]
    total_m = spatial_analysis.line_length_m(alignment)
    sample_pts = spatial_analysis.sample_line_points(alignment, num_samples=30)
    elev = await terrain.sample_elevations(sample_pts)
    elevations = elev["elevations_m"]
    distances = [total_m * i / max(1, len(elevations) - 1) for i in range(len(elevations))]

    return {
        "points": [
            {"distance_m": round(distances[i], 1), "elevation_m": round(elevations[i], 2) if elevations[i] is not None else None}
            for i in range(len(elevations))
        ],
        "total_length_m": round(total_m, 1),
        "elevation_min_m": min((v for v in elevations if v is not None), default=None),
        "elevation_max_m": max((v for v in elevations if v is not None), default=None),
        "provider": elev["provider"],
        "assumed": elev["assumed"],
        "disclaimer": DISCLAIMER,
    }


@router.get("")
def get_latest_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    get_owned_project(project_id, db, user_id)
    analysis = (
        db.query(SiteAnalysis)
        .filter(SiteAnalysis.project_id == project_id)
        .order_by(SiteAnalysis.created_at.desc())
        .first()
    )
    if analysis is None:
        return None
    return _analysis_out(analysis)
