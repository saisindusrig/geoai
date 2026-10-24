// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as C from "cesium";
import WorkspaceMouseControls from "./WorkspaceMouseControls";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useProjectStore } from "@/stores/projectStore";

function setup() {
  const canvas = document.createElement("canvas"); document.body.append(canvas);
  canvas.setPointerCapture = vi.fn(); canvas.hasPointerCapture = () => false;
  const entities = new C.EntityCollection();
  const entity = entities.add({ id:"editable:a",name:"Beam A",position:C.Cartesian3.fromDegrees(0,0),properties:{editableComponentId:"a",previewRadiusM:1} });
  const controls = {enableInputs:true,rotateEventTypes:[0],translateEventTypes:[1],zoomEventTypes:[2],tiltEventTypes:[3],lookEventTypes:[4]};
  const camera = {frustum:{fovy:Math.PI/3},positionWC:C.Cartesian3.fromDegrees(0,0,100),directionWC:new C.Cartesian3(-1,0,0),upWC:C.Cartesian3.UNIT_Z,rightWC:C.Cartesian3.UNIT_Y,heading:0,pitch:-.5,cancelFlight:vi.fn(),lookAt:vi.fn(),lookAtTransform:vi.fn(),setView:vi.fn(),flyToBoundingSphere:vi.fn(),getPickRay:()=>new C.Ray(C.Cartesian3.fromDegrees(0,0,100),new C.Cartesian3(-1,0,0)),getPixelSize:()=>1,pickEllipsoid:()=>entity.position!.getValue(C.JulianDate.now())};
  const scene = {screenSpaceCameraController:controls,drillPick:vi.fn(()=>[{id:entity}]),pick:vi.fn(()=>({id:entity})),requestRender:vi.fn(),globe:{pick:vi.fn(()=>entity.position!.getValue(C.JulianDate.now()))}};
  const viewer = {canvas,scene,camera,clock:{currentTime:C.JulianDate.now()}} as unknown as C.Viewer;
  const editor = {document:{components:[{id:"a",name:"Beam A",visible:true,locked:false,geometry:{kind:"box"}}]},selectedIds:[],tool:"select",selectMany:vi.fn(),setTool:vi.fn()} as unknown as EditableModelEditor;
  render(<WorkspaceMouseControls viewer={viewer} C={C} editor={editor} modelView={true} entities={()=>entities.values} bounds={()=>new C.BoundingSphere(C.Cartesian3.fromDegrees(0,0),10)} fit={vi.fn()} />);
  const pointer = (name:string,x:number,y:number,button=0,shiftKey=false) => fireEvent(canvas,new MouseEvent(name,{clientX:x,clientY:y,button,shiftKey,bubbles:true}));
  return {canvas,controls,camera,scene,editor,pointer};
}
beforeEach(()=>{localStorage.clear();useProjectStore.setState({activeTool:"select",scene3dMeasureTool:"none",pendingSave:null});});
afterEach(()=>{vi.useRealTimers();cleanup();document.querySelectorAll("canvas").forEach(canvas=>canvas.remove());});
describe("workspace gesture ownership",()=>{
  it("waits to open the inspector until a double click has fitted the original target",()=>{
    vi.useFakeTimers();const s=setup();const inspect=vi.fn(()=>expect(s.camera.flyToBoundingSphere).toHaveBeenCalledOnce());
    window.addEventListener("geoai:selection-inspect",inspect);
    s.pointer("pointerdown",30,30);s.pointer("pointerup",30,30);expect(inspect).not.toHaveBeenCalled();
    s.editor.selectedIds=["a"];s.scene.drillPick.mockReturnValue([]);s.pointer("pointerdown",30,30);s.pointer("pointerup",30,30);fireEvent.doubleClick(s.canvas,{clientX:30,clientY:30});expect(inspect).toHaveBeenCalledOnce();
    act(()=>vi.advanceTimersByTime(500));expect(inspect).toHaveBeenCalledOnce();
    window.removeEventListener("geoai:selection-inspect",inspect);vi.useRealTimers();
  });
  it("selects once on release and never gives a camera gesture to selection",()=>{
    const s=setup();s.pointer("pointerdown",30,30);s.pointer("pointerup",30,30);expect(s.editor.selectMany).toHaveBeenCalledWith(["a"]);
    vi.mocked(s.editor.selectMany).mockClear();s.pointer("pointerdown",30,30,1);expect(s.controls.enableInputs).toBe(false);s.pointer("pointermove",60,45,1);s.pointer("pointerup",60,45,1);
    expect(s.camera.setView).toHaveBeenCalledOnce();expect(s.editor.selectMany).not.toHaveBeenCalled();expect(s.controls.enableInputs).toBe(true);
  });
  it("pans with Shift-middle and restores controls after lost capture",()=>{
    const s=setup();s.pointer("pointerdown",30,30,1,true);s.pointer("pointermove",80,45,1,true);expect(s.camera.setView).toHaveBeenCalledOnce();fireEvent(s.canvas,new Event("lostpointercapture"));expect(s.controls.enableInputs).toBe(true);expect(s.editor.selectMany).not.toHaveBeenCalled();
  });
  it("leaves transform handles and drawing clicks to their existing owners",()=>{
    const s=setup();s.scene.pick.mockReturnValue({id:{id:"transform:X"}} as never);s.pointer("pointerdown",10,10);expect(s.controls.enableInputs).toBe(true);expect(s.editor.selectMany).not.toHaveBeenCalled();
    s.scene.pick.mockReturnValue({id:{id:"editable:a"}} as never);act(()=>useProjectStore.setState({activeTool:"draw-polygon"}));s.pointer("pointerdown",10,10);s.pointer("pointerup",10,10);expect(s.editor.selectMany).not.toHaveBeenCalled();
  });
  it("cancels a rectangle on blur without selection and restores prior disabled controls",()=>{
    const s=setup();s.controls.enableInputs=false;s.pointer("pointerdown",10,10);s.pointer("pointermove",80,80);fireEvent(window,new Event("blur"));expect(s.editor.selectMany).not.toHaveBeenCalled();expect(s.controls.enableInputs).toBe(false);
  });
  it("ignores focus shortcuts typed outside the viewport",()=>{
    const s=setup();const input=document.createElement("input");document.body.append(input);input.focus();fireEvent.keyDown(s.canvas,{key:"f"});expect(s.camera.flyToBoundingSphere).not.toHaveBeenCalled();input.remove();
  });
  it("zooms through the pointer ray without selecting and exposes object actions",()=>{
    const s=setup();fireEvent.wheel(s.canvas,{deltaY:-120,clientX:20,clientY:20});expect(s.camera.setView).toHaveBeenCalledOnce();expect(s.editor.selectMany).not.toHaveBeenCalled();fireEvent.contextMenu(s.canvas,{clientX:20,clientY:20});expect(screen.getByRole("menuitem",{name:"Move"})).toBeEnabled();fireEvent.click(screen.getByRole("menuitem",{name:"Move"}));expect(s.editor.setTool).toHaveBeenCalledWith("translate");
  });
  it("applies rectangle modifiers atomically",()=>{
    vi.spyOn(C.SceneTransforms,"worldToWindowCoordinates").mockReturnValue(new C.Cartesian2(50,50));
    const s=setup();s.editor.selectedIds=["b"];
    s.pointer("pointerdown",20,20,0,true);s.pointer("pointermove",80,80,0,true);s.pointer("pointerup",80,80,0,true);
    expect(s.editor.selectMany).toHaveBeenLastCalledWith(["b","a"]);
    s.editor.selectedIds=["a","b"];
    fireEvent(s.canvas,new MouseEvent("pointerdown",{clientX:20,clientY:20,ctrlKey:true,bubbles:true}));s.pointer("pointermove",80,80);s.pointer("pointerup",80,80);
    expect(s.editor.selectMany).toHaveBeenLastCalledWith(["b"]);vi.restoreAllMocks();
  });
  it("keeps locked objects inspectable but disables editing in the context menu",()=>{
    const s=setup();s.editor.document!.components[0].locked=true;fireEvent.contextMenu(s.canvas,{clientX:20,clientY:20});
    expect(screen.getByRole("menuitem",{name:"Inspect"})).toBeEnabled();expect(screen.getByRole("menuitem",{name:"Move"})).toBeDisabled();expect(screen.getByRole("menuitem",{name:"Scale"})).toBeDisabled();
  });
  it("orients around model bounds instead of hidden terrain",()=>{
    const s=setup();act(()=>window.dispatchEvent(new CustomEvent("geoai:orient-view",{detail:{heading:0,pitch:-90}})));
    expect(s.camera.flyToBoundingSphere).toHaveBeenCalledWith(expect.objectContaining({center:C.Cartesian3.fromDegrees(0,0),radius:10}),expect.objectContaining({offset:expect.objectContaining({pitch:-Math.PI/2,range:34})}));
    expect(s.scene.globe.pick).not.toHaveBeenCalled();expect(s.editor.selectMany).not.toHaveBeenCalled();
  });
});
