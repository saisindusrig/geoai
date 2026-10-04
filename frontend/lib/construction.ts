import type { GeoPoint, SiteContext } from "@/lib/civicspan";

export const CONSTRUCTION_TYPES = [
  "bridge",
  "flyover",
  "building",
  "road",
  "pipeline",
  "dam",
] as const;
export type ConstructionType = (typeof CONSTRUCTION_TYPES)[number];
export type ConstructionStage = "site" | "foundation" | "structure" | "finish";

export type ConstructionSpec = {
  project_type: ConstructionType;
  width_m: number;
  length_m: number;
  height_m: number;
  supports: number;
  style: string;
  stages: ConstructionStage[];
};

export type ConstructionPlan = {
  summary: string;
  spec: ConstructionSpec;
  assumptions: string[];
  warnings: string[];
  explanation: string;
};

export const CONSTRUCTION_LABELS: Record<ConstructionType, string> = {
  bridge: "Pedestrian bridge",
  flyover: "Flyover / overpass",
  building: "Building massing",
  road: "Road corridor",
  pipeline: "Pipeline corridor",
  dam: "Dam / reservoir",
};

export const TEMPLATE_PROMPTS: Record<ConstructionType, string> = {
  bridge:
    "Create a 4 metre wide steel truss pedestrian bridge with concrete foundations, supports, railings, and a durable walking deck.",
  flyover:
    "Create a two-lane elevated flyover with concrete piers, a simple deck structure, and safe edge barriers.",
  building:
    "Create a mid-rise public building massing concept with a clear entrance, regular floors, and a practical structural grid.",
  road: "Create a two-lane road corridor with shoulders, drainage allowance, and a straightforward terrain alignment.",
  pipeline:
    "Create a utility pipeline corridor with visible access chambers, a safe route, and maintainable spacing.",
  dam: "Create a conceptual concrete gravity dam across this terrain with a spillway, foundation zone, and reservoir-facing wall.",
};

const DEFAULTS: Record<
  ConstructionType,
  Omit<ConstructionSpec, "project_type">
> = {
  bridge: {
    width_m: 4,
    length_m: 72,
    height_m: 6,
    supports: 2,
    style: "steel truss",
    stages: ["site", "foundation", "structure", "finish"],
  },
  flyover: {
    width_m: 12,
    length_m: 180,
    height_m: 8,
    supports: 6,
    style: "concrete viaduct",
    stages: ["site", "foundation", "structure", "finish"],
  },
  building: {
    width_m: 30,
    length_m: 42,
    height_m: 24,
    supports: 0,
    style: "mid-rise massing",
    stages: ["site", "foundation", "structure", "finish"],
  },
  road: {
    width_m: 9,
    length_m: 220,
    height_m: 1,
    supports: 0,
    style: "two-lane corridor",
    stages: ["site", "foundation", "structure", "finish"],
  },
  pipeline: {
    width_m: 2,
    length_m: 180,
    height_m: 2,
    supports: 4,
    style: "utility corridor",
    stages: ["site", "foundation", "structure", "finish"],
  },
  dam: {
    width_m: 36,
    length_m: 120,
    height_m: 28,
    supports: 0,
    style: "gravity dam",
    stages: ["site", "foundation", "structure", "finish"],
  },
};

export function defaultSpec(projectType: ConstructionType): ConstructionSpec {
  return { project_type: projectType, ...DEFAULTS[projectType] };
}

export function spanMeters(start: GeoPoint, end: GeoPoint) {
  const radians = (value: number) => (value * Math.PI) / 180;
  const radius = 6_371_000;
  const dLat = radians(end.lat - start.lat);
  const dLng = radians(end.lng - start.lng);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(radians(start.lat)) *
      Math.cos(radians(end.lat)) *
      Math.sin(dLng / 2) ** 2;
  return 2 * radius * Math.asin(Math.sqrt(a));
}

export function offlineConstructionPlan(
  site: SiteContext,
  request: string,
  projectType: ConstructionType,
): ConstructionPlan {
  const spec = defaultSpec(projectType);
  const width = request.match(
    /(\d+(?:\.\d+)?)\s*(?:m|metre|meter)\s*(?:wide|width)/i,
  );
  if (width) spec.width_m = Math.min(80, Math.max(2, Number(width[1])));
  if (/tall|height/i.test(request) && projectType === "building")
    spec.height_m = 32;
  if (/longer|long/i.test(request))
    spec.length_m = Math.round(spec.length_m * 1.25);
  if (/truss/i.test(request)) spec.style = "steel truss";
  if (/concrete/i.test(request))
    spec.style =
      projectType === "dam" ? "concrete gravity dam" : "concrete structure";
  const span = Math.max(1, spanMeters(site.start, site.end));
  return {
    summary: `Conceptual ${CONSTRUCTION_LABELS[projectType].toLowerCase()} for a ${span.toFixed(0)}m map-derived context span.`,
    spec,
    assumptions: [
      "Map coordinates provide visual context only, not survey-grade measurements.",
      "A qualified professional must validate site conditions, safety, structure, cost, permits, and construction details.",
    ],
    warnings: [
      "Local concept preview shown. Configure Nebius Token Factory to use Nemotron planning.",
    ],
    explanation:
      "The local preview produces a constrained, editable construction concept. The same fields are sent to Nemotron when the AI planner is available.",
  };
}
