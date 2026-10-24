"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { COMPONENT_SIZES } from "@/lib/local-sandbox";
import type { StructuralElementType } from "@/lib/types";
import { componentObject, releaseComponentObject } from "@/lib/sandbox-geometry";

type Props = {
  editor: EditableModelEditor;
  placement: StructuralElementType | null;
  onPlaced: () => void;
  fit: { sequence: number; selected: boolean };
};

function Scene({ editor, placement, onPlaced, fit }: Props) {
  const { camera, gl, scene } = useThree();
  const orbit = useRef<OrbitControls | null>(null);
  const rootRef = useRef<THREE.Group | null>(null);

  useEffect(() => {
    const controls = new OrbitControls(camera, gl.domElement);
    controls.enableDamping = true;
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minDistance = 1;
    controls.maxDistance = 5000;
    orbit.current = controls;
    return () => { controls.dispose(); orbit.current = null; };
  }, [camera, gl]);
  useFrame(() => orbit.current?.update());

  const { document, selectedIds, tool, snapMeters, select, commitTransforms, addStructuralComponent } = editor;
  useEffect(() => {
    if (!document) return;
    const root = new THREE.Group();
    root.rotation.x = -Math.PI / 2;
    rootRef.current = root;
    scene.add(root);
    for (let distance = -50; distance <= 50; distance += 10) {
      if (distance === 0) continue;
      for (const axis of [0, 1]) {
        const labelCanvas = window.document.createElement("canvas");
        labelCanvas.width = 128; labelCanvas.height = 48;
        const context = labelCanvas.getContext("2d")!;
        context.font = "500 28px sans-serif"; context.fillStyle = "#a4b2a4"; context.textAlign = "center";
        context.fillText(`${distance} m`, 64, 33);
        const texture = new THREE.CanvasTexture(labelCanvas);
        const marker = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: true }));
        marker.position.set(axis === 0 ? distance : 0, axis === 1 ? distance : 0, 0.03);
        marker.scale.set(3, 1.125, 1);
        root.add(marker);
      }
    }
    const objects = new Map<string, THREE.Group>();
    for (const component of document.components) {
      if (!component.visible) continue;
      const object = componentObject(component);
      if (selectedIds.includes(component.id)) object.traverse((o) => {
        if (o instanceof THREE.Mesh) { o.material.emissive = new THREE.Color("#bfff00"); o.material.emissiveIntensity = 0.22; }
      });
      objects.set(component.id, object);
      root.add(object);
    }

    const editable = document.components.filter((c) => selectedIds.includes(c.id) && !c.locked && c.visible);
    const pivot = new THREE.Group();
    root.add(pivot);
    if (editable.length) {
      for (const c of editable) pivot.position.add(new THREE.Vector3().fromArray(c.transform.position));
      pivot.position.divideScalar(editable.length);
    }
    root.updateMatrixWorld(true);
    const control = new TransformControls(camera, gl.domElement);
    control.setSpace("local");
    control.setTranslationSnap(snapMeters);
    control.setRotationSnap(THREE.MathUtils.degToRad(15));
    control.setScaleSnap(0.1);
    control.setSize(0.85);
    if (tool !== "select" && editable.length && !placement) {
      control.setMode(tool);
      control.attach(pivot);
    }
    scene.add(control.getHelper());
    let cancelled = false;
    let startMatrix = new THREE.Matrix4();
    let originals = new Map<string, THREE.Matrix4>();
    const begin = () => {
      cancelled = false;
      orbit.current!.enabled = false;
      pivot.updateMatrix();
      startMatrix = pivot.matrix.clone();
      originals = new Map(editable.map((c) => { const object = objects.get(c.id)!; object.updateMatrix(); return [c.id, object.matrix.clone()]; }));
    };
    const previewTransform = () => {
      if (!control.dragging || cancelled) return;
      pivot.scale.set(Math.max(0.05, pivot.scale.x), Math.max(0.05, pivot.scale.y), Math.max(0.05, pivot.scale.z));
      pivot.updateMatrix();
      const delta = pivot.matrix.clone().multiply(startMatrix.clone().invert());
      for (const [id, original] of originals) {
        const object = objects.get(id)!;
        delta.clone().multiply(original).decompose(object.position, object.quaternion, object.scale);
      }
    };
    const finish = () => {
      if (orbit.current) orbit.current.enabled = true;
      if (cancelled) return;
      const patches = editable.map((c) => {
        const object = objects.get(c.id)!;
        return { id: c.id, transform: {
          position: object.position.toArray() as [number, number, number],
          rotation_deg: [object.rotation.x, object.rotation.y, object.rotation.z].map(THREE.MathUtils.radToDeg) as [number, number, number],
          scale: object.scale.toArray() as [number, number, number],
        } };
      });
      commitTransforms(patches);
    };
    const restoreDrag = () => {
      if (!control.dragging) return;
      cancelled = true;
      control.reset();
      for (const [id, matrix] of originals) {
        const object = objects.get(id)!;
        matrix.decompose(object.position, object.quaternion, object.scale);
      }
      control.pointerUp(null);
      if (orbit.current) orbit.current.enabled = true;
    };
    const cancelDrag = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || (event.target instanceof HTMLElement && (event.target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)))) return;
      restoreDrag();
    };
    control.addEventListener("mouseDown", begin);
    control.addEventListener("objectChange", previewTransform);
    control.addEventListener("mouseUp", finish);
    window.addEventListener("keydown", cancelDrag);
    window.addEventListener("blur", restoreDrag);
    gl.domElement.addEventListener("pointercancel", restoreDrag);
    gl.domElement.addEventListener("lostpointercapture", restoreDrag);

    let ghost: THREE.Mesh | null = null;
    if (placement) {
      const size = COMPONENT_SIZES[placement];
      ghost = new THREE.Mesh(new THREE.BoxGeometry(...size), new THREE.MeshStandardMaterial({ color: "#c7ff00", transparent: true, opacity: 0.35, depthWrite: false }));
      ghost.visible = false;
      root.add(ghost);
    }
    const raycaster = new THREE.Raycaster();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const cursor = new THREE.Vector2();
    const worldPoint = new THREE.Vector3();
    const setRay = (event: PointerEvent) => {
      const rect = gl.domElement.getBoundingClientRect();
      cursor.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(cursor, camera);
    };
    const move = (event: PointerEvent) => {
      if (!ghost || !placement) return;
      setRay(event);
      if (!raycaster.ray.intersectPlane(plane, worldPoint)) { ghost.visible = false; return; }
      ghost.visible = true;
      ghost.position.set(Math.round(worldPoint.x / snapMeters) * snapMeters, Math.round(-worldPoint.z / snapMeters) * snapMeters, COMPONENT_SIZES[placement][2] / 2);
    };
    let down: { x: number; y: number; gizmo: boolean } | null = null;
    const pointerDown = (event: PointerEvent) => {
      down = { x: event.clientX, y: event.clientY, gizmo: Boolean(control.axis) };
    };
    const pointerUp = (event: PointerEvent) => {
      if (event.button !== 0 || !down || down.gizmo || control.dragging || Math.hypot(event.clientX - down.x, event.clientY - down.y) > 4) return;
      if (placement && ghost) {
        move(event);
        if (ghost.visible) { addStructuralComponent(placement, ghost.position.toArray() as [number, number, number]); onPlaced(); }
        return;
      }
      setRay(event);
      const hit = raycaster.intersectObjects([...objects.values()], true)[0];
      let picked: THREE.Object3D | null = hit?.object ?? null;
      while (picked && !picked.userData.componentId) picked = picked.parent;
      select(picked?.userData.componentId ?? null, event.shiftKey || event.ctrlKey || event.metaKey);
    };
    gl.domElement.addEventListener("pointermove", move);
    gl.domElement.addEventListener("pointerdown", pointerDown);
    gl.domElement.addEventListener("pointerup", pointerUp);
    const enable = () => { control.enabled = true; };
    gl.domElement.addEventListener("pointerup", enable);
    gl.domElement.setAttribute("data-sandbox-ready", "true");
    gl.domElement.setAttribute("data-placement", placement ?? "");
    return () => {
      restoreDrag();
      gl.domElement.removeAttribute("data-sandbox-ready");
      gl.domElement.removeAttribute("data-placement");
      window.removeEventListener("keydown", cancelDrag);
      window.removeEventListener("blur", restoreDrag);
      gl.domElement.removeEventListener("pointercancel", restoreDrag);
      gl.domElement.removeEventListener("lostpointercapture", restoreDrag);
      gl.domElement.removeEventListener("pointermove", move);
      gl.domElement.removeEventListener("pointerdown", pointerDown);
      gl.domElement.removeEventListener("pointerup", pointerUp);
      gl.domElement.removeEventListener("pointerup", enable);
      if (orbit.current) orbit.current.enabled = true;
      control.detach(); control.dispose(); scene.remove(control.getHelper());
      scene.remove(root); releaseComponentObject(root); rootRef.current = null;
    };
  }, [document, selectedIds, tool, snapMeters, select, commitTransforms, addStructuralComponent, placement, onPlaced, camera, gl, scene]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root || !orbit.current) return;
    const bounds = new THREE.Box3();
    for (const child of root.children) {
      if (!child.userData.componentId || (fit.selected && !editor.selectedIds.includes(child.userData.componentId))) continue;
      bounds.expandByObject(child);
    }
    const center = bounds.isEmpty() ? new THREE.Vector3() : bounds.getCenter(new THREE.Vector3());
    const size = bounds.isEmpty() ? 30 : Math.max(5, bounds.getSize(new THREE.Vector3()).length());
    const perspective = camera as THREE.PerspectiveCamera;
    const distance = size / (2 * Math.tan(THREE.MathUtils.degToRad(perspective.fov / 2))) / Math.min(1, perspective.aspect) * 1.4;
    camera.position.copy(center).add(new THREE.Vector3(1, 0.9, 1).normalize().multiplyScalar(distance));
    orbit.current.target.copy(center);
    orbit.current.update();
    // Fit is an explicit action; editing never resets the camera.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fit.sequence, camera]);

  return <>
    <color attach="background" args={["#171d21"]} />
    <ambientLight intensity={1.3} />
    <directionalLight position={[40, 65, 25]} intensity={2.2} />
    <gridHelper args={[200, 200, "#46544a", "#2a3438"]} position={[0, -0.02, 0]} />
    <gridHelper args={[200, 20, "#6f8b52", "#42514b"]} position={[0, -0.01, 0]} />
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.03, 0]}><planeGeometry args={[10000, 10000]} /><meshStandardMaterial color="#171d21" /></mesh>
    <axesHelper args={[8]} rotation={[-Math.PI / 2, 0, 0]} />
  </>;
}

export default function SandboxGrid(props: Props) {
  return <Canvas aria-label="3D layout grid" camera={{ position: [32, 28, 32], fov: 45, near: 0.1, far: 20000 }} dpr={[1, 1.5]}><Scene {...props} /></Canvas>;
}
