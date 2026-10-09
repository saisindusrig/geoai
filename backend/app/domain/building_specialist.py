"""Building V1 concepts reuse existing bounded architectural primitives."""
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id
from app.domain.building_primitives import Room, Wall, Opening, Column, Beam, Number


class ConceptColumn(Column):
    id: Id


class ConceptBeam(Beam):
    id: Id


class PreviewAssumption(Contract):
    field: str
    value: str
    reason: str
    source: Literal["PREVIEW_ASSUMPTION"] = "PREVIEW_ASSUMPTION"


class BuildingSpec(Contract):
    schema_version: Literal["building-concept/1"] = "building-concept/1"
    building_id: Id
    name: Annotated[str,Field(min_length=1,max_length=255)]
    footprint: Annotated[list[tuple[Number,Number]],Field(min_length=4,max_length=5)]
    orientation: Annotated[float,Field(ge=-360,le=360,allow_inf_nan=False)] = 0
    floors: Annotated[int,Field(ge=1,le=10)]
    floor_height: Annotated[float,Field(ge=2.4,le=5,allow_inf_nan=False)]
    slab_thickness: Annotated[float,Field(ge=.1,le=.4,allow_inf_nan=False)]
    spaces: Annotated[list[Room],Field(min_length=1,max_length=100)]
    walls: Annotated[list[Wall],Field(min_length=4,max_length=250)]
    openings: Annotated[list[Opening],Field(max_length=200)] = Field(default_factory=list)
    columns: Annotated[list[ConceptColumn],Field(max_length=100)] = Field(default_factory=list)
    beams: Annotated[list[ConceptBeam],Field(max_length=150)] = Field(default_factory=list)
    constraints: Annotated[list[str],Field(max_length=30)] = Field(default_factory=list)
    assumptions: Annotated[list[PreviewAssumption],Field(max_length=30)] = Field(default_factory=list)
    input_source: Literal["USER_PROVIDED","PREVIEW_ASSUMPTION"]
    unknowns: dict[str,Literal["UNKNOWN","UNAVAILABLE","UNVALIDATED"]] = Field(default_factory=lambda:{
        "soil":"UNKNOWN","foundationDesign":"UNAVAILABLE","surveyElevation":"UNKNOWN",
        "designLoads":"UNKNOWN","structuralAdequacy":"UNVALIDATED"})
    requested_features: list[Literal["ARCHITECTURAL_CONCEPT","STRUCTURAL_CONCEPT"]] = Field(default_factory=lambda:["ARCHITECTURAL_CONCEPT"])
