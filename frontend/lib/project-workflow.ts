import type { DesignScenario, Project } from "@/lib/types";

export const WORKFLOW_STEPS = [
  { id: "site", label: "Site Selection" },
  { id: "boundary", label: "Boundary" },
  { id: "parameters", label: "Parameters" },
  { id: "generate", label: "Generate" },
  { id: "review", label: "Review" },
] as const;

export type WorkflowStepId = (typeof WORKFLOW_STEPS)[number]["id"];

export function workflowHref(projectId: number, step: WorkflowStepId): string {
  switch (step) {
    case "site":
      return `/projects/${projectId}/map`;
    case "boundary":
      return `/projects/${projectId}/map?tool=draw-polygon`;
    case "parameters":
      return `/projects/${projectId}/workspace#parameters`;
    case "generate":
      return `/projects/${projectId}/workspace`;
    case "review":
      return `/projects/${projectId}/estimate`;
  }
}

export interface WorkflowState {
  hasLocation: boolean;
  hasBoundary: boolean;
  hasParameters: boolean;
  hasDesign: boolean;
}

export function getWorkflowState(
  project: Project,
  scenario?: DesignScenario | null,
  hasPendingParams?: boolean,
): WorkflowState {
  return {
    hasLocation: !!(project.location_name || (project.center_lat != null && project.center_lng != null)),
    hasBoundary: !!project.boundary_geojson,
    hasParameters: !!(hasPendingParams ?? scenario?.input_parameters_json),
    hasDesign: project.status === "designed" || scenario?.status === "completed",
  };
}

export interface ProjectHealth extends WorkflowState {
  hasAnalysis: boolean;
  hasEstimate: boolean;
  scenarioCount: number;
  progress: number;
}

export function computeHealth(
  project: Project,
  scenarios: DesignScenario[] = [],
  hasEstimate = false,
  hasAnalysis = false,
): ProjectHealth {
  const completed = scenarios.filter((s) => s.status === "completed");
  const latest = completed[0] ?? scenarios[0] ?? null;
  const ws = getWorkflowState(project, latest);
  const flags = [
    ws.hasLocation,
    ws.hasBoundary,
    hasAnalysis,
    ws.hasParameters,
    ws.hasDesign,
    hasEstimate,
  ];
  return {
    ...ws,
    hasAnalysis,
    hasEstimate,
    scenarioCount: scenarios.length,
    progress: Math.round((flags.filter(Boolean).length / flags.length) * 100),
  };
}

/** Bearing in radians between two WGS84 points (lat/lng in degrees). */
export function geoBearingRad(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const lat1r = (lat1 * Math.PI) / 180;
  const lat2r = (lat2 * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2r);
  const x = Math.cos(lat1r) * Math.sin(lat2r) - Math.sin(lat1r) * Math.cos(lat2r) * Math.cos(dLng);
  return Math.atan2(y, x);
}

/** Bearing in radians from first segment of a LineString alignment. */
export function alignmentBearing(alignment: { type: string; coordinates: unknown } | null): number {
  if (alignment?.type !== "LineString") return 0;
  const coords = alignment.coordinates as [number, number][];
  if (coords.length < 2) return 0;
  const [lng1, lat1] = coords[0];
  const [lng2, lat2] = coords[coords.length - 1];
  return geoBearingRad(lat1, lng1, lat2, lng2);
}

/** Anchor design GLB at alignment midpoint with overall line bearing. */
export function alignmentModelPlacement(
  alignment: { type: string; coordinates: unknown } | null,
  fallbackLng: number,
  fallbackLat: number,
): { lng: number; lat: number; bearingRad: number } {
  if (alignment?.type !== "LineString") {
    return { lng: fallbackLng, lat: fallbackLat, bearingRad: 0 };
  }
  const coords = alignment.coordinates as [number, number][];
  if (coords.length < 2) {
    return { lng: fallbackLng, lat: fallbackLat, bearingRad: 0 };
  }
  const mid = coords[Math.floor(coords.length / 2)];
  return {
    lng: mid[0],
    lat: mid[1],
    bearingRad: geoBearingRad(coords[0][1], coords[0][0], coords[coords.length - 1][1], coords[coords.length - 1][0]),
  };
}

/** Anchor exported GLB at project center; backend local meters originate here. */
export function designModelAnchor(
  alignment: { type: string; coordinates: unknown } | null,
  centerLng: number,
  centerLat: number,
): { lng: number; lat: number; bearingRad: number } {
  return {
    lng: centerLng,
    lat: centerLat,
    bearingRad: alignmentBearing(alignment),
  };
}

import type { ModelLayerVisibility } from "@/stores/projectStore";

/** Map BIM layer toggles to GLB node layer prefixes (named meshes in export). */
export function modelLayerVisibility(modelLayers: ModelLayerVisibility) {
  const layerPrefixes: Record<keyof ModelLayerVisibility, string[]> = {
    outer: ["facade", "barrier", "deck", "asphalt"],
    inner: ["core", "slab"],
    foundation: ["foundation", "bedding", "piers"],
    steel: ["steel"],
    concrete: ["concrete", "pier_caps", "column"],
    drainage: ["pipe_drain", "backfill", "excavation"],
    electrical: [],
    pipeline: ["pipe_water", "pipe_drain", "manhole"],
    traffic: ["road_marking", "shoulder", "barrier"],
  };

  const activePrefixes = new Set<string>();
  for (const [key, prefixes] of Object.entries(layerPrefixes) as [keyof ModelLayerVisibility, string[]][]) {
    if (modelLayers[key]) prefixes.forEach((p) => activePrefixes.add(p));
  }

  return {
    showProjectModel: activePrefixes.size > 0,
    showExcavation: modelLayers.foundation || modelLayers.drainage,
    activePrefixes: [...activePrefixes],
  };
}
