"""BIM foundation: bounded data, independent of AI3D V1 wire format.

Provenance is bound by server code, never trusted from model output.
This contract describes conceptual geometry, not engineering certification.
"""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from app.domain.stage1 import Contract, Id, Finite
from app.domain.ai3d import Primitive, XYZ

BoundedIds = Annotated[list[Id], Field(max_length=250)]


class SourceProvenance(Contract):
    design_id: Id
    design_version: Annotated[int, Field(ge=1, strict=True)]
    source_model_revision_id: Id | None = None
    source_kind: Literal["USER_PROVIDED", "PREVIEW_ASSUMPTION", "UNKNOWN"]


class Parameter(Contract):
    id: Id
    value: Annotated[float, Field(ge=-2000, le=2000, allow_inf_nan=False)]
    unit: Literal["m", "deg", "count", "ratio"]


class Material(Contract):
    id: Id
    name: Id
    category: Literal["CONCRETE", "STEEL", "TIMBER", "ASPHALT", "OTHER", "UNKNOWN"]
    engineering_verification: Literal["UNVERIFIED"] = "UNVERIFIED"


class CrossSection(Contract):
    id: Id
    profile: Literal["RECTANGLE", "CIRCLE", "I", "CUSTOM"]
    parameters: Annotated[list[Parameter], Field(max_length=20)]


class GeometryDefinition(Contract):
    # Only the existing bounded primitive vocabulary is executable in this batch.
    primitive: Primitive
    cross_section_id: Id | None = None


class Placement(Contract):
    coordinate_frame: Literal["ASSEMBLY_LOCAL"] = "ASSEMBLY_LOCAL"
    origin: XYZ = (0, 0, 0)
    heading_deg: Annotated[float, Field(ge=-360, le=360, allow_inf_nan=False)] = 0


class Connection(Contract):
    id: Id
    from_component_id: Id
    to_component_id: Id
    kind: Literal["SUPPORTED_BY", "CONNECTS_TO", "ADJACENT_TO"]
    engineering_verification: Literal["UNVERIFIED"] = "UNVERIFIED"


class Constraint(Contract):
    id: Id
    component_id: Id
    parameter_id: Id
    minimum: Finite
    maximum: Finite

    @model_validator(mode="after")
    def valid_range(self):
        if self.minimum > self.maximum:
            raise ValueError("INVALID_CONSTRAINT_RANGE")
        return self


class Dependency(Contract):
    id: Id
    source_component_id: Id
    source_parameter_id: Id
    target_component_id: Id
    target_parameter_id: Id
    operation: Literal["COPY", "UNRESOLVED"]
    # No expressions, solver claims, or automatic engineering member sizing.


class Component(Contract):
    id: Id
    asset_id: Id
    assembly_id: Id
    component_type: Literal["BEAM", "GIRDER", "SLAB", "DECK", "COLUMN", "PIER", "WALL", "PILE", "PILE_CAP", "BEARING", "JOINT", "RAILING", "BARRIER", "BRACING", "PLATE", "CONNECTOR", "REINFORCEMENT"]
    parameters: Annotated[list[Parameter], Field(max_length=30)]
    placement: Placement
    material_id: Id
    relationship_ids: BoundedIds = Field(default_factory=list)
    dependency_ids: BoundedIds = Field(default_factory=list)
    geometry: GeometryDefinition
    provenance: SourceProvenance
    validation_status: Literal["UNVALIDATED", "PARAMETRIC_VALID"] = "UNVALIDATED"


class Assembly(Contract):
    id: Id
    asset_id: Id
    role: Id
    component_ids: BoundedIds
    placement: Placement = Field(default_factory=Placement)


class BIMAsset(Contract):
    id: Id
    asset_type: Id
    assembly_ids: BoundedIds


class BIMProject(Contract):
    schema_version: Literal["bim-project/1"] = "bim-project/1"
    assets: Annotated[list[BIMAsset], Field(min_length=1, max_length=20)]
    assemblies: Annotated[list[Assembly], Field(min_length=1, max_length=100)]
    components: Annotated[list[Component], Field(min_length=1, max_length=250)]
    materials: Annotated[list[Material], Field(min_length=1, max_length=50)]
    cross_sections: Annotated[list[CrossSection], Field(max_length=50)] = Field(default_factory=list)
    connections: Annotated[list[Connection], Field(max_length=250)] = Field(default_factory=list)
    constraints: Annotated[list[Constraint], Field(max_length=250)] = Field(default_factory=list)
    dependencies: Annotated[list[Dependency], Field(max_length=250)] = Field(default_factory=list)
    unknowns: Annotated[list[Id], Field(max_length=50)] = Field(default_factory=lambda: ["terrain", "soil", "loads", "verticalDatum", "engineeringApproval"])
    engineering_status: Literal["UNVERIFIED"] = "UNVERIFIED"
