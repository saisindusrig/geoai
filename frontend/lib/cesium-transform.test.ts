// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import * as C from "cesium";
import { installCesiumTransform } from "./cesium-transform";
import { defaultTransformSettings } from "./editor-transform";
import type { EditableModelDocument } from "./types";

const doc = { origin: { lng: 0, lat: 0, elevation_m: 0, heading_deg: 0 }, components: [{ id: "a", geometry: { kind: "box", size: [2,2,2] }, visible: true, locked: false, transform: { position: [0,0,0], rotation_deg: [0,0,0], scale: [1,1,1] } }] } as EditableModelDocument;
function setup(commitFailure=false) {
  const canvas = document.createElement("canvas"); document.body.append(canvas);
  canvas.setPointerCapture = vi.fn(); canvas.hasPointerCapture = () => false;
  const frame = C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(0,0));
  const world = (point: C.Cartesian3) => C.Matrix4.multiplyByPoint(frame,point,new C.Cartesian3());
  const direction = C.Matrix4.multiplyByPointAsVector(frame,new C.Cartesian3(0,1,-1),new C.Cartesian3());
  const controls = { enableInputs: true };
  const primitive = { modelMatrix: C.Matrix4.clone(C.Matrix4.IDENTITY) };
  const viewer = { scene: { canvas, screenSpaceCameraController: controls, pick: () => ({ id: { id: "transform:X" } }), requestRender: vi.fn() }, camera: { positionWC: world(new C.Cartesian3(0,-100,100)), directionWC: direction, getPickRay: (point: C.Cartesian2) => new C.Ray(world(new C.Cartesian3(point.x,-10,10)),direction) }, dataSources: { add: vi.fn(), remove: vi.fn() }, isDestroyed: () => false };
  const commit = vi.fn((patches:{id:string;transform:EditableModelDocument["components"][number]["transform"]}[])=>{void patches;if(commitFailure)throw new Error("Commit failed");}); const feedback = vi.fn();
  const dispose = installCesiumTransform(C, viewer as unknown as C.Viewer,doc,["a"],{...defaultTransformSettings,mode:"translate"},{ get:()=>primitive } as unknown as C.PrimitiveCollection,commit,feedback);
  const pointer = (name: string, x: number) => canvas.dispatchEvent(new MouseEvent(name,{clientX:x,bubbles:true,button:0}));
  return { canvas, controls, primitive, commit, dispose, pointer };
}
describe("Cesium transform transaction cleanup", () => {
  it("previews without committing, then commits one action on release", () => {
    const s = setup(); s.pointer("pointerdown",0); expect(s.controls.enableInputs).toBe(false);
    s.pointer("pointermove",2.6); s.pointer("pointermove",5.1); expect(s.commit).not.toHaveBeenCalled();
    window.dispatchEvent(new MouseEvent("pointerup")); expect(s.commit).toHaveBeenCalledTimes(1);
    expect(s.commit.mock.calls[0][0][0].transform.position).toEqual([5,0,0]); expect(s.controls.enableInputs).toBe(true);
    s.dispose(); s.canvas.remove();
  });
  it.each(["Escape","blur","pointercancel","lostpointercapture","unmount"])("restores preview and camera after %s", interruption => {
    const s = setup(); s.pointer("pointerdown",0); s.pointer("pointermove",3);
    if (interruption === "Escape") window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    else if (interruption === "blur") window.dispatchEvent(new Event("blur"));
    else if (interruption === "unmount") s.dispose();
    else s.canvas.dispatchEvent(new Event(interruption));
    expect(s.controls.enableInputs).toBe(true); expect(s.commit).not.toHaveBeenCalled(); expect(s.primitive.modelMatrix).toEqual(C.Matrix4.IDENTITY);
    if (interruption !== "unmount") s.dispose(); s.canvas.remove();
  });
  it("restores matrices and camera when committing throws",()=>{
    const s=setup(true);s.pointer("pointerdown",0);s.pointer("pointermove",3);window.dispatchEvent(new MouseEvent("pointerup"));
    expect(s.commit).toHaveBeenCalledTimes(1);expect(s.controls.enableInputs).toBe(true);expect(s.primitive.modelMatrix).toEqual(C.Matrix4.IDENTITY);s.dispose();s.canvas.remove();
  });
});

