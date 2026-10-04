/**
 * Survey terrain state is deliberately split into independent lifecycles.
 * In particular, an active terrain is not evidence of verified accuracy, and
 * a changed terrain must never silently move an existing model.
 */
export type TerrainDatasetKind = "WORLD_TERRAIN" | "SURVEY_TERRAIN" | "FUSED_TERRAIN" | "NEUTRAL_GLOBE";
export type TerrainProcessingState = "UPLOADED" | "METADATA_REQUIRED" | "READY_TO_PROCESS" | "PROCESSING_QUEUED" | "PROCESSING" | "READY" | "PROCESSING_FAILED" | "ARCHIVED";
export type HorizontalCRSType = "WGS84_GEOGRAPHIC" | "WGS84_ECEF" | "PROJECTED" | "LOCAL" | "UNKNOWN";
export type VerticalReferenceType = "ELLIPSOIDAL" | "ORTHOMETRIC" | "LOCAL_DATUM" | "UNKNOWN";
export type LinearUnit = "METRE" | "FOOT" | "US_SURVEY_FOOT" | "UNKNOWN";
export type VerticalResolutionState = "NOT_CHECKED" | "MISSING_METADATA" | "REFERENCE_IDENTIFIED" | "CONVERSION_REQUIRED" | "RESOLVED" | "UNSUPPORTED";
export type ActivationBlockReason = "INVALID_DATASET_KIND" | "PROCESSING_NOT_READY" | "CRS_UNKNOWN" | "VERTICAL_DATUM_UNKNOWN" | "VERTICAL_CONVERSION_UNAVAILABLE" | "UNITS_UNKNOWN" | "COVERAGE_UNKNOWN" | "ION_ASSET_MISSING";
export type SurveyValidationState = "NOT_RUN" | "INSUFFICIENT_CHECKPOINTS" | "READY_TO_VALIDATE" | "VALIDATING" | "VALIDATED" | "VALIDATION_FAILED" | "STALE";
export type ControlPointRole = "ADJUSTMENT" | "VALIDATION_CHECKPOINT";
export type PlacementMode = "GROUND_RELATIVE" | "ABSOLUTE";
export type ModelHeightReference = "TERRAIN" | "ELLIPSOID" | "ORTHOMETRIC" | "PROJECT_DATUM";
export type CoordinateAxisMode = "LOCAL_ENU" | "WORLD";
export type GroundSource = "WORLD_TERRAIN" | "SURVEY_TERRAIN" | "FUSED_TERRAIN" | "NONE";
export type GroundSampleStatus = "NOT_SAMPLED" | "SAMPLING" | "VALID" | "FAILED" | "OUTSIDE_COVERAGE" | "STALE";
export type PlacementState = "UNPLACED" | "PLACEMENT_PENDING" | "VALID" | "REVIEW_REQUIRED" | "INVALID";
export type PlacementValidationError = "INVALID_LONGITUDE" | "INVALID_LATITUDE" | "INVALID_ANCHOR_ELEVATION" | "UNKNOWN_VERTICAL_REFERENCE" | "INVALID_HEADING" | "INVALID_ELEVATION_OFFSET" | "GROUND_SAMPLE_REQUIRED" | "GROUND_SAMPLE_ELEVATION_MISSING" | "GROUND_SAMPLE_SOURCE_MISSING" | "TERRAIN_DATASET_REQUIRED" | "TERRAIN_VERSION_REQUIRED" | "TERRAIN_DATASET_MISMATCH" | "TERRAIN_VERSION_MISMATCH" | "VERTICAL_REFERENCE_MISMATCH" | "VERTICAL_CONVERSION_UNAVAILABLE" | "INVALID_HEIGHT_REFERENCE_FOR_PLACEMENT_MODE" | "INVALID_TRANSFORM" | "INVALID_SCALE";
export type CheckpointInvalidReason = "MISSING_XY" | "MISSING_ELEVATION" | "CRS_CONVERSION_FAILED" | "VERTICAL_DATUM_MISMATCH" | "TERRAIN_SAMPLE_FAILED" | "OUTSIDE_DATASET_COVERAGE";

