import {
  corridorPolygon,
  lineFromCenter,
  lineLengthM,
  polygonAreaSqm,
  rectanglePolygon,
} from "@/lib/geo";
import { projectTypeFamily } from "@/lib/project-catalog";
import type { GeoJSONFeature, GeoJSONGeometry, ProjectType } from "@/lib/types";

export interface SiteSuggestion {
  id: string;
  label: string;
  reason: string;
  score: number;
  geometry: GeoJSONGeometry;
  kind: "boundary" | "alignment";
  building_clashes?: string[];
}

function ringFromPolygon(g: GeoJSONGeometry): [number, number][] | null {
  if (g.type !== "Polygon") return null;
  return (g.coordinates as [number, number][][])[0];
}

function nearestRoadBearing(
  lng: number,
  lat: number,
  roads: GeoJSONFeature[],
): number | null {
  let bestDist = Infinity;
  let bestBearing: number | null = null;
  for (const f of roads) {
    if (f.geometry.type !== "LineString") continue;
    const coords = f.geometry.coordinates as [number, number][];
    for (let i = 1; i < coords.length; i++) {
      const mid: [number, number] = [
        (coords[i - 1][0] + coords[i][0]) / 2,
        (coords[i - 1][1] + coords[i][1]) / 2,
      ];
      const d = Math.hypot(mid[0] - lng, mid[1] - lat);
      if (d < bestDist) {
        bestDist = d;
        const [lng1, lat1] = coords[i - 1];
        const [lng2, lat2] = coords[i];
        const dLng = lng2 - lng1;
        const dLat = lat2 - lat1;
        bestBearing = (Math.atan2(dLng, dLat) * 180) / Math.PI;
      }
    }
  }
  return bestDist < 0.02 ? bestBearing : null;
}

function scoreArea(areaSqm: number, targetMin: number, targetMax: number): number {
  if (areaSqm >= targetMin && areaSqm <= targetMax) return 92;
  if (areaSqm < targetMin) return Math.max(55, 90 - ((targetMin - areaSqm) / targetMin) * 30);
  return Math.max(50, 88 - ((areaSqm - targetMax) / targetMax) * 25);
}

export function generateSiteSuggestions(
  lng: number,
  lat: number,
  projectType: ProjectType,
  roads: GeoJSONFeature[] = [],
): SiteSuggestion[] {
  const family = projectTypeFamily(projectType);
  const roadBearing = nearestRoadBearing(lng, lat, roads);
  const alignBearings = roadBearing != null ? [roadBearing, roadBearing + 90] : [0, 90, 45];

  const suggestions: SiteSuggestion[] = [];

  if (family === "building") {
    const presets: { w: number; h: number; label: string; reason: string }[] = [
      { w: 60, h: 45, label: "Compact plot", reason: "Suitable for mid-rise massing (~2,700 m²)" },
      { w: 100, h: 80, label: "Standard campus", reason: "Typical institutional / commercial block" },
      { w: 150, h: 120, label: "Large footprint", reason: "Warehouse or multi-block development" },
    ];
    presets.forEach((p, i) => {
      const geom = rectanglePolygon(lng, lat, p.w, p.h);
      const ring = ringFromPolygon(geom)!;
      const area = polygonAreaSqm(ring.slice(0, -1));
      suggestions.push({
        id: `building-${i}`,
        label: p.label,
        reason: p.reason,
        score: scoreArea(area, 2000, 20000),
        geometry: geom,
        kind: "boundary",
      });
    });
  }

  if (family === "flyover" || family === "road") {
    const length = family === "flyover" ? 650 : 500;
    const width = family === "flyover" ? 45 : 35;
    alignBearings.forEach((bearing, i) => {
      const geom = corridorPolygon(lng, lat, length, width, bearing);
      const ring = ringFromPolygon(geom)!;
      const area = polygonAreaSqm(ring.slice(0, -1));
      const aligned = roadBearing != null && Math.abs(bearing - roadBearing) < 15;
      suggestions.push({
        id: `corridor-${i}`,
        label: aligned ? "Road-aligned corridor" : `Corridor ${Math.round(bearing)}°`,
        reason: aligned
          ? "Follows nearest mapped road — good for flyover / grade-separator study"
          : "Alternative alignment axis for comparison",
        score: aligned ? 94 : 78 - i * 3,
        geometry: geom,
        kind: "boundary",
      });
      const line = lineFromCenter(lng, lat, length, bearing);
      suggestions.push({
        id: `align-${i}`,
        label: aligned ? "Centerline (road)" : `Centerline ${Math.round(bearing)}°`,
        reason: "Use as road / flyover alignment for AI design",
        score: aligned ? 90 : 72,
        geometry: line,
        kind: "alignment",
      });
      void area;
    });
  }

  if (family === "pipeline") {
    [600, 900].forEach((length, i) => {
      const bearing = alignBearings[i] ?? 0;
      const line = lineFromCenter(lng, lat, length, bearing);
      const len = lineLengthM(line.coordinates as [number, number][]);
      suggestions.push({
        id: `pipeline-${i}`,
        label: `${length} m trench run`,
        reason: roadBearing != null && i === 0 ? "Parallel to nearest utility corridor" : "Cross-country alternative",
        score: i === 0 ? 88 : 75,
        geometry: line,
        kind: "alignment",
      });
      const buffer = corridorPolygon(lng, lat, length, 12, bearing);
      suggestions.push({
        id: `pipeline-buffer-${i}`,
        label: `Trench buffer ${length} m`,
        reason: `${len.toFixed(0)} m centerline with 12 m easement`,
        score: 80 - i * 5,
        geometry: buffer,
        kind: "boundary",
      });
    });
  }

  // Universal: site pad around pin
  suggestions.push({
    id: "pad-standard",
    label: "200 m site pad",
    reason: "General study area around map center — works for any project type",
    score: 70,
    geometry: rectanglePolygon(lng, lat, 200, 200),
    kind: "boundary",
  });

  return suggestions.sort((a, b) => b.score - a.score).slice(0, 8);
}
