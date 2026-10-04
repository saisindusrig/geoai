import { GeoJsonLayer } from "@deck.gl/layers";
import type { WorkspaceFeatureCollection } from "@/components/map/mapTypes";

export function drawnGeoJsonLayer(data: WorkspaceFeatureCollection, selectedId?: string | null) {
  return new GeoJsonLayer({
    id: "geoai-drawn-features",
    data,
    pickable: true,
    stroked: true,
    filled: true,
    extruded: false,
    lineWidthMinPixels: 2,
    pointRadiusMinPixels: 5,
    getFillColor: (feature) => {
      const kind = feature.properties?.kind;
      if (kind === "project-boundary" || kind === "area" || kind === "rectangle") return [34, 211, 238, 36];
      return [59, 130, 246, 80];
    },
    getLineColor: (feature) => {
      if (feature.properties?.id === selectedId) return [34, 211, 238, 255];
      const kind = feature.properties?.kind;
      if (kind === "road" || kind === "project-alignment") return [59, 130, 246, 255];
      return [34, 211, 238, 230];
    },
    getPointRadius: 8,
    getLineWidth: (feature) => (feature.properties?.id === selectedId ? 7 : 4),
  });
}

export function aiPlaceholderLayer(data: WorkspaceFeatureCollection) {
  return new GeoJsonLayer({
    id: "geoai-ai-placeholder-3d",
    data,
    pickable: false,
    stroked: true,
    filled: true,
    extruded: true,
    elevationScale: 1,
    getElevation: (feature) => {
      const kind = feature.properties?.kind;
      if (kind === "project-alignment") return 18;
      if (kind === "road") return 10;
      if (kind === "area" || kind === "rectangle" || kind === "project-boundary") return 3;
      return 0;
    },
    getFillColor: (feature) => {
      const kind = feature.properties?.kind;
      if (kind === "project-alignment" || kind === "road") return [59, 130, 246, 180];
      return [34, 211, 238, 70];
    },
    getLineColor: [34, 211, 238, 240],
    getLineWidth: 6,
    lineWidthMinPixels: 3,
  });
}
