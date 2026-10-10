import type { GeoJSONFeature, GeoJSONGeometry } from "@/lib/types";
import { haversineM } from "@/lib/geo";

const R = 6371000;
const rad = (d: number) => (d * Math.PI) / 180;

export type ToolHint = "flyover" | "pipeline" | "building" | "terrain" | null;

export function geometryToVertices(g: GeoJSONGeometry | null | undefined): [number, number][] {
  if (!g) return [];
  if (g.type === "LineString") {
    return [...(g.coordinates as [number, number][])];
  }
  if (g.type === "Polygon") {
    const ring = (g.coordinates as [number, number][][])[0] ?? [];
    if (ring.length > 1 && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1]) {
      return ring.slice(0, -1);
    }
    return [...ring];
  }
  return [];
}

export function verticesToPolygon(vertices: [number, number][]): GeoJSONGeometry {
  return { type: "Polygon", coordinates: [[...vertices, vertices[0]]] };
}

export function verticesToLine(vertices: [number, number][]): GeoJSONGeometry {
  return { type: "LineString", coordinates: vertices };
}

/** Draw a smooth Catmull–Rom curve through the alignment's placed control points. */
export function verticesToSmoothLine(vertices: [number, number][], samplesPerSegment = 8): GeoJSONGeometry {
  if (vertices.length < 3) return verticesToLine(vertices);
  const points: [number, number][] = [];
  for (let segment = 0; segment < vertices.length - 1; segment++) {
    const p0 = vertices[Math.max(0, segment - 1)];
    const p1 = vertices[segment];
    const p2 = vertices[segment + 1];
    const p3 = vertices[Math.min(vertices.length - 1, segment + 2)];
    for (let sample = 0; sample < samplesPerSegment; sample++) {
      const t = sample / samplesPerSegment;
      const t2 = t * t;
      const t3 = t2 * t;
      points.push([0, 1].map(axis => 0.5 * (
        2 * p1[axis] + (-p0[axis] + p2[axis]) * t +
        (2 * p0[axis] - 5 * p1[axis] + 4 * p2[axis] - p3[axis]) * t2 +
        (-p0[axis] + 3 * p1[axis] - 3 * p2[axis] + p3[axis]) * t3
      )) as [number, number]);
    }
  }
  points.push(vertices.at(-1)!);
  return verticesToLine(points);
}

/** Rectangle from two opposite corners. */
export function rectangleFromCorners(a: [number, number], b: [number, number]): GeoJSONGeometry {
  const ring: [number, number][] = [
    [a[0], a[1]],
    [b[0], a[1]],
    [b[0], b[1]],
    [a[0], b[1]],
    [a[0], a[1]],
  ];
  return { type: "Polygon", coordinates: [ring] };
}

/** Buffer a polyline into a corridor polygon (half-width in meters). */
export function corridorFromLine(coords: [number, number][], widthM: number): GeoJSONGeometry | null {
  if (coords.length < 2 || widthM <= 0) return null;
  const half = widthM / 2;
  const left: [number, number][] = [];
  const right: [number, number][] = [];

  for (let i = 0; i < coords.length; i++) {
    const prev = coords[Math.max(0, i - 1)];
    const next = coords[Math.min(coords.length - 1, i + 1)];
    const [lng, lat] = coords[i];
    const dLng = next[0] - prev[0];
    const dLat = next[1] - prev[1];
    const len = Math.hypot(dLng, dLat) || 1;
    const perpLng = -dLat / len;
    const perpLat = dLng / len;
    const cosLat = Math.cos(rad(lat));
    const eastL = (half * perpLng) / (R * cosLat);
    const northL = (half * perpLat) / R;
    const eastR = (-half * perpLng) / (R * cosLat);
    const northR = (-half * perpLat) / R;
    left.push([lng + (eastL * 180) / Math.PI, lat + (northL * 180) / Math.PI]);
    right.push([lng + (eastR * 180) / Math.PI, lat + (northR * 180) / Math.PI]);
  }

  const ring = [...left, ...right.reverse(), left[0]];
  return { type: "Polygon", coordinates: [ring] };
}

/** Nearest point on segment ab to point p; returns [point, distanceM]. */
export function nearestPointOnSegment(
  p: [number, number],
  a: [number, number],
  b: [number, number],
): [[number, number], number] {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return [a, haversineM(p, a)];
  let t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  const q: [number, number] = [a[0] + t * dx, a[1] + t * dy];
  return [q, haversineM(p, q)];
}

