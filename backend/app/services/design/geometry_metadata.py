"""Shared metadata envelope; no solver or quantity calculations."""
from __future__ import annotations
from app.services.design.alignment_geometry import AlignmentContext
from app.services.design.elevation_profile import ElevationProfile


def geometry_spec_metadata(
    length: float,
    geometry_mode: str,
    alignment_ctx: AlignmentContext | None,
    elevation_profile: ElevationProfile | None = None,
) -> dict:
    meta: dict = {
        "objects": [],
        "frame": "local_meters",
        "length_m": length,
        "geometry_mode": geometry_mode,
    }
    if alignment_ctx is not None:
        meta["alignment_anchor"] = {
            "center_lng": alignment_ctx.center_lng,
            "center_lat": alignment_ctx.center_lat,
        }
        meta["centerline_xy"] = [list(pt) for pt in alignment_ctx.centerline_xy]
    if elevation_profile is not None:
        meta.update(elevation_profile.to_spec_metadata())
    return meta
