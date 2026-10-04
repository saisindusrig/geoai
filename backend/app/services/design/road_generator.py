"""Road segment conceptual generator."""

from __future__ import annotations

import logging

from app.services.calculations import earthwork
from app.services.design.alignment_geometry import (
    AlignmentContext,
    assign_segment_stations,
    corridor_segment_boxes,
    offset_corridor_segment_boxes,
    offset_point,
    polyline_segments,
)
from app.services.design.elevation_profile import ElevationProfile
from app.services.design.geometry_utils import box

logger = logging.getLogger(__name__)


def _quantities_and_boq(
    length: float,
    width: float,
    lanes: int,
    asphalt_thk: float,
    base_thk: float,
    shoulder_w: float,
) -> tuple[dict, list[dict], dict]:
    strip_depth = asphalt_thk + base_thk + 0.15
    asphalt_vol = length * width * asphalt_thk
    base_vol = length * (width + 2 * shoulder_w) * base_thk
    excavation = earthwork.rectangular_excavation_m3(length, width + 2 * shoulder_w, strip_depth)

    quantities = {
        "concrete_m3": round(length * 0.12, 1),
        "cement_bags": round(length * 0.12 * 7.0),
        "steel_kg": round(length * 0.12 * 30),
        "rebar_kg": round(length * 0.12 * 30),
        "excavation_m3": round(excavation, 1),
        "backfill_m3": 0,
        "formwork_sqm": round(length * 0.5, 1),
        "asphalt_m3": round(asphalt_vol, 1),
        "pipe_length_m": 0,
        "pipe_diameter_mm": 0,
    }
    boq_inputs = [
        {
            "item_code": "EXC-SOIL",
            "item_name": "Formation excavation/stripping",
            "category": "earthwork",
            "quantity": quantities["excavation_m3"],
            "unit": "m3",
            "assumption": f"{round(strip_depth, 2)}m formation depth",
        },
        {
            "item_code": "ROAD-BASE",
            "item_name": "Granular base/WMM",
            "category": "road",
            "quantity": round(base_vol, 1),
            "unit": "m3",
            "assumption": f"{int(base_thk * 1000)}mm base",
        },
        {
            "item_code": "ASPHALT",
            "item_name": "Bituminous surfacing",
            "category": "road",
            "quantity": quantities["asphalt_m3"],
            "unit": "m3",
            "assumption": f"{int(asphalt_thk * 1000)}mm asphalt, {lanes} lanes",
        },
        {
            "item_code": "CONC-M25",
            "item_name": "Kerbs and drains concrete",
            "category": "concrete",
            "quantity": quantities["concrete_m3"],
            "unit": "m3",
            "assumption": "0.12 m3 per running meter allowance",
        },
    ]
    return quantities, boq_inputs, {"base_volume_m3": round(base_vol, 1), "lanes": lanes}


