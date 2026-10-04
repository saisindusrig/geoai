import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { ASSET_TYPES, ASSET_CATEGORIES, assetDefinition, searchAssets } from "./asset-types";
import { PROJECT_TYPE_OPTIONS } from "./project-catalog";

describe("infrastructure catalogue compatibility and search", () => {
  it("keeps the browser catalogue in sync with the API source", () => {
    expect(JSON.parse(readFileSync(new URL("../../backend/app/core/asset-types.json", import.meta.url), "utf8")).assets).toEqual(ASSET_TYPES);
  });
  it("retains every existing API identifier and generation path", () => {
    for (const old of PROJECT_TYPE_OPTIONS) {
      expect(assetDefinition(old.id)?.supportsGeneration, old.id).toBe(true);
    }
    expect(new Set(ASSET_TYPES.map((asset) => asset.id)).size).toBe(ASSET_TYPES.length);
    expect(ASSET_CATEGORIES).toHaveLength(12);
    expect(ASSET_TYPES.length).toBeGreaterThan(190);
  });
  it("finds bridge subtypes and aliased flyovers, including typo searches", () => {
    const names = searchAssets("bridge").map((asset) => asset.name);
    for (const name of ["Highway Bridge", "Railway Bridge", "Pedestrian Bridge", "Cable-Stayed Bridge", "Suspension Bridge", "Bridge / Viaduct", "Flyover / Overpass"]) expect(names).toContain(name);
    expect(searchAssets("bridg").length).toBeGreaterThan(5);
    expect(searchAssets("brdige").length).toBeGreaterThan(5);
    expect(searchAssets("solar", "energy").every((asset) => asset.category === "energy")).toBe(true);
    expect(searchAssets("zzzzzzzzz")).toEqual([]);
  });
  it("keeps custom and reference types free of inherited engineering capabilities", () => {
    const custom = assetDefinition("custom_asset");
    expect(custom?.supportsGeneration).toBe(false);
    expect(custom?.maturity).toBe("REFERENCE");
    for (const asset of ASSET_TYPES.filter((asset) => asset.maturity === "REFERENCE")) {
      expect(asset.supportsGeneration).toBe(false);
      expect(Object.values(asset.capabilities).some(Boolean)).toBe(false);
    }
  });
});
