import { describe, expect, it } from "vitest";
import { shouldMountCesiumView } from "@/lib/map-view-mode";

describe("shouldMountCesiumView", () => {
  it("mounts Cesium only in 3D mode", () => {
    expect(shouldMountCesiumView("3d")).toBe(true);
    expect(shouldMountCesiumView("2d")).toBe(false);
  });
});
