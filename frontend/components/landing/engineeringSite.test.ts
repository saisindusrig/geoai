import { describe, expect, it } from "vitest";
import { SITE, alignmentZ, approachEarthwork, bridgeGrade, roadGrade, storyPosition, terrainHeight } from "./engineeringSite";

describe("homepage demonstration geometry", () => {
  it("clamps scroll stages and supports backward traversal", () => {
    expect(storyPosition(-1)).toEqual({stage:0,progress:0});
    expect(storyPosition(.5)).toEqual({stage:2,progress:.5});
    expect(storyPosition(1).stage).toBe(4);
    expect(storyPosition(2).progress).toBeLessThan(1);
    expect(storyPosition(.2).stage).toBe(1);
  });
  it("keeps five equal spans and the displayed bridge grade", () => {
    expect(SITE.bridgeLength).toBe(SITE.span*5);
    expect((bridgeGrade(10)-bridgeGrade(-10))/20).toBeCloseTo(.02);
    expect(alignmentZ(-10)).toBe(alignmentZ(10));
    for(const x of SITE.pierStations) expect(bridgeGrade(x)).toBeGreaterThan(terrainHeight(x,alignmentZ(x)));
  });
  it("keeps the road profile continuous and below 3 percent longitudinal grade", () => {
    for(let x=-17;x<17;x+=.1) expect(Math.abs((roadGrade(x+.01)-roadGrade(x))/.01)).toBeLessThan(.03);
  });
  it("returns finite non-negative illustrative quantities", () => {
    const quantities=approachEarthwork();
    expect(Number.isFinite(quantities.cut)).toBe(true);
    expect(Number.isFinite(quantities.fill)).toBe(true);
    expect(quantities.cut).toBeGreaterThanOrEqual(0);
    expect(quantities.fill).toBeGreaterThan(0);
  });
});
