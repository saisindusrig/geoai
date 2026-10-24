import type * as Cesium from "cesium";
import * as THREE from "three";
import type { EditableModelDocument,GeoJSONGeometry } from "./types";
import { applyTransformDelta, cameraLease, snap, transformMatrix, transformPivot, type TransformSettings } from "./editor-transform";
import { numericTransformValue } from "./viewport-interaction";
import { engineeringSnapTargets, snapTranslationToTargets } from "./engineering-snap";

type Patch = ReturnType<typeof applyTransformDelta>;
export function installCesiumTransform(C: typeof Cesium, viewer: Cesium.Viewer, doc: EditableModelDocument, selectedIds: string[], settings: TransformSettings,
  collection: Cesium.PrimitiveCollection, commit: (patches: Patch) => void, feedback: (message: string | null) => void, alignment?:GeoJSONGeometry|null, modelEntities: Cesium.Entity[] = [], pointerFeedback?: (point: {x:number;y:number} | null) => void) {
  const canvas = viewer.scene.canvas;
  const selected = selectedIds.map(id => doc.components.find(item => item.id === id)).filter((item): item is EditableModelDocument["components"][number] => !!item && item.visible && !item.locked && item.geometry.kind !== "asset_instance");
  if (!selected.length || settings.mode === "select") {
    if(settings.mode!=="select" && selectedIds.length)feedback(doc.components.some(item=>selectedIds.includes(item.id)&&item.locked)?"OBJECT LOCKED · Unlock to edit.":"This reference geometry does not support viewport transforms.");
    return () => {};
  }
  const origin = C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(doc.origin.lng, doc.origin.lat, doc.origin.elevation_m));
  const frame = new THREE.Matrix4().fromArray(Array.from(origin)).multiply(new THREE.Matrix4().makeRotationZ(doc.origin.heading_deg * Math.PI / 180));
  const inverse = frame.clone().invert();
  const pivot = transformPivot(selected, settings.pivot);
  const alignmentTargets:ReturnType<typeof engineeringSnapTargets>=[];
  if(alignment?.type==="LineString"){
    try{
      const coordinates=alignment.coordinates as [number,number][];
      let chainage=0;
      for(let index=1;index<coordinates.length;index++){
        const a=coordinates[index-1],b=coordinates[index];
        if(![...a,...b].every(Number.isFinite))continue;
        const line=new C.EllipsoidGeodesic(C.Cartographic.fromDegrees(a[0],a[1]),C.Cartographic.fromDegrees(b[0],b[1]));
        if(line.surfaceDistance<=0)continue;
        const add=(coordinate:Cesium.Cartographic,name:string)=>{
          const world=C.Cartesian3.fromRadians(coordinate.longitude,coordinate.latitude,doc.origin.elevation_m);
          const point=new THREE.Vector3(world.x,world.y,world.z).applyMatrix4(inverse);point.z=pivot.z;
          alignmentTargets.push({name,point});
        };
        add(C.Cartographic.fromDegrees(a[0],a[1]),"Alignment endpoint (plan)");
        for(let station=Math.ceil(chainage/20)*20;station<=chainage+line.surfaceDistance && alignmentTargets.length<1000;station+=20)add(line.interpolateUsingSurfaceDistance(station-chainage),`Alignment ${station.toFixed(0)} m (plan)`);
        chainage+=line.surfaceDistance;
        add(C.Cartographic.fromDegrees(b[0],b[1]),"Alignment endpoint (plan)");
      }
    }catch{feedback("Alignment snapping requires valid geographic design coordinates.");}
  }
  const toWorld = (point: THREE.Vector3) => { const world = point.clone().applyMatrix4(frame); return new C.Cartesian3(world.x, world.y, world.z); };
  const ds = new C.CustomDataSource("transform-handles");
  void viewer.dataSources.add(ds);
  let length = Math.max(.15, C.Cartesian3.distance(viewer.camera.positionWC, toWorld(pivot)) * 0.075);
  const axes = [new THREE.Vector3(1,0,0), new THREE.Vector3(0,1,0), new THREE.Vector3(0,0,1)].map(axis => settings.coordinates === "world" ? axis.transformDirection(inverse) : axis);
  const colors = ["#db6666", "#72b47c", "#659bd1"];
  const handle = (id: string, position: THREE.Vector3, color: string) => ds.entities.add({ id: `transform:${id}`, position: toWorld(position), point: { pixelSize: 20, color: C.Color.fromCssColorString(color), outlineColor: C.Color.BLACK, outlineWidth: 1, disableDepthTestDistance: Infinity }, label:{text:id === "uniform" ? "All" : id,font:"600 12px sans-serif",pixelOffset:new C.Cartesian2(14,-12),fillColor:C.Color.WHITE,showBackground:true,backgroundColor:C.Color.BLACK.withAlpha(.7),disableDepthTestDistance:Infinity} });
  ds.entities.add({ position: toWorld(pivot), point: { pixelSize: 8, color: C.Color.WHITE, disableDepthTestDistance: Infinity } });
  axes.forEach((axis, index) => {
    const name = "XYZ"[index];
    if (settings.mode === "rotate") {
      const u = axes[(index + 1) % 3], v = axes[(index + 2) % 3];
      ds.entities.add({ id: `transform:${name}`, polyline: { positions: Array.from({length: 73}, (_, step) => toWorld(pivot.clone().addScaledVector(u, Math.cos(step * Math.PI / 36) * length).addScaledVector(v, Math.sin(step * Math.PI / 36) * length))), width: 8, material: C.Color.fromCssColorString(colors[index]), depthFailMaterial: C.Color.fromCssColorString(colors[index]) } });
    } else {
      const supported = settings.mode !== "scale" || settings.coordinates === "local" && selected.every(item => item.transform.rotation_deg.every(value => value === 0));
      if (!supported) return;
      ds.entities.add({ id: `transform:line-${name}`, polyline: { positions: [toWorld(pivot), toWorld(pivot.clone().addScaledVector(axis, length))], width: 4, material: settings.mode === "translate" ? new C.PolylineArrowMaterialProperty(C.Color.fromCssColorString(colors[index])) : C.Color.fromCssColorString(colors[index]) } });
      handle(name, pivot.clone().addScaledVector(axis, length), colors[index]);
    }
  });
  if (settings.mode === "translate") for (const [i,j] of [[0,1],[0,2],[1,2]]) handle(`${"XYZ"[i]}${"XYZ"[j]}`, pivot.clone().addScaledVector(axes[i], length * 0.3).addScaledVector(axes[j], length * 0.3), "#9eaa92");
  if (settings.mode === "scale") handle("uniform", pivot, "#60a5fa");
  const primitives = new Map<string, Cesium.Primitive>();
  for (let index = 0; index < collection.length; index++) {
    const primitive = collection.get(index) as Cesium.Primitive & {componentId?: string};
    if (primitive.componentId) primitives.set(primitive.componentId, primitive);
  }
  const originals = modelEntities.flatMap(entity => {
    const properties = entity.properties?.getValue(viewer.clock.currentTime);
    if (!properties?.transformEdge || !selectedIds.includes(properties.editableComponentId)) return [];
    const positions = entity.polyline?.positions?.getValue(viewer.clock.currentTime);
    return positions ? [{ entity, positions: positions.map((p: Cesium.Cartesian3) => C.Cartesian3.clone(p)), id: String(properties.editableComponentId) }] : [];
  });
  const sameTransform = (patch: Patch[number]) => JSON.stringify(patch.transform) === JSON.stringify(selected.find(item => item.id === patch.id)?.transform);
  let numeric = "";
  let lastEvent: PointerEvent | null = null;
  let drag: { pointer: number; name: string; plane: THREE.Plane; start: THREE.Vector3; x: number; y: number; axis: THREE.Vector3; release: () => void; patches: Patch } | null = null;
  let disposed = false;
  const ray = (event: PointerEvent) => {
    const rect = canvas.getBoundingClientRect();
    const world = viewer.camera.getPickRay(new C.Cartesian2(event.clientX - rect.left, event.clientY - rect.top));
    if (!world) return null;
    return new THREE.Ray(new THREE.Vector3(world.origin.x, world.origin.y, world.origin.z).applyMatrix4(inverse), new THREE.Vector3(world.direction.x,world.direction.y,world.direction.z).transformDirection(inverse));
  };
  const finish = (cancel: boolean) => {
    const active = drag; drag = null;
    if (!active) return;
    try {
      for (const item of selected) { const primitive = primitives.get(item.id); if (primitive && !primitive.isDestroyed?.()) primitive.modelMatrix = C.Matrix4.clone(C.Matrix4.IDENTITY); }
      for (const edge of originals) edge.entity.polyline!.positions = new C.ConstantProperty(edge.positions);
      if (!cancel && active.patches.some(patch => !sameTransform(patch))) commit(active.patches);
    } catch (error) { feedback(error instanceof Error ? error.message : "Transform failed"); }
    finally {
      active.release(); delete canvas.dataset.mouseOwner; numeric = ""; lastEvent = null; pointerFeedback?.(null); canvas.style.cursor = "";
      if (active.pointer >= 0 && canvas.hasPointerCapture(active.pointer)) canvas.releasePointerCapture(active.pointer);
      if (!viewer.isDestroyed()) viewer.scene.requestRender();
      feedback(null);
    }
  };
  const down = (event: PointerEvent) => {
    if (event.button !== 0 || disposed || canvas.dataset.mouseOwner && canvas.dataset.mouseOwner !== "transform") return;
    if (drag?.pointer === -1) finish(true);
    if (drag) return;
    const rect = canvas.getBoundingClientRect();
    const entity = viewer.scene.pick(new C.Cartesian2(event.clientX - rect.left,event.clientY - rect.top))?.id;
    const id: string = entity?.id ?? "";
    if (!id.startsWith("transform:")) return;
    event.stopImmediatePropagation(); event.preventDefault();
    const name = id.slice(10).replace("line-", "");
    const axis = axes[Math.max(0, "XYZ".indexOf(name))];
    const cameraDirection = new THREE.Vector3(viewer.camera.directionWC.x, viewer.camera.directionWC.y, viewer.camera.directionWC.z).transformDirection(inverse);
    const normal = settings.mode === "rotate" ? axis.clone() : name.length === 2 ? axes["XYZ".indexOf("XYZ".split("").find(value => !name.includes(value))!)].clone() : cameraDirection.clone().addScaledVector(axis,-cameraDirection.dot(axis)).normalize();
    if (normal.lengthSq() < 0.001) return;
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(normal,pivot);
    const start = ray(event)?.intersectPlane(plane,new THREE.Vector3());
    if (!start) return;
    const release = cameraLease(viewer.scene.screenSpaceCameraController);
    try { canvas.setPointerCapture(event.pointerId); drag = { pointer:event.pointerId,name,plane,start,x:event.clientX,y:event.clientY,axis,release,patches:[] }; canvas.dataset.mouseOwner="transform"; lastEvent=event; feedback(`${settings.mode.toUpperCase()} ${name} · drag or type a value · Enter confirms · Esc cancels`); canvas.focus({preventScroll:true}); canvas.style.cursor="grabbing"; }
    catch (error) { release(); feedback(String(error)); }
  };
  const move = (event: PointerEvent) => {
    if (!drag) return;
    lastEvent = event; pointerFeedback?.({x:event.clientX-canvas.getBoundingClientRect().left+18,y:event.clientY-canvas.getBoundingClientRect().top+18});
    event.stopImmediatePropagation();
    try {
      const point = ray(event)?.intersectPlane(drag.plane,new THREE.Vector3());
      if (!point) return;
      const displacement = point.clone().sub(drag.start);
      let amount = displacement.dot(drag.axis);
      let delta: THREE.Vector3 | undefined;
      if (settings.mode === "rotate") {
        const start = drag.start.clone().sub(pivot).normalize(), current = point.clone().sub(pivot).normalize();
        amount = Math.atan2(drag.axis.dot(start.clone().cross(current)), start.dot(current)) * 180 / Math.PI;
      } else if (settings.mode === "scale") amount = 1 + (event.clientX - drag.x) / 150;
      else if (drag.name.length === 2) delta = drag.name.split("").reduce((sum,name) => { const axis = axes["XYZ".indexOf(name)]; return sum.addScaledVector(axis,snap(displacement.dot(axis),settings.translationSnap)); },new THREE.Vector3());
      let snapTarget:string|null=null;
      if(settings.mode === "translate" && event.altKey){
        const allowed=drag.name.length===2?drag.name.split("").map(name=>axes["XYZ".indexOf(name)]):[drag.axis];
        const targets=[...engineeringSnapTargets(doc,selectedIds),...(allowed.every(axis=>Math.abs(axis.z)<1e-6)?alignmentTargets:[])];
        const target=snapTranslationToTargets(pivot,delta ?? drag.axis.clone().multiplyScalar(snap(amount,settings.translationSnap)),allowed,targets,Math.max(.25,settings.translationSnap));
        if(target){delta=target.delta;snapTarget=target.name;}
      }
      const exact = numericTransformValue(numeric, settings.mode);
      if (numeric && exact === null) { feedback(`Enter a valid ${settings.mode === "scale" ? "positive scale multiplier" : settings.mode === "rotate" ? "angle in degrees" : "distance in metres"}`); return; }
      if (exact !== null) { amount = exact; delta = undefined; snapTarget = null; }
      const effectiveSettings = exact !== null ? {...settings, translationSnap:0, rotationSnap:0, scaleSnap:0} : settings;
      drag.patches = applyTransformDelta(selected,effectiveSettings, drag.name === "uniform" ? new THREE.Vector3() : drag.axis,amount,delta);
      for (const patch of drag.patches) {
        const original = selected.find(item => item.id === patch.id)!;
        const matrix = frame.clone().multiply(transformMatrix(patch.transform)).multiply(transformMatrix(original.transform).invert()).multiply(inverse);
        const primitive = primitives.get(patch.id);
        if (primitive) primitive.modelMatrix = C.Matrix4.fromArray(matrix.elements);
        for (const edge of originals.filter(edge => edge.id === patch.id)) edge.entity.polyline!.positions = new C.ConstantProperty(edge.positions.map((p:Cesium.Cartesian3) => C.Matrix4.multiplyByPoint(C.Matrix4.fromArray(matrix.elements), p, new C.Cartesian3())));
      }
      const value = numeric || (settings.mode === "rotate" ? snap(amount,effectiveSettings.rotationSnap).toFixed(2) : settings.mode === "scale" ? snap(amount,effectiveSettings.scaleSnap).toFixed(3) : (delta?.length() ?? snap(amount,effectiveSettings.translationSnap)).toFixed(3));
      feedback(`${numeric ? "EXACT " : ""}${settings.mode.toUpperCase()} ${drag.name.toUpperCase()} · ${value}${settings.mode === "rotate" ? "°" : settings.mode === "scale" ? "×" : " m"}`);
      viewer.scene.requestRender();
      if(snapTarget)feedback(`MOVE ${drag.name} · SNAP ${snapTarget}`);
    } catch (error) { finish(true); feedback(error instanceof Error ? error.message : "Transform failed"); }
  };
  const up = (event: PointerEvent) => { if (drag && (event.pointerId === undefined || event.pointerId === drag.pointer) && !numeric) finish(false); }, cancel = () => finish(true);
  const key = (event: KeyboardEvent) => {
    if (document.activeElement !== canvas) return;
    if (!drag && !event.ctrlKey && !event.metaKey && !event.altKey && (/^[xyz]$/i.test(event.key) || /^[0-9.+-]$/.test(event.key))) {
      // Keyboard precision mode: G/R/S, optional axis, value, Enter.
      const name = /^[xyz]$/i.test(event.key) ? event.key.toUpperCase() : settings.mode === "scale" ? "uniform" : settings.mode === "rotate" ? "Z" : "X";
      const axis = axes[Math.max(0,"XYZ".indexOf(name))];
      const screen = C.SceneTransforms.worldToWindowCoordinates(viewer.scene,toWorld(pivot));
      if(!screen)return;
      const rect=canvas.getBoundingClientRect();
      const input={clientX:screen.x+rect.left,clientY:screen.y+rect.top,stopImmediatePropagation:()=>{}} as PointerEvent;
      const direction=new THREE.Vector3(viewer.camera.directionWC.x,viewer.camera.directionWC.y,viewer.camera.directionWC.z).transformDirection(inverse);
      const normal=settings.mode === "rotate" ? axis.clone() : direction.clone().addScaledVector(axis,-direction.dot(axis)).normalize();
      if(normal.lengthSq()<.001)return;
      const plane=new THREE.Plane().setFromNormalAndCoplanarPoint(normal,pivot),start=ray(input)?.intersectPlane(plane,new THREE.Vector3());if(!start)return;
      drag={pointer:-1,name,axis,plane,start,x:input.clientX,y:input.clientY,release:cameraLease(viewer.scene.screenSpaceCameraController),patches:[]};
      lastEvent=input;canvas.dataset.mouseOwner="transform";canvas.style.cursor="crosshair";
      feedback(`${settings.mode.toUpperCase()} ${name} · type a value · Enter confirms · Esc cancels`);
    }
    if (!drag) return;
    if (event.key === "Escape") { event.preventDefault(); event.stopImmediatePropagation(); cancel(); return; }
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === "Enter") { event.preventDefault(); event.stopImmediatePropagation(); if (!numeric || numericTransformValue(numeric,settings.mode) !== null) finish(false); return; }
    if (/^[xyz]$/i.test(event.key)) {
      event.preventDefault(); event.stopImmediatePropagation(); const name=event.key.toUpperCase(),axis=axes["XYZ".indexOf(name)];
      const cameraDirection = new THREE.Vector3(viewer.camera.directionWC.x,viewer.camera.directionWC.y,viewer.camera.directionWC.z).transformDirection(inverse);
      const normal=settings.mode === "rotate" ? axis.clone() : cameraDirection.clone().addScaledVector(axis,-cameraDirection.dot(axis)).normalize();
      if(normal.lengthSq()<.001)return;
      const plane=new THREE.Plane().setFromNormalAndCoplanarPoint(normal,pivot);
      const start=ray({clientX:drag.x,clientY:drag.y} as PointerEvent)?.intersectPlane(plane,new THREE.Vector3());
      if(start){drag.name=name;drag.axis=axis;drag.plane=plane;drag.start=start;if(lastEvent)move(lastEvent);}
    } else if (/^[0-9.+-]$/.test(event.key) || event.key === "Backspace") {
      event.preventDefault(); event.stopImmediatePropagation(); numeric=event.key === "Backspace" ? numeric.slice(0,-1) : numeric + event.key;
      if(lastEvent)move(lastEvent);
    }
  };
  canvas.addEventListener("pointerdown",down,true); canvas.addEventListener("pointermove",move,true);
  window.addEventListener("pointerup",up); canvas.addEventListener("pointercancel",cancel); canvas.addEventListener("lostpointercapture",cancel);
  window.addEventListener("blur",cancel); window.addEventListener("keydown",key,true);
  canvas.addEventListener("blur",cancel);
  canvas.dataset.transformReady = "true";
  const removeDiagnostics=viewer.scene.postRender?.addEventListener(()=>{
    const handles:Record<string,{x:number;y:number}>={};
    // Keep handles approximately 75 pixels long while navigating.
    if (!drag && viewer.camera.getPixelSize) {
      const nextLength = Math.max(.05, viewer.camera.getPixelSize(new C.BoundingSphere(toWorld(pivot),1),canvas.width,canvas.height) * 75 * canvas.width / Math.max(1,canvas.clientWidth));
      if(Number.isFinite(nextLength) && nextLength>0 && Math.abs(nextLength-length)>.001){
        const ratio=nextLength/length;
        for(const entity of ds.entities.values){
          const resize=(p:Cesium.Cartesian3)=>toWorld(new THREE.Vector3(p.x,p.y,p.z).applyMatrix4(inverse).sub(pivot).multiplyScalar(ratio).add(pivot));
          const p=entity.position?.getValue(viewer.clock.currentTime);if(p)entity.position=new C.ConstantPositionProperty(resize(p));
          const points=entity.polyline?.positions?.getValue(viewer.clock.currentTime);if(points)entity.polyline!.positions=new C.ConstantProperty(points.map(resize));
        }
        length=nextLength;
      }
    }
    const pivotScreen=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,toWorld(pivot));
    if(pivotScreen)handles.pivot={x:pivotScreen.x,y:pivotScreen.y};
    for(const entity of ds.entities.values){
      const position=entity.position?.getValue(viewer.clock.currentTime);
      if(!position)continue;
      const screen=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,position);
      if(screen)handles[entity.id.replace("transform:","")]={x:screen.x,y:screen.y};
    }
    canvas.dataset.transformHandles=JSON.stringify(handles);
    canvas.dataset.transformCameraEnabled=String(viewer.scene.screenSpaceCameraController.enableInputs);
  });
  viewer.scene.requestRender();
  return () => {
    disposed = true; cancel(); delete canvas.dataset.transformReady;
    removeDiagnostics?.();delete canvas.dataset.transformHandles;delete canvas.dataset.transformCameraEnabled;
    canvas.removeEventListener("pointerdown",down,true); canvas.removeEventListener("pointermove",move,true); window.removeEventListener("pointerup",up);
    canvas.removeEventListener("pointercancel",cancel); canvas.removeEventListener("lostpointercapture",cancel); window.removeEventListener("blur",cancel); window.removeEventListener("keydown",key,true);
    canvas.removeEventListener("blur",cancel);
    if (!viewer.isDestroyed()) viewer.dataSources.remove(ds,true);
  };
}
