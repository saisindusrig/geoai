# GeoAI Stage 1 implementation architecture

Status: proposed implementation contract, reviewed 8 October 2026. This document does not claim these changes are implemented. Scope: persistent conversation, evidence-backed site understanding, generic proposals, and one complete building vertical slice. No new road, bridge, dam, or tunnel generators in this milestone.

## 0. Repository integration and non-negotiable boundaries

Keep Cesium and the current workspace layout, Assistant tab, Layers, Inspect, History, Checks, Engineering Dock, and advanced selection. Extend their data contracts; do not introduce another workspace or chat page.

Reuse these inspected implementation points:

- `backend/app/db/models.py`: Project, ModelRevision, BuildingPlan, TerrainDatasetVersion, ActiveTerrainConfiguration, ModelPlacement, GroundSample, EngineeringAnalysis, ConstraintDataset and audit records.
- `services/survey/engineering_evidence.py`: existing readiness states UNCONFIGURED, VISUAL_REFERENCE, SPATIAL_READY, SURVEY_READY, ENGINEERING_READY and BLOCKED. Do not replace them with an AI score.
- `services/survey/terrain_activation.py`: activation marks affected placement/check state for review without moving geometry. Preserve this behavior.
- `services/survey/terrain_capabilities.py`: explicit PostGIS/authoritative-survey capability boundary.
- `services/ai/building_plan.py`, `api/routes/building_plans.py`, `services/design/planned_building.py`: adapt the existing structured building specification, validation, approval and deterministic generation.
- `frontend/components/workspace/AssistantPanel.tsx`: currently local text history and direct update_parameters/regenerate callbacks. Replace this mutation path before exposing the new assistant.
- `frontend/components/workspace/BuildingAssistant.tsx`: move reusable proposal review controls into the existing Assistant tab; avoid two independent assistants.
- Existing model editor selection (`selectedIds`) and model revisions: capture these on message submission, not later when a tool happens to execute.

Important existing-schema issue: ModelPlacement.anchor_elevation is non-null with a zero default. Never interpret that legacy value as known ground. Add an explicit resolution state and make unknown elevation nullable after a provenance-aware backfill; preserve known zero and all legacy transforms. Render-only local z=0 is permitted as a local coordinate, never as an asserted geographic elevation.

Architecture: one modular FastAPI application, existing workers and jobs, PostgreSQL/PostGIS production storage, typed services and an asset plugin registry. No additional microservices, graph database or vector database in Stage 1.

## 1. Common contracts and SiteProfile

All IDs below are opaque strings at the API boundary; existing numeric database IDs remain numeric internally. All times are UTC ISO-8601. Models reject extra fields, NaN/Infinity, invalid references and unbounded arrays. Generate TypeScript contracts from Pydantic/OpenAPI instead of maintaining two independent schemas.

```ts
type Ref = { id: string; version: number; contentHash: string };
type SourceKind = 'MEASURED' | 'SURVEY' | 'PUBLIC_MAP' | 'USER_PROVIDED'
  | 'DERIVED' | 'AI_ASSUMPTION' | 'UNKNOWN';
type UnknownReason = 'NOT_COLLECTED' | 'UNAVAILABLE' | 'OUTSIDE_COVERAGE'
  | 'REFERENCE_UNRESOLVED' | 'RETRIEVAL_FAILED' | 'CONFLICTING_EVIDENCE';
type Fact<T> =
  | { id: string; sourceKind: Exclude<SourceKind, 'UNKNOWN'>; value: T;
      evidenceIds: string[]; use: 'CONTEXT_ONLY' | 'CONCEPT' | 'VALIDATED_INPUT';
      verification: 'UNVERIFIED' | 'VERIFIED' | 'CONFLICTED' | 'EXPIRED' }
  | { id: string; sourceKind: 'UNKNOWN'; value: null; reason: UnknownReason;
      evidenceIds: string[]; missingInformationIds: string[] };
type Quantity<U extends string> = { value: number; unit: U };
type ApplicableFact<T> = { applicability: 'APPLICABLE'; fact: Fact<T> }
  | { applicability: 'NOT_APPLICABLE'; reason: string };
type HorizontalCRS =
  | { status: 'RESOLVED'; definition: string; axisOrder: 'XY'; unit: 'METRE' | 'DEGREE'; transformId: string | null }
  | { status: 'UNKNOWN'; definition: null; axisOrder: null; unit: null; transformId: null };
type VerticalReference =
  | { status: 'RESOLVED'; kind: 'ORTHOMETRIC' | 'ELLIPSOIDAL' | 'LOCAL_DATUM';
      identifier: string; unit: 'METRE'; geoidModelVersion: string | null }
  | { status: 'UNKNOWN'; kind: null; identifier: null; unit: null; geoidModelVersion: null };
type GeoPosition = { longitude: number; latitude: number };
type ObjectRef = { assetId: string; objectId: string; modelRevisionId: string;
  componentId: string; geometryHash: string };
type ContextFeature = { id: string; kind: 'ROAD' | 'WATERWAY' | 'BUILDING' | 'UTILITY';
  geometry: Fact<GeometryRef>; name: Fact<string>; attributes: ContextAttributes };
// ContextAttributes is a discriminated union: Road(width,class), Waterway(type),
// Building(height,use), Utility(service,depth,operator); each field is a Fact.
type GeometryRef = { id: string; hash: string; horizontalCRS: HorizontalCRS };
type ElevationSample = { position: GeoPosition; elevation: Fact<Quantity<'m'>>;
  verticalReference: VerticalReference; groundSampleId: string | null };
type TerrainCoverage = { status: 'FULL' | 'PARTIAL' | 'NONE' | 'UNKNOWN';
  coveredFraction: number | null; checkedGeometryHash: string;
  methodVersion: string; evidenceIds: string[] };
type Constraint = { id: string; kind: 'SETBACK' | 'EASEMENT' | 'FLOOD_ZONE'
  | 'PROTECTED_AREA' | 'HEIGHT_LIMIT' | 'OTHER'; description: Fact<string>;
  geometry: Fact<GeometryRef>; limit: Fact<Quantity<'m' | 'm2'>>;
  applicability: 'VERIFIED' | 'UNVERIFIED' | 'NOT_APPLICABLE'; datasetRef: Ref | null };
type ContextCollection<T> = { retrieval: 'COMPLETE' | 'PARTIAL' | 'FAILED' | 'NOT_REQUESTED';
  features: T[]; evidenceIds: string[]; queryExtent: GeometryRef; truncated: boolean };
interface SiteProfileVersion {
  id: string; siteProfileId: string; projectId: string; version: number;
  schemaVersion: 'site-profile/1'; contentHash: string; createdAt: string;
  selectionVersion: Ref; boundarySnapshot: Fact<GeometryRef>;
  location: Fact<GeoPosition>; coordinateSystem: HorizontalCRS;
  calculationCRS: HorizontalCRS; verticalReference: VerticalReference;
  units: { length: 'm'; area: 'm2'; angle: 'deg'; slope: 'percent' };
  dimensions: { area: ApplicableFact<Quantity<'m2'>>; perimeter: ApplicableFact<Quantity<'m'>>;
    routeLength: ApplicableFact<Quantity<'m'>>; crossingSpan: ApplicableFact<Quantity<'m'>>;
    boundingWidth: ApplicableFact<Quantity<'m'>>; boundingDepth: ApplicableFact<Quantity<'m'>> };
  orientation: { azimuth: Fact<Quantity<'deg'>>;
    method: 'PRINCIPAL_AXIS' | 'ENDPOINT_BEARING' | 'USER_AXIS' | 'UNDEFINED' };
  terrain: { activeConfigurationRevision: number | null; datasetId: string | null;
    versionId: string | null; coverage: TerrainCoverage; sampleSetId: string | null;
    sampleSummary: { requested: number; valid: number; failed: number } };
  relief: { minElevation: Fact<Quantity<'m'>>; maxElevation: Fact<Quantity<'m'>>;
    meanSlope: Fact<Quantity<'percent'>>; maxSlope: Fact<Quantity<'percent'>>;
    slopeMethodVersion: string | null; profileIds: string[] };
  nearby: { roads: ContextCollection<ContextFeature>; waterways: ContextCollection<ContextFeature>;
    buildings: ContextCollection<ContextFeature>; utilities: ContextCollection<ContextFeature> };
  surveyDatasetRefs: Ref[]; constraints: Constraint[];
  environmentalFacts: Fact<string>[]; planningFacts: Fact<string>[];
  onSiteObjects: ObjectRef[]; evidenceIds: string[]; missingInformationIds: string[];
  readinessAssessmentId: string; dependencyManifestId: string;
}
interface SiteProfile { id: string; projectId: string; selectionId: string;
  latestVersionId: string | null; refreshState: 'IDLE' | 'QUEUED' | 'RUNNING' | 'FAILED' }
```

