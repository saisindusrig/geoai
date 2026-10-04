import type maplibregl from "maplibre-gl";
import { mapboxToken } from "@/lib/map/providers";

const TERRAIN_SOURCE_ID = "geoai-mapbox-dem";

export function terrainAvailable() {
  return Boolean(mapboxToken());
}

export function ensureTerrainSource(map: maplibregl.Map) {
  const token = mapboxToken();
  if (!token || map.getSource(TERRAIN_SOURCE_ID)) return Boolean(token);
  map.addSource(TERRAIN_SOURCE_ID, {
    type: "raster-dem",
    url: `mapbox://mapbox.mapbox-terrain-dem-v1?access_token=${token}`,
    tileSize: 512,
    maxzoom: 14,
  });
  return true;
}

export function setTerrainEnabled(map: maplibregl.Map, enabled: boolean, exaggeration = 1) {
  if (!enabled) {
    map.setTerrain(null);
    return { ok: true, message: null };
  }
  if (!ensureTerrainSource(map)) {
    return { ok: false, message: "Terrain requires NEXT_PUBLIC_MAPBOX_TOKEN." };
  }
  map.setTerrain({ source: TERRAIN_SOURCE_ID, exaggeration });
  return { ok: true, message: null };
}
