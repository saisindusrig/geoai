export type GeoPoint = { lat: number; lng: number; elevation_m?: number };

export type SiteContext = {
  start: GeoPoint;
  end: GeoPoint;
  crossing: "waterway" | "road" | "terrain" | "unknown";
  terrain_slope_pct: number;
  nearby_buildings: number;
  nearby_roads: number;
};

export type BridgeSpec = {
  bridge_type: "pedestrian_bridge";
  structure_type: "steel_truss" | "steel_girder";
  width_m: number;
  deck_elevation_m: number;
  supports: number;
  deck_material: "concrete";
  structure_material: "steel";
  railings: boolean;
  stages: Array<"foundation" | "supports" | "steel" | "deck" | "finished">;
};

export type BridgePlan = {
  summary: string;
  spec: BridgeSpec;
  assumptions: string[];
  warnings: string[];
  explanation: string;
};

export const STAGES: Array<BridgeSpec["stages"][number]> = [
  "foundation",
  "supports",
  "steel",
  "deck",
  "finished",
];

export function spanMeters(start: GeoPoint, end: GeoPoint) {
  const radians = (value: number) => (value * Math.PI) / 180;
  const radius = 6_371_000;
  const dLat = radians(end.lat - start.lat);
  const dLng = radians(end.lng - start.lng);
  const lat1 = radians(start.lat);
  const lat2 = radians(end.lat);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * radius * Math.asin(Math.sqrt(a));
}

export function offlinePlan(site: SiteContext, prompt: string): BridgePlan {
  const truss = /truss/i.test(prompt);
  const supports = /two more support/i.test(prompt) ? 4 : 2;
  return {
    summary: `Conceptual ${truss ? "steel truss" : "steel girder"} pedestrian bridge across a ${spanMeters(site.start, site.end).toFixed(0)}m map-derived span.`,
    spec: {
      bridge_type: "pedestrian_bridge",
      structure_type: truss ? "steel_truss" : "steel_girder",
      width_m: /5\s*(m|meter)/i.test(prompt) ? 5 : 4,
      deck_elevation_m: 5,
      supports,
      deck_material: "concrete",
      structure_material: "steel",
      railings: true,
      stages: STAGES,
    },
    assumptions: [
      "Map endpoints and span are visual context, not survey data.",
      "A qualified engineer must validate foundation, accessibility, hydraulic, and structural requirements.",
    ],
    warnings: ["Local demo preview shown. Start the API with NEBIUS_API_KEY to invoke Nemotron."],
    explanation: "The local preview uses the same constrained BridgeSpec that the Nemotron planner returns, so every geometry change remains editable and safe to render.",
  };
}
