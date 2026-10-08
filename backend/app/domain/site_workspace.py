"""Typed site, conversation and memory contracts for Stage 1 steps 4–5."""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator
from app.domain.stage1 import (Contract, Id, Ids, Digest, Finite, Fact, HorizontalCRS,
    VerticalReference, SiteSelection, ObjectRef, Ref, MissingSiteInformation, AssetCapability)


class Quantity(Contract):
    value: Finite
    unit: Literal["m", "m2", "deg", "percent"]


class ApplicableQuantity(Contract):
    applicability: Literal["APPLICABLE", "NOT_APPLICABLE"]
    fact: Fact[Quantity] | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def applicable(self):
        if (self.applicability == "APPLICABLE") != (self.fact is not None):
            raise ValueError("Applicable dimensions require a fact")
        if self.applicability == "NOT_APPLICABLE" and not self.reason:
            raise ValueError("Nonapplicable dimensions require a reason")
        return self


class Position(Contract):
    longitude: Annotated[float, Field(ge=-180, le=180)]
    latitude: Annotated[float, Field(ge=-90, le=90)]


class GeometryReference(Contract):
    id: Id
    hash: Digest
    horizontal_crs: HorizontalCRS


class Dimensions(Contract):
    area: ApplicableQuantity
    perimeter: ApplicableQuantity
    route_length: ApplicableQuantity
    crossing_span: ApplicableQuantity
    bounding_width: ApplicableQuantity
    bounding_depth: ApplicableQuantity
    endpoint_distance: ApplicableQuantity


class Orientation(Contract):
    azimuth: Fact[Quantity]
    method: Literal["PRINCIPAL_AXIS", "ENDPOINT_BEARING", "USER_AXIS", "UNDEFINED"]


class Coverage(Contract):
    status: Literal["FULL", "PARTIAL", "NONE", "UNKNOWN"]
    covered_fraction: Annotated[float, Field(ge=0, le=1)] | None
    checked_geometry_hash: Digest
    method_version: str
    evidence_ids: Ids


class SampleSummary(Contract):
    requested: int
    valid: int
    failed: int


class TerrainSummary(Contract):
    active_configuration_revision: int | None
    dataset_id: Id | None
    version_id: Id | None
    coverage: Coverage
    sample_set_id: Id | None
    sample_summary: SampleSummary


class Relief(Contract):
    min_elevation: Fact[Quantity]
    max_elevation: Fact[Quantity]
    mean_slope: Fact[Quantity]
    max_slope: Fact[Quantity]
    slope_method_version: str | None
    profile_ids: Ids


class RoadAttributes(Contract):
    kind: Literal["ROAD"]
    classification: Fact[str]
    width: Fact[Quantity]
    access: Fact[str]


class WaterwayAttributes(Contract):
    kind: Literal["WATERWAY"]
    waterway_type: Fact[str]
    flow_direction: Fact[str]


class BuildingAttributes(Contract):
    kind: Literal["BUILDING"]
    height: Fact[Quantity]
    storeys: Fact[Finite]
    use: Fact[str]


class UtilityAttributes(Contract):
    kind: Literal["UTILITY"]
    service: Fact[str]
    depth: Fact[Quantity]
    operator: Fact[str]


class ContextFeature(Contract):
    """Retained project context only; absence never means clearance."""
    id: Id
    kind: Literal["ROAD", "WATERWAY", "BUILDING", "UTILITY"]
    geometry: Fact[GeometryReference]
    name: Fact[str]
    attributes: Annotated[RoadAttributes | WaterwayAttributes | BuildingAttributes | UtilityAttributes, Field(discriminator="kind")]


class ElevationSample(Contract):
    position: Position
    chainage_m: Annotated[float, Field(ge=0)] | None
    elevation: Fact[Quantity]
    vertical_reference: VerticalReference
    ground_sample_id: Id | None


class ProfileUnits(Contract):
    length: Literal["m"] = "m"
    area: Literal["m2"] = "m2"
    angle: Literal["deg"] = "deg"
    slope: Literal["percent"] = "percent"


class ContextCollection(Contract):
    retrieval: Literal["COMPLETE", "PARTIAL", "FAILED", "NOT_REQUESTED"]
    features: Annotated[list[ContextFeature], Field(max_length=100)]
    evidence_ids: Ids
    query_extent: GeometryReference
    truncated: bool