Fact wrappers are typed fields, not a single metadata bag. `UNKNOWN` cannot carry a numeric value. An unavailable utility search is not evidence of no utilities. Unsupported/nonapplicable dimensions have an explicit applicability flag in their Pydantic field contract; they are not fabricated measurements. Conflicting elevations remain separate observations with a conflicted resolved fact, never silently averaged. AI assumptions belong in proposal/memory records; adding one does not rewrite the observed site profile.

Geometry types are imported from the application's GeoJSON contracts. `ContextAttributes` must be implemented as four strict named schemas, not `Record<string, unknown>`: Road has classification/width/access; Waterway has waterwayType/flowDirection; Building has height/storeys/use; Utility has service/depth/operator. All are Fact-wrapped and use explicit units. Elevation profiles are immutable ordered `{chainageM, position, elevationFact, verticalReference}` samples plus route version, sampling method/version, spacing, coverage and nodata intervals. Never interpolate across unknown intervals without a separately identified derived result and an approved calculation policy.

Storage: immutable `site_profile_versions`, typed JSONB snapshot validated by schema, normalized evidence/missing-information references, paginated sample/profile sets. No raster or thousands of samples inside every API response. Backend: `site_profiles/service.py`. API: section 22. Frontend: status summary and evidence drill-down via Inspect/Engineering Dock. Version changes on new captured inputs or calculation versions; repeated identical refresh returns the existing version. Tests: null preservation, classified facts, immutable snapshots, hash stability.

## 2. Selection and coordinate model

```ts
type SiteSelection =
  | { kind: 'AREA'; geometry: Polygon | MultiPolygon }
  | { kind: 'ROUTE'; geometry: LineString; corridorWidthM: number | null }
  | { kind: 'CROSSING'; geometry: LineString; endpointA: Point; endpointB: Point;
      crossedFeatureRef: string | null; studyArea: Polygon | null }
  | { kind: 'POINT'; geometry: Point }
  | { kind: 'ENDPOINTS'; endpointA: Point; endpointB: Point };
interface SelectionVersion {
  id: string; selectionId: string; projectId: string; version: number;
  selection: SiteSelection; originalCRS: HorizontalCRS;
  originalGeometry: GeoJSON.Geometry; canonicalCRS: 'EPSG:4326';
  canonicalGeometry: GeoJSON.Geometry; transformationEvidenceId: string;
  contentHash: string; createdBy: string; createdAt: string;
}
```

GeoJSON types above are ordinary 2D types; elevation is separate with its vertical reference. Canonical coordinates are longitude/latitude, never latitude/longitude. An unresolved original CRS cannot produce canonical geometry; quarantine imports pending resolution. Store original geometry plus transformation provenance. Use geodesic measurements or a persisted, appropriate metric working CRS; never calculate metres from angular degrees. Large extents, antimeridian crossings and projection distortion outside tested limits return UNSUPPORTED_EXTENT in Stage 1 rather than silently using the wrong projection. Do not infer a crossing path from just endpoints without an explicit proposal.

Buildings/developments use AREA; a dam study may use AREA followed by a proposed axis. Roads/pipelines/drainage/tunnels use ROUTE or ENDPOINTS during exploration. Bridges/culverts use CROSSING. POINT is suitable for an intake, outfall, support location or initial site exploration. Registry distinguishes accepted exploratory input from generation-required input; buildings require a valid plot AREA for generation. Stage 1 validates/persists all variants, but only AREA gets the full building workflow.

Storage: `site_selections` and immutable `site_selection_versions`, PostGIS `geometry(Geometry,4326)` with kind-specific checks, GiST index, typed original geometry JSONB. Boundary remains owned by Project; profile references its content snapshot/hash, not another editable boundary. Selection service exposes create/revise/get; frontend adapts existing selection/drawing. Every revision invalidates only dependent profiles/proposals. Tests: every geometry kind, axis order, invalid/self-intersecting area, unresolved CRS and two distinct endpoints.

## 3. Deterministic site-understanding pipeline

Run through the existing job infrastructure; persist a bounded input manifest first.

1. Authorize project and selection, capture boundary/model/placement refs in a consistent transaction.
2. Resolve horizontal CRS, units and working CRS. Failure is explicit and blocks dependent calculations.
3. Resolve explicit active terrain configuration and immutable version. Do not activate a different terrain dataset as a fallback.
4. **Retrieval:** read coverage, request bounded terrain samples from the existing resolver, discover project survey evidence and constraints, query permitted public context adapters.
5. **Calculations:** bounds, geodesic/metric dimensions, orientation, terrain profile and slope using compatible valid samples only. Store algorithm versions, spacing, nodata policy and input refs. A flat/near-square area may have ambiguous orientation; report UNDEFINED or user axis.
6. **Retrieval:** snapshot current on-site object references and accepted project data. Save per-source success/partial/failure status, retrieval timestamp and query extent.
7. **Calculations:** create missing-information records and apply existing readiness rules plus operation-specific prerequisites.
8. Commit immutable profile/evidence references; mark it current only if captured dependency versions still match. A concurrent terrain change produces an old-context result, never a misleading current profile.
9. Assemble bounded assistant context. **AI interpretation begins here:** explain known facts, propose questions and assumptions. AI cannot fill failed observations.

A failed public-context request produces a partial profile with UNKNOWN context; a failed required CRS calculation blocks profile readiness. Refresh creates another immutable snapshot; it never modifies placement. Existing profiles remain viewable. Pipeline events expose task progress, not hidden reasoning.

Backend separation: `SiteRetrievalService`, `SiteDerivationService`, `SiteProfileService`, existing `readiness()`. Persist steps in existing job status plus immutable result refs. Tests: adapter failure, partial coverage, race on terrain activation, no silent placement movement.

Cache keys include source version, query geometry, parameters and adapter version. Public sources without immutable versions require a retained response digest/artifact and retrievedAt; a cache TTL is not evidence validity. Retrieval failure must not erase previously captured evidence, but older context is labelled with its age and excluded from operations whose freshness policy it fails.

## 4. Evidence/provenance

