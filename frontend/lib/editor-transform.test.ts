import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { applyTransformDelta, cameraLease, defaultTransformSettings, snap, cylinderFrame } from "./editor-transform";
import type { EditableModelComponent } from "./types";

const component = (id: string, position: [number,number,number], locked = false) => ({ id, locked, transform: { position, rotation_deg: [0,0,0], scale: [1,1,1] } }) as EditableModelComponent;
it("resolves horizontal pipe endpoints with saved translation, rotation and scale", () => {
  const pipe = { ...component("pipe", [3,4,5]), geometry: { kind: "cylinder", start: [0,0,0], end: [10,0,0], radius_m: .2 } } as EditableModelComponent;
  pipe.transform.rotation_deg = [0,0,90]; pipe.transform.scale = [2,2,2];
  const frame = cylinderFrame(pipe);
  expect(frame.start.toArray()).toEqual([3,4,5]);
  expect(frame.end.x).toBeCloseTo(3); expect(frame.end.y).toBeCloseTo(24); expect(frame.end.z).toBeCloseTo(5);
  expect(frame.length).toBeCloseTo(20); expect(frame.radius).toBeCloseTo(.4);
});
describe("engineering transform math", () => {
  it.each([0,1,2])("constrains translation to axis %i and respects snap", index => {
    const axis = new THREE.Vector3().setComponent(index,1);
    const result = applyTransformDelta([component("a",[1,2,3])], { ...defaultTransformSettings, mode:"translate" },axis,2.6)[0].transform.position;
    result.forEach((value,i) => expect(value).toBeCloseTo([1,2,3][i] + (i === index ? 2.5 : 0)));
  });
  it("supports Off and fractional snapping", () => { expect(snap(1.234,0)).toBe(1.234); expect(snap(1.234,0.01)).toBeCloseTo(1.23); });
  it("rotates around the active pivot without changing locked objects", () => {
    const result = applyTransformDelta([component("a",[0,0,0]),component("b",[10,0,0]),component("lock",[20,0,0],true)],{...defaultTransformSettings,mode:"rotate"},new THREE.Vector3(0,0,1),88);
    expect(result).toHaveLength(2); expect(result[1].transform.position[0]).toBeCloseTo(0); expect(result[1].transform.position[1]).toBeCloseTo(10);
  });
  it("keeps individual origins fixed and scales around median", () => {
    const items = [component("a",[0,0,0]),component("b",[10,0,0])];
    const individual = applyTransformDelta(items,{...defaultTransformSettings,mode:"rotate",pivot:"individual"},new THREE.Vector3(0,0,1),45);
    expect(individual[1].transform.position).toEqual([10,0,0]);
    const scaled = applyTransformDelta(items,{...defaultTransformSettings,mode:"scale",pivot:"median"},new THREE.Vector3(),2);
    expect(scaled.map(item=>item.transform.position[0])).toEqual([-5,15]);
  });
  it("rejects invalid scale and nonuniform scaling that would introduce shear", () => {
    expect(()=>applyTransformDelta([component("a",[0,0,0])],{...defaultTransformSettings,mode:"scale"},new THREE.Vector3(),0)).toThrow("greater than zero");
    expect(()=>applyTransformDelta([component("a",[0,0,0])],{...defaultTransformSettings,mode:"scale",coordinates:"world"},new THREE.Vector3(1,0,0),2)).toThrow("preserve geometry");
  });
  it.each([true,false])("restores exact camera state %s once", enableInputs => {
    const camera = { enableInputs }; const release = cameraLease(camera);
    expect(camera.enableInputs).toBe(false); release(); expect(camera.enableInputs).toBe(enableInputs);
    camera.enableInputs = !enableInputs; release(); expect(camera.enableInputs).toBe(!enableInputs);
  });
});
