import type { GeoJSONGeometry } from "./types";
import type { TerrainProvider } from "cesium";

export interface ProjectTerrainSource {
  id: number;
  state: string;
  ion_asset_id: number;
  coverage: GeoJSONGeometry;
}

function inRing(ring: number[][], lng: number, lat: number) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [x, y] = ring[i];
    const [px, py] = ring[j];
    if ((y > lat) !== (py > lat) && lng < (px - x) * (lat - y) / (py - y) + x) inside = !inside;
  }
  return inside;
}

export function terrainCoversSite(coverage: GeoJSONGeometry | null | undefined, lng: number, lat: number) {
  if (!coverage || !Number.isFinite(lng) || !Number.isFinite(lat)) return false;
  const polygons = coverage.type === "Polygon" ? [coverage.coordinates as number[][][]]
    : coverage.type === "MultiPolygon" ? coverage.coordinates as number[][][][] : [];
  return polygons.some((rings) => rings.length > 0 && inRing(rings[0], lng, lat) && !rings.slice(1).some((ring) => inRing(ring, lng, lat)));
}

/** Prefer the active site dataset, then world terrain. Never substitute invented heights. */
export async function resolveAutomaticTerrain(options: {
  project: ProjectTerrainSource | null;
  longitude: number;
  latitude: number;
  load: (assetId: number) => Promise<TerrainProvider>;
}) {
  const { project, longitude, latitude, load } = options;
  let fallback: string | null = null;
  if (project) {
    if (project.state !== "READY" || !project.ion_asset_id) fallback = "Project terrain is not ready.";
    else if (!terrainCoversSite(project.coverage, longitude, latitude)) fallback = "Site is outside project terrain coverage.";
    else {
      try {
        return { provider: await load(project.ion_asset_id), source: "project" as const, version: project.id, fallback: null };
      } catch { fallback = "Project terrain could not load; using world terrain."; }
    }
  }
  return { provider: await load(1), source: "world" as const, version: null, fallback };
}
