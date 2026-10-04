import type { LineString, Point, Polygon, Position } from "geojson";
import type { GeoJSONGeometry, ProjectType } from "@/lib/types";

export type PreviewStage =
  | "idle"
  | "queued"
  | "analyzing"
  | "layout"
  | "quantities"
  | "finalizing"
  | "completed"
  | "failed";

export interface PreviewSiteContext {
  boundary: GeoJSONGeometry | null;
  alignment: GeoJSONGeometry | null;
  center: [number, number];
  projectType: ProjectType;
  projectId: number;
}

export interface PreviewLayoutGeometry {
  boundaryRing: Position[] | null;
  siteHighlight: Polygon | null;
  scanLine: LineString | null;
  roads: LineString[];
  blocks: Polygon[];
  flyoverDeck: LineString | null;
  piers: Point[];
  buildings: Polygon[];
  labelAnchors: { position: Position; text: string }[];
}

function seeded(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function ringFromGeometry(geometry: GeoJSONGeometry | null): Position[] | null {
  if (!geometry) return null;
  if (geometry.type === "Polygon") {
    const coords = geometry.coordinates as Position[][];
    return coords[0] ?? null;
  }
  if (geometry.type === "MultiPolygon") {
    const coords = geometry.coordinates as Position[][][];
    return coords[0]?.[0] ?? null;
  }
  return null;
}

function centroid(ring: Position[]): [number, number] {
  if (!ring.length) return [0, 0];
  let lng = 0;
  let lat = 0;
  for (const [x, y] of ring) {
    lng += x;
    lat += y;
  }
  return [lng / ring.length, lat / ring.length];
}

function bbox(ring: Position[]) {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;
  for (const [lng, lat] of ring) {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  }
  return { minLng, minLat, maxLng, maxLat, width: maxLng - minLng, height: maxLat - minLat };
}

function defaultSiteRing(center: [number, number], meters = 220): Position[] {
  const dLng = meters / 111320 / Math.cos((center[1] * Math.PI) / 180);
  const dLat = meters / 110540;
  return [
    [center[0] - dLng, center[1] - dLat],
    [center[0] + dLng, center[1] - dLat],
    [center[0] + dLng, center[1] + dLat],
    [center[0] - dLng, center[1] + dLat],
    [center[0] - dLng, center[1] - dLat],
  ];
}

function lineFromAlignment(alignment: GeoJSONGeometry | null, ring: Position[], rnd: () => number): LineString {
  if (alignment?.type === "LineString") {
    const coords = alignment.coordinates as Position[];
    if (coords.length >= 2) {
      return { type: "LineString", coordinates: coords };
    }
  }
  const box = bbox(ring);
  const [cx, cy] = centroid(ring);
  const angle = rnd() * Math.PI;
  const len = Math.min(box.width, box.height) * 0.75;
  const dx = (Math.cos(angle) * len) / 2;
  const dy = (Math.sin(angle) * len) / 2;
  return {
    type: "LineString",
    coordinates: [
      [cx - dx, cy - dy],
      [cx - dx * 0.35, cy - dy * 0.35],
      [cx, cy],
      [cx + dx * 0.35, cy + dy * 0.35],
      [cx + dx, cy + dy],
    ],
  };
}

function rectPolygon(cx: number, cy: number, w: number, h: number, angle = 0): Polygon {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const corners: Position[] = [
    [-w / 2, -h / 2],
    [w / 2, -h / 2],
    [w / 2, h / 2],
    [-w / 2, h / 2],
    [-w / 2, -h / 2],
  ].map(([x, y]) => [cx + x * cos - y * sin, cy + x * sin + y * cos]);
  return { type: "Polygon", coordinates: [corners] };
}

export function buildPreviewLayout(ctx: PreviewSiteContext): PreviewLayoutGeometry {
  const ring =
    ringFromGeometry(ctx.boundary) ??
    (ctx.alignment?.type === "LineString"
      ? defaultSiteRing(centroid(ctx.alignment.coordinates as Position[]), 180)
      : defaultSiteRing(ctx.center, 220));

  const rnd = seeded(ctx.projectId * 9973 + Math.round((ring[0]?.[0] ?? 0) * 1e5));
  const box = bbox(ring);
  const [cx, cy] = centroid(ring);
  const flyover = lineFromAlignment(ctx.alignment, ring, rnd);

  const roads: LineString[] = [];
  const blocks: Polygon[] = [];
  const buildings: Polygon[] = [];
  const piers: Point[] = [];

  const roadCount = ctx.projectType === "road" ? 4 : 2;
  for (let i = 0; i < roadCount; i += 1) {
    const t = (i + 1) / (roadCount + 1);
    const lat = box.minLat + box.height * t;
    roads.push({
      type: "LineString",
      coordinates: [
        [box.minLng + box.width * 0.08, lat],
        [box.minLng + box.width * 0.92, lat],
      ],
    });
  }

  if (ctx.projectType === "building" || ctx.projectType === "flyover") {
    for (let i = 0; i < 3; i += 1) {
      const bx = box.minLng + box.width * (0.2 + rnd() * 0.55);
      const by = box.minLat + box.height * (0.15 + rnd() * 0.55);
      const w = box.width * (0.08 + rnd() * 0.12);
      const h = box.height * (0.08 + rnd() * 0.12);
      buildings.push(rectPolygon(bx, by, w, h, rnd() * Math.PI));
    }
  }

  if (ctx.projectType === "flyover" || ctx.projectType === "road") {
    const coords = flyover.coordinates;
    for (let i = 1; i < coords.length - 1; i += 1) {
      piers.push({ type: "Point", coordinates: coords[i] });
    }
    blocks.push(
      rectPolygon(cx, cy, box.width * 0.22, box.height * 0.14, rnd() * 0.4),
    );
  }

  if (ctx.projectType === "pipeline") {
    roads.push(flyover);
  }

  const labelAnchors = [
    { position: [cx, cy + box.height * 0.18] as Position, text: "Calculating earthwork" },
    { position: [cx - box.width * 0.15, cy] as Position, text: "Estimating concrete" },
    { position: [cx + box.width * 0.15, cy] as Position, text: "Estimating steel" },
  ];

  return {
    boundaryRing: ring,
    siteHighlight: { type: "Polygon", coordinates: [ring] },
    scanLine: {
      type: "LineString",
      coordinates: [
        [box.minLng, box.minLat],
        [box.maxLng, box.maxLat],
      ],
    },
    roads,
    blocks,
    flyoverDeck: ctx.projectType === "flyover" || ctx.projectType === "road" ? flyover : null,
    piers,
    buildings,
    labelAnchors,
  };
}

export function scanLineAtProgress(ring: Position[], progress: number): LineString {
  const box = bbox(ring);
  const y = box.minLat + box.height * progress;
  return {
    type: "LineString",
    coordinates: [
      [box.minLng, y],
      [box.maxLng, y],
    ],
  };
}

export function stageFromJob(
  status: "queued" | "running" | "completed" | "failed" | undefined,
  runningElapsedMs: number,
): PreviewStage {
  if (!status || status === "completed") return status === "completed" ? "completed" : "idle";
  if (status === "failed") return "failed";
  if (status === "queued") return "queued";
  if (runningElapsedMs < 3500) return "analyzing";
  if (runningElapsedMs < 9000) return "layout";
  if (runningElapsedMs < 14000) return "quantities";
  return "finalizing";
}

export function stageLabel(stage: PreviewStage): string {
  switch (stage) {
    case "queued":
      return "Queued";
    case "analyzing":
      return "Analyzing site";
    case "layout":
      return "Generating 3D layout";
    case "quantities":
      return "Calculating BOQ";
    case "finalizing":
      return "Finalizing";
    case "completed":
      return "Complete";
    case "failed":
      return "Failed";
    default:
      return "Idle";
  }
}

export function stageMapLabel(stage: PreviewStage): string {
  switch (stage) {
    case "queued":
      return "Preparing generation…";
    case "analyzing":
      return "Reading site geometry";
    case "layout":
      return "Generating 3D layout";
    case "quantities":
      return "Estimating quantities";
    case "finalizing":
      return "Finalizing design";
    default:
      return "";
  }
}
