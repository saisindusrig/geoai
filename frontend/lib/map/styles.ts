import type { StyleSpecification } from "maplibre-gl";
import type { WorkspaceMapStyle } from "@/components/map/mapTypes";
import { mapboxToken } from "@/lib/map/providers";

const CARTO_DARK =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const OSM_RASTER: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
      maxzoom: 19,
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

function mapboxStyle(style: string) {
  const token = mapboxToken();
  return token ? `https://api.mapbox.com/styles/v1/mapbox/${style}?access_token=${token}` : null;
}

export function resolveMapStyle(style: WorkspaceMapStyle): string | StyleSpecification {
  if (style === "dark") return CARTO_DARK;
  if (style === "streets") return mapboxStyle("streets-v12") ?? OSM_RASTER;
  if (style === "satellite") return mapboxStyle("satellite-v9") ?? OSM_RASTER;
  if (style === "hybrid") return mapboxStyle("satellite-streets-v12") ?? OSM_RASTER;
  return CARTO_DARK;
}

export function styleProviderLabel(style: WorkspaceMapStyle) {
  if (style === "dark") return "Carto dark";
  if (mapboxToken()) return `Mapbox ${style}`;
  return "OSM fallback";
}