export interface VerticalReference { type: VerticalReferenceType; datumName?: string; datumId?: string; unit: LinearUnit; conversionToEllipsoidAvailable: boolean; conversionMethod?: string; transformationId?: string; }
export interface TerrainCoverage { crs: "EPSG:4326"; geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon; }
export interface TerrainDatasetState {
  id: string; version: number; kind: TerrainDatasetKind; processingState: TerrainProcessingState;
  horizontalCrsType: HorizontalCRSType; horizontalCrsCode?: string; verticalReference: VerticalReference;
  verticalResolutionState: VerticalResolutionState; sourceUnit: LinearUnit; coverage?: TerrainCoverage;
  cesiumIonAssetId?: number; validationState: SurveyValidationState;
}
export interface GroundSample { status: GroundSampleStatus; longitude: number; latitude: number; elevation?: number; verticalReference?: VerticalReference; source: GroundSource; datasetId?: string; datasetVersion?: number; sampledAt?: string; failureReason?: string; }
export interface ModelPlacementState {
  placementMode: PlacementMode; heightReference: ModelHeightReference;
  anchor: { longitude: number; latitude: number; elevation: number; verticalReference: VerticalReference; headingDeg: number; elevationOffset: number; locked: boolean; };
  terrainDatasetId?: string; terrainDatasetVersion?: number; groundSample?: GroundSample;
  localTransform: { positionENU: { east: number; north: number; up: number }; rotationDeg: { x: number; y: number; z: number }; scale: { x: number; y: number; z: number } };
  placementState: PlacementState; legacyPlacement?: boolean;
}

export interface ActiveTerrainConfiguration { projectId: string; datasetId: string; datasetVersion: number; activatedAt: string; activatedBy: string; }
export interface SurveyCheckpointResidual { checkpointId: string; deltaEast?: number; deltaNorth?: number; deltaVertical?: number; horizontalError?: number; valid: boolean; invalidReason?: CheckpointInvalidReason; }
export interface SurveyValidationResult { datasetId: string; datasetVersion: number; totalCheckpointCount: number; validCheckpointCount: number; invalidCheckpointCount: number; excludedCheckpointCount: number; horizontalRmse?: number; verticalRmse?: number; maxHorizontalError?: number; maxVerticalError?: number; residuals: SurveyCheckpointResidual[]; calculatedAt: string; }
export interface PlacementValidationResult { valid: boolean; errors: PlacementValidationError[]; }

