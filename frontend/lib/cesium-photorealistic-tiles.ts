/**
 * Cesium ion OSM building tiles for the engineering workspace.
 */

import { cesiumDevLog, applyIonOsmBuildingTileStyle } from "@/lib/cesium-scene";
import type { MapRuntimeConfig, TileProvidersResponse } from "@/lib/map-imagery";

/** Cesium Ion global OSM 3D buildings (fallback when Google is unavailable). */
export const CESIUM_ION_OSM_BUILDINGS_ASSET_ID = 96188;

export type PhotorealisticTileProvider = "ion-osm" | null;

export interface PhotorealisticTileState {
  google: unknown | null;
  ion: unknown | null;
  activeProvider: PhotorealisticTileProvider;
  loadGeneration: number;
}

export function createPhotorealisticTileState(): PhotorealisticTileState {
  return {
    google: null,
    ion: null,
    activeProvider: null,
    loadGeneration: 0,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function destroyTileset(viewer: any, tileset: any | null) {
  if (!tileset) return;
  try {
    tileset.show = false;
    viewer?.scene?.primitives?.remove(tileset);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(tileset as any).isDestroyed?.()) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (tileset as any).destroy?.();
    }
  } catch {
    /* viewer shutting down */
  }
}

/** Remove all managed photorealistic tilesets from the scene. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function destroyPhotorealisticTiles(viewer: any, state: PhotorealisticTileState, reason?: string) {
  destroyTileset(viewer, state.google);
  destroyTileset(viewer, state.ion);
  if (reason) {
    cesiumDevLog("tiles-google", `Photorealistic 3D tiles destroyed (${reason})`);
  }
  viewer?.scene?.requestRender?.();
  return createPhotorealisticTileState();
}

/** Apply quality defaults — never force white/debug colors on photorealistic tiles. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function configurePhotorealisticTileset(tileset: any) {
  tileset.show = true;
  tileset.maximumScreenSpaceError = 8;
  tileset.dynamicScreenSpaceError = true;
}

export interface SyncPhotorealisticTilesParams {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  viewer: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Cesium: any;
  enabled: boolean;
  state: PhotorealisticTileState;
  providers?: TileProvidersResponse;
  runtime: Pick<MapRuntimeConfig, "google_maps_api_key" | "cesium_ion_token">;
  isCurrent?: () => boolean;
  onStatus?: (status: "READY" | "MISSING_TOKEN" | "FAILED") => void;
}

/**
 * Rebuild photorealistic 3D tiles from scratch when enabled.
 * Returns updated state; stale async loads are ignored via loadGeneration.
 */
export async function syncPhotorealisticTiles({
  viewer,
  Cesium,
  enabled,
  state,
  runtime,
  isCurrent = () => true,
  onStatus,
}: SyncPhotorealisticTilesParams): Promise<PhotorealisticTileState> {
  const nextGeneration = state.loadGeneration + 1;

  if (!enabled || viewer.isDestroyed?.()) {
    destroyPhotorealisticTiles(viewer, state, enabled ? "viewer destroyed" : "disabled");
    return { ...createPhotorealisticTileState(), loadGeneration: nextGeneration };
  }

  // Full rebuild — destroy any previous tilesets before loading fresh ones.
  destroyPhotorealisticTiles(viewer, state);
  const working: PhotorealisticTileState = {
    google: null,
    ion: null,
    activeProvider: null,
    loadGeneration: nextGeneration,
  };

  const stillEnabled = () => isCurrent() && !viewer.isDestroyed?.();

  // --- Cesium ion OSM 3D buildings ---
  const ionToken = runtime.cesium_ion_token;
  if (stillEnabled() && ionToken) {
    try {
      const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(CESIUM_ION_OSM_BUILDINGS_ASSET_ID, { accessToken: ionToken });
      if (!stillEnabled()) {
        destroyTileset(viewer, tileset);
        return working;
      }
      applyIonOsmBuildingTileStyle(Cesium, tileset);
      configurePhotorealisticTileset(tileset);
      viewer.scene.primitives.add(tileset);
      working.ion = tileset;
      working.activeProvider = "ion-osm";
      onStatus?.("READY");
      cesiumDevLog("tiles-ion", "3D tiles rebuilt (Cesium Ion OSM fallback)");
      viewer.scene.requestRender();
      return working;
    } catch (error) {
      cesiumDevLog("tiles-ion", "Cesium Ion 3D tiles failed", error);
      if (stillEnabled()) onStatus?.("FAILED");
    }
  }

  cesiumDevLog("tiles-google", "No photorealistic 3D tile provider available");
  if (stillEnabled() && !ionToken) onStatus?.("MISSING_TOKEN");
  return working;
}

/** Toggle visibility without rebuilding (layer panel / quick hide). */
export function setPhotorealisticTilesVisible(state: PhotorealisticTileState, visible: boolean) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const setShow = (t: any) => {
    if (t && !t.isDestroyed?.()) t.show = visible;
  };
  setShow(state.google);
  setShow(state.ion);
}
