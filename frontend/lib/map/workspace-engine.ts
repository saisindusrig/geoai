import { getMapEngine } from "@/lib/map/providers";

export type WorkspaceMapEngineChoice = "cesium" | "maplibre";

/**
 * Workspace viewer selection:
 * - `NEXT_PUBLIC_MAP_ENGINE=cesium` → always Cesium
 * - completed GLB exists → Cesium for reliable mesh viewing
 * - otherwise → MapLibre for drawing/planning
 */
export function resolveWorkspaceMapEngine(
  hasCompletedGlb: boolean,
  configuredEngine: "maplibre" | "cesium" = getMapEngine(),
): WorkspaceMapEngineChoice {
  if (configuredEngine === "cesium") return "cesium";
  if (hasCompletedGlb) return "cesium";
  return "maplibre";
}

export function shouldUseCesiumWorkspace(
  hasCompletedGlb: boolean,
  configuredEngine: "maplibre" | "cesium" = getMapEngine(),
): boolean {
  return resolveWorkspaceMapEngine(hasCompletedGlb, configuredEngine) === "cesium";
}
