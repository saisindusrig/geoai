"""Typed, bounded commands for the civil assistant; no executable model code."""
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id, Digest, CivilIntent, ApprovalCommand, Finite, ProposalPayload, ValidationResult, ProposalStatus
from app.domain.site_workspace import MessageContext
from app.domain.composition import AssetProposal

Text = Annotated[str, Field(min_length=1, max_length=4000)]


class ConceptAsset(Contract):
    asset_request_id: Id | None = None
    asset_type: Id
    name: Annotated[str, Field(min_length=1, max_length=255)]
    requirements: Annotated[list[Text], Field(max_length=30)] = Field(default_factory=list)


class TranslationPreview(Contract):
    object_ids: Annotated[list[Id], Field(min_length=1, max_length=100)]
    coordinate_system: Literal["LOCAL"] = "LOCAL"
    delta_m: tuple[Finite, Finite, Finite]


class ConceptAlternative(Contract):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    rationale: Text


class ProposalRequest(Contract):
    client_request_id: Id
    message_id: Id
    title: Annotated[str, Field(min_length=1, max_length=255)]
    rationale: Text
    assets: Annotated[list[ConceptAsset], Field(min_length=1, max_length=20)]
    assumptions: Annotated[list[Text], Field(max_length=20)] = Field(default_factory=list)
    warnings: Annotated[list[Text], Field(max_length=20)] = Field(default_factory=list)
    translation: TranslationPreview | None = None
    alternatives: Annotated[list[ConceptAlternative], Field(max_length=5)] = Field(default_factory=list)
    parent_version_id: Id | None = None


class ApplicationApproval(ApprovalCommand):
    client_request_id: Id


class RetryCommand(Contract):
    client_request_id: Id


class ToolInvocation(Contract):
    name: Literal["get_site_profile", "get_site_readiness", "get_active_terrain", "sample_terrain",
        "get_selected_objects", "get_model_revision", "get_project_requirements", "query_nearby_context",
        "get_checks", "get_constraints", "create_proposal", "revise_proposal", "validate_proposal"]
    arguments: Annotated[str, Field(max_length=18000)] = "{}"


class Clarification(Contract):
    question: Text
    options: Annotated[list[Text], Field(max_length=5)] = Field(default_factory=list)


class ProviderResponse(Contract):
    text: Annotated[str, Field(max_length=6000)] = ""
    clarification: Clarification | None = None
    tool_calls: Annotated[list[ToolInvocation], Field(max_length=8)] = Field(default_factory=list)
    evidence_ids: Annotated[list[Id], Field(max_length=20)] = Field(default_factory=list)


class NoArguments(Contract):
    pass


class TerrainArguments(Contract):
    sample_count: Annotated[int, Field(ge=1, le=25)] = 10


class NearbyArguments(Contract):
    radius_m: Annotated[float, Field(gt=0, le=500)] = 500
    category: Literal["roads", "waterways", "buildings", "utilities"] = "roads"


class ProposalToolArguments(Contract):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    rationale: Text
    assets: Annotated[list[ConceptAsset], Field(min_length=1, max_length=20)]
    assumptions: Annotated[list[Text], Field(max_length=20)] = Field(default_factory=list)
    warnings: Annotated[list[Text], Field(max_length=20)] = Field(default_factory=list)
    translation: TranslationPreview | None = None
    alternatives: Annotated[list[ConceptAlternative], Field(max_length=5)] = Field(default_factory=list)
    parent_version_id: Id | None = None


class ProposalReference(Contract):
    proposal_version_id: Id


class ProposalContent(Contract):
    asset_proposals: list[AssetProposal] = Field(default_factory=list)
    contract: ProposalPayload
    context: MessageContext
    request: ProposalRequest
    request_hash: Digest
    preview: TranslationPreview | None
    preview_only: Literal[True]
    validation_id: Id


class AlternativeView(Contract):
    id: Id
    name: str
    payload: ConceptAlternative


class ProposalView(Contract):
    id: Id
    proposal_id: Id
    version: int
    status: ProposalStatus
    current: bool
    content_hash: Digest
    dependency_hash: Digest
    validation_hash: Digest
    validation: ValidationResult | None
    content: ProposalContent
    alternatives: list[AlternativeView]


class RuntimeContracts(Contract):
    proposal_request: ProposalRequest
    application_approval: ApplicationApproval
    retry: RetryCommand
    response: ProviderResponse
    tool_invocation: ToolInvocation
    intent: CivilIntent
    proposal_view: ProposalView