const PROCESSING_TRANSITIONS: Record<TerrainProcessingState, TerrainProcessingState[]> = {
  UPLOADED: ["METADATA_REQUIRED", "READY_TO_PROCESS", "ARCHIVED"], METADATA_REQUIRED: ["READY_TO_PROCESS", "ARCHIVED"],
  READY_TO_PROCESS: ["PROCESSING_QUEUED", "ARCHIVED"], PROCESSING_QUEUED: ["PROCESSING", "PROCESSING_FAILED"],
  PROCESSING: ["READY", "PROCESSING_FAILED"], READY: ["ARCHIVED"],
  PROCESSING_FAILED: ["READY_TO_PROCESS", "PROCESSING_QUEUED", "ARCHIVED"], ARCHIVED: [],
};
const VERTICAL_TRANSITIONS: Record<VerticalResolutionState, VerticalResolutionState[]> = {
  NOT_CHECKED: ["MISSING_METADATA", "REFERENCE_IDENTIFIED"], MISSING_METADATA: ["REFERENCE_IDENTIFIED"],
  REFERENCE_IDENTIFIED: ["RESOLVED", "CONVERSION_REQUIRED"], CONVERSION_REQUIRED: ["RESOLVED", "UNSUPPORTED"],
  RESOLVED: ["CONVERSION_REQUIRED"], UNSUPPORTED: ["REFERENCE_IDENTIFIED"],
};
const VALIDATION_TRANSITIONS: Record<SurveyValidationState, SurveyValidationState[]> = {
  NOT_RUN: ["INSUFFICIENT_CHECKPOINTS", "READY_TO_VALIDATE"], INSUFFICIENT_CHECKPOINTS: ["READY_TO_VALIDATE"],
  READY_TO_VALIDATE: ["VALIDATING", "INSUFFICIENT_CHECKPOINTS"], VALIDATING: ["VALIDATED", "VALIDATION_FAILED"],
  VALIDATED: ["STALE"], VALIDATION_FAILED: ["READY_TO_VALIDATE"], STALE: ["READY_TO_VALIDATE"],
};
const PLACEMENT_TRANSITIONS: Record<PlacementState, PlacementState[]> = {
  UNPLACED: ["PLACEMENT_PENDING"], PLACEMENT_PENDING: ["VALID", "INVALID", "UNPLACED"],
  VALID: ["REVIEW_REQUIRED", "INVALID", "PLACEMENT_PENDING"], REVIEW_REQUIRED: ["PLACEMENT_PENDING", "VALID", "INVALID"],
  INVALID: ["PLACEMENT_PENDING", "UNPLACED"],
};
export const canTransitionProcessingState = (from: TerrainProcessingState, to: TerrainProcessingState) => PROCESSING_TRANSITIONS[from].includes(to);
export const canTransitionVerticalResolution = (from: VerticalResolutionState, to: VerticalResolutionState) => VERTICAL_TRANSITIONS[from].includes(to);
export const canTransitionValidation = (from: SurveyValidationState, to: SurveyValidationState) => VALIDATION_TRANSITIONS[from].includes(to);
export const canTransitionPlacement = (from: PlacementState, to: PlacementState) => PLACEMENT_TRANSITIONS[from].includes(to);
export const markValidationStale = (state: SurveyValidationState): SurveyValidationState => state === "VALIDATED" ? "STALE" : state;
export const markGroundSampleStale = (sample?: GroundSample): GroundSample | undefined => sample ? { ...sample, status: "STALE" } : undefined;
export const normalizeHeading = (degrees: number) => ((degrees % 360) + 360) % 360;
export function verticalReferencesCompatible(a: VerticalReference, b: VerticalReference) {
  if (a.type === "UNKNOWN" || b.type === "UNKNOWN" || a.unit === "UNKNOWN" || b.unit === "UNKNOWN") return false;
  if (a.datumId && b.datumId && a.datumId === b.datumId) return true;
  if (a.type === "ELLIPSOIDAL" && b.type === "ELLIPSOIDAL") return true;
  return Boolean(a.transformationId && b.transformationId && a.transformationId === b.transformationId);
}
export function hasValidCoverage(coverage?: TerrainCoverage) {
  if (!coverage || coverage.crs !== "EPSG:4326") return false;
  const rings = coverage.geometry.type === "Polygon" ? coverage.geometry.coordinates : coverage.geometry.coordinates.flat();
  return rings.some((ring) => ring.length >= 4 && ring[0][0] === ring.at(-1)?.[0] && ring[0][1] === ring.at(-1)?.[1] && ring.every(([lng, lat]) => Number.isFinite(lng) && Number.isFinite(lat) && lng >= -180 && lng <= 180 && lat >= -90 && lat <= 90));
}
export function isValidHeightReferenceForPlacement(placementMode: PlacementMode, heightReference: ModelHeightReference) {
  return placementMode === "GROUND_RELATIVE"
    ? heightReference === "TERRAIN"
    : heightReference === "ELLIPSOID" || heightReference === "ORTHOMETRIC" || heightReference === "PROJECT_DATUM";
}

export function terrainActivationBlockReason(dataset: TerrainDatasetState): ActivationBlockReason | null {
  if (dataset.kind !== "SURVEY_TERRAIN" && dataset.kind !== "FUSED_TERRAIN") return "INVALID_DATASET_KIND";
  if (dataset.processingState !== "READY") return "PROCESSING_NOT_READY";
  if (dataset.horizontalCrsType === "UNKNOWN") return "CRS_UNKNOWN";
  if (dataset.verticalResolutionState === "UNSUPPORTED") return "VERTICAL_CONVERSION_UNAVAILABLE";
  if (dataset.verticalResolutionState !== "RESOLVED") return "VERTICAL_DATUM_UNKNOWN";
  if (dataset.sourceUnit === "UNKNOWN") return "UNITS_UNKNOWN";
  if (!hasValidCoverage(dataset.coverage)) return "COVERAGE_UNKNOWN";
  if (dataset.verticalReference.type === "UNKNOWN") return "VERTICAL_DATUM_UNKNOWN";
  if (dataset.verticalReference.unit === "UNKNOWN") return "UNITS_UNKNOWN";
  if (dataset.verticalReference.type !== "ELLIPSOIDAL" && !dataset.verticalReference.conversionToEllipsoidAvailable) return "VERTICAL_CONVERSION_UNAVAILABLE";
  if (dataset.cesiumIonAssetId == null) return "ION_ASSET_MISSING";
  return null;
}

