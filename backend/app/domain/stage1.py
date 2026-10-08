"""Stage 1 foundation contracts. No retrieval, generation or AI execution.

Pydantic is the source of truth for the checked-in JSON Schema/TypeScript bundle.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from pydantic.alias_generators import to_camel
from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely.geometry import shape

Id = Annotated[str, Field(min_length=1, max_length=128)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Ids = Annotated[list[Id], Field(max_length=1000)]
T = TypeVar("T")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True,
                              alias_generator=to_camel, populate_by_name=True)


class SourceKind(str, Enum):
    MEASURED = "MEASURED"
    SURVEY = "SURVEY"
    PUBLIC_MAP = "PUBLIC_MAP"
    USER_PROVIDED = "USER_PROVIDED"
    DERIVED = "DERIVED"
    AI_ASSUMPTION = "AI_ASSUMPTION"
    UNKNOWN = "UNKNOWN"


UnknownReason = Literal["NOT_COLLECTED", "UNAVAILABLE", "OUTSIDE_COVERAGE",
                        "REFERENCE_UNRESOLVED", "RETRIEVAL_FAILED", "CONFLICTING_EVIDENCE"]


class KnownFact(Contract, Generic[T]):
    id: Id
    source_kind: Literal["MEASURED", "SURVEY", "PUBLIC_MAP", "USER_PROVIDED", "DERIVED", "AI_ASSUMPTION"]
    value: T
    evidence_ids: Annotated[list[Id], Field(min_length=1, max_length=1000)]
    use: Literal["CONTEXT_ONLY", "CONCEPT", "VALIDATED_INPUT"]
    verification: Literal["UNVERIFIED", "VERIFIED", "CONFLICTED", "EXPIRED"]

    @model_validator(mode="after")
    def evidence_use(self):
        if self.value is None:
            raise ValueError("Known facts require a value")
        if self.source_kind in {"PUBLIC_MAP", "AI_ASSUMPTION"} and self.use == "VALIDATED_INPUT":
            raise ValueError("Context/assumptions are not validated engineering inputs")
        if self.use == "VALIDATED_INPUT" and self.verification != "VERIFIED":
            raise ValueError("Validated input requires verified evidence")
        return self


class UnknownFact(Contract):
    id: Id
    source_kind: Literal["UNKNOWN"]
    value: None
    reason: UnknownReason
    evidence_ids: Ids = Field(default_factory=list)
    missing_information_ids: Ids = Field(default_factory=list)


class Fact(RootModel[Annotated[KnownFact[T] | UnknownFact, Field(discriminator="source_kind")]], Generic[T]):
    pass


class ResolvedHorizontalCRS(Contract):
    status: Literal["RESOLVED"]
    definition: Annotated[str, Field(min_length=1, max_length=8192)]
    axis_order: Literal["XY"]
    unit: Literal["METRE", "DEGREE"]
    transform_id: Id | None = None

    @model_validator(mode="after")
    def valid_crs(self):
        try:
            crs = CRS.from_user_input(self.definition)
        except CRSError as exc:
            raise ValueError("Unrecognized horizontal CRS") from exc
        if not (crs.is_geographic or crs.is_projected) or len(crs.axis_info) != 2:
            raise ValueError("A two-dimensional horizontal CRS is required")
        expected = "DEGREE" if crs.is_geographic else "METRE"
        if self.unit != expected or any(a.unit_name.lower() not in {"degree", "metre", "meter"} for a in crs.axis_info):
            raise ValueError("CRS units do not match the contract")
        return self


class UnknownHorizontalCRS(Contract):
    status: Literal["UNKNOWN"]
    definition: None = None
    axis_order: None = None
    unit: None = None
    transform_id: None = None


HorizontalCRS = Annotated[ResolvedHorizontalCRS | UnknownHorizontalCRS, Field(discriminator="status")]


class ResolvedVerticalReference(Contract):
    status: Literal["RESOLVED"]
    kind: Literal["ORTHOMETRIC", "ELLIPSOIDAL", "LOCAL_DATUM"]
    identifier: Id
    unit: Literal["METRE"]
    geoid_model_version: Id | None = None


class UnknownVerticalReference(Contract):
    status: Literal["UNKNOWN"]
    kind: None = None
    identifier: None = None
    unit: None = None
    geoid_model_version: None = None


VerticalReference = Annotated[ResolvedVerticalReference | UnknownVerticalReference, Field(discriminator="status")]


class Ref(Contract):
    id: Id
    version: Annotated[int, Field(ge=1)]
    content_hash: Digest


class ObjectRef(Contract):
    asset_id: Id
    object_id: Id
    model_revision_id: Id
    component_id: Id
    geometry_hash: Digest


XY = tuple[Finite, Finite]
Line = Annotated[list[XY], Field(min_length=2, max_length=10000)]
Ring = Annotated[list[XY], Field(min_length=4, max_length=10000)]
PolygonCoordinates = Annotated[list[Ring], Field(min_length=1, max_length=100)]


class Geometry(Contract):
    type: Literal["Point", "MultiPoint", "LineString", "Polygon", "MultiPolygon"]
    coordinates: XY | Line | PolygonCoordinates | list[PolygonCoordinates]

    @model_validator(mode="after")
    def valid_geometry(self):
        try:
            geom = shape(self.model_dump())
            if geom.is_empty or not geom.is_valid or geom.has_z:
                raise ValueError("Invalid or empty 2D geometry")
            if geom.geom_type in {"Polygon", "MultiPolygon"}:
                polygons = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
                raw_polygons = [self.coordinates] if geom.geom_type == "Polygon" else self.coordinates
                if any(ring[0] != ring[-1] for poly in raw_polygons for ring in poly):
                    raise ValueError("Polygon rings must be explicitly closed")
                if any(p.area <= 0 for p in polygons):
                    raise ValueError("Area must be positive")
        except (TypeError, IndexError, AttributeError) as exc:
            raise ValueError("Coordinates do not match geometry type") from exc
        return self


class AreaSelection(Contract):
    kind: Literal["AREA"]
    geometry: Geometry

    @model_validator(mode="after")
    def area(self):
        if self.geometry.type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("AREA requires a polygon")
        return self


class RouteSelection(Contract):
    kind: Literal["ROUTE"]
    geometry: Geometry
    corridor_width_m: Annotated[float, Field(gt=0, le=10000)] | None = None

    @model_validator(mode="after")
    def route(self):
        if self.geometry.type != "LineString" or shape(self.geometry.model_dump()).length <= 0:
            raise ValueError("ROUTE requires a nonzero LineString")
        return self


class PointSelection(Contract):
    kind: Literal["POINT"]
    geometry: Geometry

    @model_validator(mode="after")
    def point(self):
        if self.geometry.type != "Point":
            raise ValueError("POINT requires a point")
        return self


class EndpointsSelection(Contract):
    kind: Literal["ENDPOINTS"]
    endpoint_a: Geometry
    endpoint_b: Geometry

    @model_validator(mode="after")
    def endpoints(self):
        if self.endpoint_a.type != "Point" or self.endpoint_b.type != "Point" or self.endpoint_a == self.endpoint_b:
            raise ValueError("Two distinct points required")
        return self


class CrossingSelection(Contract):
    kind: Literal["CROSSING"]
    geometry: Geometry
    endpoint_a: Geometry
    endpoint_b: Geometry
    crossed_feature_ref: Id | None = None
    study_area: Geometry | None = None

    @model_validator(mode="after")
    def crossing(self):
        EndpointsSelection(kind="ENDPOINTS", endpoint_a=self.endpoint_a, endpoint_b=self.endpoint_b)
        if self.geometry.type != "LineString" or self.geometry.coordinates[0] != self.endpoint_a.coordinates or self.geometry.coordinates[-1] != self.endpoint_b.coordinates:
            raise ValueError("Crossing line must match its endpoints")
        if self.study_area and self.study_area.type != "Polygon":
            raise ValueError("Study area must be Polygon")
        return self


SiteSelection = Annotated[AreaSelection | RouteSelection | CrossingSelection | PointSelection | EndpointsSelection, Field(discriminator="kind")]


class SelectionVersion(Contract):
    id: Id
    selection_id: Id
    project_id: Id
    version: Annotated[int, Field(ge=1)]
    selection: SiteSelection
    original_crs: ResolvedHorizontalCRS
    original_geometry: Geometry
    canonical_crs: Literal["EPSG:4326"]
    canonical_geometry: Geometry
    transformation_evidence_id: Id
    content_hash: Digest
    created_by: Id
    created_at: datetime

    @model_validator(mode="after")
    def canonical(self):
        g = shape(self.canonical_geometry.model_dump())
        lo, la, hi, ha = g.bounds
        if not (-180 <= lo <= hi <= 180 and -90 <= la <= ha <= 90):
            raise ValueError("Canonical coordinates must be longitude/latitude")
        expected = (Geometry(type="MultiPoint", coordinates=[self.selection.endpoint_a.coordinates, self.selection.endpoint_b.coordinates])
                    if self.selection.kind == "ENDPOINTS" else self.selection.geometry)
        if expected != self.canonical_geometry:
            raise ValueError("Selection uses canonical geometry; it must match")
        return self


class MeasuredSource(Contract):
    kind: Literal["MEASURED"]
    measurement_id: Id
    instrument: str | None = None
    operator_id: Id | None = None


class SurveySource(Contract):
    kind: Literal["SURVEY"]
    survey_dataset_id: Id | None = None
    terrain_dataset_id: Id | None = None
    source_file_id: Id
    validation_run_id: Id | None = None

    @model_validator(mode="after")
    def dataset_required(self):
        if not (self.survey_dataset_id or self.terrain_dataset_id):
            raise ValueError("Survey evidence requires a dataset")
        return self


class PublicMapSource(Contract):
    kind: Literal["PUBLIC_MAP"]
    provider: Id
    feature_id: Id | None = None
    source_url: Annotated[str, Field(pattern=r"^https?://", max_length=2048)]
    license: Annotated[str, Field(min_length=1, max_length=500)]
    query_extent_hash: Digest


class UserSource(Contract):
    kind: Literal["USER_PROVIDED"]
    message_id: Id | None = None
    source_record_id: Id | None = None
    actor_id: Id

    @model_validator(mode="after")
    def source_required(self):
        if not (self.message_id or self.source_record_id):
            raise ValueError("User evidence requires a message or saved source record")
        return self


class DerivedSource(Contract):
    kind: Literal["DERIVED"]
    input_evidence_ids: Annotated[list[Id], Field(min_length=1, max_length=1000)]
    algorithm_id: Id
    algorithm_version: Id
    parameters_hash: Digest
    output_artifact_id: Id | None = None


class AssumptionSource(Contract):
    kind: Literal["AI_ASSUMPTION"]
    message_id: Id
    assumption_id: Id
    model_id: Id


class UnknownSource(Contract):
    kind: Literal["UNKNOWN"]
    reason: UnknownReason
    failed_operation_id: Id | None = None


EvidenceSource = Annotated[MeasuredSource | SurveySource | PublicMapSource | UserSource | DerivedSource | AssumptionSource | UnknownSource, Field(discriminator="kind")]


class Accuracy(Contract):
    horizontal_rmse_m: Annotated[float, Field(ge=0)] | None = None
    vertical_rmse_m: Annotated[float, Field(ge=0)] | None = None
    method: str | None = None
    validation_run_id: Id | None = None
    independent_checkpoint_count: Annotated[int, Field(ge=0)] | None = None

    @model_validator(mode="after")
    def accuracy_evidence(self):
        if (self.horizontal_rmse_m is not None or self.vertical_rmse_m is not None) and not self.method:
            raise ValueError("Accuracy needs a measurement/validation method, not image resolution")
        return self


class Evidence(Contract):
    id: Id
    project_id: Id
    source_type: SourceKind
    source_id: Id | None = None
    dataset_id: Id | None = None
    dataset_version_id: Id | None = None
    captured_at: datetime | None = None
    retrieved_at: datetime
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    horizontal_crs: HorizontalCRS
    vertical_reference: VerticalReference
    accuracy: Accuracy
    status: Literal["UNVERIFIED", "VERIFIED", "CONFLICTED", "EXPIRED", "FAILED"]
    source: EvidenceSource
    content_hash: Digest
    supersedes_id: Id | None = None

    @model_validator(mode="after")
    def consistent_source(self):
        if self.source_type.value != self.source.kind:
            raise ValueError("Source discriminators must agree")
        if self.source.kind in {"UNKNOWN", "AI_ASSUMPTION"} and self.status == "VERIFIED":
            raise ValueError("Unknown/assumed evidence is not verified")
        if self.source.kind == "SURVEY" and self.status == "VERIFIED" and not self.source.validation_run_id:
            raise ValueError("Survey verification requires validation evidence")
        return self


class MissingSiteInformation(Contract):
    id: Id
    profile_version_id: Id
    type: Literal["SOIL_BEARING_CAPACITY", "GROUNDWATER", "UTILITIES", "DESIGN_FLOOD_LEVEL", "SURVEY_ACCURACY", "OWNERSHIP", "LOCAL_CODE", "ELEVATION", "OTHER"]
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    why_needed: Annotated[str, Field(min_length=1, max_length=2000)]
    required_for: list[Literal["CONCEPT_LAYOUT", "GEOMETRY_CHECK", "FOUNDATION_ANALYSIS", "HYDRAULIC_ANALYSIS", "CONSTRUCTION_DOCUMENTATION"]]
    blocking_level: Literal["NONE", "CONCEPT", "GEOMETRY", "ENGINEERING"]
    resolution_method: list[Literal["USER_CONFIRMATION", "SURVEY_UPLOAD", "GEOTECH_REPORT", "UTILITY_SURVEY", "AUTHORITY_SOURCE", "VALIDATED_CALCULATION"]]
    status: Literal["OPEN", "RESOLVED", "NOT_APPLICABLE"]
    resolution_evidence_ids: Ids = Field(default_factory=list)

    @model_validator(mode="after")
    def resolved(self):
        if self.status == "RESOLVED" and not self.resolution_evidence_ids:
            raise ValueError("Resolution needs evidence")
        return self


Level = Literal["FULL", "PARTIAL", "CONCEPT_ONLY", "UNSUPPORTED"]
Operation = Literal["DISCUSS", "PLAN", "PROPOSE", "GENERATE", "VALIDATE_GEOMETRY", "ANALYZE"]


class RequiredInput(Contract):
    operation: Operation
    field: Id
    minimum_evidence_use: Literal["CONTEXT_ONLY", "CONCEPT", "VALIDATED_INPUT"]


class AssetCapability(Contract):
    asset_type: Id
    asset_family: Id | None = None
    display_name: str | None = None
    component_kinds: list[Id] = Field(default_factory=list)
    registry_version: Id
    discussion_support: Level
    planning_support: Level
    proposal_support: Level
    generation_support: Level
    geometry_validation_support: Level
    engineering_analysis_support: Level
    site_selection_types: list[Literal["AREA", "ROUTE", "CROSSING", "POINT", "ENDPOINTS"]]
    required_inputs: list[RequiredInput] = Field(default_factory=list)
    optional_inputs: Ids = Field(default_factory=list)
    specification_schema_id: Id | None = None
    generator_id: Id | None = None
    generator_version: Id | None = None
    validator_ids: Ids = Field(default_factory=list)
    analysis_calculator_ids: Ids = Field(default_factory=list)
    supported_operations: list[Operation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def executable(self):
        mapping = {"DISCUSS": self.discussion_support, "PLAN": self.planning_support,
                   "PROPOSE": self.proposal_support, "GENERATE": self.generation_support,
                   "VALIDATE_GEOMETRY": self.geometry_validation_support, "ANALYZE": self.engineering_analysis_support}
        if any(mapping[op] not in {"FULL", "PARTIAL"} for op in self.supported_operations):
            raise ValueError("Unsupported/concept-only operations cannot execute")
        if "GENERATE" in self.supported_operations and not (self.generator_id and self.generator_version and self.specification_schema_id):
            raise ValueError("Executable generation must name a versioned module")
        if "ANALYZE" in self.supported_operations and not self.analysis_calculator_ids:
            raise ValueError("Analysis requires dedicated calculators")
        if "VALIDATE_GEOMETRY" in self.supported_operations and not self.validator_ids:
            raise ValueError("Geometry validation requires validators")
        return self


class AssetRequest(Contract):
    id: Id
    asset_type: Id  # Open registry identifier, never a building-only enum.
    asset_family: Id | None = None
    requested_asset_name: Annotated[str, Field(min_length=1, max_length=255)]
    registry_id: Id | None = None
    requirements: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    referenced_objects: Annotated[list[ObjectRef], Field(max_length=1000)] = Field(default_factory=list)


class CivilIntent(Contract):
    kind: Literal["QUESTION", "SITE_QUERY", "DESIGN_REQUEST", "CHANGE_REQUEST", "ANALYSIS_REQUEST",
                  "EXPLANATION_REQUEST", "PROPOSAL_APPROVAL", "GENERAL_DISCUSSION"]
    domain: Literal["CIVIL_INFRASTRUCTURE", "GENERAL", "UNRESOLVED"]
    assets: Annotated[list[AssetRequest], Field(max_length=100)]
    needs_clarification: bool
    clarification_question: str | None = None

    @model_validator(mode="after")
    def unique_assets(self):
        if len({a.id for a in self.assets}) != len(self.assets):
            raise ValueError("Asset requests need distinct identities")
        return self


class Dependency(Contract):
    kind: Literal["SELECTION", "BOUNDARY", "TERRAIN", "PLACEMENT", "MODEL", "MEMORY", "CONSTRAINT", "SURVEY_EVIDENCE", "RELATIONSHIP", "GENERATOR", "VALIDATOR"]
    id: Id
    version: Id
    content_hash: Digest
    policy: Literal["MUST_MATCH_CURRENT", "PINNED_SNAPSHOT"]
    scope: Id


class DependencyManifest(Contract):
    schema_version: Literal["dependencies/1"]
    entries: Annotated[list[Dependency], Field(max_length=1000)]
    hash: Digest


class ValidationIssue(Contract):
    code: Id
    severity: Literal["INFO", "WARNING", "BLOCKER"]
    component_ids: Ids
    field_paths: Ids
    evidence_ids: Ids
    message: str
    remediation: str


class ValidationResult(Contract):
    id: Id
    level: Literal["CONCEPT_VALIDATION", "GEOMETRY_VALIDATION", "ENGINEERING_ANALYSIS"]
    validator_id: Id
    validator_version: Id
    input_hash: Digest
    status: Literal["PASSED", "FAILED", "NOT_RUN", "UNSUPPORTED", "ERROR", "STALE"]
    issues: Annotated[list[ValidationIssue], Field(max_length=1000)]
    output_artifact_id: Id | None = None

    @model_validator(mode="after")
    def passed(self):
        if self.status == "PASSED" and any(i.severity == "BLOCKER" for i in self.issues):
            raise ValueError("A blocked validation cannot pass")
        return self


ProposalStatus = Literal["DRAFT", "GENERATING", "READY_FOR_REVIEW", "HAS_ISSUES", "APPROVED", "STALE", "REJECTED", "BUILT"]


class ProposalPayload(Contract):
    schema_version: Literal["proposal/1"]
    site_profile_version_id: Id
    input_memory_version_ids: Ids
    asset_specification_version_ids: Ids
    layout_geometry_refs: list[Ref]
    assumption_version_ids: Ids
    alternative_ids: Ids
    source_scenario_id: Id
    source_model_revision_id: Id | None
    dependency_manifest_id: Id
    parent_version_id: Id | None


class ApprovalCommand(Contract):
    proposal_version_id: Id
    proposal_hash: Digest
    dependency_hash: Digest
    validation_hash: Digest
    alternative_id: Id | None
    acknowledged_assumption_version_ids: Ids
    expected_model_revision_id: Id | None


class ProposalCommand(Contract):
    effect: Literal["PROPOSAL_ONLY"]
    kind: Literal["DESIGN_REQUEST", "CHANGE_REQUEST"]
    request: Annotated[str, Field(min_length=1, max_length=6000)]
    objects: Annotated[list[ObjectRef], Field(max_length=1000)]


class FoundationContracts(Contract):
    """Export root; not an API request or stored aggregate."""
    numeric_fact: Fact[Finite]
    text_fact: Fact[str]
    horizontal_crs: HorizontalCRS
    vertical_reference: VerticalReference
    reference: Ref
    object_reference: ObjectRef
    selection: SelectionVersion
    evidence: Evidence
    missing_information: MissingSiteInformation
    capability: AssetCapability
    dependencies: DependencyManifest
    validation: ValidationResult
    proposal: ProposalPayload
    approval: ApprovalCommand
    proposal_command: ProposalCommand
    civil_intent: CivilIntent
