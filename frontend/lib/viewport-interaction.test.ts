import { describe, expect, it } from "vitest";
import { dragStarted, intersectsRectangle, numericTransformValue, selectionOperation } from "./viewport-interaction";
describe("viewport selection and precision", () => {
  it("uses atomic replace, add, remove and toggle without duplicate identities", () => {
    expect(selectionOperation(["a", "b"], ["b", "c", "c"], "toggle")).toEqual(["a", "c"]);
    expect(selectionOperation(["a"], ["a", "b"], "add")).toEqual(["a", "b"]);
    expect(selectionOperation(["a", "b"], ["a"], "remove")).toEqual(["b"]);
    expect(selectionOperation(["a"], [], "replace")).toEqual([]);
  });
  it("separates a small click jitter from a rectangle gesture", () => {
    expect(dragStarted(3, 3, 0, 0)).toBe(false); expect(dragStarted(3, 4, 0, 0)).toBe(true);
  });
  it("includes partial object intersections and rejects separated bounds", () => {
    const box = {x:10,y:10,width:20,height:20};
    expect(intersectsRectangle(box,{x:29,y:29,width:10,height:10})).toBe(true);
    expect(intersectsRectangle(box,{x:31,y:10,width:10,height:10})).toBe(false);
  });
  it("accepts exact signed distances and angles, rejecting incomplete or invalid input", () => {
    expect(numericTransformValue("-.125","translate")).toBe(-.125);
    expect(numericTransformValue("23.75","rotate")).toBe(23.75);
    for (const text of ["", "-", "1.2.3", "Infinity", "1e309"]) expect(numericTransformValue(text,"translate")).toBeNull();
    expect(numericTransformValue("0","scale")).toBeNull(); expect(numericTransformValue("-2","scale")).toBeNull(); expect(numericTransformValue("1.075","scale")).toBe(1.075);
  });
});
