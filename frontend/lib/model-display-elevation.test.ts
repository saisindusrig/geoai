import { describe, expect, it } from "vitest";
import { globalBuildingsVisible, modelDisplayElevation } from "./model-display-elevation";
describe("model and city elevation consistency", () => {
  it("previews a zero-origin model at the context ground elevation", () => {
    expect(modelDisplayElevation(0, null, 920)).toBe(920);
    expect(modelDisplayElevation(0, null, -15)).toBe(-15);
  });
  it("never shifts accepted placements or explicit absolute elevations", () => {
    expect(modelDisplayElevation(0, { elevation: 900, offset: 4 }, 920)).toBe(904);
    expect(modelDisplayElevation(0, { elevation: 0, offset: 0 }, 920)).toBe(0);
    expect(modelDisplayElevation(850, null, 920)).toBe(850);
  });
  it("handles missing elevations without inventing terrain", () => {
    expect(modelDisplayElevation(0, null, null)).toBe(0);
    expect(modelDisplayElevation(0, null, NaN)).toBe(0);
  });
  it("hides absolute-height buildings on a flat or unavailable terrain", () => {
    expect(globalBuildingsVisible(true, false, true, false)).toBe(false);
    expect(globalBuildingsVisible(true, true, false, false)).toBe(false);
    expect(globalBuildingsVisible(true, true, true, false)).toBe(true);
    expect(globalBuildingsVisible(true, true, true, true)).toBe(false);
  });
});