```ts
interface Evidence {
  id: string; projectId: string; sourceType: SourceKind;
  sourceId: string | null; datasetId: string | null; datasetVersionId: string | null;
  capturedAt: string | null; retrievedAt: string; validFrom: string | null; validTo: string | null;
  horizontalCRS: HorizontalCRS; verticalReference: VerticalReference;
  accuracy: { horizontalRmseM: number | null; verticalRmseM: number | null;
    method: string | null; validationRunId: string | null; independentCheckpointCount: number | null };
  status: 'UNVERIFIED' | 'VERIFIED' | 'CONFLICTED' | 'EXPIRED' | 'FAILED';
  source: EvidenceSource; contentHash: string; supersedesId: string | null;
}
type EvidenceSource =
  | { kind: 'MEASURED'; measurementId: string; instrument: string | null; operatorId: string | null }
  | { kind: 'SURVEY'; surveyDatasetId: string; sourceFileId: string; validationRunId: string | null }
  | { kind: 'PUBLIC_MAP'; provider: string; featureId: string | null; sourceURL: string;
      license: string; queryExtentHash: string }
  | { kind: 'USER_PROVIDED'; messageId: string; actorId: string }
  | { kind: 'DERIVED'; inputEvidenceIds: string[]; algorithmId: string; algorithmVersion: string;
      parametersHash: string; outputArtifactId: string | null }
  | { kind: 'AI_ASSUMPTION'; messageId: string; assumptionId: string; modelId: string }
  | { kind: 'UNKNOWN'; reason: UnknownReason; failedOperationId: string | null };
```

Verification is an auditable determination, not an LLM confidence percentage. SURVEY alone does not mean validated. DERIVED cannot have greater engineering usability than its weakest required input. Missing accuracy is null, never inferred from imagery pixel resolution.

- “Road east of site”: PUBLIC_MAP road geometry plus DERIVED directional relationship from the selected site's frame; contextual, not a survey or access-right claim.
- “Elevation 621.482 m”: SURVEY observation with dataset version, horizontal coordinates, named vertical datum, units, capture date and validation/accuracy evidence. Decimal precision alone is not accuracy.
- “Underground utility here”: USER_PROVIDED observation linked to the exact message and drawn geometry, unverified. Display as reported utility, not located/cleared utility.

Evidence service accepts only server-built source records and stores immutable rows. External URLs are evidence links, not arbitrary URLs the model may fetch. GET evidence is project-authorized. Inspect shows source and limitations. Reverification adds evidence rather than overwriting history. Tests cover source-specific required fields, derivation lineage and conflicting observations.

## 5. Missing information and readiness

```ts
interface MissingSiteInformation {
  id: string; profileVersionId: string;
  type: 'SOIL_BEARING_CAPACITY' | 'GROUNDWATER' | 'UTILITIES' | 'DESIGN_FLOOD_LEVEL'
    | 'SURVEY_ACCURACY' | 'OWNERSHIP' | 'LOCAL_CODE' | 'ELEVATION' | 'OTHER';
  severity: 'INFO' | 'WARNING' | 'CRITICAL'; whyNeeded: string;
  requiredFor: Array<'CONCEPT_LAYOUT' | 'GEOMETRY_CHECK' | 'FOUNDATION_ANALYSIS'
    | 'HYDRAULIC_ANALYSIS' | 'CONSTRUCTION_DOCUMENTATION'>;
  blockingLevel: 'NONE' | 'CONCEPT' | 'GEOMETRY' | 'ENGINEERING';
  resolutionMethod: Array<'USER_CONFIRMATION' | 'SURVEY_UPLOAD' | 'GEOTECH_REPORT'
    | 'UTILITY_SURVEY' | 'AUTHORITY_SOURCE' | 'VALIDATED_CALCULATION'>;
  status: 'OPEN' | 'RESOLVED' | 'NOT_APPLICABLE'; resolutionEvidenceIds: string[];
}
```

Readiness includes the existing site-data state AND per-operation eligibility/reasons. Soil and groundwater can be nonblocking for conceptual room layout but blocking for foundation analysis. Ownership and local codes remain unverified for planning/construction decisions; not every missing item must block a sketch. Defaults cannot resolve measured-data gaps. Store the rule-set version; readiness assessment changes when evidence or policy changes. Backend deterministic rules, frontend concise count with links to Engineering Dock. Tests verify operation-dependent blocking and “defaults” never turning UNKNOWN into verified facts.

## 6. Persistent conversation

```ts
interface Conversation { id: string; projectId: string; title: string;
  createdBy: string; createdAt: string; archivedAt: string | null; nextSequence: number }
interface MessageContext {
  selection: ObjectRef[]; siteSelectionVersionId: string | null;
  siteProfileVersionId: string | null; modelRevisionId: string | null;
  scenarioId: string | null; proposalVersionId: string | null;
  memoryVersionIds: string[]; editorDirty: boolean;
}
type MessagePart = { kind: 'TEXT'; text: string }
  | { kind: 'ATTACHMENT'; attachmentId: string; mediaType: string; contentHash: string }
  | { kind: 'PROPOSAL'; proposalVersionId: string }
  | { kind: 'QUESTION'; questionId: string; text: string; options: string[] }
  | { kind: 'EVIDENCE'; evidenceIds: string[] }
  | { kind: 'ASSUMPTION'; assumptionVersionId: string };
interface Message { id: string; conversationId: string; sequence: number;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM_EVENT'; parts: MessagePart[];
  context: MessageContext; runId: string | null; createdAt: string;
  status: 'COMPLETE' | 'INTERRUPTED' | 'FAILED'; clientRequestId: string | null }
interface ToolExecution { id: string; runId: string; toolName: string; toolVersion: string;
  arguments: unknown; status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  resultRef: string | null; errorCode: string | null; dependencyRefs: Ref[];
  startedAt: string | null; completedAt: string | null }
```

Tool arguments/results use per-tool schemas, not unrestricted arbitrary JSON despite the abbreviated union above. Store structured results or bounded artifact refs, never credentials or raw chain-of-thought. Attachments reference existing authorized storage with size/type limits; attachment text remains untrusted evidence.

Message submit atomically stores user message, immutable context and queued run, with uniqueness on (conversation_id, client_request_id). Server assigns sequence numbers. A failed Nebius call leaves the user message and a retryable run failure. Reload retrieves history and outstanding runs. At most one generating run per conversation initially; parallel tabs get an explicit conflict or queue, not interleaved replies.

“This bridge” resolves to the message's captured selection. Multiple plausible referents produce a clarification. Selection changes during a run do not redirect it. Dirty unsaved model: allow discussion, but require save/rebase before a geometry proposal can be approved.

Storage: conversations, messages, runs, tool executions, attachment/context JSONB with typed schemas. Backend `ConversationService`; frontend server-backed pagination and local composer only. Tests: reload, request retries, ordered concurrent submission, selected-object snapshot and ownership.

## 7. Project memory is separate from chat

```ts
type MemoryStatus = 'PROPOSED' | 'ACCEPTED' | 'REJECTED' | 'SUPERSEDED';
interface MemoryBase { id: string; version: number; projectId: string;
  assetId: string | null; status: MemoryStatus; sourceMessageIds: string[];
  evidenceIds: string[]; proposedBy: string; acceptedBy: string | null;
  acceptedAt: string | null; supersedesVersionId: string | null }
type ProjectRequirement = MemoryBase & { kind: 'REQUIREMENT'; key: string;
  constraint: { operator: 'EQ' | 'MIN' | 'MAX' | 'IN'; value: string | number | boolean | string[];
    unit: string | null }; hardness: 'HARD' | 'SOFT' };
type ProjectPreference = MemoryBase & { kind: 'PREFERENCE'; key: string;
  value: string; priority: 'LOW' | 'NORMAL' | 'HIGH' };
type ProjectDecision = MemoryBase & { kind: 'DECISION'; statement: string;
  rationale: string; selectedAlternativeId: string | null };
type ProjectAssumption = MemoryBase & { kind: 'ASSUMPTION'; statement: string;
  impact: string; requiredVerification: string | null; scope: 'CONCEPT_ONLY' | 'PROJECT' };
```

