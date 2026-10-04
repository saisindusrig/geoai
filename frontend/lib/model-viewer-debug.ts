import type { ModelUrlSource } from "@/lib/model-url-resolution";
import type { WorkspaceMapEngineChoice } from "@/lib/map/workspace-engine";

export interface ModelViewerDebugState {
  scenarioId: number | null;
  modelUrl: string | null;
  modelSource: ModelUrlSource;
  mapEngine: WorkspaceMapEngineChoice;
  projectModelLayerEnabled: boolean;
  generating?: boolean;
}

/** Dev-only concise logging for model viewer diagnostics. */
export function logModelViewerState(state: ModelViewerDebugState): void {
  if (process.env.NODE_ENV !== "development") return;
  console.debug("[sitegeoai model viewer]", {
    scenarioId: state.scenarioId,
    modelSource: state.modelSource ?? "none",
    modelUrl: state.modelUrl ? truncateUrl(state.modelUrl) : null,
    mapEngine: state.mapEngine,
    projectModelLayer: state.projectModelLayerEnabled ? "on" : "off",
    generating: state.generating ?? false,
  });
}

function truncateUrl(url: string, max = 72): string {
  if (url.length <= max) return url;
  return `${url.slice(0, max - 3)}...`;
}
