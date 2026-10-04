import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { componentObject, ENU_TO_GRID, releaseComponentObject } from "./sandbox-geometry";
import type { EditableModelComponent } from "./types";

const box: EditableModelComponent = {
  id: "box", parent_id: null, name: "Box", category: "building", visible: true, locked: false,
  geometry: { kind: "box", size: [2, 4, 6] },
  transform: { position: [10, 20, 3], rotation_deg: [0, 0, 0], scale: [1, 1, 1] },
  material: { name: "Concrete", color: "#60a5fa", roughness: 0.75, metalness: 0 },
};

describe("sandbox geometry coordinate parity", () => {
  it("maps document east/north/up into grid east/up/south", () => {
    const point = new THREE.Vector3(10, 20, 3).applyMatrix4(ENU_TO_GRID);
    expect(point.x).toBeCloseTo(10);
    expect(point.y).toBeCloseTo(3);
    expect(point.z).toBeCloseTo(-20);
  });

  it("retains the dimensions and coordinate axes of a document box", () => {
    const object = componentObject(box);
    const bounds = new THREE.Box3().setFromObject(object);
    expect(bounds.getCenter(new THREE.Vector3()).toArray()).toEqual([10, 20, 3]);
    expect(bounds.getSize(new THREE.Vector3()).toArray()).toEqual([2, 4, 6]);
    releaseComponentObject(object);
  });

  it("applies cylinder endpoints, rotation, translation, and nonuniform scale", () => {
    const cylinder = componentObject({ ...box, geometry: { kind: "cylinder", start: [0, 0, 0], end: [0, 0, 10], radius_m: 1 }, transform: { position: [5, 6, 7], rotation_deg: [90, 0, 0], scale: [2, 3, 1] } });
    const bounds = new THREE.Box3().setFromObject(cylinder);
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    expect(center.x).toBeCloseTo(5);
    expect(center.y).toBeCloseTo(1);
    expect(center.z).toBeCloseTo(7);
    expect(size.x).toBeCloseTo(4);
    expect(size.y).toBeCloseTo(10);
    expect(size.z).toBeCloseTo(6);
    releaseComponentObject(cylinder);
  });
});
