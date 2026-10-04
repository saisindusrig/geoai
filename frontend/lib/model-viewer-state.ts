import type { Scene3DLayerKey } from "@/lib/cesium-scene";
import type { LayerVisibility } from "@/stores/projectStore";

export type ProjectTypeFamily = "flyover" | "road" | "building" | "pipeline" | "other";

export function projectTypeFamily(projectType: string): ProjectTypeFamily {
  const t = projectType.toLowerCase();
  if (t.includes("flyover") || t.includes("bridge")) return "flyover";
  if (t.includes("road") || t.includes("highway")) return "road";
  if (t.includes("building") || t.includes("tower")) return "building";
  if (t.includes("pipeline") || t.includes("pipe")) return "pipeline";
  return "other";
}

/** Scene3D layer keys to enable when a model loads for this project type. */
export function scene3dLayersForProjectType(projectType: string): Partial<Record<Scene3DLayerKey, boolean>> {
  switch (projectTypeFamily(projectType)) {
    case "flyover":
      return { flyover: true, bridge: true, excavation: true, construction: true };
    case "road":
      return { roads: true, excavation: true, construction: true };
    case "building":
      return { buildings: true, excavation: true, construction: true };
    case "pipeline":
      return { pipeline: true, drainage: true, excavation: true };
    default:
      return { flyover: true, excavation: true, construction: true };
  }
}

export function layerVisibilityForModel(): Partial<LayerVisibility> {
  return { projectModel: true, excavation: true };
}

export interface ModelLayerEnableState {
  layers: Partial<LayerVisibility>;
  scene3dLayers: Partial<Record<Scene3DLayerKey, boolean>>;
  projectModelEnabled: boolean;
}

/** Defaults applied when a model URL is available — no manual layer toggling required. */
export function modelLayerEnableState(projectType: string, hasModelUrl: boolean): ModelLayerEnableState {
  if (!hasModelUrl) {
    return {
      layers: {},
      scene3dLayers: {},
      projectModelEnabled: false,
    };
  }
  return {
    layers: layerVisibilityForModel(),
    scene3dLayers: scene3dLayersForProjectType(projectType),
    projectModelEnabled: true,
  };
}
