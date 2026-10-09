import * as THREE from "three";
import type { EditableModelComponent } from "./types";

export type TransformSettings = {
  mode: "select" | "translate" | "rotate" | "scale";
  coordinates: "local" | "world";
  pivot: "active" | "median" | "individual";
  translationSnap: number;
  rotationSnap: number;
  scaleSnap: number;
};
export const defaultTransformSettings: TransformSettings = {
  mode: "select", coordinates: "local", pivot: "active",
  translationSnap: 0.5, rotationSnap: 15, scaleSnap: 0.1,
};
export const snap = (value: number, interval: number) => interval > 0 ? Math.round(value / interval) * interval : value;
export function transformMatrix(transform: EditableModelComponent["transform"]) {
  return new THREE.Matrix4().compose(new THREE.Vector3(...transform.position),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(...transform.rotation_deg.map(THREE.MathUtils.degToRad) as [number, number, number])),
    new THREE.Vector3(...transform.scale));
}
/** Resolve endpoint geometry through the same saved transform used by the editor. */
export function cylinderFrame(component: EditableModelComponent) {
  if (component.geometry.kind !== "cylinder" && component.geometry.kind !== "sweep") throw new Error("Cylinder geometry required");
  const matrix = transformMatrix(component.transform);
  const start = new THREE.Vector3(...component.geometry.start).applyMatrix4(matrix);
  const end = new THREE.Vector3(...component.geometry.end).applyMatrix4(matrix);
  return { start, end, center: start.clone().add(end).multiplyScalar(.5), length: start.distanceTo(end),
    radius: component.geometry.radius_m * Math.max(component.transform.scale[0], component.transform.scale[1]) };
}
export function transformPivot(components: EditableModelComponent[], pivot: TransformSettings["pivot"]) {
  if (!components.length) return new THREE.Vector3();
  if (pivot !== "median") return new THREE.Vector3(...components[0].transform.position);
  return components.reduce((sum, component) => sum.add(new THREE.Vector3(...component.transform.position)), new THREE.Vector3()).divideScalar(components.length);
}
/** All deltas use document ENU coordinates; the viewport converts ECEF axes here. */
export function applyTransformDelta(components: EditableModelComponent[], settings: TransformSettings, axis: THREE.Vector3, amount: number, translation?: THREE.Vector3) {
  const editable = components.filter(component => !component.locked);
  const pivot = transformPivot(editable, settings.pivot);
  const angle = snap(amount, settings.rotationSnap) * Math.PI / 180;
  const factor = snap(amount, settings.scaleSnap);
  if (settings.mode === "scale" && (!Number.isFinite(factor) || factor <= 0)) throw new Error("Scale must remain greater than zero.");
  return editable.map(component => {
    const transform = structuredClone(component.transform);
    if (settings.mode === "translate") {
      const delta = translation ?? axis.clone().multiplyScalar(snap(amount, settings.translationSnap));
      transform.position = new THREE.Vector3(...transform.position).add(delta).toArray() as [number, number, number];
    } else if (settings.mode === "rotate") {
      const rotation = new THREE.Quaternion().setFromAxisAngle(axis, angle);
      const original = new THREE.Quaternion().setFromEuler(new THREE.Euler(...transform.rotation_deg.map(THREE.MathUtils.degToRad) as [number, number, number]));
      const euler = new THREE.Euler().setFromQuaternion(rotation.clone().multiply(original));
      transform.rotation_deg = [euler.x, euler.y, euler.z].map(THREE.MathUtils.radToDeg) as [number, number, number];
      if (settings.pivot !== "individual") transform.position = new THREE.Vector3(...transform.position).sub(pivot).applyQuaternion(rotation).add(pivot).toArray() as [number, number, number];
    } else if (settings.mode === "scale") {
      const uniform = axis.lengthSq() === 0;
      if (!uniform && (settings.coordinates !== "local" || editable.some(item => item.transform.rotation_deg.some(value => value !== 0)))) throw new Error("Axis scaling requires unrotated geometry in Local ENU. Use uniform scale to preserve geometry.");
      const factors = uniform ? new THREE.Vector3(factor, factor, factor) : new THREE.Vector3(1, 1, 1).add(axis.clone().multiplyScalar(factor - 1));
      transform.scale = new THREE.Vector3(...transform.scale).multiply(factors).toArray() as [number, number, number];
      if (settings.pivot !== "individual") transform.position = new THREE.Vector3(...transform.position).sub(pivot).multiply(factors).add(pivot).toArray() as [number, number, number];
    }
    return { id: component.id, transform };
  });
}

/** Recover the exact camera flags, including controls disabled before editing. */
export function cameraLease(camera: { enableInputs: boolean }) {
  const previous = camera.enableInputs;
  camera.enableInputs = false;
  let released = false;
  return () => { if (!released) { released = true; camera.enableInputs = previous; } };
}
