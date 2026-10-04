import { describe, expect, it, vi } from "vitest";
import { createPhotorealisticTileState, syncPhotorealisticTiles } from "./cesium-photorealistic-tiles";
import type { TileProvidersResponse } from "./map-imagery";

describe("context tiles lifecycle", () => {
  it("loads visible buildings with the runtime token even when provider metadata is stale", async () => {
    const tiles = { show: false };
    const fromIonAssetId = vi.fn().mockResolvedValue(tiles);
    const viewer = { scene: { primitives: { add: vi.fn(), remove: vi.fn() }, requestRender: vi.fn() } };
    const Cesium = {
      Cesium3DTileset: { fromIonAssetId },
      Cesium3DTileStyle: class { constructor(public options: unknown) {} },
    };
    const status = vi.fn();
    const result = await syncPhotorealisticTiles({ viewer, Cesium, enabled: true,
      state: createPhotorealisticTileState(), providers: { cesium_ion_available: false } as TileProvidersResponse,
      runtime: { cesium_ion_token: "runtime-read-token", google_maps_api_key: null }, onStatus: status });
    expect(fromIonAssetId).toHaveBeenCalledWith(96188, { accessToken: "runtime-read-token" });
    expect(viewer.scene.primitives.add).toHaveBeenCalledWith(tiles);
    expect(tiles.show).toBe(true);
    expect(result.activeProvider).toBe("ion-osm");
    expect(status).toHaveBeenCalledWith("READY");
  });
  it("destroys a late building load after cancellation", async () => {
    let current = true;
    let resolve: (tiles: unknown) => void = () => {};
    const loading = new Promise((done) => { resolve = done; });
    const tiles = { destroy: vi.fn(), isDestroyed: () => false };
    const viewer = { scene: { primitives: { add: vi.fn(), remove: vi.fn() }, requestRender: vi.fn() } };
    const Cesium = { Ion: { defaultAccessToken: "read" }, Cesium3DTileset: { fromIonAssetId: () => loading } };
    const result = syncPhotorealisticTiles({ viewer, Cesium, enabled: true, state: createPhotorealisticTileState(), providers: { cesium_ion_available: true } as TileProvidersResponse,
      runtime: { cesium_ion_token: "read", google_maps_api_key: null }, isCurrent: () => current });
    current = false; resolve(tiles); await result;
    expect(viewer.scene.primitives.add).not.toHaveBeenCalled();
    expect(tiles.destroy).toHaveBeenCalledOnce();
  });
  it("reports missing read credentials explicitly", async () => {
    const status = vi.fn();
    await syncPhotorealisticTiles({ viewer: { scene: { requestRender() {} } }, Cesium: {}, enabled: true,
      state: createPhotorealisticTileState(), providers: { cesium_ion_available: false } as TileProvidersResponse,
      runtime: { cesium_ion_token: null, google_maps_api_key: null }, onStatus: status });
    expect(status).toHaveBeenCalledWith("MISSING_TOKEN");
  });
});
