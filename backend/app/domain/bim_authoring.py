"""Offline AI data contracts. No server identities, approval or execution fields."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from app.domain.stage1 import Contract, Id, Digest
from app.domain.bim import Component, Placement, Parameter, Material, CrossSection, Dependency, Constraint
from app.experimental.bim_cad import CADRecipe

Text = Annotated[str, Field(min_length=1, max_length=1000)]
SelectionKind = Literal["AREA", "ROUTE", "CROSSING", "ENDPOINTS", "POINT"]
ComponentKind = Component.model_fields["component_type"].annotation


class SystemRequest(Contract):
    id: Id
    asset_type: Id
    purpose: Text
    compatible_selection_kinds: Annotated[list[SelectionKind], Field(min_length=1, max_length=5)]


class UnknownCondition(Contract):
    id: Id
    domain: Literal["TERRAIN", "SOIL", "LOADS", "FOUNDATION", "CLEARANCE", "CODE", "OTHER"]
    status: Literal["UNKNOWN"] = "UNKNOWN"
    explanation: Text


class AuthoringIntent(Contract):
    schema_version: Literal["bim-authoring-intent/1"] = "bim-authoring-intent/1"
    requested_structure: Text
    systems: Annotated[list[SystemRequest], Field(min_length=1, max_length=8)]
    requested_features: Annotated[list[Id], Field(max_length=20)] = Field(default_factory=list)
    requested_selection_ref: Id | None = None
    requested_object_refs: Annotated[list[Id], Field(max_length=50)] = Field(default_factory=list)
    assumptions: Annotated[list[Text], Field(max_length=16)] = Field(default_factory=list)
    unknowns: Annotated[list[UnknownCondition], Field(max_length=30)] = Field(default_factory=list)


class PlannedAsset(Contract):
    id: Id
    system_request_id: Id
    asset_type: Id
    name: Annotated[str, Field(min_length=1, max_length=255)]


class PlannedGroup(Contract):
    id: Id
    role: Id
    component_type: ComponentKind
    count: Annotated[int, Field(strict=True, ge=1, le=8)]


class PlannedAssembly(Contract):
    id: Id
    asset_id: Id
    parent_id: Id | None = None
    role: Id
    placement: Placement = Field(default_factory=Placement)
    groups: Annotated[list[PlannedGroup], Field(min_length=1, max_length=16)]


class AssemblyPlan(Contract):
    schema_version: Literal["bim-assembly-plan/1"] = "bim-assembly-plan/1"
    intent_hash: Digest
    assets: Annotated[list[PlannedAsset], Field(min_length=1, max_length=8)]
    assemblies: Annotated[list[PlannedAssembly], Field(min_length=1, max_length=16)]
    materials: Annotated[list[Material], Field(min_length=1, max_length=30)]
    cross_sections: Annotated[list[CrossSection], Field(max_length=30)] = Field(default_factory=list)


class AuthoredComponent(Contract):
    id: Id
    group_id: Id
    role: Id
    component_type: ComponentKind
    material_id: Id
    parameters: Annotated[list[Parameter], Field(min_length=1, max_length=9)]
    cross_section_id: Id | None = None
    placement: Placement = Field(default_factory=Placement)
    recipe: CADRecipe


class AssemblyExpansion(Contract):
    schema_version: Literal["bim-assembly-expansion/1"] = "bim-assembly-expansion/1"
    plan_hash: Digest
    assembly_id: Id
    components: Annotated[list[AuthoredComponent], Field(min_length=1, max_length=8)]


class ConnectionIntent(Contract):
    id: Id
    from_component_id: Id
    to_component_id: Id | None = None
    external_support: Literal["UNKNOWN_FOUNDATION"] | None = None
    kind: Literal["SUPPORTED_BY", "CONNECTS_TO", "ADJACENT_TO"]
    status: Literal["UNRESOLVED"] = "UNRESOLVED"
    explanation: Text

    @model_validator(mode="after")
    def target(self):
        if (self.to_component_id is None) == (self.external_support is None):
            raise ValueError("EXACTLY_ONE_CONNECTION_TARGET_REQUIRED")
        if self.external_support and self.kind != "SUPPORTED_BY":
            raise ValueError("EXTERNAL_SUPPORT_KIND")
        return self


class ClearanceIntent(Contract):
    id: Id
    component_ids: Annotated[list[Id], Field(min_length=2, max_length=64)]
    status: Literal["UNRESOLVED"] = "UNRESOLVED"
    explanation: Text


class AssemblyRelationships(Contract):
    schema_version: Literal["bim-assembly-relationships/1"] = "bim-assembly-relationships/1"
    plan_hash: Digest
    connections: Annotated[list[ConnectionIntent], Field(max_length=128)]
    clearances: Annotated[list[ClearanceIntent], Field(max_length=64)]
    dependencies: Annotated[list[Dependency], Field(max_length=128)] = Field(default_factory=list)
    constraints: Annotated[list[Constraint], Field(max_length=128)] = Field(default_factory=list)


class AuthoringBundle(Contract):
    schema_version: Literal["bim-authoring/1"] = "bim-authoring/1"
    intent: AuthoringIntent
    plan: AssemblyPlan
    expansions: Annotated[list[AssemblyExpansion], Field(min_length=1, max_length=16)]
    relationships: AssemblyRelationships
