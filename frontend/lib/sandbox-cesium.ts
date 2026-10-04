import * as THREE from "three";
import type * as CesiumTypes from "cesium";
import type { EditableModelDocument } from "@/lib/types";
import { componentObject, releaseComponentObject } from "@/lib/sandbox-geometry";
import { clipGeometry, clipPlanes, type AnalysisClip } from "./editor-clipping";

/** Use the same primitive meshes as the grid, including tilted/scaled cylinders. */
export function buildSandboxMapPrimitives(
  Cesium: typeof CesiumTypes,
  entities: CesiumTypes.EntityCollection,
  doc: EditableModelDocument,
  selected: string[],
  ground: number,
  clip?: AnalysisClip,
  ghost = false,
) {
  const enu = Cesium.Transforms.eastNorthUpToFixedFrame(Cesium.Cartesian3.fromDegrees(doc.origin.lng, doc.origin.lat, ground + doc.origin.elevation_m));
  const heading = new THREE.Matrix4().makeRotationZ(THREE.MathUtils.degToRad(doc.origin.heading_deg));
  const collection = new Cesium.PrimitiveCollection();
  const spheres: CesiumTypes.BoundingSphere[] = [];
  for (const component of doc.components) {
    if (!component.visible || component.geometry.kind === "asset_instance") continue;
    const object = componentObject(component);
    object.updateMatrixWorld(true);
    const mesh = object.children[0] as THREE.Mesh<THREE.BufferGeometry>;
    const planes = clip ? clipPlanes(clip) : [];
    let fullyClipped = false;
    if (planes.length) {
      const original = mesh.geometry;
      const clipped = clipGeometry(original,mesh.matrixWorld,planes);
      fullyClipped = clipped.getAttribute("position").count === 0;
      if (fullyClipped) clipped.dispose();
      else { mesh.geometry = clipped; original.dispose(); mesh.matrixWorld.identity(); }
    }
    const local = heading.clone().multiply(mesh.matrixWorld);
    const normalsMatrix = new THREE.Matrix3().getNormalMatrix(local);
    const sourcePositions = mesh.geometry.getAttribute("position");
    const sourceNormals = mesh.geometry.getAttribute("normal");
    const positions = new Float64Array(sourcePositions.count * 3);
    const normals = new Float32Array(sourceNormals.count * 3);
    const point = new THREE.Vector3();
    const normal = new THREE.Vector3();
    for (let i = 0; i < sourcePositions.count; i++) {
      point.fromBufferAttribute(sourcePositions, i).applyMatrix4(local);
      const world = Cesium.Matrix4.multiplyByPoint(enu, new Cesium.Cartesian3(point.x, point.y, point.z), new Cesium.Cartesian3());
      positions.set([world.x, world.y, world.z], i * 3);
      normal.fromBufferAttribute(sourceNormals, i).applyMatrix3(normalsMatrix).normalize();
      const worldNormal = Cesium.Matrix4.multiplyByPointAsVector(enu, new Cesium.Cartesian3(normal.x, normal.y, normal.z), new Cesium.Cartesian3());
      normals.set([worldNormal.x, worldNormal.y, worldNormal.z], i * 3);
    }
    const sphere = Cesium.BoundingSphere.fromVertices(positions);
    spheres.push(sphere);
    const entity = entities.add({
      id: `editable:${component.id}`, name: component.name, position: sphere.center,
      properties: { ...(ghost ? { referenceRevisionComponentId: component.id } : { editableComponentId: component.id }), layer: component.category, objectType: component.geometry.kind },
      ...(selected.includes(component.id) && !ghost ? {label:{text:component.name.toUpperCase(),font:"600 11px sans-serif",fillColor:Cesium.Color.fromCssColorString("#c8ff32"),showBackground:true,backgroundColor:Cesium.Color.BLACK.withAlpha(0.7),pixelOffset:new Cesium.Cartesian2(0,-24),disableDepthTestDistance:Infinity}} : {}),
    });
    const geometry = new Cesium.Geometry({
      attributes: Object.assign(new Cesium.GeometryAttributes(), {
        position: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.DOUBLE, componentsPerAttribute: 3, values: positions }),
        normal: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.FLOAT, componentsPerAttribute: 3, values: normals }),
      }),
      indices: new Uint32Array(mesh.geometry.index?.array ?? Array.from({ length: sourcePositions.count }, (_, i) => i)),
      primitiveType: Cesium.PrimitiveType.TRIANGLES, boundingSphere: sphere,
    });
    const base = Cesium.Color.fromCssColorString(ghost ? "#8ca79f" : component.material.color);
    const color = (selected.includes(component.id) && !ghost ? Cesium.Color.lerp(base,Cesium.Color.fromCssColorString("#c8ff32"),0.22,new Cesium.Color()) : base).withAlpha(ghost ? 0.25 : 1);
    collection.add(new Cesium.Primitive({
      show: !fullyClipped,
      geometryInstances: new Cesium.GeometryInstance({ geometry, id: entity, attributes: { color: Cesium.ColorGeometryInstanceAttribute.fromColor(color) } }),
      appearance: new Cesium.PerInstanceColorAppearance({ translucent: ghost, closed: true }),
      shadows: ghost ? Cesium.ShadowMode.DISABLED : Cesium.ShadowMode.ENABLED,
      asynchronous: false,
    }));
    releaseComponentObject(object);
  }
  return { collection, bounds: spheres.length ? Cesium.BoundingSphere.fromBoundingSpheres(spheres) : null };
}
