import math
from app.services.survey.engineering_evidence import checkpoint_statistics, readiness, sample_result


def test_xy_rmse_uses_both_axes_and_vertical_independent_reference():
    stats = checkpoint_statistics([{"id": 1, "role": "VALIDATION_CHECKPOINT", "same_reference": True, "reference": [0, 0, 100], "observed": [3, 4, 102]}])
    assert stats["horizontal_rmse_m"] == 5
    assert stats["vertical_rmse_m"] == 2
    assert stats["max_horizontal_error_m"] == 5


def test_missing_failed_excluded_and_adjustment_points_remain_visible():
    stats = checkpoint_statistics([
        {"id": 1, "role": "ADJUSTMENT"},
        {"id": 2, "role": "VALIDATION_CHECKPOINT", "same_reference": False},
        {"id": 3, "role": "VALIDATION_CHECKPOINT", "same_reference": True, "observed": [math.nan, 0, 0], "reference": [0, 0, 0]},
        {"id": 4, "role": "VALIDATION_CHECKPOINT", "excluded": True},
    ])
    assert stats["valid_count"] == 0
    assert stats["invalid_count"] == 2
    assert stats["excluded_count"] == 2
    assert stats["horizontal_rmse_m"] is None
    assert len(stats["residuals"]) == 4


def test_imagery_cannot_promote_readiness():
    assert readiness({"imagery_available": True, "pixel_size_m": .001}) == "VISUAL_REFERENCE"
    assert readiness({}) == "UNCONFIGURED"
    evidence = dict(terrain_available=True, horizontal_crs_resolved=True, vertical_reference_resolved=True, units_resolved=True, coverage_verified=True, survey_authoritative=True, validation_status="VALID")
    assert readiness(evidence) == "SPATIAL_READY"
    evidence["checkpoint_statistics"] = dict(valid_count=3, invalid_count=0, horizontal_rmse_m=.02, vertical_rmse_m=.03)
    assert readiness(evidence) == "SURVEY_READY"
    evidence["engineering_checks_valid"] = True
    assert readiness(evidence) == "ENGINEERING_READY"
    evidence["validation_status"] = "STALE"
    assert readiness(evidence) == "SPATIAL_READY"


def test_unknown_height_never_becomes_zero():
    assert sample_result(longitude=77, latitude=12, height=None)["elevation"] is None
    assert sample_result(longitude=77, latitude=12, height=0)["elevation"] is None
    result = sample_result(longitude=77, latitude=12, height=0, source="WORLD_TERRAIN", vertical_reference={"type": "ELLIPSOIDAL"})
    assert result["status"] == "VALID" and result["elevation"] == 0
