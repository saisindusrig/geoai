"""Alignment-driven local centerline helpers for procedural 3D generation."""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass

from app.services.design.geometry_utils import box, line_length_lnglat, line_to_local_xy

logger = logging.getLogger(__name__)

MIN_ALIGNMENT_LENGTH_M = 5.0


@dataclass(frozen=True)
class AlignmentContext:
    """Resolved alignment for segment-based corridor geometry."""

    mode: str  # "alignment" | "straight"
    length_m: float
    centerline_xy: list[tuple[float, float]]
    center_lng: float
    center_lat: float
    coords_lnglat: list[list[float]]


def parse_linestring_coords(alignment_geojson: dict | None) -> list[list[float]] | None:
    if not alignment_geojson or alignment_geojson.get("type") != "LineString":
        return None
    coords = alignment_geojson.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return None
    parsed: list[list[float]] = []
    for pt in coords:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            return None
        parsed.append([float(pt[0]), float(pt[1])])
    return parsed


def alignment_length_m(alignment_geojson: dict | None) -> float | None:
    coords = parse_linestring_coords(alignment_geojson)
    if coords is None:
        return None
    return float(line_length_lnglat(coords))


def polyline_length_xy(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _bearing_deg(x0: float, y0: float, x1: float, y1: float) -> float:
    return math.degrees(math.atan2(y1 - y0, x1 - x0))


def polyline_segments(points: list[tuple[float, float]]) -> list[dict]:
    """Segment metadata for corridor meshing: length, midpoint, bearing."""
    segments: list[dict] = []
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        length_m = math.hypot(x1 - x0, y1 - y0)
        if length_m < 1e-6:
            continue
        segments.append(
            {
                "length_m": length_m,
                "mid_x": (x0 + x1) / 2,
                "mid_y": (y0 + y1) / 2,
                "bearing_deg": _bearing_deg(x0, y0, x1, y1),
                "start": (x0, y0),
                "end": (x1, y1),
                "station_m": 0.0,
            }
        )
    return segments


def assign_segment_stations(
    segments: list[dict],
    points: list[tuple[float, float]],
    total_length_m: float,
) -> None:
    """Map each segment midpoint to chainage (m) along alignment."""
    xy_total = polyline_length_xy(points)
    cumulative = 0.0
    for seg in segments:
        mid_xy = cumulative + seg["length_m"] / 2
        seg["station_m"] = (mid_xy / xy_total * total_length_m) if xy_total > 1e-6 else 0.0
        cumulative += seg["length_m"]


def sample_station(
    points: list[tuple[float, float]],
    station_m: float,
) -> tuple[float, float, float]:
    """Return (x, y, bearing_deg) at distance station_m from polyline start."""
    if not points:
        return 0.0, 0.0, 0.0
    if len(points) == 1:
        return points[0][0], points[0][1], 0.0

    remaining = max(0.0, station_m)
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        seg_len = math.hypot(x1 - x0, y1 - y0)
        if seg_len < 1e-6:
            continue
        if remaining <= seg_len or i == len(points) - 2:
            t = 0.0 if seg_len < 1e-6 else min(1.0, remaining / seg_len)
            return (
                x0 + t * (x1 - x0),
                y0 + t * (y1 - y0),
                _bearing_deg(x0, y0, x1, y1),
            )
        remaining -= seg_len
    x0, y0 = points[-2]
    x1, y1 = points[-1]
    return x1, y1, _bearing_deg(x0, y0, x1, y1)


def pier_stations(total_length_m: float, pier_count: int) -> list[float]:
    if pier_count <= 1:
        return [0.0]
    if pier_count == 2:
        return [0.0, total_length_m]
    step = total_length_m / (pier_count - 1)
    return [i * step for i in range(pier_count)]


def corridor_segment_boxes(
    segments: list[dict],
    *,
    width_m: float,
    thickness_m: float,
    z_center: float | list[float] | Callable[[dict], float],
    layer: str,
    name_prefix: str,
) -> list[dict]:
    """Place rotated box primitives along each centerline segment."""
    if isinstance(z_center, list):
        z_values = z_center
    elif callable(z_center):
        z_values = [float(z_center(seg)) for seg in segments]
    else:
        z_values = [float(z_center) for _ in segments]

    objects: list[dict] = []
    for idx, seg in enumerate(segments):
        objects.append(
            box(
                f"{name_prefix}_{idx + 1}",
                layer,
                (seg["mid_x"], seg["mid_y"], z_values[idx]),
                (seg["length_m"], width_m, thickness_m),
                rotation_z_deg=seg["bearing_deg"],
            )
        )
    return objects


def offset_corridor_segment_boxes(
    segments: list[dict],
    *,
    offset_m: float,
    side: str,
    width_m: float,
    thickness_m: float,
    z_center: float | list[float] | Callable[[dict], float],
    layer: str,
    name_prefix: str,
) -> list[dict]:
    """Corridor boxes offset perpendicular to each segment centerline."""
    shifted: list[dict] = []
    for seg in segments:
        mx, my = offset_point(seg["mid_x"], seg["mid_y"], seg["bearing_deg"], offset_m, side)
        shifted.append({**seg, "mid_x": mx, "mid_y": my})
    return corridor_segment_boxes(
        shifted,
        width_m=width_m,
        thickness_m=thickness_m,
        z_center=z_center,
        layer=layer,
        name_prefix=name_prefix,
    )


def offset_point(x: float, y: float, bearing_deg: float, offset_m: float, side: str) -> tuple[float, float]:
    """Offset point perpendicular to bearing. side='left'|'right'."""
    rad = math.radians(bearing_deg)
    sign = 1.0 if side == "left" else -1.0
    nx = -math.sin(rad) * sign
    ny = math.cos(rad) * sign
    return x + nx * offset_m, y + ny * offset_m


def resolve_alignment_context(
    alignment_geojson: dict | None,
    center_lng: float | None,
    center_lat: float | None,
    *,
    min_length_m: float = MIN_ALIGNMENT_LENGTH_M,
) -> AlignmentContext | None:
    coords = parse_linestring_coords(alignment_geojson)
    if coords is None:
        return None

    length_m = float(line_length_lnglat(coords))
    if length_m < min_length_m:
        logger.info(
            "Alignment too short (%.1fm < %.1fm); will use straight fallback",
            length_m,
            min_length_m,
        )
        return None

    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    anchor_lng = center_lng if center_lng is not None else (min(lngs) + max(lngs)) / 2
    anchor_lat = center_lat if center_lat is not None else (min(lats) + max(lats)) / 2

    centerline_xy = line_to_local_xy(coords, anchor_lng, anchor_lat)
    xy_length = polyline_length_xy(centerline_xy)
    if xy_length < min_length_m:
        logger.info(
            "Local centerline too short (%.1fm); will use straight fallback",
            xy_length,
        )
        return None

    return AlignmentContext(
        mode="alignment",
        length_m=length_m,
        centerline_xy=centerline_xy,
        center_lng=anchor_lng,
        center_lat=anchor_lat,
        coords_lnglat=coords,
    )
