"""Data-only bounded parametric language. No executable expressions or code."""
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id, Ref, Finite
from app.domain.building_specialist import PreviewAssumption

Coordinate = Annotated[float, Field(ge=-2000, le=2000, allow_inf_nan=False)]
XYZ = tuple[Coordinate, Coordinate, Coordinate]
Positive = Annotated[float, Field(gt=0, le=500, allow_inf_nan=False)]


class Point(Contract):
    primitive_type: Literal["POINT"]
    position: XYZ


class Path(Contract):
    primitive_type: Literal["PATH"]
    points: Annotated[list[XYZ], Field(min_length=2, max_length=50)]


class Polygon(Contract):
    primitive_type: Literal["POLYGON"]
    points: Annotated[list[XYZ], Field(min_length=4, max_length=50)]


class Box(Contract):
    primitive_type: Literal["BOX"]
    center: XYZ
    size: tuple[Positive, Positive, Positive]
    heading_deg: Annotated[float, Field(ge=-360, le=360)] = 0


class Cylinder(Contract):
    primitive_type: Literal["CYLINDER"]
    start: XYZ
    end: XYZ
    radius_m: Positive


class Extrude(Contract):
    primitive_type: Literal["EXTRUDE", "SURFACE"]
    polygon_ref: Id
    height_m: Positive


class Sweep(Contract):
    primitive_type: Literal["SWEEP"]
    path_ref: Id
    width_m: Positive
    thickness_m: Positive


class Pipe(Contract):
    primitive_type: Literal["PIPE"]
    path_ref: Id
    radius_m: Positive


class Channel(Contract):
    primitive_type: Literal["CHANNEL"]
    path_ref: Id
    width_m: Positive
    depth_m: Positive
    thickness_m: Positive


class Offset(Contract):
    primitive_type: Literal["OFFSET"]
    path_ref: Id
    distance_m: Coordinate


class ArrayAlongPath(Contract):
    primitive_type: Literal["ARRAY_ALONG_PATH"]
    path_ref: Id
    template_ref: Id
    spacing_m: Positive
    count: Annotated[int, Field(ge=1, le=100, strict=True)]
    start_chainage_m: Annotated[float, Field(ge=0, le=2000)] = 0


class ArrayOnGrid(Contract):
    primitive_type: Literal["ARRAY_ON_GRID"]
    template_ref: Id
    origin: XYZ
    rows: Annotated[int, Field(ge=1, le=20, strict=True)]
    columns: Annotated[int, Field(ge=1, le=20, strict=True)]
    spacing_x_m: Positive
    spacing_y_m: Positive


Primitive = Annotated[Point | Path | Polygon | Box | Cylinder | Extrude | Sweep | Pipe | Channel | Offset | ArrayAlongPath | ArrayOnGrid, Field(discriminator="primitive_type")]


class DesignSystem(Contract):
    id: Id
    asset_type: Id
    semantic_type: Id
    role: Id


class DesignObject(Contract):
    object_id: Id
    system_id: Id
    semantic_type: Id
    role: Id
    parameters: Primitive
    parent_id: Id | None = None
    template_only: bool = False


class DesignRelationship(Contract):
    id: Id
    kind: Literal["CONNECTS_TO", "SERVES", "SUPPLIES", "CROSSES", "FOLLOWS", "AVOIDS", "CONTAINS", "ADJACENT_TO", "ABOVE", "BELOW", "SUPPORTED_BY", "DRAINS_TO", "ALIGNS_WITH", "OFFSET_FROM"]
    from_id: Id
    to_id: Id


class DesignConstraint(Contract):
    id: Id
    kind: Literal["WITHIN_AREA", "START_AT", "END_AT", "FOLLOW_ROUTE", "AVOID_AREA", "AVOID_OBJECT", "MIN_CLEARANCE", "CONNECT_TO", "OFFSET", "ORIENTATION", "MAX_FOOTPRINT"]
    target_id: Id
    reference_id: Id | None = None
    value_m: Finite | None = None


class AI3DDesign(Contract):
    schema_version: Literal["ai-3d-design/1"] = "ai-3d-design/1"
    design_id: Id
    source_model_revision_id: Id | None = None
    site_selection: Ref
    coordinate_frame: Literal["LOCAL_ENU"] = "LOCAL_ENU"
    reference_plane: Literal["LOCAL_VISUAL_REFERENCE"] = "LOCAL_VISUAL_REFERENCE"
    systems: Annotated[list[DesignSystem], Field(min_length=1, max_length=20)]
    objects: Annotated[list[DesignObject], Field(min_length=1, max_length=250)]
    relationships: Annotated[list[DesignRelationship], Field(max_length=100)] = Field(default_factory=list)
    constraints: Annotated[list[DesignConstraint], Field(max_length=100)] = Field(default_factory=list)
    assumptions: Annotated[list[PreviewAssumption], Field(max_length=20)] = Field(default_factory=list)
    unknowns: Annotated[list[Id], Field(max_length=50)] = Field(default_factory=lambda: ["groundElevation", "soil", "structuralCapacity", "designLoads", "engineeringApproval"])
    terrain_dependencies: Annotated[list[Ref], Field(max_length=10)] = Field(default_factory=list)
    input_source: Literal["USER_PROVIDED", "PREVIEW_ASSUMPTION"]
