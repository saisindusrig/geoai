"""Versioned, bounded edits to authoritative Building snapshots."""
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id, Digest
from app.domain.building_primitives import Number, Dimension

class MoveComponent(Contract):
    operation_type: Literal["MOVE_COMPONENT"]
    delta: tuple[Number, Number, Number]
    unit: Literal["m", "mm"] = "m"

class RotateComponent(Contract):
    operation_type: Literal["ROTATE_COMPONENT"]
    angle_deg: Number

class ResizeOpening(Contract):
    operation_type: Literal["RESIZE_OPENING"]
    width: Dimension

class MoveOpening(Contract):
    operation_type: Literal["MOVE_OPENING"]
    offset_m: Annotated[float, Field(ge=0, le=200, allow_inf_nan=False)]

class AddOpening(Contract):
    operation_type: Literal["ADD_OPENING"]
    opening_id: Annotated[str, Field(min_length=1, max_length=60)]
    kind: Literal["door", "window"]
    offset_m: Annotated[float, Field(ge=0, le=200, allow_inf_nan=False)]
    width: Dimension
    height: Dimension
    sill_m: Annotated[float, Field(ge=0, le=5, allow_inf_nan=False)] = 0

class RemoveOpening(Contract):
    operation_type: Literal["REMOVE_OPENING"]

Parameters = Annotated[MoveComponent | RotateComponent | ResizeOpening | MoveOpening | AddOpening | RemoveOpening, Field(discriminator="operation_type")]

class BuildingPatchOperation(Contract):
    operation_id: Id
    target_component_id: Id
    expected_component_hash: Digest
    parameters: Parameters

class BuildingPatch(Contract):
    schema_version: Literal["building-patch/1"] = "building-patch/1"
    building_id: Id
    asset_id: Id
    source_model_revision_id: Id
    source_specification_version_id: Id
    source_specification_hash: Digest
    operations: Annotated[list[BuildingPatchOperation], Field(min_length=1, max_length=1)]
    assumptions: Annotated[list[str], Field(max_length=10)] = Field(default_factory=list)
