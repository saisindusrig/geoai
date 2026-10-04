"""Elevation profile sampling and smoothing for alignment-driven 3D generation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.design.alignment_geometry import AlignmentContext
from app.services.geospatial import spatial_analysis, terrain

logger = logging.getLogger(__name__)

DEFAULT_FLAT_ELEVATION_M = 100.0
SMOOTH_WINDOW = 3
MIN_PROFILE_VARIATION_M = 0.15


@dataclass
class ElevationProfile:
    """Station elevations along alignment; z_relative_m is meters above route start."""

    mode: str  # "profile" | "flat"
    assumed: bool
    provider: str
    stations: list[dict[str, float]] = field(default_factory=list)
    min_elevation_m: float = 0.0
    max_elevation_m: float = 0.0
    max_grade_percent: float = 0.0

    def z_at_station(self, station_m: float) -> float:
        """Relative ground elevation (m) at chainage station_m."""
        if not self.stations:
            return 0.0
        if station_m <= self.stations[0]["station_m"]:
            return self.stations[0]["z_relative_m"]
        if station_m >= self.stations[-1]["station_m"]:
            return self.stations[-1]["z_relative_m"]
        for i in range(len(self.stations) - 1):
            a = self.stations[i]
            b = self.stations[i + 1]
            if a["station_m"] <= station_m <= b["station_m"]:
                span = b["station_m"] - a["station_m"]
                if span <= 1e-6:
                    return a["z_relative_m"]
                t = (station_m - a["station_m"]) / span
                return a["z_relative_m"] + t * (b["z_relative_m"] - a["z_relative_m"])
        return self.stations[-1]["z_relative_m"]

    def cache_signature(self) -> str:
        return f"{self.mode}:{self.min_elevation_m:.1f}:{self.max_elevation_m:.1f}:{self.max_grade_percent:.2f}"

    def to_spec_metadata(self) -> dict[str, Any]:
        return {
            "elevation_mode": self.mode,
            "elevation_assumed": self.assumed,
            "elevation_provider": self.provider,
            "min_elevation_m": round(self.min_elevation_m, 2),
            "max_elevation_m": round(self.max_elevation_m, 2),
            "max_grade_percent": round(self.max_grade_percent, 2),
        }


def smooth_elevations(values: list[float], window: int = SMOOTH_WINDOW) -> list[float]:
    if window <= 1 or len(values) < 3:
        return list(values)
    half = window // 2
    out: list[float] = []
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def compute_max_grade_percent(stations: list[dict[str, float]]) -> float:
    max_grade = 0.0
    for i in range(len(stations) - 1):
        a, b = stations[i], stations[i + 1]
        span = b["station_m"] - a["station_m"]
        if span <= 1e-6:
            continue
        rise = b["elevation_m"] - a["elevation_m"]
        max_grade = max(max_grade, abs(rise / span * 100.0))
    return max_grade


def build_profile_from_samples(
    *,
    length_m: float,
    distances_m: list[float],
    elevations_m: list[float],
    provider: str = "test",
    assumed: bool = False,
) -> ElevationProfile:
    """Build profile from pre-sampled station/elevation pairs (sync, for tests)."""
    if not distances_m or not elevations_m:
        return flat_profile(length_m, assumed=assumed, provider=provider)

    smoothed = smooth_elevations(elevations_m)
    base = smoothed[0]
    variation = max(smoothed) - min(smoothed)
    mode = "flat" if variation < MIN_PROFILE_VARIATION_M else "profile"

    stations: list[dict[str, float]] = []
    for idx, (station_m, elev) in enumerate(zip(distances_m, smoothed)):
        grade = 0.0
        if idx + 1 < len(smoothed):
            span = distances_m[idx + 1] - station_m
            if span > 1e-6:
                grade = (smoothed[idx + 1] - elev) / span * 100.0
        stations.append(
            {
                "station_m": float(station_m),
                "elevation_m": float(elev),
                "z_relative_m": float(elev - base),
                "grade_percent": float(grade),
            }
        )

    profile = ElevationProfile(
        mode=mode,
        assumed=assumed,
        provider=provider,
        stations=stations,
        min_elevation_m=min(smoothed),
        max_elevation_m=max(smoothed),
        max_grade_percent=compute_max_grade_percent(stations),
    )
    logger.info(
        "Elevation profile: mode=%s provider=%s min=%.1fm max=%.1fm max_grade=%.2f%%",
        profile.mode,
        profile.provider,
        profile.min_elevation_m,
        profile.max_elevation_m,
        profile.max_grade_percent,
    )
    return profile


def flat_profile(
    length_m: float,
    *,
    assumed: bool = True,
    provider: str = "flat-fallback",
    base_elevation_m: float = DEFAULT_FLAT_ELEVATION_M,
) -> ElevationProfile:
    stations = [
        {
            "station_m": 0.0,
            "elevation_m": base_elevation_m,
            "z_relative_m": 0.0,
            "grade_percent": 0.0,
        },
        {
            "station_m": max(length_m, 1.0),
            "elevation_m": base_elevation_m,
            "z_relative_m": 0.0,
            "grade_percent": 0.0,
        },
    ]
    logger.info("Elevation profile: flat fallback (assumed=%s)", assumed)
    return ElevationProfile(
        mode="flat",
        assumed=assumed,
        provider=provider,
        stations=stations,
        min_elevation_m=base_elevation_m,
        max_elevation_m=base_elevation_m,
        max_grade_percent=0.0,
    )


async def build_elevation_profile(
    alignment_geojson: dict | None,
    alignment_ctx: AlignmentContext | None,
    site_ctx: dict | None = None,
    *,
    num_samples: int = 30,
) -> ElevationProfile:
    """Sample terrain elevation along alignment; fall back to flat when unavailable."""
    length_m = alignment_ctx.length_m if alignment_ctx else 500.0
    line_geojson = None
    if alignment_ctx is not None:
        line_geojson = {"type": "LineString", "coordinates": alignment_ctx.coords_lnglat}
    elif alignment_geojson and alignment_geojson.get("type") == "LineString":
        line_geojson = alignment_geojson
        length_m = spatial_analysis.line_length_m(line_geojson)

    if line_geojson is None:
        base = DEFAULT_FLAT_ELEVATION_M
        if site_ctx and site_ctx.get("elevation_min_m") is not None:
            base = float(site_ctx["elevation_min_m"])
        return flat_profile(length_m, assumed=True, base_elevation_m=base)

    sample_pts = spatial_analysis.sample_line_points(line_geojson, num_samples=num_samples)
    if len(sample_pts) < 2:
        return flat_profile(length_m, assumed=True)

    elev_result = await terrain.sample_elevations(sample_pts)
    elevations = elev_result["elevations_m"]
    if any(value is None for value in elevations):
        # Conceptual geometry can still be generated in a local frame; this
        # zero is a local design plane, never a measured terrain elevation.
        return flat_profile(length_m, assumed=True, base_elevation_m=0, provider="conceptual-unplaced")
    distances = [length_m * i / max(1, len(elevations) - 1) for i in range(len(elevations))]

    profile = build_profile_from_samples(
        length_m=length_m,
        distances_m=distances,
        elevations_m=elevations,
        provider=str(elev_result.get("provider", "unknown")),
        assumed=bool(elev_result.get("assumed", False)),
    )
    if elev_result.get("assumed"):
        profile.mode = "flat"
    return profile
