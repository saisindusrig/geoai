import { expect, it } from "vitest";
import { cameraSurfaceFloor } from "./camera-surface";

it("keeps the camera above token-free visual reference without inventing surveyed heights", () => {
  expect(cameraSurfaceFloor(undefined, 1, 0)).toBe(2);
  expect(cameraSurfaceFloor(NaN, 1, 0)).toBe(2);
});
it("uses loaded terrain including negative heights and exaggeration relative reference", () => {
  expect(cameraSurfaceFloor(100, 2, 10)).toBe(192);
  expect(cameraSurfaceFloor(-30, 1, 0)).toBe(-28);
});
