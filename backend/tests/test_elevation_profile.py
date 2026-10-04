"""Tests for elevation-aware procedural geometry (Phase 2)."""

from app.services.design import flyover_generator, road_generator
from app.services.design.alignment_geometry import (
    assign_segment_stations,
    resolve_alignment_context,
    polyline_segments,
)
from app.services.design.elevation_profile import (
    ElevationProfile,
    build_profile_from_samples,
    flat_profile,
    smooth_elevations,
)

SAMPLE_ALIGNMENT = {
    "type": "LineString",
    "coordinates": [
        [77.5925, 12.9710],
        [77.59475, 12.97175],
        [77.5970, 12.9725],
    ],
}
CENTER_LNG = 77.5946
CENTER_LAT = 12.9716


def _rising_profile(length_m: float = 500.0) -> ElevationProfile:
    return build_profile_from_samples(
        length_m=length_m,
        distances_m=[0.0, length_m / 2, length_m],
        elevations_m=[100.0, 105.0, 110.0],
        provider="test",
        assumed=False,
    )


def test_flat_fallback_when_elevation_unavailable():
    profile = flat_profile(400.0, assumed=True)
    assert profile.mode == "flat"
    assert profile.z_at_station(0.0) == 0.0
    assert profile.z_at_station(200.0) == 0.0
    assert profile.max_grade_percent == 0.0


def test_elevation_profile_sampling_and_smoothing():
    smoothed = smooth_elevations([100.0, 102.0, 101.0, 103.0])
    assert len(smoothed) == 4
    profile = build_profile_from_samples(
        length_m=300.0,
        distances_m=[0.0, 100.0, 200.0, 300.0],
        elevations_m=[100.0, 101.5, 102.0, 104.0],
    )
    assert profile.mode == "profile"
    assert profile.min_elevation_m <= profile.max_elevation_m
    assert profile.max_elevation_m - profile.min_elevation_m >= 0.15
    assert profile.max_grade_percent > 0.0
    assert profile.z_at_station(50.0) > 0.0
    assert profile.z_at_station(150.0) > profile.z_at_station(50.0)


def test_road_segment_z_changes_with_elevation():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    profile = _rising_profile(ctx.length_m)
    params = {"length_m": 1000, "road_width_m": 7.5, "lanes": 2}
    design = {"geometry": {}}
    result = road_generator.generate(params, design, alignment_ctx=ctx, elevation_profile=profile)
    spec = result["geometry_spec"]
    assert spec["elevation_mode"] == "profile"
    pavement = [o for o in spec["objects"] if o["name"].startswith("pavement_seg_")]
    assert len(pavement) >= 2
    z_values = sorted(o["center"][2] for o in pavement)
    assert z_values[-1] > z_values[0]


def test_flyover_pier_heights_change_with_terrain():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    profile = _rising_profile(ctx.length_m)
    clearance = 5.5
    params = {"length_m": 1000, "deck_width_m": 16, "clearance_m": clearance, "pier_spacing_m": 30}
    design = {"geometry": {}, "materials": {"concrete_grade": "M35", "asphalt_thickness_mm": 80}}
    result = flyover_generator.generate(
        params, design, alignment_ctx=ctx, elevation_profile=profile
    )
    spec = result["geometry_spec"]
    assert spec["elevation_mode"] == "profile"
    piers = [o for o in spec["objects"] if o["layer"] == "piers"]
    assert len(piers) >= 2
    pier_z = sorted(o["center"][2] for o in piers)
    assert pier_z[-1] > pier_z[0]


def test_flyover_min_clearance_respected():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    profile = _rising_profile(ctx.length_m)
    clearance = 5.5
    params = {"length_m": 1000, "deck_width_m": 16, "clearance_m": clearance, "pier_spacing_m": 30}
    design = {"geometry": {}, "materials": {"concrete_grade": "M35", "asphalt_thickness_mm": 80}}
    result = flyover_generator.generate(
        params, design, alignment_ctx=ctx, elevation_profile=profile
    )
    spec = result["geometry_spec"]
    decks = [o for o in spec["objects"] if o["name"].startswith("deck_seg_")]
    assert decks
    segments = polyline_segments(ctx.centerline_xy)
    assign_segment_stations(segments, ctx.centerline_xy, ctx.length_m)
    for deck in decks:
        station = deck["name"].split("_")[-1]
        seg_idx = int(station) - 1
        seg = segments[seg_idx]
        ground = profile.z_at_station(seg["station_m"])
        deck_bottom = deck["center"][2] - deck["size"][2] / 2
        assert deck_bottom >= ground + clearance - 0.01


def test_road_flat_profile_matches_phase1_z():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    profile = flat_profile(ctx.length_m)
    params = {"length_m": 1000, "road_width_m": 7.5, "lanes": 2}
    design = {"geometry": {}}
    result = road_generator.generate(params, design, alignment_ctx=ctx, elevation_profile=profile)
    spec = result["geometry_spec"]
    assert spec["elevation_mode"] == "flat"
    pavement = [o for o in spec["objects"] if o["name"].startswith("pavement_seg_")]
    for obj in pavement:
        assert abs(obj["center"][2] - (-0.04)) < 0.001  # 80mm asphalt


def test_geometry_spec_metadata_fields():
    profile = _rising_profile()
    meta = profile.to_spec_metadata()
    assert meta["elevation_mode"] == "profile"
    assert "min_elevation_m" in meta
    assert "max_elevation_m" in meta
    assert "max_grade_percent" in meta
