import * as THREE from "three";
import type { EditableModelComponent } from "@/lib/types";
import { cadBufferGeometry } from "@/lib/cad-mesh";

/** Component meshes retain the document's east/north/up axes. */
export function componentObject(component: EditableModelComponent): THREE.Group {
  const group = new THREE.Group();
  group.userData.componentId = component.id;
  group.position.fromArray(component.transform.position);
  group.rotation.set(...component.transform.rotation_deg.map(THREE.MathUtils.degToRad) as [number, number, number]);
  group.scale.fromArray(component.transform.scale);
  const geometry = component.geometry;
  const material = new THREE.MeshStandardMaterial({ color: component.material.color, roughness: component.material.roughness, metalness: component.material.metalness });
  let mesh: THREE.Mesh;
  if (geometry.kind === "cad_mesh") {
    mesh = new THREE.Mesh(cadBufferGeometry(geometry), material);
  } else if (geometry.kind === "box" || geometry.kind === "extrusion") {
    mesh = new THREE.Mesh(new THREE.BoxGeometry(...geometry.size), material);
  } else if (geometry.kind === "cylinder" || geometry.kind === "sweep") {
    const start = new THREE.Vector3().fromArray(geometry.start);
    const end = new THREE.Vector3().fromArray(geometry.end);
    const direction = end.clone().sub(start);
    mesh = new THREE.Mesh(new THREE.CylinderGeometry(geometry.radius_m, geometry.radius_m, direction.length(), 24), material);
    mesh.position.copy(start.add(end).multiplyScalar(0.5));
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  } else {
    material.dispose();
    throw new Error("External model assets are not supported in the sandbox.");
  }
  mesh.castShadow = true; mesh.receiveShadow = true;
  group.add(mesh);
  return group;
}

export function releaseComponentObject(root: THREE.Object3D) {
  root.traverse((object) => {
    if (object instanceof THREE.Sprite) { object.material.map?.dispose(); object.material.dispose(); }
    if (object instanceof THREE.Mesh) {
      object.geometry.dispose();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

/** Rotation used only by the grid renderer: ENU -> Three east/up/south. */
export const ENU_TO_GRID = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
