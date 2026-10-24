"use client";
import {outcome,type WorkspaceCommand} from "@/lib/workspace-assistant";
import {frameEntities} from "@/lib/visual-framing";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type * as Cesium from "cesium";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useProjectStore } from "@/stores/projectStore";
import { componentDisplayName } from "@/lib/component-presentation";
import { cameraLease } from "@/lib/editor-transform";
import { dragStarted, intersectsRectangle, selectionOperation } from "@/lib/viewport-interaction";

type Props = { viewer: Cesium.Viewer; C: typeof Cesium; editor: EditableModelEditor; modelView: boolean; underground?: boolean; entities: () => Cesium.Entity[]; bounds: () => Cesium.BoundingSphere | null; fit: () => void; onSitePick?: (point: Point) => void };
type Point = { x: number; y: number };
type Box = Point & { width: number; height: number };
export default function WorkspaceMouseControls(props: Props) {
  const latest = useRef(props); useLayoutEffect(() => { latest.current = props; });
  const [mode, setMode] = useState<"select" | "orbit" | "pan">("select");
  const [box, setBox] = useState<Box | null>(null);
  const [menu, setMenu] = useState<(Point & { ids: string[] }) | null>(null);
  const [help, setHelp] = useState(false);
  const drawingTool = useProjectStore(state => state.activeTool);
  const measurementTool = useProjectStore(state => state.scene3dMeasureTool);
  const readPreferences = () => { try { return JSON.parse(localStorage.getItem("geoai:mouse-preferences") ?? "{}"); } catch { return {}; } };
  const [sensitivity, setSensitivity] = useState(() => Math.max(.25,Math.min(2, Number(readPreferences().sensitivity) || 1)));
  const [invert, setInvert] = useState(() => readPreferences().invert === true);
  const prefs = useRef({ mode, sensitivity, invert }); useLayoutEffect(() => { prefs.current = { mode, sensitivity, invert }; latest.current.viewer.canvas.dataset.navigationMode = mode; }, [mode,sensitivity,invert]);
  const savePreference = (value: number, reversed: boolean) => { setSensitivity(value); setInvert(reversed); try { localStorage.setItem("geoai:mouse-preferences", JSON.stringify({ sensitivity: value, invert: reversed })); } catch { /* session preferences still work */ } };
  useEffect(() => {
    const { viewer, C } = latest.current;
    const canvas = viewer.canvas, controller = viewer.scene.screenSpaceCameraController;
    const old = { rotate: controller.rotateEventTypes, translate: controller.translateEventTypes, zoom: controller.zoomEventTypes, tilt: controller.tiltEventTypes, look: controller.lookEventTypes };
    // Desktop gestures have one owner; Cesium retains pinch handling.
    controller.rotateEventTypes = [C.CameraEventType.PINCH]; controller.translateEventTypes = [];
    controller.zoomEventTypes = [C.CameraEventType.PINCH]; controller.tiltEventTypes = []; controller.lookEventTypes = [];
    canvas.tabIndex = 0; canvas.setAttribute("aria-label", "3D workspace viewport");
    let pivot: Cesium.Cartesian3 | null = null;
    let firstClick: {point:Point;time:number;ids:string[]} | null = null;
    const recentClick=(p:Point)=>firstClick && performance.now()-firstClick.time<1200 && Math.hypot(p.x-firstClick.point.x,p.y-firstClick.point.y)<5 ? firstClick : null;
    let inspectTimer: ReturnType<typeof setTimeout> | undefined;
    const cancelInspect=()=>{if(inspectTimer!==undefined){clearTimeout(inspectTimer);inspectTimer=undefined;}};
    let active: { pointer: number; start: Point; last: Point; kind: "select" | "orbit" | "pan"; dragged: boolean; shift: boolean; ctrl: boolean; release: () => void } | null = null;
    const point = (e: MouseEvent) => { const rect = canvas.getBoundingClientRect(); return { x: e.clientX - rect.left, y: e.clientY - rect.top }; };
    const available = () => { const s = useProjectStore.getState(); return s.activeTool === "select" && s.scene3dMeasureTool === "none" && !s.pendingSave; };
    const picked = (p: Point) => [...new Set(viewer.scene.drillPick(new C.Cartesian2(p.x, p.y), 32).flatMap(hit => {
      const id = hit.id?.properties?.getValue(viewer.clock.currentTime)?.editableComponentId;
      return latest.current.editor.document?.components.some(c => c.id === id && c.visible) ? [String(id)] : [];
    }))];
    const spheres = (ids?: string[]) => latest.current.entities().flatMap(entity => {
      const data = entity.properties?.getValue(viewer.clock.currentTime), position = entity.position?.getValue(viewer.clock.currentTime);
      return entity.show && entity.id.startsWith("editable:") && position && (!ids || ids.includes(data?.editableComponentId)) ? [new C.BoundingSphere(position, Number(data?.previewRadiusM) || .1)] : [];
    });
    const focus = (ids: string[],confirm?: (ok:boolean)=>void) => { const values = spheres(ids); if (!values.length) { if(confirm)confirm(false);else latest.current.fit(); return; } const sphere = C.BoundingSphere.fromBoundingSpheres(values); const heading=viewer.camera.heading,pitch=C.Math.toRadians(-30);
      const framed=latest.current.modelView ? frameEntities(C,latest.current.entities(),sphere,heading,pitch,Number((viewer.camera.frustum as {fovy?:number}).fovy??Math.PI/3),canvas.clientWidth/Math.max(1,canvas.clientHeight),e=>ids.includes(e.properties?.getValue(viewer.clock.currentTime)?.editableComponentId)) : null;
      pivot = C.Cartesian3.clone(framed?.sphere.center ?? sphere.center); viewer.camera.flyToBoundingSphere(framed?.sphere ?? sphere, { duration: .35, complete:()=>confirm?.(true),cancel:()=>confirm?.(false), offset: new C.HeadingPitchRange(heading,pitch,framed?.range ?? Math.max(sphere.radius * 3.5, 2)) }); };
    const pivotAt = (p: Point) => {
      if (!latest.current.modelView) { const ray = viewer.camera.getPickRay(new C.Cartesian2(p.x, p.y)); const ground = ray && viewer.scene.globe.pick(ray, viewer.scene); if (ground) return ground; }
      const selected = spheres(latest.current.editor.selectedIds);
      return selected.length ? C.BoundingSphere.fromBoundingSpheres(selected).center : pivot ?? latest.current.bounds()?.center ?? viewer.camera.pickEllipsoid(new C.Cartesian2(p.x, p.y)) ?? null;
    };
    const cameraDestination = (position: Cesium.Cartesian3) => {
      if (latest.current.modelView || latest.current.underground) return position;
      const location = C.Cartographic.fromCartesian(position), terrain = viewer.scene.globe.getHeight(location);
      const minimum = (Number.isFinite(terrain) ? terrain! : 0) + .5;
      return location.height < minimum ? C.Cartesian3.fromRadians(location.longitude, location.latitude, minimum) : position;
    };
    const stop = (cancel = false) => {
      const gesture = active; active = null; if (!gesture) return;
      if (!cancel && available() && gesture.kind === "select" && gesture.dragged) {
        const rectangle = { x: Math.min(gesture.start.x, gesture.last.x), y: Math.min(gesture.start.y, gesture.last.y), width: Math.abs(gesture.last.x - gesture.start.x), height: Math.abs(gesture.last.y - gesture.start.y) };
        const ids = latest.current.entities().filter(e => e.show && e.id.startsWith("editable:")).flatMap(entity => {
          const position = entity.position?.getValue(viewer.clock.currentTime), data = entity.properties?.getValue(viewer.clock.currentTime);
          if (!position || C.Cartesian3.dot(C.Cartesian3.subtract(position, viewer.camera.positionWC, new C.Cartesian3()), viewer.camera.directionWC) <= 0) return [];
          const screen = C.SceneTransforms.worldToWindowCoordinates(viewer.scene, position); if (!screen) return [];
          const radius = Number(data?.previewRadiusM) || .1;
          const pixels = viewer.camera.getPixelSize(new C.BoundingSphere(position, radius), canvas.width, canvas.height);
          const r = radius / Math.max(pixels, 1e-8) * canvas.clientWidth / canvas.width;
          const corners = (data.previewCorners as number[][] | undefined)?.flatMap(p => { const point=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,C.Cartesian3.fromArray(p)); return point ? [point] : []; });
          const left=corners?.length ? Math.min(...corners.map(p=>p.x)) : screen.x-r, top=corners?.length ? Math.min(...corners.map(p=>p.y)) : screen.y-r;
          const right=corners?.length ? Math.max(...corners.map(p=>p.x)) : screen.x+r, bottom=corners?.length ? Math.max(...corners.map(p=>p.y)) : screen.y+r;
          return intersectsRectangle(rectangle, { x:left, y:top, width:right-left, height:bottom-top }) ? [String(data.editableComponentId)] : [];
        });
        latest.current.editor.selectMany(selectionOperation(latest.current.editor.selectedIds, ids, gesture.ctrl ? "remove" : gesture.shift ? "add" : "replace"));
      } else if (!cancel && gesture.kind === "select" && available()) {
        const ids = picked(gesture.last).slice(0, 1);
        if(ids.length && !recentClick(gesture.last))firstClick={point:gesture.last,time:performance.now(),ids};
        if (!ids.length && !latest.current.modelView && !gesture.ctrl && !gesture.shift) latest.current.onSitePick?.(gesture.last);
        else { useProjectStore.getState().setSelectedObject3d(null); latest.current.editor.selectMany(selectionOperation(latest.current.editor.selectedIds, ids, gesture.shift || gesture.ctrl ? "toggle" : "replace")); }
      }
      if(!cancel && gesture.kind === "select" && latest.current.editor.tool === "select") {
        // Wait for the double-click sequence before changing viewport width.
        cancelInspect();inspectTimer=setTimeout(()=>{inspectTimer=undefined;if(latest.current.editor.selectedIds.length)window.dispatchEvent(new Event("geoai:selection-inspect"));},400);
      }
      gesture.release(); delete canvas.dataset.mouseOwner; canvas.style.cursor = ""; setBox(null);
      if (canvas.hasPointerCapture(gesture.pointer)) canvas.releasePointerCapture(gesture.pointer);
    };
    const down = (e: PointerEvent) => {
      if (e.pointerType === "touch" || active || canvas.dataset.mouseOwner) return;
      const p = point(e); canvas.focus({ preventScroll: true }); setMenu(null);
      const hit = viewer.scene.pick(new C.Cartesian2(p.x, p.y)); if (String(hit?.id?.id ?? "").startsWith("transform:")) return;
      const kind = e.button === 1 ? e.shiftKey ? "pan" : "orbit" : e.button === 0 && available() ? prefs.current.mode : null;
      if (!kind || kind === "select" && (!available() || latest.current.editor.tool !== "select")) return;
      e.preventDefault(); e.stopImmediatePropagation(); viewer.camera.cancelFlight();
      pivot = pivotAt(p); if (kind !== "select" && !pivot) return;
      active = { pointer: e.pointerId, start: p, last: p, kind, dragged: false, shift: e.shiftKey, ctrl: e.ctrlKey || e.metaKey, release: cameraLease(controller) };
      canvas.dataset.mouseOwner = kind; canvas.setPointerCapture(e.pointerId); canvas.style.cursor = kind === "select" ? "crosshair" : "grabbing";
    };
    const move = (e: PointerEvent) => {
      if (!active || active.pointer !== e.pointerId) return; e.preventDefault(); e.stopImmediatePropagation();
      const p = point(e), dx = p.x - active.last.x, dy = p.y - active.last.y;
      active.last = p; active.dragged ||= dragStarted(p.x, p.y, active.start.x, active.start.y);
      if (active.kind === "select") { if (active.dragged) setBox({ x: Math.min(p.x, active.start.x), y: Math.min(p.y, active.start.y), width: Math.abs(p.x - active.start.x), height: Math.abs(p.y - active.start.y) }); return; }
      if (!pivot) return;
      if (active.kind === "orbit") {
        const tilt = C.Math.clamp(viewer.camera.pitch - dy * .005 * prefs.current.sensitivity, -Math.PI / 2 + .01, latest.current.modelView || latest.current.underground ? Math.PI / 2 - .01 : -.02) - viewer.camera.pitch;
        const heading = C.Quaternion.fromAxisAngle(C.Ellipsoid.WGS84.geodeticSurfaceNormal(pivot, new C.Cartesian3()), -dx * .005 * prefs.current.sensitivity);
        const pitch = C.Quaternion.fromAxisAngle(viewer.camera.rightWC, tilt);
        const rotation = C.Matrix3.fromQuaternion(C.Quaternion.multiply(heading,pitch,new C.Quaternion()));
        const rotate = (value:Cesium.Cartesian3) => C.Matrix3.multiplyByVector(rotation,value,new C.Cartesian3());
        viewer.camera.setView({destination:cameraDestination(C.Cartesian3.add(pivot,rotate(C.Cartesian3.subtract(viewer.camera.positionWC,pivot,new C.Cartesian3())),new C.Cartesian3())),orientation:{direction:rotate(viewer.camera.directionWC),up:rotate(viewer.camera.upWC)}});
      } else {
        const distance = C.Cartesian3.distance(viewer.camera.positionWC, pivot), scale = distance * .0015 * prefs.current.sensitivity;
        const delta = C.Cartesian3.add(C.Cartesian3.multiplyByScalar(viewer.camera.rightWC, -dx * scale, new C.Cartesian3()), C.Cartesian3.multiplyByScalar(viewer.camera.upWC, dy * scale, new C.Cartesian3()), new C.Cartesian3());
        pivot = C.Cartesian3.add(pivot, delta, new C.Cartesian3()); viewer.camera.setView({ destination: cameraDestination(C.Cartesian3.add(viewer.camera.positionWC, delta, new C.Cartesian3())), orientation: { direction: viewer.camera.directionWC, up: viewer.camera.upWC } });
      } viewer.scene.requestRender();
    };
    const wheel = (e: WheelEvent) => {
      if (active || canvas.dataset.mouseOwner === "transform" || !controller.enableInputs) return;
      const p = point(e); let target: Cesium.Cartesian3 | null = null;
      if(latest.current.modelView && viewer.scene.pickPositionSupported) { try { target=viewer.scene.pickPosition(new C.Cartesian2(p.x,p.y)) ?? null; } catch { /* use the last valid pivot when depth is unavailable */ } }
      target ??= pivotAt(p); if (!target) return; e.preventDefault(); e.stopImmediatePropagation(); viewer.camera.cancelFlight();
      const ray = viewer.camera.getPickRay(new C.Cartesian2(p.x, p.y)); if (!ray) return;
      const distance = C.Cartesian3.distance(viewer.camera.positionWC, target), factor = Math.exp(C.Math.clamp(e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? canvas.clientHeight : 1) * .001 * prefs.current.sensitivity * (prefs.current.invert ? -1 : 1), -.5, .5));
      const step = distance - C.Math.clamp(distance * factor, .25, 2e7);
      viewer.camera.setView({ destination: cameraDestination(C.Cartesian3.add(viewer.camera.positionWC, C.Cartesian3.multiplyByScalar(ray.direction, step, new C.Cartesian3()), new C.Cartesian3())), orientation: { direction: viewer.camera.directionWC, up: viewer.camera.upWC } }); pivot = target; viewer.scene.requestRender();
    };
    const context = (e: MouseEvent) => { e.preventDefault(); if (!available() || active || canvas.dataset.mouseOwner === "transform") return; const p = point(e); setMenu({ x: Math.min(p.x, canvas.clientWidth - 245), y: Math.min(p.y, canvas.clientHeight - 380), ids: picked(p) }); };
    const double = (e: MouseEvent) => { cancelInspect(); if (!available()) return; e.preventDefault(); e.stopImmediatePropagation(); const p=point(e);const ids=(recentClick(p)?.ids ?? picked(p)).filter(id=>latest.current.editor.document?.components.some(c=>c.id===id&&c.visible)).slice(0,1);firstClick=null; if (ids.length) { latest.current.editor.selectMany(ids); focus(ids); window.dispatchEvent(new Event("geoai:selection-inspect")); } };
    const key = (e: KeyboardEvent) => { if (document.activeElement !== canvas) return; if (e.key === "Escape") { stop(true); setMenu(null); setMode("select"); } if (canvas.dataset.mouseOwner === "transform" || !available() || e.ctrlKey || e.metaKey || e.altKey) return; if (e.key.toLowerCase() === "f" || e.key === "Home") { e.preventDefault(); e.stopImmediatePropagation(); if (e.key === "Home") { pivot = null; latest.current.fit(); } else focus(latest.current.editor.selectedIds); } };
    const up = (e: PointerEvent) => { if (active?.pointer === e.pointerId) { e.stopImmediatePropagation(); stop(); } };
    const cancel = () => stop(true);
    const suppressClick = (e: MouseEvent) => { if (available() && latest.current.editor.tool === "select") e.stopImmediatePropagation(); };
    canvas.addEventListener("pointerdown", down, true); canvas.addEventListener("pointermove", move, true); window.addEventListener("pointerup", up, true);
    canvas.addEventListener("wheel", wheel, { capture: true, passive: false }); canvas.addEventListener("contextmenu", context); canvas.addEventListener("dblclick", double, true); canvas.addEventListener("click", suppressClick, true);
    canvas.addEventListener("pointercancel", cancel); canvas.addEventListener("lostpointercapture", cancel); window.addEventListener("blur", cancel); canvas.addEventListener("keydown", key, true);
    const modeChange = () => { cancelInspect(); stop(true); setMenu(null); }; window.addEventListener("geoai:cancel-gesture", modeChange);
    const orient = (event:Event) => {
      stop(true); const detail=(event as CustomEvent<{heading:number;pitch:number}>).detail;
      const values=spheres(latest.current.editor.selectedIds);
      const sphere=values.length ? C.BoundingSphere.fromBoundingSpheres(values) : latest.current.bounds();
      const target=latest.current.modelView && sphere ? sphere.center : pivotAt({x:canvas.clientWidth/2,y:canvas.clientHeight/2}); if(!target)return;
      pivot=C.Cartesian3.clone(target); viewer.camera.cancelFlight();
      const heading=C.Math.toRadians(detail.heading),pitch=C.Math.toRadians(detail.pitch);
      const framed=sphere&&latest.current.modelView ? frameEntities(C,latest.current.entities(),sphere,heading,pitch,Number((viewer.camera.frustum as {fovy?:number}).fovy??Math.PI/3),canvas.clientWidth/Math.max(1,canvas.clientHeight),values.length ? e=>latest.current.editor.selectedIds.includes(e.properties?.getValue(viewer.clock.currentTime)?.editableComponentId) : undefined) : null;
      viewer.camera.flyToBoundingSphere(framed?.sphere ?? new C.BoundingSphere(target,sphere?.radius ?? 1),{duration:.35,offset:new C.HeadingPitchRange(heading,pitch,framed?.range ?? (sphere ? Math.max(.5,sphere.radius*3.4) : Math.max(50,C.Cartesian3.distance(viewer.camera.positionWC,target))))});
    }; window.addEventListener("geoai:orient-view",orient);
    const assistantFocus=(event:Event)=>{const command=(event as CustomEvent<WorkspaceCommand>).detail;if(command.operation!=='focus_components')return;const ed=latest.current.editor;if(command.projectId!==ed.document?.project_id||command.revisionId!==ed.baseRevision?.id||ed.dirty){outcome(command,false,'Camera source changed.');return;}focus(command.componentIds,ok=>outcome(command,ok,ok?'Camera focused on the requested saved geometry.':'Camera focus failed or was cancelled; no completion is claimed.'));};
    window.addEventListener('geoai:workspace-camera',assistantFocus);
    const fitSelection=()=>focus(latest.current.editor.selectedIds);
    window.addEventListener("geoai:fit-selection",fitSelection);
    return () => { cancelInspect(); stop(true); controller.rotateEventTypes = old.rotate; controller.translateEventTypes = old.translate; controller.zoomEventTypes = old.zoom; controller.tiltEventTypes = old.tilt; controller.lookEventTypes = old.look;
      window.removeEventListener("geoai:workspace-camera",assistantFocus); window.removeEventListener("geoai:fit-selection",fitSelection); window.removeEventListener("geoai:orient-view",orient); delete canvas.dataset.navigationMode;
      canvas.removeEventListener("pointerdown", down, true); canvas.removeEventListener("pointermove", move, true); window.removeEventListener("pointerup", up, true); canvas.removeEventListener("wheel", wheel, true); canvas.removeEventListener("contextmenu", context); canvas.removeEventListener("dblclick", double, true); canvas.removeEventListener("click", suppressClick, true); canvas.removeEventListener("pointercancel", cancel); canvas.removeEventListener("lostpointercapture", cancel); window.removeEventListener("blur", cancel); canvas.removeEventListener("keydown", key, true); window.removeEventListener("geoai:cancel-gesture", modeChange); };
  }, [props.viewer, props.C]);
  useEffect(() => { window.dispatchEvent(new Event("geoai:cancel-gesture")); }, [props.editor.tool, props.modelView, mode, drawingTool, measurementTool]);
  const act = (action: "inspect" | "fit" | "translate" | "rotate" | "scale") => { const ids = menu?.ids[0] ? [menu.ids[0]] : props.editor.selectedIds; props.editor.selectMany(ids); if (action === "inspect") window.dispatchEvent(new Event("geoai:inspect-component")); else if (action === "fit") window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: ids[0] })); else props.editor.setTool(action); setMenu(null); };
  const target = props.editor.document?.components.find(c => c.id === (menu?.ids[0] ?? props.editor.selectedIds[0]));
  const overlapName=(id:string)=>{const c=props.editor.document?.components.find(c=>c.id===id);return c?componentDisplayName(c):"Unavailable component";};
  const editable = !!target && !target.locked && target.geometry.kind !== "asset_instance" && !props.editor.comparison && !props.editor.platformPreview;
  return <>
    {box && <div className="pointer-events-none absolute z-40 border border-sky-300 bg-sky-400/15" style={{ left: box.x, top: box.y, width: box.width, height: box.height }} />}
    <div className="absolute bottom-40 left-24 z-30 flex gap-2 rounded border border-white/15 bg-background/95 p-2 text-xs" aria-label="Mouse navigation">
      {(["select", "orbit", "pan"] as const).map(value => <button key={value} aria-pressed={mode === value} className={mode === value ? "text-primary" : "text-muted-foreground"} onClick={() => setMode(value)}>{value[0].toUpperCase() + value.slice(1)}</button>)}<button onClick={() => setHelp(!help)} aria-expanded={help}>Mouse controls</button>
    </div>
    {help && <div className="absolute bottom-52 left-24 z-40 w-72 rounded border border-white/20 bg-background p-4 text-xs shadow-xl"><p className="mb-2 font-semibold">3D modeling controls</p><p>Middle drag · orbit<br />Shift + middle drag · pan<br />Wheel · zoom toward pointer<br />Click · select · Shift/Ctrl · toggle<br />Drag · box select · Shift add / Ctrl remove<br />Double-click / F · focus · Home · fit model<br />Drag a handle · X/Y/Z constrain · type a value<br />Or G/R/S → axis → value → Enter<br />Enter · confirm · Escape · cancel · Alt · snap target</p><label className="mt-3 block">Sensitivity <input aria-label="Mouse sensitivity" type="range" min="0.25" max="2" step="0.25" value={sensitivity} onChange={e => savePreference(Number(e.target.value), invert)} /></label><label className="flex gap-2"><input type="checkbox" checked={invert} onChange={e => savePreference(sensitivity, e.target.checked)} />Invert wheel zoom</label><button className="mt-2 text-primary" onClick={() => setHelp(false)}>Close mouse controls</button></div>}
    {menu && <div role="menu" aria-label="Object actions" className="absolute z-50 w-60 overflow-auto rounded border border-white/20 bg-background p-2 text-xs shadow-xl" style={{ left: Math.max(70, menu.x), top: Math.max(0, menu.y), maxHeight: Math.max(120, props.viewer.canvas.clientHeight-8) }}>
      <p className="truncate px-2 py-1 font-semibold">{target ? componentDisplayName(target) : "No object here"}</p>{(["inspect", "fit", "translate", "rotate", "scale"] as const).map(action => <button role="menuitem" key={action} disabled={!target || !["inspect", "fit"].includes(action) && (!editable || action === "scale" && target.geometry.kind === "cad_mesh")} className="block w-full rounded px-2 py-1.5 text-left hover:bg-white/10 disabled:opacity-40" onClick={() => act(action)}>{{ inspect: "Inspect", fit: "Fit selection", translate: "Move", rotate: "Rotate", scale: "Scale" }[action]}</button>)}{menu.ids.length > 1 && <><p className="mt-2 px-2 text-muted-foreground">Choose overlapping object</p><div className="max-h-32 overflow-auto">{menu.ids.map(id => <button key={id} role="menuitem" className="block w-full truncate px-2 py-1.5 text-left hover:bg-white/10" onClick={() => { props.editor.selectMany([id]); setMenu({ ...menu, ids: [id, ...menu.ids.filter(value => value !== id)] }); }}>{overlapName(id)}</button>)}</div></>}<button className="px-2 py-1 text-muted-foreground" onClick={() => setMenu(null)}>Close</button>
    </div>}
  </>;
}
