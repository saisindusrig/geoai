export type AccuracyTier =
  "visual" | "gis_grade" | "survey_grade" | "engineering_ready";

export type EngineeringLayerType =
  | "road_centerline"
  | "road_edge"
  | "parcel"
  | "drain"
  | "bridge"
  | "retaining_wall"
  | "utility"
  | "construction_zone"
  | "mask_source";

export interface LayerMetadata {
  source: string | null;
  captureDate: string | null;
  crsEpsg: number | null;
  pixelSizeM: number | null;
  rmseHM: number | null;
  rmseVM: number | null;
  tier: AccuracyTier;
}

export interface SurveyDataset {
  id: number;
  kind: string;
  name: string;
  storage_key: string | null;
  source: string | null;
  capture_date: string | null;
  crs_epsg: number | null;
  crs_label: string | null;
  pixel_size_m: number | null;
  rmse_h_m: number | null;
  rmse_v_m: number | null;
  accuracy_tier: AccuracyTier;
  metadata_json: Record<string, unknown> | null;
}

export interface EngineeringLayer {
  id: number;
  layer_type: EngineeringLayerType;
  name: string;
  width_m: number | null;
  geom_wgs84_geojson: GeoJSONGeometry | null;
  properties_json: Record<string, unknown> | null;
  metadata: LayerMetadata;
}

export interface GroundControlPoint {
  id: number;
  name: string;
  source: string;
  lng: number;
  lat: number;
  easting_m: number | null;
  northing_m: number | null;
  horizontal_accuracy_m: number | null;
  vertical_accuracy_m: number | null;
}

export interface SurveyStatus {
  postgis_available: boolean;
  survey_mode_enabled: boolean;
  accuracy_tier: AccuracyTier;
  engineering_crs_epsg: number | null;
  visual_warning: string;
  disclaimer: string;
}

export interface ValidationReport {
  tier_result: AccuracyTier;
  passed: boolean;
  checks: { id: string; label: string; passed: boolean; detail: string }[];
  gcp_adjustment: {
    offset_e_m: number;
    offset_n_m: number;
    horizontal_rmse_m: number | null;
    vertical_rmse_m: number | null;
  };
}

export interface ProjectValidationCheck {
  id: string;
  label: string;
  passed: boolean;
  severity: "error" | "warning" | "info";
  detail: string;
  action: string | null;
}

export interface ProjectValidation {
  project_id: number;
  project_type: ProjectType;
  accuracy_tier: AccuracyTier;
  postgis_available: boolean;
  survey_mode_available: boolean;
  database_mode: "postgis" | "sqlite";
  ready_for_design: boolean;
  ready_for_boq: boolean;
  ready_for_export: boolean;
  boundary_area_sqm: number | null;
  alignment_length_m: number | null;
  engineering_crs_epsg: number | null;
  checks: ProjectValidationCheck[];
  errors: string[];
  warnings: string[];
  recommended_next_steps: string[];
  disclaimer: string;
}

export interface CopilotAction {
  type:
    | "update_parameters"
    | "run_site_analysis"
    | "generate_design"
    | "show_layer"
    | "download";
  payload: Record<string, unknown>;
}

export interface CopilotStreamResult {
  message?: string;
  actions: CopilotAction[];
  warnings: string[];
  provider?: string;
  action?: CopilotAction | null;
  disclaimer?: string;
}

export interface UsageMetric {
  current: number | null;
  max: number | null;
  unlimited?: boolean;
  reset_at?: string | null;
}

export interface UsageSummary {
  plan: string;
  unlimited: boolean;
  projects: UsageMetric;
  generations_today: UsageMetric;
  llm_plans_today: UsageMetric;
  exports_today: UsageMetric;
  limits: Record<string, number | null>;
}