class Nearby(Contract):
    roads: ContextCollection
    waterways: ContextCollection
    buildings: ContextCollection
    utilities: ContextCollection


class ConstraintSnapshot(Contract):
    id: Id
    kind: str
    content_hash: Digest
    evidence_ids: Ids
    applicability: Literal["UNVERIFIED"] = "UNVERIFIED"


class SourceSnapshotRef(Contract):
    id: Id
    version: int | None
    content_hash: Digest


class SiteProfileVersion(Contract):
    id: Id
    site_profile_id: Id
    project_id: Id
    version: int
    schema_version: Literal["site-profile/1"] = "site-profile/1"
    content_hash: Digest
    created_at: datetime
    selection_version: Ref
    boundary_snapshot: Fact[GeometryReference]
    location: Fact[Position]
    coordinate_system: HorizontalCRS
    calculation_crs: HorizontalCRS
    vertical_reference: VerticalReference
    units: ProfileUnits = Field(default_factory=ProfileUnits)
    dimensions: Dimensions
    orientation: Orientation
    terrain: TerrainSummary
    relief: Relief
    nearby: Nearby
    survey_dataset_refs: list[SourceSnapshotRef]
    constraints: list[ConstraintSnapshot]
    environmental_facts: list[Fact[str]]
    planning_facts: list[Fact[str]]
    on_site_objects: list[ObjectRef]
    evidence_ids: Ids
    missing_information_ids: Ids
    readiness_assessment_id: Id
    dependency_manifest_id: Id
    limitations: list[str]


class SelectionInput(Contract):
    selection: SiteSelection
    original_crs: HorizontalCRS
    expected_version: int | None = None


class ProfileInput(Contract):
    selection_version_id: Id


class TextPart(Contract):
    kind: Literal["TEXT"]
    text: Annotated[str, Field(min_length=1, max_length=12000)]


class AttachmentPart(Contract):
    kind: Literal["ATTACHMENT"]
    attachment_id: Id
    media_type: Annotated[str, Field(max_length=100)]
    content_hash: Digest


class ProposalPart(Contract):
    kind: Literal["PROPOSAL"]
    proposal_version_id: Id


class QuestionPart(Contract):
    kind: Literal["QUESTION"]
    question_id: Id
    text: Annotated[str, Field(min_length=1, max_length=6000)]
    options: Annotated[list[str], Field(max_length=20)]


class EvidencePart(Contract):
    kind: Literal["EVIDENCE"]
    evidence_ids: Ids


class AssumptionPart(Contract):
    kind: Literal["ASSUMPTION"]
    assumption_version_id: Id


MessagePart = Annotated[TextPart | AttachmentPart | ProposalPart | QuestionPart | EvidencePart | AssumptionPart, Field(discriminator="kind")]


class MessageContext(Contract):
    selection: Annotated[list[ObjectRef], Field(max_length=1000)] = Field(default_factory=list)
    site_selection_version_id: Id | None = None
    site_profile_version_id: Id | None = None
    model_revision_id: Id | None = None
    scenario_id: Id | None = None
    proposal_version_id: Id | None = None
    memory_version_ids: Ids = Field(default_factory=list)
    editor_dirty: bool = False


class SubmitContext(Contract):
    """Browser sends stable object IDs; server resolves hashes from the pinned revision."""
    selected_object_ids: Ids = Field(default_factory=list)
    site_selection_version_id: Id | None = None
    site_profile_version_id: Id | None = None
    model_revision_id: Id | None = None
    scenario_id: Id | None = None
    proposal_version_id: Id | None = None
    editor_dirty: bool = False


class MessageInput(Contract):
    client_request_id: Id
    parts: Annotated[list[MessagePart], Field(min_length=1, max_length=20)]
    context: SubmitContext


class ConversationInput(Contract):
    client_request_id: Id
    title: Annotated[str, Field(min_length=1, max_length=255)] = "Project discussion"


class RequirementConstraint(Contract):
    operator: Literal["EQ", "MIN", "MAX", "IN"]
    value: str | Finite | bool | Annotated[list[str], Field(min_length=1, max_length=100)]
    unit: Annotated[str, Field(max_length=50)] | None = None

    @model_validator(mode="after")
    def operator_value(self):
        if self.operator in {"MIN", "MAX"} and (isinstance(self.value, bool) or not isinstance(self.value, (int, float))):
            raise ValueError("MIN/MAX requires a numeric value")
        if self.operator == "IN" and not isinstance(self.value, list):
            raise ValueError("IN requires a list")
        if self.operator != "IN" and isinstance(self.value, list):
            raise ValueError("Only IN accepts a list")
        return self