Use one `project_memory_items` identity table and append-only `project_memory_versions` with kind-specific validated payloads; expose the four domain types through services and API filters. Separate physical tables for identical lifecycles add unnecessary complexity. Accept/reject actions are explicit UI operations. A casual “Could the road move west?” creates no accepted requirement. An explicit instruction may create a proposed memory record; the UI can offer “Remember this decision.” Approving a proposal accepts only its listed assumptions for that proposal, not all project preferences.

Conflicts between accepted requirements are surfaced, not silently resolved. Superseding a requirement preserves the old version and invalidates proposals that depended on it. Rejected/merely proposed memory does not change approved-design dependencies. Frontend compact decision/assumption cards, no separate memory dashboard required. Tests: casual question, explicit acceptance, conflicting requirements, supersession and asset scope.

## 8. Controlled assistant tools

Every tool receives a server-created `ToolContext(actorId, projectId, conversationId, runId, capturedContext, permittedCapabilities)`. The LLM cannot supply or override tenant, actor or authorization context. All entity lookups enforce project ownership, including nested IDs. Read budgets, radius, samples, result count, timeouts and call count are enforced server-side.

Common result: `{status: OK|PARTIAL|UNAVAILABLE|DENIED, data, evidenceIds, dependencyRefs, limitations, errorCode}`; `data` is the exact typed tool-specific output. Tool contracts:

```ts
get_site_profile({versionId?, sections}) -> SiteProfileSummary
get_site_readiness({profileVersionId, operation, assetType}) -> ReadinessAssessment
get_active_terrain({}) -> ActiveTerrainReference | UnknownTerrain
sample_terrain({terrainVersionId, positions, verticalReference}) -> ElevationSampleSet
get_selected_objects({}) -> CapturedSelectionObjects // never current browser selection
get_model_revision({revisionId, objectIds?, detail:'SUMMARY'|'COMPONENTS'}) -> ModelSubset
get_project_requirements({assetId?, kinds?, status:'ACCEPTED'|'PROPOSED'}) -> MemoryVersion[]
query_nearby_context({profileVersionId, kinds, radiusM}) -> ContextCollection[]
get_checks({revisionId?, profileVersionId?, levels}) -> CheckSummary[]
get_constraints({profileVersionId, assetId?}) -> Constraint[]
create_proposal({intentId, profileVersionId, memoryVersionIds, assetRequests}) -> ProposalVersionRef
revise_proposal({proposalVersionId, changeRequests, referencedObjects}) -> ProposalVersionRef
validate_proposal({proposalVersionId, levels}) -> ValidationRunRef
```

`assetRequests` and `changeRequests` are bounded discriminated module contracts, not free-form executable code. Sampling may persist cache/evidence; proposal tools may persist drafts/jobs, but none writes model geometry, placement, approval or accepted memory. No `execute_sql`, arbitrary HTTP URL, Python execution or unrestricted filesystem tools. Approval/build are authenticated application commands unavailable to the LLM. PUBLIC_MAP tools cannot turn retrieved prose into new instructions. Failed tools cannot be relabelled successful by the model.

Backend `assistant/tools/registry.py` and typed handlers delegate to domain services. Internal execution only; there is no public generic “run any tool” endpoint. UI shows sanitized tool names/progress. Tests: cross-project nested refs, invented tool, excessive samples/radius, prompt injection, output validation and mutation denial.

## 9. Context assembly

`ContextBuilder.build(runSnapshot) -> ContextEnvelope` with sections: instructions/capabilities, current request+captured selection, site summary+readiness, applicable accepted memory, current asset/model summary, active proposal/checks, recent conversation and evidence references. Store selected IDs, hashes, omission reasons and prompt-template version for reproducibility, not secret credentials.

Start with a 12,000-input-token budget configurable to the chosen model: 1,500 policy/tool/capability tokens; 2,500 current message/selection/site; 2,000 memory; 2,000 model/proposal/checks; 2,000 recent turns; 2,000 retrieved evidence/reserve. Adjust to actual tokenizer/model limits, reserve output and tool-response capacity, and fail clearly if one mandatory input cannot fit.

Rules: current message and safety/readiness limits are mandatory; select memory by project+asset+operation; prioritize selected components and adjacent dependencies; recent turns newest first up to budget; older decisions come from accepted memory, not a lossy chat summary. Include failed retrieval and unknown facts. Drop raw sample arrays, full model meshes and unrelated assets. Fetch detail through tools as needed. Structured IDs and evidence links remain after summaries. No vector store initially: scoped SQL and explicit references are enough. A compacted conversation summary is labelled a summary and cannot accept requirements.

Tests: bounded prompt, unknown facts survive truncation, selected objects preserved, no other-project content, stale summaries excluded.

## 10. Structured intent and run state

```ts
type IntentKind = 'QUESTION' | 'SITE_QUERY' | 'DESIGN_REQUEST' | 'CHANGE_REQUEST'
  | 'ANALYSIS_REQUEST' | 'EXPLANATION_REQUEST' | 'PROPOSAL_APPROVAL' | 'GENERAL_DISCUSSION';
interface Intent {
  kind: IntentKind; assetTypes: string[]; targetObjects: ObjectRef[];
  requestedOperation: string | null; proposalVersionId: string | null;
  needsClarification: boolean; clarificationQuestion: string | null;
  allowedEffect: 'READ_ONLY' | 'PROPOSAL_ONLY' | 'APPROVAL_UI_REQUIRED';
}
type RunState = 'QUEUED' | 'CLASSIFYING' | 'READING_CONTEXT' | 'WAITING_FOR_INPUT'
  | 'PROPOSING' | 'VALIDATING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
```

Nebius emits schema-validated intent based on message and captured context; server policy determines allowedEffect independently. Ambiguity defaults to a question/read-only behavior, not a mutation. Multiple intents are ordered, bounded operations within one run. “Why entrance here?” retrieves traceability/decision evidence. “Move entrance east” creates a proposal. “Slope here?” reads sample-derived facts. “Is this bridge safe?” checks registry and available validated analysis; unsupported analysis yields a limitation, never a safety verdict. “Approve it” identifies a candidate and presents the specific approval control; ordinary text is not an approval token.

Persist intent with the run. A maximum eight tool calls, bounded two schema-repair attempts and configured timeout prevent loops. Provider errors remain explicit; no mock-success fallback. Tests use fixed provider fixtures for examples, ambiguous references, malformed intent and mixed requests; real-provider smoke tests are optional and spend-controlled.

## 11. Civil asset capability registry

```ts
type Level = 'FULL' | 'PARTIAL' | 'CONCEPT_ONLY' | 'UNSUPPORTED';
interface AssetCapability {
  assetType: string; registryVersion: string;
  planningSupport: Level; generationSupport: Level;
  geometryValidationSupport: Level; engineeringAnalysisSupport: Level;
  siteSelectionTypes: SiteSelection['kind'][];
  requiredInputs: { operation: string; field: string; minimumEvidenceUse: string }[];
  optionalInputs: string[]; specificationSchemaId: string | null;
  generatorId: string | null; generatorVersion: string | null;
  validatorIds: string[]; analysisCalculatorIds: string[];
  supportedOperations: string[]; limitations: string[];
}
```

FULL means complete within a named, versioned scope, never universal engineering capability. Stage 1 release registry:

