import { expect, it } from "vitest";
import { boundaryError } from "./boundary-validation";
import { verticesToPolygon } from "./map-draw";

it.each([
  { points: [[77,12],[77.001,12],[77.001,12.001]], valid: true },
  { points: [[0,0],[1,0]], valid: false },
  { points: [[0,0],[1,0],[0,0],[0,1]], valid: false },
  { points: [[0,0],[1,1],[0,1],[1,0]], valid: false },
  { points: [[0,0],[1,0],[2,0]], valid: false },
  { points: [[0,0],[181,0],[0,1]], valid: false },
  { points: [[0,0],[NaN,1],[1,0]], valid: false },
  { points: [[0,0],[3,0],[3,3],[1,0],[0,3]], valid: false },
  { points: [[77,12],[77.000001,12],[77.000001,12.000001]], valid: true },
])("validates plan polygon $points", ({ points, valid }) => {
  expect(boundaryError(verticesToPolygon(points as [number,number][])) === null).toBe(valid);
});
