"""Flyover conceptual generator: quantities + 3D geometry spec."""

from __future__ import annotations

import logging
import math

from collections.abc import Callable

from app.services.calculations import concrete, earthwork, steel
from app.services.design.alignment_geometry import (
    AlignmentContext,
    assign_segment_stations,
    corridor_segment_boxes,
    offset_corridor_segment_boxes,
    pier_stations,
    polyline_segments,
    sample_station,
)
from app.services.design.elevation_profile import ElevationProfile
from app.services.design.geometry_utils import box

logger = logging.getLogger(__name__)

DECK_THICKNESS_M = 0.6
APPROACH_RAMP_GRADE_PERCENT = 6.0
PIER_CROSS_SECTION_M2 = 3.2          # ~1.6m x 2.0m rectangular pier
PIER_CAP_VOLUME_M3 = 12.0
FOUNDATION_VOLUME_PER_PIER_M3 = 45.0  # assumed pile cap / open foundation
FOUNDATION_PLAN_M = (6.0, 6.0)


def _quantities_and_boq(
    length: float,
    deck_width: float,
    pier_count: int,
    pier_height: float,
    foundation_depth: float,
    asphalt_thk: float,
    grade: str,
) -> tuple[dict, list[dict], dict]:
    conc = concrete.flyover_concrete(
        length,
        deck_width,
        DECK_THICKNESS_M,
        pier_count,
        PIER_CROSS_SECTION_M2,
        pier_height,
        PIER_CAP_VOLUME_M3,
        FOUNDATION_VOLUME_PER_PIER_M3,
    )
    excavation = earthwork.rectangular_excavation_m3(
        FOUNDATION_PLAN_M[0], FOUNDATION_PLAN_M[1], foundation_depth
    ) * pier_count
    steel_total = steel.steel_kg(conc["total_m3"], "flyover")
    cement = concrete.cement_bags(conc["total_m3"], grade)
    formwork = concrete.formwork_sqm(conc["total_m3"])
    asphalt = length * deck_width * asphalt_thk

    quantities = {
        "concrete_m3": conc["total_m3"],
        "cement_bags": cement,
        "steel_kg": steel_total,
        "rebar_kg": steel_total,
        "excavation_m3": round(excavation, 1),
        "backfill_m3": round(excavation * 0.6, 1),
        "formwork_sqm": formwork,
        "asphalt_m3": round(asphalt, 1),
        "pipe_length_m": 0,
        "pipe_diameter_mm": 0,
    }
    boq_inputs = [
        {
            "item_code": "EXC-SOIL",
            "item_name": "Foundation excavation",
            "category": "earthwork",
            "quantity": quantities["excavation_m3"],
            "unit": "m3",
            "assumption": f"Assumed {foundation_depth}m deep open/pile foundation per pier",
        },
        {
            "item_code": "CONC-M35",
            "item_name": f"Structural concrete {grade}",
            "category": "concrete",
            "quantity": conc["total_m3"],
            "unit": "m3",
            "assumption": "Deck/pier/cap/foundation massing approximation",
        },
        {
            "item_code": "STEEL-FE500",
            "item_name": "Reinforcement steel",
            "category": "steel",
            "quantity": steel_total,
            "unit": "kg",
            "assumption": "160 kg/m3 preliminary factor",
        },
        {
            "item_code": "FORMWORK",
            "item_name": "Formwork",
            "category": "concrete",
            "quantity": formwork,
            "unit": "sqm",
            "assumption": "4 sqm per m3 factor",
        },
        {
            "item_code": "ASPHALT",
            "item_name": "Wearing coat asphalt",
            "category": "road",
            "quantity": quantities["asphalt_m3"],
            "unit": "m3",
            "assumption": f"{int(asphalt_thk * 1000)}mm thickness",
        },
        {
            "item_code": "BARRIER",
            "item_name": "Crash barriers (both sides)",
            "category": "safety",
            "quantity": length * 2,
            "unit": "m",
            "assumption": "Both deck edges",
        },
    ]
    derived = {
        "pier_count": pier_count,
        "pier_height_m": pier_height,
        "concrete_breakdown": conc,
    }
    return quantities, boq_inputs, derived


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
    deck_width: float,
    clearance: float,
    pier_count: int,
    foundation_depth: float,
    asphalt_thk: float,
) -> list[dict]:
    deck_top = clearance + DECK_THICKNESS_M
    objects = [
        box("deck_slab", "deck", (0, 0, clearance + DECK_THICKNESS_M / 2), (length, deck_width, DECK_THICKNESS_M)),
        box("road_surface", "asphalt", (0, 0, deck_top + asphalt_thk / 2), (length, deck_width - 1.0, asphalt_thk)),
        box("barrier_left", "barrier", (0, deck_width / 2 - 0.25, deck_top + 0.55), (length, 0.5, 1.1)),
        box("barrier_right", "barrier", (0, -deck_width / 2 + 0.25, deck_top + 0.55), (length, 0.5, 1.1)),
    ]
    start_x = -length / 2
    for i in range(pier_count):
        x = start_x + i * (length / max(pier_count - 1, 1))
        objects.append(box(f"pier_{i + 1}", "piers", (x, 0, clearance / 2), (1.6, 2.0, clearance)))
        objects.append(box(f"pier_cap_{i + 1}", "pier_caps", (x, 0, clearance), (2.4, deck_width * 0.8, 1.0)))
        objects.append(
            box(f"foundation_{i + 1}", "foundation", (x, 0, -foundation_depth / 2), (*FOUNDATION_PLAN_M, foundation_depth))
        )
        objects.append(
            box(
                f"excavation_{i + 1}",
                "excavation",
                (x, 0, -foundation_depth / 2),
                (FOUNDATION_PLAN_M[0] + 1, FOUNDATION_PLAN_M[1] + 1, foundation_depth),
            )
        )
    return objects