- Building: planning PARTIAL; generation PARTIAL; geometry validation PARTIAL; engineering analysis UNSUPPORTED. AREA. Uses approved building module. Required: valid plot, requirements/accepted defaults, local frame; verified elevation needed for authoritative ground placement, not local concept layout.
- Road: planning CONCEPT_ONLY; new assistant generation UNSUPPORTED; geometry validation UNSUPPORTED; engineering analysis UNSUPPORTED. ROUTE/ENDPOINTS. Future inputs: alignment, width, design criteria and terrain profile.
- Bridge: same Stage 1 levels as road. CROSSING/ENDPOINTS. Future inputs: crossing, span arrangement, deck use, clearances and foundation evidence.
- Dam: same levels. AREA/ROUTE. Future inputs: axis, purpose, terrain, hydrology and geotechnical evidence.
- Retaining wall: same levels. ROUTE. Future inputs: retained profile, ground conditions and loading.
- Culvert: same levels. CROSSING. Future inputs: waterway/crossing and design flow.
- Drainage: same levels. ROUTE/AREA/POINT. Future inputs: catchment, outlet, levels and design rainfall.
- Tunnel: same levels. ROUTE/ENDPOINTS. Future inputs: alignment/profile, geology, use and clearance.

CONCEPT_ONLY planning here means discussion/requirements, not a validated executable specification. Unknown asset types get UNSUPPORTED, plus general discussion. Existing road/flyover/pipeline generators remain in legacy flows: their presence is not proof they implement this approval/traceability contract. Wrap and test them later before enabling registry entries. Backend registry is authoritative; GET capabilities drives UI labels and available actions, and is rechecked on each operation. Tests prevent disabled/unsupported module execution and stale client capability claims.

## 12. Multi-asset project composition

```ts
interface AssetInstance { id: string; projectId: string; assetType: string; name: string;
  siteProfileId: string; activeSpecificationVersionId: string | null;
  lifecycle: 'PROPOSED' | 'ACTIVE' | 'ARCHIVED' }
interface AssetRelationship { id: string; projectId: string; version: number;
  fromAssetId: string; toAssetId: string;
  kind: 'CONNECTS_TO' | 'CROSSES' | 'SUPPORTED_BY' | 'DRAINS_TO' | 'SERVES'
    | 'ADJACENT_TO' | 'INTERSECTS' | 'DEPENDS_ON';
  fromComponentId: string | null; toComponentId: string | null;
  evidenceIds: string[]; status: 'PROPOSED' | 'ACCEPTED' | 'SUPERSEDED' }
interface AssetSpecificationVersion { id: string; assetId: string; version: number;
  schemaId: string; schemaVersion: string; contentHash: string;
  specification: BuildingSpec /* future discriminated module schemas */ }
```

A project can have several site profiles and several assets. An asset references one primary profile; additional profiles are explicit dependencies. A coordination proposal references separate asset specification versions plus relationship changes; it never merges all specifications into one giant schema. Store relationship direction and reject self-edges where nonsensical. Validate DEPENDS_ON scheduling cycles; ADJACENT_TO can be symmetric without duplicated rows. Drainage network loops have module-specific rules, not a universal graph prohibition.

Asset/relationship services enforce ownership and endpoint existence. Stage 1 supports a single built building asset but uses stable asset IDs immediately. Future atomic multi-asset builds commit a composed model revision only when all required outputs validate; do not implement that scheduler now. UI Layers/Inspect show asset groups. Tests: foreign-project edge, referential integrity, superseded relation and stable asset identity.

## 13. Generic proposal lifecycle

```ts
type ProposalStatus = 'DRAFT' | 'GENERATING' | 'READY_FOR_REVIEW' | 'HAS_ISSUES'
  | 'APPROVED' | 'STALE' | 'REJECTED' | 'BUILT';
interface ProposalVersion {
  id: string; proposalId: string; version: number; projectId: string;
  schemaVersion: string; contentHash: string; siteProfileVersionId: string;
  inputMemoryVersionIds: string[]; assetSpecificationVersionIds: string[];
  layoutGeometryRefs: GeometryRef[]; assumptionVersionIds: string[];
  alternativeIds: string[]; selectedAlternativeId: string | null;
  validationRunIds: string[]; warnings: { code: string; message: string; evidenceIds: string[] }[];
  sourceScenarioId: string; sourceModelRevisionId: string | null;
  dependencyManifestId: string; parentVersionId: string | null;
  status: ProposalStatus; createdAt: string;
}
interface Approval { id: string; proposalVersionId: string; proposalHash: string;
  alternativeId: string | null; dependencyHash: string; validationHash: string;
  approvedBy: string; approvedAt: string; revokedAt: string | null }
```

Proposal identity has an active-version pointer. Content is immutable once generated; state changes are audited separately. Lifecycle: DRAFT → GENERATING → READY_FOR_REVIEW or HAS_ISSUES; READY_FOR_REVIEW → APPROVED → BUILT. Pre-build dependent changes → STALE; user rejection → REJECTED. Nonblocking warnings may coexist with READY_FOR_REVIEW. Blockers require revision, not a warning override. Generation failure remains a failed job/run and HAS_ISSUES with an error; no false READY state. Revising creates a new version and requires new approval; it cannot mutate an approved version. BUILT remains historical; current applicability can be stale without rewriting the fact that it was built.

Backend ProposalService, ApprovalService and module validators. Storage described below. Frontend proposal cards plus existing review surfaces; approvals explicitly name revision and alternative. Tests: immutable payload, illegal transitions, approval hash mismatch, warning vs blocker and repeat submission.

## 14. Alternatives and honest tradeoffs

```ts
interface ProposalAlternative { id: string; proposalVersionId: string; name: string;
  assetSpecificationVersionIds: string[]; layoutGeometryRefs: GeometryRef[];
  tradeoffs: Tradeoff[]; validationRunIds: string[] }
type Tradeoff =
  | { kind: 'MEASURED_TRADEOFF'; metric: string; value: Quantity<string>;
      evidenceIds: string[]; comparisonAlternativeId: string | null }
  | { kind: 'DERIVED_TRADEOFF'; metric: string; value: Quantity<string>;
      calculationRunId: string; evidenceIds: string[]; comparisonAlternativeId: string | null }
  | { kind: 'QUALITATIVE_ASSUMPTION'; statement: string; assumptionVersionId: string };
```

“Minimum earthwork” requires a real compatible terrain/design-surface calculation and a defined comparison set. Without that, label “intended to reduce earthwork; not calculated.” A measured shorter access length is not automatically cheaper. No weighted overall score without explicit metric definitions and accepted weights. Stage 1 defaults to one option; support the schema now, defer automatic three-option generation. Any chosen alternative is pinned in approval; switching alternatives requires revalidation and approval. Tests: numeric claim missing evidence, incompatible comparison units and approval of another alternative.

## 15. Shared validation

```ts
type ValidationLevel = 'CONCEPT_VALIDATION' | 'GEOMETRY_VALIDATION' | 'ENGINEERING_ANALYSIS';
interface ValidationRun { id: string; level: ValidationLevel; validatorId: string;
  validatorVersion: string; inputHash: string;
  status: 'PASSED' | 'FAILED' | 'NOT_RUN' | 'UNSUPPORTED' | 'ERROR' | 'STALE';
  issues: { code: string; severity: 'INFO' | 'WARNING' | 'BLOCKER';
    componentIds: string[]; fieldPaths: string[]; evidenceIds: string[];
    message: string; remediation: string }[]; outputArtifactId: string | null }
```

Concept checks required fields, units, supported module, references and conflicting requirements. Geometry checks valid shapes, positive finite dimensions, room overlap, plot containment, openings, connectivity and scoped clearance rules. Engineering analysis calls only an explicitly registered calculator with tested domain, version, required evidence, code basis and retained report. Existing generic quantity/cost estimates do not establish structural safety. Unsupported/not-run/error must never appear as passed.

