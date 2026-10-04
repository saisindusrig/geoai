import { describe, expect, it, vi } from "vitest";
import { sampleTerrainHeightM } from "./cesium-scene";

describe("terrain sampling", () => {
  class EllipsoidTerrainProvider {}
  const cesium = { EllipsoidTerrainProvider, Cartographic: { fromDegrees: (lng: number, lat: number) => ({ lng, lat }) }, sampleTerrainMostDetailed: vi.fn() };
  const namespace = cesium as unknown as typeof import("cesium");
  const provider = {} as import("cesium").TerrainProvider;
  it("keeps missing and neutral terrain unknown", async () => {
    expect(await sampleTerrainHeightM(namespace, null, 77, 12)).toBeNull();
    expect(await sampleTerrainHeightM(namespace, new EllipsoidTerrainProvider() as import("cesium").TerrainProvider, 77, 12)).toBeNull();
  });
  it("keeps failed or non-finite samples unknown", async () => {
    cesium.sampleTerrainMostDetailed.mockRejectedValueOnce(new Error("offline"));
    expect(await sampleTerrainHeightM(namespace, provider, 77, 12)).toBeNull();
    cesium.sampleTerrainMostDetailed.mockResolvedValueOnce([{ height: NaN }]);
    expect(await sampleTerrainHeightM(namespace, provider, 77, 12)).toBeNull();
  });
  it("preserves valid sea-level and negative elevations", async () => {
    cesium.sampleTerrainMostDetailed.mockResolvedValueOnce([{ height: 0 }]).mockResolvedValueOnce([{ height: -12 }]);
    expect(await sampleTerrainHeightM(namespace, provider, 77, 12)).toBe(0);
    expect(await sampleTerrainHeightM(namespace, provider, 77, 12)).toBe(-12);
  });
});