def _alignment_geometry(
    alignment_ctx: AlignmentContext,
    deck_width: float,
    clearance: float,
    pier_count: int,
    foundation_depth: float,
    asphalt_thk: float,
    elevation_profile: ElevationProfile | None = None,
) -> list[dict]:
    points = alignment_ctx.centerline_xy
    segments = polyline_segments(points)
    if not segments:
        return []
    assign_segment_stations(segments, points, alignment_ctx.length_m)

    use_profile = elevation_profile is not None and elevation_profile.mode == "profile"

    def deck_z(seg: dict) -> float:
        ground = _ground_z(elevation_profile, seg["station_m"])
        return ground + clearance + DECK_THICKNESS_M / 2

    def deck_top_z(station_m: float) -> float:
        ground = _ground_z(elevation_profile, station_m)
        return ground + clearance + DECK_THICKNESS_M

    objects: list[dict] = []
    deck_z_arg: float | Callable = deck_z if use_profile else clearance + DECK_THICKNESS_M / 2
    objects.extend(
        corridor_segment_boxes(
            segments,
            width_m=deck_width,
            thickness_m=DECK_THICKNESS_M,
            z_center=deck_z_arg,
            layer="deck",
            name_prefix="deck_seg",
        )
    )
    if use_profile:
        asphalt_z = lambda seg: deck_top_z(seg["station_m"]) + asphalt_thk / 2
        barrier_z = lambda seg: deck_top_z(seg["station_m"]) + 0.55
    else:
        deck_top = clearance + DECK_THICKNESS_M
        asphalt_z = deck_top + asphalt_thk / 2
        barrier_z = deck_top + 0.55

    objects.extend(
        corridor_segment_boxes(
            segments,
            width_m=max(deck_width - 1.0, 1.0),
            thickness_m=asphalt_thk,
            z_center=asphalt_z,
            layer="asphalt",
            name_prefix="asphalt_seg",
        )
    )
    objects.extend(
        offset_corridor_segment_boxes(
            segments,
            offset_m=deck_width / 2 - 0.25,
            side="left",
            width_m=0.5,
            thickness_m=1.1,
            z_center=barrier_z,
            layer="barrier",
            name_prefix="barrier_left_seg",
        )
    )
    objects.extend(
        offset_corridor_segment_boxes(
            segments,
            offset_m=deck_width / 2 - 0.25,
            side="right",
            width_m=0.5,
            thickness_m=1.1,
            z_center=barrier_z,
            layer="barrier",
            name_prefix="barrier_right_seg",
        )
    )

    for idx, station in enumerate(pier_stations(alignment_ctx.length_m, pier_count)):
        x, y, bearing = sample_station(points, station)
        ground = _ground_z(elevation_profile, station)
        local_clearance = clearance
        pier_center_z = ground + local_clearance / 2
        cap_z = ground + local_clearance
        foundation_z = ground - foundation_depth / 2
        objects.append(
            box(
                f"pier_{idx + 1}",
                "piers",
                (x, y, pier_center_z),
                (1.6, 2.0, local_clearance),
                rotation_z_deg=bearing,
            )
        )
        objects.append(
            box(
                f"pier_cap_{idx + 1}",
                "pier_caps",
                (x, y, cap_z),
                (2.4, deck_width * 0.8, 1.0),
                rotation_z_deg=bearing,
            )
        )
        objects.append(
            box(
                f"foundation_{idx + 1}",
                "foundation",
                (x, y, foundation_z),
                (*FOUNDATION_PLAN_M, foundation_depth),
                rotation_z_deg=bearing,
            )
        )
        objects.append(
            box(
                f"excavation_{idx + 1}",
                "excavation",
                (x, y, foundation_z),
                (FOUNDATION_PLAN_M[0] + 1, FOUNDATION_PLAN_M[1] + 1, foundation_depth),
                rotation_z_deg=bearing,
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
    length = float(geom.get("length_m") or params.get("length_m", 500))
    deck_width = float(geom.get("deck_width_m") or params.get("deck_width_m", 16))
    clearance = float(geom.get("clearance_m") or params.get("clearance_m", 5.5))
    pier_spacing = float(geom.get("pier_spacing_m") or params.get("pier_spacing_m", 30))
    foundation_depth = float(
        geom.get("foundation_depth_m_assumed") or params.get("foundation_depth_m_assumed", 8)
    )
    asphalt_thk = float(design.get("materials", {}).get("asphalt_thickness_mm", 80)) / 1000
    grade = design.get("materials", {}).get("concrete_grade", "M35").split()[0]

    approach_ramp_grade = float(params.get("approach_ramp_grade_percent", APPROACH_RAMP_GRADE_PERCENT))

    pier_count = int(geom.get("pier_count") or max(2, math.floor(length / pier_spacing) + 1))
    pier_height = clearance + 1.0

    elev_mode = elevation_profile.mode if elevation_profile else "flat"
    if alignment_ctx is not None:
        length = alignment_ctx.length_m
        pier_count = int(geom.get("pier_count") or max(2, math.floor(length / pier_spacing) + 1))
        objects = _alignment_geometry(
            alignment_ctx,
            deck_width,
            clearance,
            pier_count,
            foundation_depth,
            asphalt_thk,
            elevation_profile,
        )
        geometry_mode = "alignment"
        logger.info(
            "Flyover generator: alignment-based geometry (length_m=%.1f, segments=%d, piers=%d, elevation=%s)",
            length,
            len(polyline_segments(alignment_ctx.centerline_xy)),
            pier_count,
            elev_mode,
        )
    else:
        objects = _straight_geometry(length, deck_width, clearance, pier_count, foundation_depth, asphalt_thk)
        geometry_mode = "straight"
        logger.info(
            "Flyover generator: fallback straight geometry (length_m=%.1f, piers=%d, elevation=%s)",
            length,
            pier_count,
            elev_mode,
        )

    quantities, boq_inputs, derived = _quantities_and_boq(
        length, deck_width, pier_count, pier_height, foundation_depth, asphalt_thk, grade
    )
    derived["minimum_clearance_m"] = clearance
    derived["deck_depth_m"] = DECK_THICKNESS_M
    derived["approach_ramp_grade_percent"] = approach_ramp_grade
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
