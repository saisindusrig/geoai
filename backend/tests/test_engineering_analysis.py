from copy import deepcopy
import pytest
from app.services.survey.engineering_analysis import clearance_check, terrain_difference, seam_check, alignment_profile


def test_clearance_is_non_destructive_and_unknown_without_sample():
    ground = {"status": "VALID", "elevation": 100, "terrain_version_id": 3, "source": "SURVEY_TERRAIN"}
    before = deepcopy(ground)
    assert clearance_check(ground=ground, foundation_bottom_m=95, deck_bottom_m=104, required_clearance_m=5)["status"] == "POTENTIAL CONFLICT"
    assert ground == before
    assert clearance_check(ground={"status": "FAILED", "elevation": None}, foundation_bottom_m=95, deck_bottom_m=104)["clearance_m"] is None
    assert clearance_check(ground={**ground, "status": "STALE"}, foundation_bottom_m=95, deck_bottom_m=104)["status"] == "STALE"


def test_difference_preserves_missing_coverage_and_sign():
    result = terrain_difference([100,101,None,100], [101,99,102,None], 4)
    assert result["differences_m"] == [1,-2,None,None]
    assert result["mean_m"] == -.5 and result["max_absolute_difference_m"] == 2
    assert result["changed_area_m2"] == 8 and result["changed_coverage_area_m2"] == 8
    assert terrain_difference([None], [None], 1)["mean_m"] is None


def test_seam_qa_never_warps_or_compares_unresolved_datums():
    result = seam_check([{"survey_elevation_m":100,"context_elevation_m":90,"survey_vertical_reference":"WGS84","context_vertical_reference":"WGS84"},
        {"survey_elevation_m":100,"context_elevation_m":90,"survey_vertical_reference":"LOCAL","context_vertical_reference":"WGS84"},
        {"survey_elevation_m":None,"context_elevation_m":90}], .5)
    assert result["survey_geometry_modified"] is False
    assert result["samples"][0]["difference_m"] == 10
    assert result["samples"][1]["difference_m"] is None
    assert result["samples"][2]["status"] == "UNKNOWN"


def test_profile_grade_cut_fill_and_missing_stations():
    profile = alignment_profile([{"chainage_m":0,"ground_elevation_m":100,"proposed_elevation_m":101},
        {"chainage_m":20,"ground_elevation_m":104,"proposed_elevation_m":102},
        {"chainage_m":40,"ground_elevation_m":None,"proposed_elevation_m":103}])
    assert profile[0]["fill_depth_m"] == 1
    assert profile[1]["cut_depth_m"] == 2 and profile[1]["grade_percent"] == 5
    assert profile[2]["cut_depth_m"] is None
    with pytest.raises(ValueError):
        alignment_profile([{"chainage_m":0},{"chainage_m":0}])
