import type { ProviderStatus } from "@/components/map/mapTypes";

export function getMapEngine(): "maplibre" | "cesium" {
  const raw = process.env.NEXT_PUBLIC_MAP_ENGINE?.toLowerCase();
  return raw === "cesium" ? "cesium" : "maplibre";
}

export function getProviderStatus(): ProviderStatus {
  const mapEngine = getMapEngine();
  const mapboxToken = Boolean(process.env.NEXT_PUBLIC_MAPBOX_TOKEN);
  const googleMapsKey = Boolean(process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY);
  const warnings: string[] = [];

  if (!mapboxToken) {
    warnings.push("Mapbox token missing: using free OpenStreetMap/Carto basemap fallback.");
  }
  if (!googleMapsKey) {
    warnings.push("Google Maps key missing: Photorealistic 3D Tiles disabled.");
  }

  return {
    mapEngine,
    mapboxToken,
    googleMapsKey,
    terrainAvailable: mapboxToken,
    warnings,
  };
}

export function googleMapsApiKey() {
  return process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";
}

export function mapboxToken() {
  return process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";
}
