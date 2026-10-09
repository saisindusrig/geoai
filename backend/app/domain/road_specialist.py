"""Bounded conceptual straight-segment roads; no authoritative elevations."""
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id, Ref, XY
from app.domain.building_specialist import PreviewAssumption

Width = Annotated[float, Field(gt=0, le=50, allow_inf_nan=False)]
OptionalWidth = Annotated[float, Field(ge=0, le=10, allow_inf_nan=False)]


class RoadPoint(Contract):
    id: Id
    position: XY


class RoadCrossSection(Contract):
    carriageway_width_m: Width
    lane_count: Annotated[int, Field(ge=1, le=8, strict=True)] | None = None
    lane_width_m: Width | None = None
    shoulder_left_m: OptionalWidth = 0
    shoulder_right_m: OptionalWidth = 0
    median_width_m: OptionalWidth = 0
    verge_left_m: OptionalWidth = 0
    verge_right_m: OptionalWidth = 0
    surface_thickness_m: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]


class RoadSpec(Contract):
    schema_version: Literal["road-concept/1"] = "road-concept/1"
    road_id: Id
    name: Annotated[str, Field(min_length=1, max_length=255)]
    route_reference: Ref
    source_model_revision_id: Id | None = None
    coordinate_system: Literal["LOCAL_ENU"] = "LOCAL_ENU"
    alignment: Annotated[list[RoadPoint], Field(min_length=2, max_length=50)]
    cross_section: RoadCrossSection
    input_source: Literal["USER_PROVIDED", "PREVIEW_ASSUMPTION"]
    assumptions: Annotated[list[PreviewAssumption], Field(max_length=20)] = Field(default_factory=list)
    constraints: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    terrain_required: bool = False
    reference_plane: Literal["LOCAL_VISUAL_REFERENCE"] = "LOCAL_VISUAL_REFERENCE"
    requested_features: list[Literal["ROAD_CONCEPT"]] = Field(default_factory=lambda: ["ROAD_CONCEPT"])
    unknowns: dict[str, Literal["UNKNOWN", "UNAVAILABLE", "UNVALIDATED"]] = Field(default_factory=lambda: {
        "surveyElevation": "UNKNOWN", "pavementDesign": "UNAVAILABLE", "geotechnicalAdequacy": "UNVALIDATED",
        "slopeAwareRouting": "UNAVAILABLE", "engineeringApproval": "UNVALIDATED"})