export interface SystemStatus {
  database_type: string;
  postgis_available: boolean;
  database_mode_label: string;
  redis_available: boolean;
  job_store: string;
  storage_mode: string;
  survey_mode_available: boolean;
  ai: {
    configured_provider: string;
    active_provider: string;
    mock_mode: boolean;
    openai_configured: boolean;
    anthropic_configured: boolean;
    gemini_configured: boolean;
    gemini_implemented?: boolean;
    ollama: {
      primary: boolean;
      base_url: string;
      model: string;
      available: boolean;
      model_ready: boolean;
      installed_models: string[];
    };
  };
  maps: {
    google_maps_configured: boolean;
    mapbox_configured: boolean;
    cesium_ion_configured: boolean;
    osm_fallback: boolean;
  };
  production?: {
    environment: string;
    auth_required: boolean;
    auth_jwt_required: boolean;
    auth_ready: boolean;
    ownership_enforced: boolean;
    file_access_mode: string;
    roles_enabled: boolean;
    audit_enabled: boolean;
    admin_routes_protected: boolean;
    usage_limits_enabled?: boolean;
    rate_limiting_enabled?: boolean;
    redis_rate_limit_backend?: boolean;
    using_dev_secret: boolean;
    generation_timeout_seconds: number;
    warnings: { code: string; message: string; severity?: string }[];
    warning_count: number;
    critical_count: number;
    production_ready: boolean;
    deployment_ready: boolean;
  };
  observability?: {
    structured_request_logging: boolean;
    request_id_header: string;
    sentry_enabled: boolean;
    sentry_configured: boolean;
  };
  disclaimer: string;
}

export type ProjectType =
  | "flyover"
  | "building"
  | "pipeline"
  | "road"
  | "bridge"
  | "interchange"
  | "railway"
  | "tunnel"
  | "dam"
  | "substation"
  | "retaining_wall"
  | "culvert"
  | "wastewater"
  | "solar_farm"
  | (string & {});

export interface GeoJSONGeometry {
  type: string;
  coordinates: unknown;
}

export interface Project {
  id: number;
  name: string;
  project_type: ProjectType;
  status: string;
  units: string;
  location_name: string;
  center_lat: number | null;
  center_lng: number | null;
  boundary_geojson: GeoJSONGeometry | null;
  alignment_geojson: GeoJSONGeometry | null;
  folder_id: number | null;
  created_at: string;
  updated_at: string;
  disclaimer: string;
}