Reuse Checks and existing analysis records; add proposal-target linkage rather than a second competing checks UI. Run validation on exact proposal hash before approval and validate generated geometry before commit. Dedicated modules implement additional checks. Tests cover each building blocker and evidence/capability gate; do not encode engineering calculations in prompts.

## 16. Approval dependencies, staleness and concurrency

```ts
interface DependencyManifest {
  schemaVersion: 'dependencies/1';
  entries: { kind: 'SELECTION' | 'BOUNDARY' | 'TERRAIN' | 'PLACEMENT' | 'MODEL'
      | 'MEMORY' | 'CONSTRAINT' | 'SURVEY_EVIDENCE' | 'RELATIONSHIP' | 'GENERATOR'
      | 'VALIDATOR'; id: string; version: string; contentHash: string;
    policy: 'MUST_MATCH_CURRENT' | 'PINNED_SNAPSHOT'; scope: string }[];
  hash: string;
}
```

Canonical hashes use schema-versioned, sorted-key JSON, finite normalized units and exact persisted coordinate precision. Exclude timestamps, UI state and unordered presentation fields. Include explicit UNKNOWN values. Hashing a snapshot alone is insufficient: resolve all MUST_MATCH_CURRENT references again at approval, job start and final commit.

Invalidate for changed relevant selection/boundary, active terrain configuration (including unknown→known), placement, source scenario model revision, accepted scoped requirements, or applicable constraint/survey evidence. Record the changed dependency and old/new versions. A new unrelated survey file is not invalidating unless activated/accepted for that scope. In Stage 1 lock the entire source scenario revision for safety; later per-object dependencies may narrow this after read/write-set validation exists. Do not use the latest revision across the entire project when multiple scenarios exist.

Camera, layer visibility, selected objects after message submission, chat questions, project title and unrelated assets in other scenarios do not invalidate. A profile refresh with identical substantive inputs does not invalidate; changed relevant facts do. Generator/validator versions are pinned; inability to execute the approved version blocks and requires revision, never silently upgrades.

Approval transaction locks proposal/context rows, rechecks dependency and validation hashes, inserts a unique approval and audit event. Build transaction creates a unique generation request per (approval_id, generation_manifest_hash) and outbox event. Worker rechecks, computes outside long transactions, then locks/rechecks and commits revision + traceability atomically. Concurrent manual edits make commit fail with STALE, preserving user work. Retried HTTP requests reuse the logical job; failed dispatch retries that job through the outbox instead of requiring a new proposal. Existing job pipeline remains the executor.

Tests: every dependency change, unrelated UI no-op, concurrent approval, worker race, lost queue dispatch, final-commit compare-and-swap, replay after BUILT. Previously completed builds can return their historical job even when current state differs; new generation cannot bypass staleness.

## 17. Common generation contract

```python
class Generator(Protocol):
    id: str
    version: str
    specification_schema: str
    def generate(self, request: ApprovedGenerationInput) -> GenerationOutput: ...

class ApprovedGenerationInput(BaseModel):
    approval_id: str
    proposal_version_id: str
    proposal_hash: str
    asset_specification_version_id: str
    site_profile_version_id: str
    placement_snapshot_id: str | None
    source_model_revision_id: str | None
    manifest_hash: str
    # Resolved typed specification, local frame, and immutable input artifacts

class GenerationOutput(BaseModel):
    geometry_artifact_id: str
    object_records: list[GeneratedObject]
    relationships: list[GeneratedRelationship]
    warnings: list[GenerationWarning]
    source_mapping: list[ComponentObjectMapping]
    content_hash: str
```

Orchestrator resolves these refs into module-specific typed input; it never passes raw AI prose as geometry instructions. Generator has no Nebius call or “latest terrain” read. Pin dependency/library versions and any seed, deterministic component ordering and identifiers; exclude timestamps/job IDs from geometry digest. Identical input manifest plus generator version produces identical canonical geometry digest. Stable logical object IDs derive from asset+component identity, not revision number.

Outputs enter existing editable-model/revision/export pipeline. Placement is copied as a referenced immutable input, never resampled and moved implicitly. Unknown global elevation yields an explicitly unplaced/local conceptual model; absolute exports requiring known datum are blocked or labelled according to existing export contracts. Relative offsets remain valid independently of unknown absolute altitude.

Test deterministic digest, component mapping, preserved placement, failed output validation, existing export contracts and no provider calls during build.

## 18. Traceability

Every generated component stores `{objectId, assetId, proposalId, proposalVersionId, approvalId, assetSpecificationVersionId, specificationComponentId, generatorId, generatorVersion, createdInModelRevisionId}`. Revision membership is recorded separately: an unchanged object may appear in many immutable model revisions. Trace source goes in editable component metadata and a queryable `model_object_lineage` index referencing existing revisions; never duplicate meshes there.

Example: P04 → bridge asset B01 → proposal P14/v3 → support-04 → bridge-generator/2 → revision R21. Until that module is supported, this is a future contract, not an available bridge feature.

Manual edit appends a revision and records editor actor/source; retains original generation lineage plus `modifiedSinceGeneration=true`. Deleted objects have a tombstone/mapping; split or merged objects have explicit many-to-many lineage. Explanation tools distinguish original rationale from later manual changes. Tests cover untouched identity, manual modification, deletion and Inspect links.

## 19. Chat with advanced selection

On Send capture scenario, model revision and exact selected component refs. Server verifies the objects existed in that revision and stores the snapshot. A selection chip shows “3 components · revision 12.”

“Raise these piers by 0.5 m” produces a typed proposed delta `{operation: TRANSLATE, objectRefs: [P03,P04,P05], axis: LOCAL_Z, deltaM: 0.5}` only when the module supports it. Delta is relative to the captured frame; unresolved global elevation is not replaced with zero. Module validation expands or flags affected connected components; never leave a deck disconnected silently. Stage 1 can explain this request but cannot offer Apply for an unsupported bridge module.

Review shows affected IDs, before/after dimensions, dependent components, assumptions and checks. Apply is the normal approval+build command, not an editor mutation shortcut. Cancel rejects the proposal. Same stable object IDs in a newer revision require an explicit rebase/revalidation; deleted/split/merged objects require clarification or a reviewed mapping. Never target by mutable display label alone. Tests: selection drift, deleted object, split mapping, unsupported change and dirty editor state.

## 20. Assistant UI and frontend state

Keep the existing Assistant tab. Its compact header shows site readiness, active terrain label/version and unresolved-input count. A selection chip captures current targets. Conversation includes text, question cards, proposed memory, proposal summaries, assumption counts, warnings and links to evidence/checks.

Review opens existing workspace review/Engineering Dock surfaces; a temporary Cesium proposal layer is visually distinct from committed geometry and cannot be exported as the saved model. Approved build progress uses current generation-job UI. Layers and Inspect expose generated asset groups and provenance. History includes proposal approval and resulting revision links.

Server state: conversations/messages, run, profile versions, proposals, memory and jobs. Local state: composer, expanded cards, selected review alternative, preview visibility. Use existing project store/editor for selection and dirty state; don't create a competing copy. Event updates invalidate specific cached resources. Refresh/reload hydrates server records. “Use reasonable defaults” creates listed proposed assumptions, not accepted site facts.

Remove direct onApplyParameters/onRegenerate from assistant reply handling. Existing non-AI manual generation controls remain unchanged. Tests: reload conversation, no mutation from reply, review/approval controls, progress recovery, disabled stale/unsupported action.

## 21. Progress and run recovery

Persist run events with monotonic sequence: `{runId, sequence, stage, state, label, completedUnits?, totalUnits?, resourceRef?, errorCode?}`. Stages use fixed labels: Inspecting terrain, Reading constraints, Creating site profile, Generating proposal, Validating geometry. Expose stage completion and missing data; no invented percentage for model reasoning.

