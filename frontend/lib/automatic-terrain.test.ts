import { expect, it, vi } from "vitest";
import type { TerrainProvider } from "cesium";
import { resolveAutomaticTerrain, terrainCoversSite, type ProjectTerrainSource } from "./automatic-terrain";
const project: ProjectTerrainSource = { id: 7, state: "READY", ion_asset_id: 99, coverage: { type: "Polygon", coordinates: [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]] } };
const provider = {} as TerrainProvider;
it("prefers the active terrain covering the site", async () => {
  const load = vi.fn().mockResolvedValue(provider);
  expect((await resolveAutomaticTerrain({ project, longitude: 1, latitude: 1, load })).source).toBe("project");
  expect(load).toHaveBeenCalledExactlyOnceWith(99);
});
it("uses world terrain outside site coverage", async () => {
  const load = vi.fn().mockResolvedValue(provider);
  const result = await resolveAutomaticTerrain({ project, longitude: 10, latitude: 10, load });
  expect(result.source).toBe("world");
  expect(result.fallback).toContain("outside");
  expect(load).toHaveBeenCalledExactlyOnceWith(1);
});
it("recovers from an unavailable project asset", async () => {
  const load = vi.fn().mockRejectedValueOnce(new Error("unavailable")).mockResolvedValue(provider);
  const result = await resolveAutomaticTerrain({ project, longitude: 1, latitude: 1, load });
  expect(result.source).toBe("world");
  expect(load.mock.calls).toEqual([[99], [1]]);
});
it("propagates world-provider failure rather than reporting a flat globe as terrain", async () => {
  await expect(resolveAutomaticTerrain({ project: null, longitude: 1, latitude: 1, load: vi.fn().mockRejectedValue(new Error("offline")) })).rejects.toThrow("offline");
});
it("excludes holes in coverage", () => {
  expect(terrainCoversSite(null, 1, 1)).toBe(false);
  expect(terrainCoversSite({ type: "Polygon", coordinates: [...project.coverage.coordinates as number[][][], [[.5, .5], [1.5, .5], [1.5, 1.5], [.5, 1.5], [.5, .5]]] }, 1, 1)).toBe(false);
});