export function snapPointToFeatures(
  lngLat: [number, number],
  features: GeoJSONFeature[],
  maxDistM: number,
): [number, number] {
  let best: [number, number] = lngLat;
  let bestDist = maxDistM;

  for (const f of features) {
    const g = f.geometry;
    if (g.type === "LineString") {
      const coords = g.coordinates as [number, number][];
      for (let i = 1; i < coords.length; i++) {
        const [q, d] = nearestPointOnSegment(lngLat, coords[i - 1], coords[i]);
        if (d < bestDist) {
          bestDist = d;
          best = q;
        }
      }
    } else if (g.type === "Point") {
      const c = g.coordinates as [number, number];
      const d = haversineM(lngLat, c);
      if (d < bestDist) {
        bestDist = d;
        best = c;
      }
    } else if (g.type === "Polygon") {
      const ring = (g.coordinates as [number, number][][])[0] ?? [];
      for (const c of ring) {
        const d = haversineM(lngLat, c);
        if (d < bestDist) {
          bestDist = d;
          best = c;
        }
      }
      for (let i = 1; i < ring.length; i++) {
        const [q, d] = nearestPointOnSegment(lngLat, ring[i - 1], ring[i]);
        if (d < bestDist) {
          bestDist = d;
          best = q;
        }
      }
    }
  }
  return best;
}

export function defaultCorridorWidth(projectType: string, toolHint: ToolHint): number {
  if (toolHint === "pipeline") return 20;
  if (toolHint === "flyover") return 16;
  if (projectType === "pipeline") return 20;
  if (projectType === "road") return 24;
  if (projectType === "flyover") return 16;
  return 30;
}

export function defaultRectangleSize(projectType: string): { w: number; h: number } {
  if (projectType === "building") return { w: 45, h: 45 };
  return { w: 80, h: 60 };
}

export function parseKmlToGeometry(text: string): GeoJSONGeometry | null {
  try {
    const doc = new DOMParser().parseFromString(text, "text/xml");
    const coordsEl =
      doc.querySelector("Polygon coordinates") ??
      doc.querySelector("LineString coordinates") ??
      doc.querySelector("coordinates");
    if (!coordsEl?.textContent) return null;
    const pairs = coordsEl.textContent
      .trim()
      .split(/\s+/)
      .map((s) => s.split(",").map(Number))
      .filter((a) => a.length >= 2 && !Number.isNaN(a[0]) && !Number.isNaN(a[1]));
    if (pairs.length < 2) return null;
    const coords = pairs.map(([lng, lat]) => [lng, lat] as [number, number]);
    const isPolygon = !!doc.querySelector("Polygon");
    if (isPolygon && coords.length >= 3) {
      const ring = coords[0][0] === coords[coords.length - 1][0] ? coords : [...coords, coords[0]];
      return { type: "Polygon", coordinates: [ring] };
    }
    return { type: "LineString", coordinates: coords };
  } catch {
    return null;
  }
}

export function downloadGeoJson(filename: string, geometry: GeoJSONGeometry) {
  const fc = { type: "FeatureCollection" as const, features: [{ type: "Feature" as const, geometry, properties: {} }] };
  const blob = new Blob([JSON.stringify(fc, null, 2)], { type: "application/geo+json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function toolInstruction(tool: string): string {
  switch (tool) {
    case "select":
      return "Pan map · Click buildings to use as boundary";
    case "suggest-site":
      return "Click map to generate AI site suggestions";
    case "draw-polygon":
      return "Click corners · Enter or double-click to finish · Esc cancel · Backspace undo";
    case "draw-line":
    case "draw-corridor":
      return "Click path points · Enter or double-click to finish · Esc cancel · Backspace undo";
    case "draw-rectangle":
      return "Click first corner, then opposite corner";
    case "measure-distance":
      return "Click two or more points · Esc to clear";
    case "measure-area":
      return "Click polygon corners · Enter to measure · Esc to clear";
    case "edit-boundary":
    case "edit-alignment":
      return "Drag vertices · Drag midpoint to add · Alt-click vertex to remove · Save or Revert in sidebar";
    default:
      return "";
  }
}
