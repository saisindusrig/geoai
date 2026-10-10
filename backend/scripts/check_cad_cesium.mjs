// Headless compatibility check, not a production workspace adapter or GPU test.
import { readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Geometry, GeometryAttribute, GeometryInstance, GeometryPipeline,
  ComponentDatatype, PrimitiveType, BoundingSphere, Cartesian3, Transforms,
  Matrix4 } from '../../frontend/node_modules/cesium/Source/Cesium.js';

const output = new URL('../.cad-proof-output/', import.meta.url);
const results = JSON.parse(await readFile(new URL('results.json', output), 'utf8'));
// Synthetic anchor for API verification only. No terrain/datum claim.
const anchor = Cartesian3.fromDegrees(0, 0, 0);
const matrix = Transforms.eastNorthUpToFixedFrame(anchor);
assert(Cartesian3.distance(Matrix4.multiplyByPoint(matrix, Cartesian3.ZERO, new Cartesian3()), anchor) < 1e-7);
const rows = [];
for (const [id, component] of Object.entries(results.before.outputs)) {
  const values = new Float64Array(component.mesh.positions.flat());
  assert([...values].every(Number.isFinite));
  const geometry = new Geometry({
    attributes: { position: new GeometryAttribute({ componentDatatype: ComponentDatatype.DOUBLE, componentsPerAttribute: 3, values }) },
    indices: new Uint32Array(component.mesh.triangles.flat()), primitiveType: PrimitiveType.TRIANGLES,
    boundingSphere: BoundingSphere.fromVertices(values),
  });
  GeometryPipeline.computeNormal(geometry);
  assert([...geometry.attributes.normal.values].every(Number.isFinite));
  const instance = new GeometryInstance({ id, geometry, modelMatrix: matrix });
  assert.equal(instance.id, component.id);
  assert(geometry.boundingSphere.radius > 0);
  rows.push({ id: instance.id, vertices: values.length / 3, triangles: geometry.indices.length / 3,
    materialId: component.materialId, assemblyId: component.assemblyId, radiusM: geometry.boundingSphere.radius });
}
const summary = { componentCount: rows.length, coordinateCheck: 'Synthetic local ENU -> ECEF origin verified',
  perComponentGeometryIds: true, normalsFinite: true, gpuRenderingTested: false, productionAdapterImplemented: false, components: rows };
await writeFile(new URL('cesium-summary.json', output), JSON.stringify(summary, null, 2));
console.log(JSON.stringify({ componentCount: rows.length, perComponentGeometryIds: true, normalsFinite: true,
  output: fileURLToPath(new URL('cesium-summary.json', output)) }));
