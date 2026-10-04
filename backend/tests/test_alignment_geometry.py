"""Tests for alignment-driven procedural geometry."""

from app.services.design import flyover_generator, road_generator
from app.services.design.alignment_geometry import (
    MIN_ALIGNMENT_LENGTH_M,
    alignment_length_m,
    parse_linestring_coords,
    polyline_length_xy,
    polyline_segments,
    resolve_alignment_context,
    sample_station,
)
from app.services.design.geometry_utils import line_length_lnglat, line_to_local_xy


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


def test_parse_linestring_coords_valid():
    coords = parse_linestring_coords(SAMPLE_ALIGNMENT)
    assert coords is not None
    assert len(coords) == 3


def test_parse_linestring_coords_invalid():
    assert parse_linestring_coords(None) is None
    assert parse_linestring_coords({"type": "Polygon", "coordinates": []}) is None
    assert parse_linestring_coords({"type": "LineString", "coordinates": [[1, 2]]}) is None


def test_alignment_length_calculation():
    coords = parse_linestring_coords(SAMPLE_ALIGNMENT)
    assert coords is not None
    length = line_length_lnglat(coords)
    assert length > MIN_ALIGNMENT_LENGTH_M
    assert alignment_length_m(SAMPLE_ALIGNMENT) == length


def test_local_meter_conversion():
    coords = parse_linestring_coords(SAMPLE_ALIGNMENT)
    assert coords is not None
    local = line_to_local_xy(coords, CENTER_LNG, CENTER_LAT)
    assert len(local) == 3
    assert abs(local[0][0]) < 5000
    assert abs(local[0][1]) < 5000
    xy_len = polyline_length_xy(local)
    assert xy_len > MIN_ALIGNMENT_LENGTH_M


def test_resolve_alignment_context_success():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    assert ctx is not None
    assert ctx.mode == "alignment"
    assert ctx.length_m > MIN_ALIGNMENT_LENGTH_M
    assert len(ctx.centerline_xy) == 3


def test_resolve_alignment_context_too_short():
    short = {"type": "LineString", "coordinates": [[77.59, 12.97], [77.59001, 12.97001]]}
    assert resolve_alignment_context(short, CENTER_LNG, CENTER_LAT) is None


def test_sample_station_endpoints():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    assert ctx is not None
    x0, y0, _ = sample_station(ctx.centerline_xy, 0.0)
    x1, y1, _ = sample_station(ctx.centerline_xy, ctx.length_m)
    assert abs(x0 - ctx.centerline_xy[0][0]) < 1e-6
    assert abs(y0 - ctx.centerline_xy[0][1]) < 1e-6
    assert abs(x1 - ctx.centerline_xy[-1][0]) < 50  # geodesic vs equirectangular tolerance
    assert abs(y1 - ctx.centerline_xy[-1][1]) < 50


def test_flyover_generator_uses_alignment():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    params = {"length_m": 9999, "deck_width_m": 16, "clearance_m": 5.5, "pier_spacing_m": 30}
    design = {"geometry": {"length_m": 9999}, "materials": {"concrete_grade": "M35", "asphalt_thickness_mm": 80}}
    result = flyover_generator.generate(params, design, alignment_ctx=ctx)
    spec = result["geometry_spec"]
    assert spec["geometry_mode"] == "alignment"
    assert spec["length_m"] == ctx.length_m
    assert spec["length_m"] != 9999
    assert len(spec["objects"]) > 4
    assert any(obj["name"].startswith("deck_seg_") for obj in spec["objects"])
    assert any(obj["layer"] == "piers" for obj in spec["objects"])


def test_flyover_generator_straight_fallback():
    params = {"length_m": 400, "deck_width_m": 16, "clearance_m": 5.5, "pier_spacing_m": 30}
    design = {"geometry": {}, "materials": {"concrete_grade": "M35", "asphalt_thickness_mm": 80}}
    result = flyover_generator.generate(params, design, alignment_ctx=None)
    spec = result["geometry_spec"]
    assert spec["geometry_mode"] == "straight"
    assert spec["length_m"] == 400
    assert any(obj["name"] == "deck_slab" for obj in spec["objects"])


def test_road_generator_uses_alignment():
    ctx = resolve_alignment_context(SAMPLE_ALIGNMENT, CENTER_LNG, CENTER_LAT)
    params = {"length_m": 8888, "road_width_m": 7.5, "lanes": 2}
    design = {"geometry": {"length_m": 8888}}
    result = road_generator.generate(params, design, alignment_ctx=ctx)
    spec = result["geometry_spec"]
    assert spec["geometry_mode"] == "alignment"
    assert spec["length_m"] == ctx.length_m
    assert len(polyline_segments(ctx.centerline_xy)) >= 2
    assert any(obj["name"].startswith("pavement_seg_") for obj in spec["objects"])


def test_road_generator_straight_fallback():
    params = {"length_m": 500, "road_width_m": 7.5, "lanes": 2}
    design = {"geometry": {}}
    result = road_generator.generate(params, design, alignment_ctx=None)
    spec = result["geometry_spec"]
    assert spec["geometry_mode"] == "straight"
    assert any(obj["name"] == "pavement" for obj in spec["objects"])
