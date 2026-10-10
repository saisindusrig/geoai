import * as THREE from "three";
import { apiUrl, getAuthToken } from "@/lib/api";
import type { EditableGeometry, EditableModelDocument } from "@/lib/types";

type CadGeometry = Extract<EditableGeometry, {kind: "cad_mesh"}>;
type Mesh = {positions: number[][]; triangles: number[][]; units: string};
const meshes = new Map<string, Mesh>();
const key = (geometry: CadGeometry) => `${geometry.catalog_id}:${geometry.mesh_hash}`;

export function validateCadMesh(value: unknown): Mesh {
  const mesh = value as Mesh;
  if (!mesh || mesh.units !== "m" || !Array.isArray(mesh.positions) || !Array.isArray(mesh.triangles)
      || mesh.positions.length > 250000 || mesh.positions.length < 3 || mesh.triangles.length > 500000 || !mesh.triangles.length
      || mesh.positions.some(p => !Array.isArray(p) || p.length !== 3 || p.some(v => typeof v !== "number" || !Number.isFinite(v)))
      || mesh.triangles.some(t => !Array.isArray(t) || t.length !== 3 || t.some(v => !Number.isInteger(v) || v < 0 || v >= mesh.positions.length))) {
    throw new Error("CAD mesh is invalid. Reload verified artifacts; mesh editing is unsupported.");
  }
  return mesh;
}

export async function loadCadMeshes(document: EditableModelDocument) {
  const refs = document.components.filter(c => c.geometry.kind === "cad_mesh").map(c => c.geometry as CadGeometry);
  const unique = [...new Map(refs.map(g => [key(g), g])).values()];
  await Promise.all(unique.map(async geometry => {
    if (!/^[a-f0-9]{64}$/.test(geometry.mesh_hash) || !Number.isSafeInteger(geometry.catalog_id) || geometry.catalog_id <= 0) throw new Error("Invalid CAD reference.");
    // Reauthorize even when bytes are cached; no anonymous/public artifact URL.
    const token = getAuthToken();
    const response = await fetch(apiUrl(`/api/projects/${document.project_id}/experimental-cad/catalogs/${geometry.catalog_id}/meshes/${geometry.mesh_hash}`),
      {credentials: "include", cache: "no-store", headers: token ? {Authorization: `Bearer ${token}`} : {}});
    if (!response.ok) throw new Error(`CAD mesh unavailable or unauthorized (${response.status}).`);
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength > 32000000) throw new Error("CAD mesh exceeds its limit.");
    const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(v => v.toString(16).padStart(2,"0")).join("");
    if (hash !== geometry.mesh_hash) throw new Error("CAD mesh content hash mismatch.");
    meshes.delete(key(geometry));
    meshes.set(key(geometry), validateCadMesh(JSON.parse(new TextDecoder().decode(bytes))));
    // Two maximum-size revisions can coexist during comparison (250 each).
    if (meshes.size > 500) meshes.delete(meshes.keys().next().value!);
  }));
}

export function cadBufferGeometry(geometry: CadGeometry) {
  const mesh = meshes.get(key(geometry));
  if (!mesh) throw new Error("Verified CAD mesh has not loaded.");
  const buffer = new THREE.BufferGeometry();
  // Native artifacts retain project-local coordinates. The editable node uses
  // a component-local pivot at its bounds center, without altering those bytes.
  const center = [0,1,2].map(i => (geometry.bounds_m[i] + geometry.bounds_m[i+3])/2);
  buffer.setAttribute("position", new THREE.Float32BufferAttribute(mesh.positions.flatMap(p => p.map((v,i) => v - center[i])), 3));
  buffer.setIndex(mesh.triangles.flat());
  buffer.computeVertexNormals();
  return buffer;
}