Use authenticated SSE with Last-Event-ID replay, with polling fallback through existing API transport. Persist final status so reload never depends on an open stream. Cancellation stops future steps; completed immutable evidence/drafts remain auditable, no geometry changes occur. Tool errors show actionable, sanitized messages. Never stream secrets, internal prompts or chain-of-thought. Test reconnect, duplicate events, cancellation and timeout.

## 22. FastAPI endpoints and service boundaries

All paths below are under `/api/projects/{project_id}` and enforce the current project's authorization policy. Writes accept Idempotency-Key where retried; revision changes use expected version/If-Match. 404 for inaccessible IDs, 409 for stale/conflicting versions, 422 for schema/geometry errors, 503 for unavailable provider, 202 for queued work. Return typed error codes and resource/run links.

```text
GET    /assistant/capabilities
POST   /site-selections                         -> SelectionVersion
GET    /site-selections/{id}/versions/{version}
POST   /site-selections/{id}/versions            -> SelectionVersion
POST   /site-profiles {selectionVersionId}       -> 202 job/profile reference
GET    /site-profiles/{id}?version=...
POST   /site-profiles/{id}/refresh               -> 202 job reference
GET    /site-profiles/{id}/readiness?operation=...
GET    /site-evidence/{id}
GET    /site-profiles/{id}/samples?cursor=...

POST   /conversations                           -> Conversation
GET    /conversations
GET    /conversations/{id}/messages?before=...&limit=...
POST   /conversations/{id}/messages              -> 202 {messageId,runId}
GET    /assistant/runs/{id}
GET    /assistant/runs/{id}/events               -> SSE
POST   /assistant/runs/{id}/cancel
POST   /assistant/runs/{id}/retry                -> linked new attempt

GET    /memory?kind=...&status=...&assetId=...
POST   /memory                                  -> proposed item version
POST   /memory/{id}/versions
POST   /memory/{id}/versions/{version}/accept
POST   /memory/{id}/versions/{version}/reject

POST   /proposals                               -> 202 generation run
GET    /proposals
GET    /proposals/{id}/versions/{version}
POST   /proposals/{id}/versions                  -> 202 revision run
POST   /proposals/{id}/versions/{version}/validate
POST   /proposals/{id}/versions/{version}/approve
POST   /proposals/{id}/versions/{version}/reject
POST   /proposals/{id}/versions/{version}/build  -> existing job reference
GET    /assets
GET    /assets/{id}
```

Approve body: `{proposalHash, dependencyHash, validationHash, alternativeId, acknowledgedAssumptionVersionIds, expectedModelRevisionId}`. Actor/time are server-derived. Build body: `{approvalId}`. The UI may sequence Approve then Build, but the services and records remain separate.

Routes remain thin: SelectionService → SiteProfileService; ConversationService → AssistantRunService → ContextBuilder/IntentPolicy/ToolRegistry; MemoryService; ProposalService → module planner/ValidationService; ApprovalService → GenerationCoordinator → existing jobs. `services/ai/nebius.py` remains provider adapter with configured server-only credentials/model/base URL. No giant business-logic `/ai` route.

Adapt old building-plan routes to the new service during migration with a legacy ID mapping. Do not dual-write two authorities. Previously built plans retain historical provenance; unbuilt plans lacking dependency evidence require new review. Existing persisted jobs remain readable. API tests focus on ownership, typed errors, concurrency and idempotency.

## 23. PostgreSQL/PostGIS storage and migrations

New tables and responsibilities:

- `site_selections`, `site_selection_versions`: identity, immutable geometry, source CRS and geometry hash; unique selection/version, GiST canonical geometry.
- `site_profiles`, `site_profile_versions`: selection binding, current pointer, typed snapshot, dependency hash and readiness reference; unique profile/version and substantive input hash.
- `site_evidence`: immutable typed provenance with source/dataset refs, accuracy and timestamps. `site_profile_evidence` links snapshots. `site_missing_information` is version-scoped.
- `site_sample_sets`, `site_profile_lines`: bounded immutable sample/profile artifacts and summaries; refer to GroundSample where applicable, never create a second authoritative terrain model.
- `project_conversations`, `conversation_messages`: owner/project, sequence, structured parts/context, idempotent client message ID.
- `assistant_runs`, `assistant_tool_executions`, `assistant_run_events`: request lifecycle, sanitized typed I/O, event replay and provider/template versions.
- `project_memory_items`, `project_memory_versions`: requirements, preferences, decisions, assumptions distinguished by checked kind and typed schema. Optional SQL views named project_requirements/project_decisions/project_assumptions for convenience, not duplicate state.
- `design_proposals`, `design_proposal_versions`: identity, immutable payload/manifest hashes, parent version, audited lifecycle.
- `asset_specification_versions`, `proposal_asset_specifications`: separate module schemas and explicit membership.
- `proposal_alternatives`, `proposal_approvals`: version-bound alternatives and append-only approval records.
- `asset_instances`, `asset_relationships` (versioned rows): asset identity and relationship graph.
- `dependency_manifests`, `model_object_lineage`: immutable inputs and compact lineage index.
- `generation_requests`, `job_outbox`: unique logical approved build and reliable dispatch into existing job system.

Reuse Project, terrain datasets/versions, active configuration, ModelRevision, ModelPlacement, GroundSample, existing checks/analysis and audit tables. Add proposal-target/dependency references to checks; do not duplicate terrain elevations/meshes in profile storage. If a mutable legacy survey/constraint record has no version, store its content hash and immutable evidence snapshot, not an invented version number.

Every child carries project_id. Use composite unique keys/FKs `(project_id,id)` for references where practical, plus service authorization; JSON nested refs are validated server-side. Index conversations(project_id,updated_at), messages(conversation_id,sequence), proposals(project_id,status), assets(project_id,type), evidence(project_id,dataset_version), and dependency lookup keys. No blanket JSONB GIN indexes initially. Immutable rows cannot be updated except explicitly separate lifecycle fields; content writes occur through one service.

Migrations are additive in phases: foundations; conversation/memory; proposals/assets; lineage/outbox and legacy adapter. Backfill building-plan history without inventing missing evidence. ModelPlacement migration first introduces resolution state, audits legacy records, then allows null altitude. Downgrade must not silently discard new histories; document backup/restore requirement for destructive rollback. Test on real PostgreSQL/PostGIS as well as demo SQLite.

## 24. SQLite fallback

Supports conversation/memory, typed snapshot storage as JSON, small AREA selection, local pyproj/Shapely concept checks, building proposals, deterministic local generation, revision history and conditional-update idempotency. Display DEMO capability limits explicitly through the registry/readiness endpoint.

PostGIS is required for production spatial indexes, scalable coverage/context joins, authoritative project survey terrain workflows under existing policy, and production concurrent approval/generation locking. SQLite spatial operations are bounded application calculations, not equivalent PostGIS queries. Do not label SQLite outputs engineering-ready. Replace FOR UPDATE assumptions with checked conditional writes/unique constraints for demo operations; never claim they provide production concurrency parity. Test fallback separately and ensure unavailable capabilities are disabled instead of returning empty success.

## 25. First polished building slice and acceptance gate

