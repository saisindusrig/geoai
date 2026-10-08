"""Extensible civil composition, patch and lineage contracts."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from app.domain.stage1 import Contract, Id, Digest, Finite, Ref, AssetCapability

RelationshipKind=Literal["CONNECTS_TO","CROSSES","SUPPORTED_BY","HOSTED_BY","SERVES","DRAINS_TO","ALIGNS_WITH","DEPENDS_ON","ADJACENT_TO","PART_OF","INTERSECTS"]


class RelationshipInput(Contract):
    client_request_id: Id
    from_asset_id: Id
    to_asset_id: Id
    kind: RelationshipKind
    relationship_id: Id | None = None
    expected_version: Annotated[int,Field(ge=1)] | None = None


class AssetProposal(Contract):
    asset_request_id: Id
    asset_id: Id
    asset_type: Id
    asset_family: Id
    display_name: str
    requirements: list[str]
    assumptions: list[str]
    constraint_ids: list[Id]
    specification_ref: Ref
    capabilities: AssetCapability
    warnings: list[str]
    blockers: list[str]
    dependency_refs: list[Id]
    proposal_state: Literal["CONCEPT_REVIEW"] = "CONCEPT_REVIEW"
    generation_eligible: bool = False


class TranslatePatch(Contract):
    operation: Literal["TRANSLATE_COMPONENT"]
    delta_m: tuple[Finite,Finite,Finite]
    coordinate_system: Literal["LOCAL"] = "LOCAL"


class RotatePatch(Contract):
    operation: Literal["ROTATE_COMPONENT"]
    axis: Literal["X","Y","Z"]
    angle_degrees: Annotated[float,Field(ge=-360,le=360)]


class DimensionPatch(Contract):
    operation: Literal["SET_DIMENSION"]
    dimension: Literal["WIDTH","HEIGHT","LENGTH","THICKNESS","DIAMETER"]
    value_m: Annotated[float,Field(gt=0,le=100000)]


class PropertyPatch(Contract):
    operation: Literal["SET_PROPERTY"]
    property: Literal["NAME","MATERIAL","CLASSIFICATION"]
    value: Annotated[str,Field(min_length=1,max_length=255)]


class SpecificationPatch(Contract):
    operation: Literal["REPLACE_COMPONENT","ADD_COMPONENT"]
    specification_version_id: Id
    specification_component_id: Id


class RemovePatch(Contract):
    operation: Literal["REMOVE_COMPONENT"]


PatchParameters=Annotated[TranslatePatch|RotatePatch|DimensionPatch|PropertyPatch|SpecificationPatch|RemovePatch,Field(discriminator="operation")]


class PatchProposal(Contract):
    base_model_revision_id: Id
    target_component_id: Id
    expected_component_hash: Digest
    asset_type: Id
    parameters: PatchParameters
    affected_component_ids: Annotated[list[Id],Field(max_length=100)] = Field(default_factory=list)


class ObjectLineage(Contract):
    object_id: Id
    origin: Literal["MANUAL","GENERATED"]
    asset_id: Id | None = None
    asset_type: Id | None = None
    asset_family: Id | None = None
    component_kind: Id | None = None
    specification_component_id: Id | None = None
    proposal_id: Id | None = None
    proposal_version_id: Id | None = None
    approval_id: Id | None = None
    generator_id: Id | None = None
    generator_version: Id | None = None
    created_in_revision_id: Id
    last_modified_in_revision_id: Id

    @model_validator(mode="after")
    def provenance(self):
        if self.origin=="GENERATED" and not all((self.asset_id,self.asset_type,self.asset_family,self.component_kind,self.specification_component_id,
            self.proposal_id,self.proposal_version_id,self.approval_id,self.generator_id,self.generator_version)):
            raise ValueError("Generated lineage requires real proposal, approval and generator references")
        if self.origin=="MANUAL" and any((self.proposal_id,self.proposal_version_id,self.approval_id,self.generator_id,self.generator_version)):
            raise ValueError("Manual objects must not invent proposal provenance")
        return self


class CompositionContracts(Contract):
    relationship: RelationshipInput
    asset_proposal: AssetProposal
    patch: PatchProposal
    lineage: ObjectLineage