export function canActivateSurveyTerrain(dataset: TerrainDatasetState) { return terrainActivationBlockReason(dataset) === null; }
export function isActiveTerrain(dataset: TerrainDatasetState, active: ActiveTerrainConfiguration | null) { return active?.datasetId === dataset.id && active.datasetVersion === dataset.version; }

/** Terrain changes invalidate provenance only. They never alter model coordinates. */
export function markPlacementForTerrainChange(placement: ModelPlacementState, activeTerrain: ActiveTerrainConfiguration): ModelPlacementState {
  const terrainChanged = placement.terrainDatasetId !== activeTerrain.datasetId || placement.terrainDatasetVersion !== activeTerrain.datasetVersion;
  if (!terrainChanged) return placement;
  if (placement.placementMode === "ABSOLUTE") return { ...placement, groundSample: markGroundSampleStale(placement.groundSample) };
  return { ...placement, placementState: "REVIEW_REQUIRED", groundSample: markGroundSampleStale(placement.groundSample) };
}

export function validatePlacement(placement: ModelPlacementState): PlacementValidationResult {
  const errors: PlacementValidationError[] = [];
  if (!Number.isFinite(placement.anchor.longitude) || placement.anchor.longitude < -180 || placement.anchor.longitude > 180) errors.push("INVALID_LONGITUDE");
  if (!Number.isFinite(placement.anchor.latitude) || placement.anchor.latitude < -90 || placement.anchor.latitude > 90) errors.push("INVALID_LATITUDE");
  if (!Number.isFinite(placement.anchor.elevation)) errors.push("INVALID_ANCHOR_ELEVATION");
  if (placement.anchor.verticalReference.type === "UNKNOWN") errors.push("UNKNOWN_VERTICAL_REFERENCE");
  if (!Number.isFinite(placement.anchor.headingDeg)) errors.push("INVALID_HEADING");
  if (!Number.isFinite(placement.anchor.elevationOffset)) errors.push("INVALID_ELEVATION_OFFSET");
  if (!isValidHeightReferenceForPlacement(placement.placementMode, placement.heightReference)) errors.push("INVALID_HEIGHT_REFERENCE_FOR_PLACEMENT_MODE");
  const vectors = [placement.localTransform.positionENU, placement.localTransform.rotationDeg, placement.localTransform.scale];
  if (vectors.some((vector) => !Object.values(vector).every(Number.isFinite))) errors.push("INVALID_TRANSFORM");
  if (Object.values(placement.localTransform.scale).some((value) => value <= 0)) errors.push("INVALID_SCALE");
  if (placement.placementMode === "GROUND_RELATIVE") {
    if (!placement.terrainDatasetId) errors.push("TERRAIN_DATASET_REQUIRED");
    if (placement.terrainDatasetVersion == null) errors.push("TERRAIN_VERSION_REQUIRED");
    const sample = placement.groundSample;
    if (sample?.status !== "VALID") errors.push("GROUND_SAMPLE_REQUIRED");
    else {
      if (sample.elevation == null) errors.push("GROUND_SAMPLE_ELEVATION_MISSING");
      if (sample.source === "NONE" || !sample.datasetId || sample.datasetVersion == null || !sample.verticalReference) errors.push("GROUND_SAMPLE_SOURCE_MISSING");
      if (sample.verticalReference && !verticalReferencesCompatible(placement.anchor.verticalReference, sample.verticalReference)) errors.push("VERTICAL_REFERENCE_MISMATCH");
      if (sample.datasetId && placement.terrainDatasetId && sample.datasetId !== placement.terrainDatasetId) errors.push("TERRAIN_DATASET_MISMATCH");
      if (sample.datasetVersion != null && placement.terrainDatasetVersion != null && sample.datasetVersion !== placement.terrainDatasetVersion) errors.push("TERRAIN_VERSION_MISMATCH");
    }
  }
  return { valid: errors.length === 0, errors };
}