1. Create building project and save plot; site-profile job creates version 1 with explicit unknowns.
2. Open existing Assistant tab; persisted chat captures selection/profile/model context.
3. Ask intended use, storeys/space program and key preferences; “defaults” shows proposed assumptions for approval.
4. Accepted requirements + exact site profile produce a validated BuildingSpec proposal through the existing planner adapter.
5. Show map/local layout preview, components, dimensions, assumptions, unsupported-analysis label and warnings.
6. Request changes; create proposal version 2, preserving version 1 and discussion.
7. Approve exact version/hash; submit idempotent build; existing generator saves editable model and placement provenance.
8. Inspect components and ask “Why is this entrance here?”; answer using spec, accepted decisions and evidence, no regeneration.
9. Select a supported building component, request change, review proposed patch and affected objects, approve and create next revision.
10. Manually edit a wall, save, then ask another AI edit: planner reads actual saved geometry plus original lineage; does not blindly regenerate the original specification over manual edits.
11. Reload and recover conversation, selected proposal, job result and history.

Critical edit strategy: new building generation may create a full asset; later changes use typed patches against the current editable model. Preserve untouched geometry. If a manual model cannot be represented by the module, explain the unsupported edit or propose an explicitly reviewed replacement. Add stable component IDs to current columns/beams and other generated members; current simple BuildingSpec has no IDs on some of these. Stairs and connected building circulation need explicit schema/generator/validation work before claiming a complete multi-storey layout. Scope initial editing to supported operations and surface these limits.

The building module input is a strict union: `CreateBuildingSpec` or `EditBuildingSpec {baseRevisionId, operations}`. Initial edit operations are SET_DIMENSION and TRANSLATE on supported component types, and REPLACE_COMPONENT with an explicit before hash and typed replacement. Each operation includes componentId, expectedComponentHash and its local frame. The deterministic adapter applies these to a copy of the pinned base model, runs building validators, and returns the resulting component set plus changed/deleted/unchanged mappings. New-object IDs are preassigned in the approved specification. Unsupported operations fail before approval. Full asset replacement is a distinct, visibly labelled operation with a complete affected-object list, never an automatic fallback for a failed patch.

Acceptance: no chat reply directly changes geometry; no lost manual edits; no unknown→0 conversion; terrain activation never moves models; duplicate build produces one revision; explanations cite actual sources; provider failure preserves history and allows retry; existing nonbuilding generation/export workflows continue unchanged.

## 26. Focused test plan

Start with these module suites; expand only when failures or new behavior justify it:

1. `test_site_contracts`: source-specific evidence, unknown/null, incompatible datum and invalid selection variants.
2. `test_site_profiles`: deterministic dimensions, partial terrain/context failure, version dedup, refresh/activation race, readiness and placement unchanged.
3. `test_conversations`: persistence/reload, idempotent sends, immutable selection/context, one active run and cross-project refs.
4. `test_project_memory`: casual question not accepted, explicit acceptance, supersession/conflicts and proposal-scoped defaults.
5. `test_assistant_policy`: structured intent examples, ambiguity, registry restrictions, tool auth/budgets and untrusted context.
6. `test_nebius_orchestration`: missing credentials, timeout, malformed output, bounded repair, interrupted run and retry; fixture provider by default.
7. `test_context_builder`: token bounds, preserved unknowns/selection, accepted relevant memory and omitted unrelated data.
8. `test_proposals`: immutable versions/alternatives, validation blockers, exact approval, dependency invalidation and irrelevant UI no-op.
9. `test_generation_commit`: deterministic output, idempotent job, outbox retry, race with manual edit, lineage, preserved placement and exports.
10. `test_building_edits`: current model read, supported patch, untouched object retention, unsupported manual geometry and unknown elevation.

Run a small PostgreSQL/PostGIS integration suite for geometry columns, tenant FKs and concurrent approval/final-commit locks; SQLite tests cannot substitute. Frontend component tests cover question/default cards, captured selection, stale controls, proposal review and failure/reconnect state.

Two browser scenarios first: full building flow including revision/explanation/reload; manual edit + AI proposal + concurrent model change causing stale approval. Use mocked provider responses for reproducibility, real app APIs/database and actual Cesium/editable model rendering. Separately one optional live Nebius smoke test with a spending bound verifies configured connectivity, not model quality. Regression checks preserve current nonbuilding jobs and existing exports. No hundreds of speculative asset tests.

## 27. Strict implementation order and exit criteria

1. **Inventory and contracts:** map existing stores/APIs; freeze domain schemas, registry levels, error types and unknown-elevation semantics. Exit: contract fixtures round-trip and unsupported modules cannot claim generation.
2. **Safety boundary:** disable direct geometry effects from assistant responses behind the Stage 1 flag; introduce proposal-only dispatcher and explicit approval endpoint skeleton. Existing manual flows remain available. Exit: question/change replies cannot mutate saved geometry.
3. **Additive migrations:** selection/profile/evidence, conversation/memory, proposal/assets, approval/outbox/lineage; provenance-aware legacy placement handling. Exit: PostgreSQL and SQLite migrations preserve current data and revisions.
4. **Site services:** deterministic retrieval/derivation, immutable profiles, missing data and readiness integration. Exit: saved plot yields evidence-backed profile and terrain changes never reposition models.
5. **Conversation and memory APIs:** immutable context captures, message/run persistence, accepted decisions. Exit: reload and concurrent/idempotent send tests pass.
6. **Generic proposal/approval services:** versioning, dependency manifests, validation contracts, race-safe build claim. Build initially uses fixtures. Exit: stale and duplicate commands behave correctly without an LLM.
7. **Building module adapter:** wrap existing planner/spec/generator; stable components, current-model patch support, traceability, output validation and outbox dispatch. Exit: fixture-approved building produces one editable revision preserving placement.
8. **Controlled tools and context builder:** typed registry, auth, quotas, bounded context, capability gates. Exit: no arbitrary reads/writes and no hidden geometry mutation.
9. **Nebius orchestration:** intent, tools, clarification, proposal creation, failure recovery and progress events. Exit: fixture-driven runs work and one optional real-provider check succeeds.
10. **Existing Assistant UI integration:** persistent chat, status/selection chips, compact proposal/default cards, existing Dock/Checks/History integration; consolidate BuildingAssistant review. Exit: no workspace redesign or separate assistant authority.
11. **Polish building slice:** preview, multi-storey/stair scope, explanation, supported edits, manual-edit handling, reload/reconnect. Exit: section 25 acceptance gate passes.
12. **Browser and production-storage validation:** two focused workflows, authorization, concurrency and existing generation/export regressions. Enable Stage 1 after passing. No road/bridge/dam implementation until this gate is met.

## 28. Complexity and risk decisions

- Do not equate broad discussion with broad generation support. Registry entries must describe shipped, tested operations.
- Do not build a universal civil-asset schema/generator. Share lifecycle, evidence and placement; keep specifications/validators specialized.
- Do not rewrite terrain, readiness, model revisions or checks. Profile is an immutable view/reference set over these systems.
- Avoid one table per minor chat part or duplicated memory lifecycle tables. Typed JSONB is appropriate for immutable payloads; relational columns own identity, references, ordering and concurrency.
- Avoid vector search, microservices, autonomous background redesign and mandatory three alternatives in Stage 1.
- The hardest technical risk is preserving manual edits while translating later AI requests. Implement current-model patches and clear unsupported-edit behavior before advertising unrestricted chat editing.
- The strongest correctness risk is a stale check that passes before an asynchronous build but fails before commit. Transactional recheck and outbox/idempotency are required, not optional polish.
- Public-map absence is not proof of absence; imagery is not elevation; survey origin is not validation. Evidence and unknowns must survive every API, prompt, model and export boundary.
- Human proposal approval authorizes that model change only. It does not establish structural safety, regulatory compliance, property rights or engineering approval.

Stage 1 is finished when the building workflow is coherent and auditable end-to-end. Future civil modules then implement a schema, planner adapter, generator, validators and registry entry against this foundation.