def _geometry_spec_meta(
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


def _ground_z(profile: ElevationProfile | None, station_m: float) -> float:
    if profile is None or profile.mode == "flat":
        return 0.0
    return profile.z_at_station(station_m)


def _straight_geometry(
    length: float,
    width: float,
    lanes: int,
    asphalt_thk: float,
    base_thk: float,
    shoulder_w: float,
) -> list[dict]:
    strip_depth = asphalt_thk + base_thk + 0.15
    objects = [
        box("excavation", "excavation", (0, 0, -strip_depth / 2), (length, width + 2 * shoulder_w, strip_depth)),
        box("base_course", "foundation", (0, 0, -asphalt_thk - base_thk / 2), (length, width + 2 * shoulder_w, base_thk)),
        box("pavement", "asphalt", (0, 0, -asphalt_thk / 2), (length, width, asphalt_thk)),
        box(
            "shoulder_left",
            "shoulder",
            (0, width / 2 + shoulder_w / 2, -asphalt_thk / 2),
            (length, shoulder_w, asphalt_thk),
        ),
        box(
            "shoulder_right",
            "shoulder",
            (0, -width / 2 - shoulder_w / 2, -asphalt_thk / 2),
            (length, shoulder_w, asphalt_thk),
        ),
        box("drain_left", "pipe_drain", (0, width / 2 + shoulder_w + 0.3, -0.3), (length, 0.6, 0.6)),
        box("drain_right", "pipe_drain", (0, -width / 2 - shoulder_w - 0.3, -0.3), (length, 0.6, 0.6)),
    ]
    for i in range(1, lanes):
        y = -width / 2 + i * (width / lanes)
        objects.append(box(f"lane_marking_{i}", "road_marking", (0, y, 0.005), (length, 0.15, 0.01)))
    return objects


def _alignment_geometry(
    alignment_ctx: AlignmentContext,
    width: float,
    lanes: int,
    asphalt_thk: float,
    base_thk: float,
    shoulder_w: float,
    elevation_profile: ElevationProfile | None = None,
) -> list[dict]:
    points = alignment_ctx.centerline_xy
    segments = polyline_segments(points)
    if not segments:
        return []
    assign_segment_stations(segments, points, alignment_ctx.length_m)

    strip_depth = asphalt_thk + base_thk + 0.15
    total_width = width + 2 * shoulder_w
    use_profile = elevation_profile is not None and elevation_profile.mode == "profile"

    def ground(seg: dict) -> float:
        return _ground_z(elevation_profile, seg["station_m"])

    if use_profile:
        excavation_z = lambda seg: ground(seg) - strip_depth / 2
        base_z = lambda seg: ground(seg) - asphalt_thk - base_thk / 2
        pavement_z = lambda seg: ground(seg) - asphalt_thk / 2
        shoulder_z = pavement_z
        drain_z = lambda seg: ground(seg) - 0.3
        marking_z = lambda seg: ground(seg) + 0.005
    else:
        excavation_z = -strip_depth / 2
        base_z = -asphalt_thk - base_thk / 2
        pavement_z = -asphalt_thk / 2
        shoulder_z = -asphalt_thk / 2
        drain_z = -0.3
        marking_z = 0.005

    objects: list[dict] = []

    objects.extend(
        corridor_segment_boxes(
            segments,
            width_m=total_width,
            thickness_m=strip_depth,
            z_center=excavation_z,
            layer="excavation",
            name_prefix="excavation_seg",
        )
    )
    objects.extend(
        corridor_segment_boxes(
            segments,
            width_m=total_width,
            thickness_m=base_thk,
            z_center=base_z,
            layer="foundation",
            name_prefix="base_seg",
        )
    )
    objects.extend(
        corridor_segment_boxes(
            segments,
            width_m=width,
            thickness_m=asphalt_thk,
            z_center=pavement_z,
            layer="asphalt",
            name_prefix="pavement_seg",
        )
    )
    objects.extend(
        offset_corridor_segment_boxes(
            segments,
            offset_m=width / 2 + shoulder_w / 2,
            side="left",
            width_m=shoulder_w,
            thickness_m=asphalt_thk,
            z_center=shoulder_z,
            layer="shoulder",
            name_prefix="shoulder_left_seg",
        )
    )
    objects.extend(
        offset_corridor_segment_boxes(
            segments,
            offset_m=width / 2 + shoulder_w / 2,
            side="right",
            width_m=shoulder_w,
            thickness_m=asphalt_thk,
            z_center=shoulder_z,
            layer="shoulder",
            name_prefix="shoulder_right_seg",
        )
    )

    drain_offset = width / 2 + shoulder_w + 0.3
    for idx, seg in enumerate(segments):
        lx, ly = offset_point(seg["mid_x"], seg["mid_y"], seg["bearing_deg"], drain_offset, "left")
        rx, ry = offset_point(seg["mid_x"], seg["mid_y"], seg["bearing_deg"], drain_offset, "right")
        dz = drain_z(seg) if use_profile else float(drain_z)
        objects.append(
            box(
                f"drain_left_{idx + 1}",
                "pipe_drain",
                (lx, ly, dz),
                (seg["length_m"], 0.6, 0.6),
                rotation_z_deg=seg["bearing_deg"],
            )
        )
        objects.append(
            box(
                f"drain_right_{idx + 1}",
                "pipe_drain",
                (rx, ry, dz),
                (seg["length_m"], 0.6, 0.6),
                rotation_z_deg=seg["bearing_deg"],
            )
        )

    if lanes > 1:
        for lane_idx in range(1, lanes):
            lane_offset = -width / 2 + lane_idx * (width / lanes)
            for seg_idx, seg in enumerate(segments):
                mx, my = offset_point(seg["mid_x"], seg["mid_y"], seg["bearing_deg"], lane_offset, "left")
                mark_z = marking_z(seg) if use_profile else float(marking_z)
                objects.append(
                    box(
                        f"lane_marking_{lane_idx}_{seg_idx + 1}",
                        "road_marking",
                        (mx, my, mark_z),
                        (seg["length_m"], 0.15, 0.01),
                        rotation_z_deg=seg["bearing_deg"],
                    )
                )

    return objects


def generate(
    params: dict,
    design: dict,
    *,
    alignment_ctx: AlignmentContext | None = None,
    elevation_profile: ElevationProfile | None = None,
) -> dict:
    geom = design.get("geometry", {})
    length = float(geom.get("length_m") or params.get("length_m", 1000))
    width = float(geom.get("road_width_m") or params.get("road_width_m", 7.5))
    lanes = int(params.get("lanes", 2))
    asphalt_thk = float(params.get("asphalt_thickness_mm", 80)) / 1000
    base_thk = float(params.get("base_thickness_mm", 250)) / 1000
    shoulder_w = float(params.get("shoulder_width_m", 1.5))

    elev_mode = elevation_profile.mode if elevation_profile else "flat"

    if alignment_ctx is not None:
        length = alignment_ctx.length_m
        objects = _alignment_geometry(
            alignment_ctx, width, lanes, asphalt_thk, base_thk, shoulder_w, elevation_profile
        )
        geometry_mode = "alignment"
        logger.info(
            "Road generator: alignment-based geometry (length_m=%.1f, segments=%d, elevation=%s)",
            length,
            len(polyline_segments(alignment_ctx.centerline_xy)),
            elev_mode,
        )
    else:
        objects = _straight_geometry(length, width, lanes, asphalt_thk, base_thk, shoulder_w)
        geometry_mode = "straight"
        logger.info("Road generator: fallback straight geometry (length_m=%.1f, elevation=%s)", length, elev_mode)

    quantities, boq_inputs, derived = _quantities_and_boq(
        length, width, lanes, asphalt_thk, base_thk, shoulder_w
    )
    if elevation_profile is not None:
        derived.update(elevation_profile.to_spec_metadata())
    spec = _geometry_spec_meta(length, geometry_mode, alignment_ctx, elevation_profile)
    spec["objects"] = objects

    return {
        "quantities": quantities,
        "boq_inputs": boq_inputs,
        "geometry_spec": spec,
        "timeline_driver": ("length_m", length),
        "derived": derived,
    }
