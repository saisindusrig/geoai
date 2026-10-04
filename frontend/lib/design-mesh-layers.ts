import type { GeometrySpec, GeometrySpecObject } from "@/lib/types";

export interface DesignMeshLayerGroup {
  id: string;
  label: string;
  meshCount: number;
  meshes: { name: string; kind: string }[];
}

/** Display order for known generator layer ids (unknown layers sort alphabetically after). */
const LAYER_ORDER = [
  "deck",
  "asphalt",
  "barrier",
  "road_marking",
  "shoulder",
  "piers",
  "pier_caps",
  "column",
  "slab",
  "core",
  "facade",
  "foundation",
  "concrete",
  "steel",
  "pipe_water",
  "pipe_drain",
  "manhole",
  "bedding",
  "backfill",
  "excavation",
];

const LAYER_LABELS: Record<string, string> = {
  deck: "Bridge deck",
  asphalt: "Road surface",
  barrier: "Crash barriers",
  road_marking: "Road markings",
  shoulder: "Shoulders",
  piers: "Piers",
  pier_caps: "Pier caps",
  foundation: "Foundations",
  excavation: "Excavation volume",
  slab: "Floor slabs",
  column: "Columns",
  core: "Core / stairs",
  facade: "Facade envelope",
  concrete: "Concrete",
  steel: "Reinforcement",
  pipe_water: "Water main",
  pipe_drain: "Drainage pipe",
  manhole: "Manholes",
  bedding: "Pipe bedding",
  backfill: "Backfill",
};

const IS_DEV = process.env.NODE_ENV === "development";

function devWarn(message: string, error?: unknown) {
  if (IS_DEV) {
    console.warn(`[design-mesh-layers] ${message}`, error ?? "");
  }
}

