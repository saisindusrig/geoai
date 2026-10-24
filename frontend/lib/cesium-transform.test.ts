// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import * as C from "cesium";
import { installCesiumTransform } from "./cesium-transform";
import { defaultTransformSettings } from "./editor-transform";
import type { EditableModelDocument } from "./types";

const doc = { origin: { lng: 0, lat: 0, elevation_m: 0, heading_deg: 0 }, components: [{ id: "a", geometry: { kind: "box", size: [2,2,2] }, visible: true, locked: false, transform: { position: [0,0,0], rotation_deg: [0,0,0], scale: [1,1,1] } }] } as EditableModelDocument;
function setup(commitFailure=false, mode: "translate" | "rotate" | "scale" = "translate") {
  const canvas = document.createElement("canvas"); document.body.append(canvas);
  canvas.tabIndex=0; canvas.focus(); canvas.setPointerCapture = vi.fn(); canvas.hasPointerCapture = () => false;
  const frame = C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(0,0));
  const world = (point: C.Cartesian3) => C.Matrix4.multiplyByPoint(frame,point,new C.Cartesian3());
  const direction = C.Matrix4.multiplyByPointAsVector(frame,new C.Cartesian3(0,1,-1),new C.Cartesian3());
  const controls = { enableInputs: true };
  const primitive = { componentId:"a", modelMatrix: C.Matrix4.clone(C.Matrix4.IDENTITY) };
  const unrelated = {componentId:"unrelated", modelMatrix:C.Matrix4.clone(C.Matrix4.IDENTITY)};
  const clock = {currentTime:C.JulianDate.now()};
  const positions=[world(new C.Cartesian3(0,0,0)),world(new C.Cartesian3(1,0,0))];
  const edge = new C.Entity({properties:{editableComponentId:"a",transformEdge:true},polyline:{positions}});
  const viewer = { clock, scene: { canvas, screenSpaceCameraController: controls, pick: () => ({ id: { id: "transform:X" } }), requestRender: vi.fn() }, camera: { positionWC: world(new C.Cartesian3(0,-100,100)), directionWC: direction, getPickRay: (point: C.Cartesian2) => new C.Ray(world(new C.Cartesian3(point.x,-10,10)),direction) }, dataSources: { add: vi.fn(), remove: vi.fn() }, isDestroyed: () => false };
  const commit = vi.fn((patches:{id:string;transform:EditableModelDocument["components"][number]["transform"]}[])=>{void patches;if(commitFailure)throw new Error("Commit failed");}); const feedback = vi.fn();
  const dispose = installCesiumTransform(C, viewer as unknown as C.Viewer,doc,["a"],{...defaultTransformSettings,mode},{ length:2, get:(index:number)=>index===0?unrelated:primitive } as unknown as C.PrimitiveCollection,commit,feedback,undefined,[edge]);
  const pointer = (name: string, x: number) => canvas.dispatchEvent(new MouseEvent(name,{clientX:x,bubbles:true,button:0}));
  return { canvas, controls, primitive, unrelated, edge, positions, clock, commit, dispose, pointer };
}
describe("Cesium transform transaction cleanup", () => {
  it("does not create history for unchanged or snapped-to-zero drags",()=>{
    const s=setup();s.pointer("pointerdown",0);s.pointer("pointermove",.1);window.dispatchEvent(new MouseEvent("pointerup"));expect(s.commit).not.toHaveBeenCalled();expect(s.controls.enableInputs).toBe(true);s.dispose();s.canvas.remove();
  });
  it("commits exact numeric distance without rounding to the snap interval",()=>{
    const s=setup();s.pointer("pointerdown",0);s.pointer("pointermove",3);
    for(const key of ["1",".","2","5"])window.dispatchEvent(new KeyboardEvent("keydown",{key}));
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));expect(s.commit).toHaveBeenCalledTimes(1);expect(s.commit.mock.calls[0][0][0].transform.position).toEqual([1.25,0,0]);expect(s.controls.enableInputs).toBe(true);s.dispose();s.canvas.remove();
  });
  it("cancels exact numeric preview without creating history",()=>{
    const s=setup();s.pointer("pointerdown",0);window.dispatchEvent(new KeyboardEvent("keydown",{key:"2"}));window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));expect(s.commit).not.toHaveBeenCalled();expect(s.primitive.modelMatrix).toEqual(C.Matrix4.IDENTITY);expect(s.controls.enableInputs).toBe(true);s.dispose();s.canvas.remove();
  });
  it("moves the identified solid and its edge outline together and restores both on cancel",()=>{
    const s=setup();s.pointer("pointerdown",0);s.pointer("pointermove",3);
    expect(s.unrelated.modelMatrix).toEqual(C.Matrix4.IDENTITY);expect(s.primitive.modelMatrix).not.toEqual(C.Matrix4.IDENTITY);
    expect(s.edge.polyline!.positions!.getValue(s.clock.currentTime)).not.toEqual(s.positions);
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));expect(s.edge.polyline!.positions!.getValue(s.clock.currentTime)).toEqual(s.positions);s.dispose();s.canvas.remove();
  });
  it("constrains an exact movement to the chosen axis",()=>{
    const s=setup();s.pointer("pointerdown",0);s.pointer("pointermove",3);
    for(const key of ["y","2","Enter"])window.dispatchEvent(new KeyboardEvent("keydown",{key}));
    expect(s.commit).toHaveBeenCalledTimes(1);expect(s.commit.mock.calls[0][0][0].transform.position).toEqual([0,2,0]);s.dispose();s.canvas.remove();
  });
  it("supports keyboard precision entry without holding a mouse button",()=>{
    vi.spyOn(C.SceneTransforms,"worldToWindowCoordinates").mockReturnValue(new C.Cartesian2(0,0));
    const s=setup();for(const key of ["y","2",".","7","5","Enter"])window.dispatchEvent(new KeyboardEvent("keydown",{key}));
    expect(s.commit).toHaveBeenCalledTimes(1);expect(s.commit.mock.calls[0][0][0].transform.position).toEqual([0,2.75,0]);expect(s.controls.enableInputs).toBe(true);s.dispose();s.canvas.remove();vi.restoreAllMocks();
  });
  it.each([["rotate","23.75"],["scale","1.075"]] as const)("supports exact %s input",(mode,text)=>{
    const s=setup(false,mode);s.pointer("pointerdown",0);for(const key of text)window.dispatchEvent(new KeyboardEvent("keydown",{key}));window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));expect(s.commit).toHaveBeenCalledTimes(1);
    const transform=s.commit.mock.calls[0][0][0].transform;
    if(mode==="rotate")expect(transform.rotation_deg[0]).toBeCloseTo(23.75);else expect(transform.scale).toEqual([1.075,1,1]);s.dispose();s.canvas.remove();
  });
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

