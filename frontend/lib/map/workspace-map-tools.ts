import type { MapTool } from "@/stores/projectStore";

/** Tools that only MapView (2D MapLibre) implements — not CesiumView. */
const MAPLIBRE_ONLY_TOOLS: MapTool[] = [
  "draw-polygon",
  "draw-line",
  "draw-rectangle",
  "draw-corridor",
  "measure-distance",
  "measure-area",
  "suggest-site",
  "edit-boundary",
  "edit-alignment",
];

export function toolRequires2dMap(tool: MapTool): boolean {
  return MAPLIBRE_ONLY_TOOLS.includes(tool);
}