export interface ProjectFolder {
  id: number;
  name: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface SiteAnalysis {
  id: number;
  project_id: number;
  area_sqm: number | null;
  perimeter_m: number | null;
  elevation_min_m: number | null;
  elevation_max_m: number | null;
  slope_percent_estimate: number | null;
  nearby_roads_json: { features: GeoJSONFeature[] } | null;
  existing_buildings_json: { features: GeoJSONFeature[] } | null;
  risks_json: unknown[] | null;
  raw_geojson: { features: GeoJSONFeature[] } | null;
  created_at: string;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: GeoJSONGeometry;
  properties: Record<string, unknown>;
}

export interface DesignScenario {
  id: number;
  name: string;
  status: string;
  input_parameters_json: Record<string, unknown> | null;
  design_output_json: DesignOutput | null;
  assumptions_json: string[] | null;
  created_at: string;
}

export interface ScenarioSummary {
  scenario_id: number;
  name: string;
  title?: string;
  status: string;
  created_at: string | null;
  generation_mode?: string;
  planning_mode?: string | null;
  project_type?: string;
  length_m?: number | null;
  lanes?: number | null;
  width_m?: number | null;
  clearance_m?: number | null;
  pier_spacing_m?: number | null;
  cost_total?: number | null;
  cost_currency?: string;
  materials_summary?: Record<string, number | null>;
  validation_status?: string | null;
  validation_score?: number | null;
  warning_count?: number;
  error_count?: number;
  geometry_mode?: string | null;
  elevation_mode?: string | null;
  max_grade_percent?: number | null;
  model_url?: string | null;
  preview_url?: string | null;
  report_url?: string | null;
  key_assumptions?: string[];
  duration_months?: number | null;
}

export interface ScenarioListResponse {
  summaries: ScenarioSummary[];
  scenarios: ScenarioSummary[];
}

export interface ScenarioCompareRow {
  scenario_id: number;
  name: string;
  cost_total?: number | null;
  validation_score?: number | null;
  validation_status?: string | null;
  length_m?: number | null;
  width_m?: number | null;
  lanes?: number | null;
  pier_spacing_m?: number | null;
  max_grade_percent?: number | null;
  geometry_mode?: string | null;
  elevation_mode?: string | null;
  warning_count?: number;
  error_count?: number;
  recommendations?: string[];
  duration_months?: number | null;
}

export interface ScenarioCompareResult {
  project_id: number;
  scenario_ids: number[];
  rows: ScenarioCompareRow[];
  best_option_by: {
    lowest_cost?: number | null;
    highest_validation_score?: number | null;
    fewest_warnings?: number | null;
  };
  notes: string[];
}

export interface GeometrySpecObject {
  kind: "box" | "cylinder";
  name: string;
  layer: string;
  size?: [number, number, number];
  center?: [number, number, number];
  rotation_z_deg?: number;
  start?: [number, number, number];
  end?: [number, number, number];
  radius_m?: number;
}

export interface GeometrySpec {
  objects: GeometrySpecObject[];
  frame?: string;
  length_m?: number;
  geometry_mode?: "alignment" | "straight";
  elevation_mode?: "profile" | "flat";
  elevation_assumed?: boolean;
  elevation_provider?: string;
  min_elevation_m?: number;
  max_elevation_m?: number;
  max_grade_percent?: number;
}

export interface DesignValidationResult {
  validation_status: "pass" | "warning" | "fail";
  score: number;
  warnings: { code: string; message: string; field?: string | null }[];
  errors: { code: string; message: string; field?: string | null }[];
  recommendations: { code: string; message: string }[];
  assumptions: string[];
  conceptual_disclaimer?: string;
}

export interface DesignReviewSummary {
  project_type?: string;
  final_parameters?: Record<string, unknown>;
  geometry_mode?: string;
  elevation_mode?: string;
  max_grade_percent?: number;
  alignment_based?: boolean;
  elevation_aware?: boolean;
  planning_mode?: string;
  validation_status?: string;
  validation_score?: number;
  warnings?: string[];
  errors?: string[];
  recommendations?: string[];
  assumptions?: string[];
  conceptual_disclaimer?: string;
  not_for_construction?: boolean;
}

export interface DesignPlanningMetadata {
  planning_mode?: "llm" | "template" | "fallback";
  llm_provider?: string | null;
  llm_model?: string | null;
  design_assumptions?: string[];
  design_warnings?: string[];
  missing_inputs?: { field: string; reason: string }[];
  final_parameters?: Record<string, unknown>;
}

export interface DesignOutput {
  project_type: string;
  summary: string;
  assumptions: string[];
  geometry: Record<string, number | string>;
  materials: Record<string, string | number>;
  layers: { name: string; description: string }[];
  construction_sequence: string[];
  risks: unknown[];
  required_engineer_review: boolean;
  required_permissions: string[];
  ai_provider?: string;
  geometry_spec?: GeometrySpec;
  planning?: DesignPlanningMetadata;
  validation?: DesignValidationResult;
  design_review?: DesignReviewSummary;
  editable_model_revision_id?: number;
  editable_model_revision_number?: number;
  calculated?: {
    quantities: Record<string, number>;
    derived: Record<string, unknown>;
    timeline: Record<string, number | string>;
    cost_summary: CostSummary;
  };
}

export type EditableGeometry =
  | { kind: "box" | "extrusion"; size: [number, number, number] }
  | { kind: "cylinder" | "sweep"; start: [number, number, number]; end: [number, number, number]; radius_m: number }
  | { kind: "asset_instance"; asset_url: string };

export interface EditableModelComponent {
  id: string;
  parent_id: string | null;
  name: string;
  category: string;
  visible: boolean;
  locked: boolean;
  geometry: EditableGeometry;
  transform: {
    position: [number, number, number];
    rotation_deg: [number, number, number];
    scale: [number, number, number];
  };
  material: { name: string; color: string; roughness: number; metalness: number };
  quantity?: { included?: boolean };
}

export interface EditableModelDocument {
  schema_version: 1;
  project_id: number;
  scenario_id: number;
  project_type: string;
  units: "metric";
  origin: { lng: number; lat: number; elevation_m: number; heading_deg: number };
  generator_parameters: Record<string, unknown>;
  components: EditableModelComponent[];
  metadata: { source: string; frame: "local_enu_meters" };
  structural_layout?: StructuralLayoutMetadata;
}

export type StructuralElementType = "site_boundary" | "building" | "grid" | "column" | "beam" | "wall" | "slab" | "foundation" | "road" | "bridge" | "retaining_wall" | "drainage" | "pipeline" | "utility" | "zone" | "construction_phase";
export interface StructuralRuleViolation { rule: string; component_id?: string; related_component_id?: string; message: string; action: string; }
export interface StructuralLayoutValidation { passed: boolean; preset: Record<string, number>; violations: StructuralRuleViolation[]; disclaimer: string; }
export interface StructuralLayoutMetadata { rule_preset?: Record<string, number>; assumptions?: string[]; approval?: { approved_by: number; approved_role: string; status: "approved" }; impact?: { estimated_cost?: number }; }
export interface StructuralAlternative { id: string; name: string; score: number | null; cost_delta_percent: number; estimated_cost?: number; constructability: string; rule_compliant: boolean; }
export interface StructuralAnalysisResult {
  id: number;
  imported_at: string;
  revision_id: number;
  solver: string;
  summary: string;
  findings: { component_id: string; status: "pass" | "warning" | "fail"; message: string }[];
}

export interface ModelRevision {
  id: number;
  project_id: number;
  scenario_id: number;
  revision_number: number;
  source: "manual_edit" | "ai_edit" | "ai_generate" | "import";
  prompt: string | null;
  user_id: number | null;
  created_at: string;
  document?: EditableModelDocument;
}

export interface ModelImpact {
  quantities: {
    concrete_m3: number;
    cement_bags: number;
    steel_kg: number;
    rebar_kg: number;
    excavation_m3: number;
    backfill_m3: number;
    formwork_sqm: number;
    asphalt_m3: number;
    pipe_length_m: number;
    pipe_diameter_mm: number;
  };
  total_cost_estimate: number;
  currency: string;
}

export interface CostSummary {
  direct_cost: number;
  contingency_percent: number;
  contingency: number;
  design_survey_approval: number;
  total_low: number;
  total_medium: number;
  total_high: number;
  currency: string;
}

export interface LineItem {
  item_code: string;
  item_name: string;
  category: string;
  quantity: number;
  unit: string;
  rate: number;
  amount: number;
  assumption: string;
  currency?: string;
}

export interface QuantityEstimate {
  id: number;
  design_scenario_id: number;
  concrete_m3: number;
  cement_bags: number;
  steel_kg: number;
  rebar_kg: number;
  excavation_m3: number;
  backfill_m3: number;
  formwork_sqm: number;
  asphalt_m3: number;
  pipe_length_m: number;
  pipe_diameter_mm: number;
  total_cost_estimate: number;
  line_items: LineItem[];
  created_at: string;
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  stage?: import("@/lib/generation-job").JobStage;
  stage_label?: string;
  progress?: number;
  message?: string | null;
  preview_ready?: boolean;
  preview_glb_url?: string | null;
  /** Populated on completed jobs — same as `result.glb_url` when present. */
  final_glb_url?: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  error_type?: string | null;
  safe_error_message?: string | null;
  failed_stage?: string | null;
  retryable?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  duration_ms?: number | null;
  timings?: Record<string, number> | null;
  diagnostics?: JobDiagnostics | null;
}

export interface JobDiagnostics {
  total_duration_ms?: number | null;
  llm_planning_ms?: number | null;
  elevation_sampling_ms?: number | null;
  glb_preview_ms?: number | null;
  glb_final_ms?: number | null;
  boq_ms?: number | null;
  validation_ms?: number | null;
  file_save_ms?: number | null;
  provider?: string | null;
  generation_mode?: string | null;
  failure_reason?: string | null;
  failed_stage?: string | null;
  cancelled?: boolean;
  timings_ms?: Record<string, number> | null;
}

export type GenerationMode = import("@/lib/generation-job").GenerationMode;

export interface GeneratedFileInfo {
  id: number;
  file_type: string;
  file_url: string;
  scenario_id: number | null;
  created_at: string;
}

export interface RateItem {
  id: number;
  region: string;
  item_code: string;
  item_name: string;
  unit: string;
  rate: number;
  currency: string;
}

export interface ProjectTemplate {
  id: number;
  project_type: string;
  name: string;
  default_parameters_json: Record<string, unknown>;
}

export interface GeocodeResult {
  name: string;
  lat: number;
  lng: number;
  provider: string;
}