class ProjectRequirement(Contract):
    kind: Literal["REQUIREMENT"]
    key: Annotated[str, Field(min_length=1, max_length=128)]
    constraint: RequirementConstraint
    hardness: Literal["HARD", "SOFT"]


class ProjectPreference(Contract):
    kind: Literal["PREFERENCE"]
    key: Id
    value: Annotated[str, Field(min_length=1, max_length=2000)]
    priority: Literal["LOW", "NORMAL", "HIGH"]


class ProjectDecision(Contract):
    kind: Literal["DECISION"]
    statement: Annotated[str, Field(min_length=1, max_length=4000)]
    rationale: Annotated[str, Field(max_length=4000)]
    selected_alternative_id: Id | None = None


class ProjectAssumption(Contract):
    kind: Literal["ASSUMPTION"]
    statement: Annotated[str, Field(min_length=1, max_length=4000)]
    impact: Annotated[str, Field(max_length=2000)]
    required_verification: Annotated[str, Field(max_length=2000)] | None = None
    scope: Literal["CONCEPT_ONLY", "PROJECT"]


MemoryPayload = Annotated[ProjectRequirement | ProjectPreference | ProjectDecision | ProjectAssumption, Field(discriminator="kind")]


class MemoryInput(Contract):
    client_request_id: Id
    asset_id: Id | None = None
    content: MemoryPayload
    source_message_ids: Ids = Field(default_factory=list)
    evidence_ids: Ids = Field(default_factory=list)


class MemoryRevisionInput(MemoryInput):
    expected_version: Annotated[int, Field(ge=1)]


class MemoryAction(Contract):
    expected_status: Literal["PROPOSED", "ACCEPTED", "REJECTED", "SUPERSEDED"] = "PROPOSED"


class RunSummary(Contract):
    id: Id
    status: str
    error_code: str | None
    message_id: Id
    conversation_id: Id
    progress: str | None = None
    capabilities: list["AssetCapability"] = Field(default_factory=list)


class MessageView(Contract):
    id: Id
    conversation_id: Id
    sequence: int
    role: Literal["USER", "ASSISTANT", "SYSTEM_EVENT"]
    parts: list[MessagePart]
    context: MessageContext
    created_at: datetime
    client_request_id: Id | None
    status: Literal["COMPLETE", "INTERRUPTED", "FAILED"]
    run: RunSummary | None


class ConversationView(Contract):
    id: Id
    project_id: Id
    title: str
    created_by: Id
    created_at: datetime
    archived_at: datetime | None
    next_sequence: int


class MemoryView(Contract):
    id: Id
    version_id: Id
    version: int
    project_id: Id
    asset_id: Id | None
    status: Literal["PROPOSED", "ACCEPTED", "REJECTED", "SUPERSEDED"]
    content_hash: Digest
    supersedes_version_id: Id | None
    actor_id: Id | None
    content: MemoryPayload
    source_message_ids: Ids
    evidence_ids: Ids
    proposed_by: Id
    created_at: datetime
    accepted_by: Id | None
    accepted_at: datetime | None


class ProfileView(Contract):
    id: Id
    selection_id: Id
    refresh_state: str
    job_id: Id | None
    error_code: str | None
    current: bool
    version: SiteProfileVersion | None


class ReadinessOperation(Contract):
    operation: str
    eligible: bool
    reasons: list[str]


class ReadinessView(Contract):
    site_data_state: str
    current: bool
    database_mode: str | None = None
    rule_set_version: str | None = None
    status: str | None = None
    operations: list[ReadinessOperation]


class WorkspaceContracts(Contract):
    profile: SiteProfileVersion
    selection_input: SelectionInput
    profile_input: ProfileInput
    message_context: MessageContext
    message_input: MessageInput
    conversation_input: ConversationInput
    memory_input: MemoryInput
    memory_revision: MemoryRevisionInput
    memory_action: MemoryAction
    message_view: MessageView
    conversation_view: ConversationView
    memory_view: MemoryView
    profile_view: ProfileView
    readiness_view: ReadinessView
    elevation_sample: ElevationSample