function layerLabel(id: string): string {
  if (LAYER_LABELS[id]) return LAYER_LABELS[id];
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function layerSortIndex(id: string): number {
  const idx = LAYER_ORDER.indexOf(id);
  return idx === -1 ? 1000 : idx;
}

export function extractDesignMeshLayers(spec?: GeometrySpec | null): DesignMeshLayerGroup[] {
  if (!spec?.objects?.length) return [];

  const byLayer = new Map<string, GeometrySpecObject[]>();
  for (const obj of spec.objects) {
    const layer = obj.layer || "misc";
    const list = byLayer.get(layer) ?? [];
    list.push(obj);
    byLayer.set(layer, list);
  }

  return [...byLayer.entries()]
    .map(([id, objects]) => ({
      id,
      label: layerLabel(id),
      meshCount: objects.length,
      meshes: objects.map((o) => ({ name: o.name, kind: o.kind })),
    }))
    .sort((a, b) => layerSortIndex(a.id) - layerSortIndex(b.id) || a.label.localeCompare(b.label));
}

export function designMeshNodeName(obj: { layer: string; name: string }) {
  return `${obj.layer}/${obj.name}`;
}

/** Minimal Cesium Model surface used for mesh visibility (CesiumJS 1.142). */
export type CesiumModel = {
  getNode?: (name: string) => { show: boolean } | undefined;
  ready?: boolean;
  readyEvent?: {
    addEventListener: (listener: () => void) => () => void;
    numberOfListeners?: number;
  };
  readyPromise?: Promise<unknown>;
  isDestroyed?: () => boolean;
};

type MeshCatalogEntry = { layer: string; name: string };

type PendingMeshVisibility = {
  catalog: MeshCatalogEntry[];
  visibility: Record<string, boolean>;
};

const pendingByModel = new WeakMap<CesiumModel, PendingMeshVisibility>();
const generationByModel = new WeakMap<CesiumModel, number>();

function modelIsUsable(model: CesiumModel | null | undefined): model is CesiumModel {
  if (!model?.getNode) return false;
  try {
    if (model.isDestroyed?.()) return false;
  } catch {
    return false;
  }
  return true;
}

function isModelReady(model: CesiumModel): boolean {
  return model.ready === true;
}

/** Wait until Cesium marks the model ready (readyPromise / readyEvent / ready flag). */
export async function waitForCesiumModelReady(model: CesiumModel): Promise<boolean> {
  if (!modelIsUsable(model)) return false;
  if (isModelReady(model)) return true;

  try {
    if (model.readyPromise) {
      await model.readyPromise;
    } else if (model.readyEvent?.addEventListener) {
      await new Promise<void>((resolve) => {
        if (!modelIsUsable(model)) {
          resolve();
          return;
        }
        if (isModelReady(model)) {
          resolve();
          return;
        }
        const cleanupRef: { current?: () => void } = {};
        const onReady = () => {
          cleanupRef.current?.();
          resolve();
        };
        cleanupRef.current = model.readyEvent!.addEventListener(onReady);
      });
    } else {
      devWarn("Model has no readyPromise/readyEvent; skipping mesh visibility until ready flag is true");
      return false;
    }
  } catch (error) {
    devWarn("Model failed to load before mesh visibility could be applied", error);
    return false;
  }

  if (!modelIsUsable(model)) {
    devWarn("Model was destroyed before mesh visibility could be applied");
    return false;
  }

  if (!isModelReady(model)) {
    devWarn("Model finished loading but ready flag is still false; skipping getNode calls");
    return false;
  }

  return true;
}

/**
 * Apply visibility toggles to loaded Cesium Model nodes (GLB node names = layer/mesh).
 * Never throws — skips when the model is not ready.
 */
export function applyDesignMeshVisibilityToModel(
  model: CesiumModel | null | undefined,
  catalog: MeshCatalogEntry[],
  visibility: Record<string, boolean>,
): void {
  if (!modelIsUsable(model) || !catalog.length) return;
  if (!isModelReady(model)) return;

  for (const obj of catalog) {
    try {
      const node = model.getNode!(designMeshNodeName(obj));
      if (node) node.show = visibility[obj.layer] !== false;
    } catch (error) {
      devWarn(`Could not set visibility for node ${designMeshNodeName(obj)}`, error);
    }
  }
}

/**
 * Schedule mesh visibility when the model is ready.
 * Stores the latest catalog + visibility so toggles during load apply the most recent state.
 */
export function applyDesignMeshVisibilityWhenReady(
  model: CesiumModel | null | undefined,
  catalog: MeshCatalogEntry[],
  visibility: Record<string, boolean>,
): void {
  if (!modelIsUsable(model) || !catalog.length) return;

  pendingByModel.set(model, { catalog, visibility });
  const generation = (generationByModel.get(model) ?? 0) + 1;
  generationByModel.set(model, generation);

  if (isModelReady(model)) {
    applyDesignMeshVisibilityToModel(model, catalog, visibility);
    return;
  }

  void (async () => {
    const ready = await waitForCesiumModelReady(model);
    if (!ready || !modelIsUsable(model)) return;
    if (generationByModel.get(model) !== generation) return;

    const pending = pendingByModel.get(model);
    if (!pending) return;

    applyDesignMeshVisibilityToModel(model, pending.catalog, pending.visibility);
  })();
}

/** @deprecated Use applyDesignMeshVisibilityWhenReady — same behavior. */
export async function applyDesignMeshVisibilityWhenReadyAsync(
  model: CesiumModel | null | undefined,
  catalog: MeshCatalogEntry[],
  visibility: Record<string, boolean>,
): Promise<void> {
  applyDesignMeshVisibilityWhenReady(model, catalog, visibility);
  if (!modelIsUsable(model) || !catalog.length) return;
  if (isModelReady(model)) return;
  await waitForCesiumModelReady(model);
  const pending = pendingByModel.get(model);
  if (pending && modelIsUsable(model) && isModelReady(model)) {
    applyDesignMeshVisibilityToModel(model, pending.catalog, pending.visibility);
  }
}
