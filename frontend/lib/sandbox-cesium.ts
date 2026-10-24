import * as THREE from "three";
import { readPlatform, platformMembers } from "./parametric-platform";
import type * as CesiumTypes from "cesium";
import type { EditableModelDocument } from "@/lib/types";
import { componentObject, releaseComponentObject } from "@/lib/sandbox-geometry";
import { clipGeometry, clipPlanes, type AnalysisClip } from "./editor-clipping";
import { componentRole, componentDisplayName } from "./component-presentation";
import { displayMaterial } from "./display-material";

/** Use the same primitive meshes as the grid, including tilted/scaled cylinders. */
export function buildSandboxMapPrimitives(
  Cesium: typeof CesiumTypes,
  entities: CesiumTypes.EntityCollection,
  doc: EditableModelDocument,
  selected: string[],
  ground: number,
  clip?: AnalysisClip,
  ghost = false,
  displayOpacity: Record<string,number> = {},
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
    const surfacePositions = new Float32Array(sourcePositions.count * 3);
    const point = new THREE.Vector3();
    const normal = new THREE.Vector3();
    for (let i = 0; i < sourcePositions.count; i++) {
      point.fromBufferAttribute(sourcePositions, i).applyMatrix4(local);
      surfacePositions.set([point.x,point.y,point.z],i*3);
      const world = Cesium.Matrix4.multiplyByPoint(enu, new Cesium.Cartesian3(point.x, point.y, point.z), new Cesium.Cartesian3());
      positions.set([world.x, world.y, world.z], i * 3);
      normal.fromBufferAttribute(sourceNormals, i).applyMatrix3(normalsMatrix).normalize();
      const worldNormal = Cesium.Matrix4.multiplyByPointAsVector(enu, new Cesium.Cartesian3(normal.x, normal.y, normal.z), new Cesium.Cartesian3());
      normals.set([worldNormal.x, worldNormal.y, worldNormal.z], i * 3);
    }
    const sphere = Cesium.BoundingSphere.fromVertices(positions);
    // Tight component bounds in ENU, not an expanded Earth-fixed axis-aligned box.
    const localExtents=[Infinity,Infinity,Infinity,-Infinity,-Infinity,-Infinity];
    for(let i=0;i<surfacePositions.length;i+=3)for(let a=0;a<3;a++){localExtents[a]=Math.min(localExtents[a],surfacePositions[i+a]);localExtents[a+3]=Math.max(localExtents[a+3],surfacePositions[i+a]);}
    const previewCorners=Array.from({length:8},(_,index)=>{const p=[0,1,2].map(a=>localExtents[a+((index>>a)&1)*3]);const v=Cesium.Matrix4.multiplyByPoint(enu,new Cesium.Cartesian3(...p as [number,number,number]),new Cesium.Cartesian3());return [v.x,v.y,v.z];});
    if (!fullyClipped) spheres.push(sphere);
    const entity = entities.add({
      show: !fullyClipped, id: `editable:${component.id}`, name: componentDisplayName(component), position: sphere.center,
      properties: { ...(ghost ? { referenceRevisionComponentId: component.id } : { editableComponentId: component.id }), previewRadiusM: sphere.radius, previewCorners, structuralPresentation: /column|beam|slab|foundation|footing|stair|brac|brace|plate|connection/.test(componentRole(component)), layer: component.category, objectType: component.geometry.kind },

    });
    const geometry = new Cesium.Geometry({
      attributes: Object.assign(new Cesium.GeometryAttributes(), {
        position: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.DOUBLE, componentsPerAttribute: 3, values: positions }),
        surfacePosition: new Cesium.GeometryAttribute({componentDatatype:Cesium.ComponentDatatype.FLOAT,componentsPerAttribute:3,values:surfacePositions}),
        normal: new Cesium.GeometryAttribute({ componentDatatype: Cesium.ComponentDatatype.FLOAT, componentsPerAttribute: 3, values: normals }),
      }),
      indices: new Uint32Array(mesh.geometry.index?.array ?? Array.from({ length: sourcePositions.count }, (_, i) => i)),
      primitiveType: Cesium.PrimitiveType.TRIANGLES, boundingSphere: sphere,
    });
    const finish=displayMaterial(component);
    const visualMetal=/Steel|Connection|Stair/.test(finish.finish);
    const base = Cesium.Color.fromCssColorString(ghost ? "#8ca79f" : component.metadata?.source==='assistant_supervised_primitive' ? '#E879F9' : finish.color);
    // Temporary display state, never copied into the saved material/document.
    const alpha=ghost ? .25 : Math.max(.1,Math.min(1,displayOpacity[component.id]??1));
    const color = (selected.includes(component.id) && !ghost ? Cesium.Color.lerp(base,Cesium.Color.fromCssColorString("#74b7dc"),0.10,new Cesium.Color()) : base).withAlpha(alpha);
    const solid = collection.add(new Cesium.Primitive({
      show: !fullyClipped,
      geometryInstances: new Cesium.GeometryInstance({ geometry, id: entity, attributes: { color: Cesium.ColorGeometryInstanceAttribute.fromColor(color) } }),
      appearance: new Cesium.PerInstanceColorAppearance({ translucent: alpha<1, closed: true,
        vertexShaderSource: `in vec3 position3DHigh; in vec3 position3DLow; in vec3 normal; in vec4 color; in float batchId; in vec3 surfacePosition;
          out vec3 v_positionEC; out vec3 v_normalEC; out vec4 v_color; out vec3 v_surface;
          void main(){vec4 p=czm_computePosition();v_positionEC=(czm_modelViewRelativeToEye*p).xyz;v_normalEC=czm_normal*normal;v_color=color;v_surface=surfacePosition;gl_Position=czm_modelViewProjectionRelativeToEye*p;}`,

        // Display finish only; no engineering material properties are inferred.
        fragmentShaderSource: `in vec3 v_positionEC; in vec3 v_normalEC; in vec4 v_color; in vec3 v_surface;
          void main() {
            vec3 n = normalize(v_normalEC); vec3 eye = normalize(-v_positionEC);
            vec4 c = czm_gammaCorrect(v_color);
            float diffuse = 0.32 + 0.56 * max(dot(n, normalize(vec3(-0.4, 0.6, 0.8))), 0.0) + 0.20 * max(dot(n, normalize(vec3(0.7, -0.2, 0.4))), 0.0);
            float rim = 0.045 * pow(1.0 - abs(dot(n, eye)), 2.0);
            float shine = pow(max(dot(reflect(-normalize(vec3(-0.4, 0.6, 0.8)), n), eye), 0.0), ${Math.max(4, 48 * (1 - (visualMetal ? .38 : .92))).toFixed(1)});
            float grain = fract(sin(dot(floor(v_surface*240.0),vec3(12.9898,78.233,45.164)))*43758.5453)-0.5;
            float detail = ${visualMetal ? '0.008*grain' : '0.022*grain'};
            out_FragColor = vec4(c.rgb * (diffuse+detail) + vec3(rim + shine * ${(visualMetal ? 0.16 : 0.015).toFixed(3)}), c.a);
          }`,
      }),
      shadows: ghost ? Cesium.ShadowMode.DISABLED : Cesium.ShadowMode.ENABLED,
      asynchronous: false,
    }));
    solid.componentId = component.id;
    // Real silhouette edges from the existing mesh; identity and picking remain on the solid.
    if (!ghost && !fullyClipped) {
      const edges = new THREE.EdgesGeometry(mesh.geometry, 30);
      const vertices = edges.getAttribute("position");
      const edgeColor = Cesium.Color.fromCssColorString(selected.includes(component.id) ? "#6ce8ff" : (visualMetal ? "#20303d" : "#5e605b"));
      for (let i = 0; i < vertices.count; i += 2) {
        const worldPoints = [i, i + 1].map(index => {
          const p = new THREE.Vector3().fromBufferAttribute(vertices, index).applyMatrix4(local);
          return Cesium.Matrix4.multiplyByPoint(enu, new Cesium.Cartesian3(p.x, p.y, p.z), new Cesium.Cartesian3());
        });
        entities.add({ properties: { editableComponentId: component.id, transformEdge: true }, polyline: { positions: worldPoints, arcType: Cesium.ArcType.NONE, width: selected.includes(component.id) ? 2 : .65, material: edgeColor } });
      }
      edges.dispose();
    }
    releaseComponentObject(object);
  }
  const platform = !ghost && readPlatform(doc), members = platformMembers(doc);
  if (platform && members) {
    const deck=members[0], column=members[5];
    const base=column.transform.position[2]-(column.geometry.kind === "box" ? column.geometry.size[2]/2 : 0);
    const rotation=deck.transform.rotation_deg[2]*Math.PI/180;
    const world=(x:number,y:number,z:number)=>{
      const p=new THREE.Vector3(deck.transform.position[0]+x*Math.cos(rotation)-y*Math.sin(rotation),deck.transform.position[1]+x*Math.sin(rotation)+y*Math.cos(rotation),base+z).applyMatrix4(heading);
      return Cesium.Matrix4.multiplyByPoint(enu,new Cesium.Cartesian3(p.x,p.y,p.z),new Cesium.Cartesian3());
    };
    const {length:l,width:w,height:h}=platform;
    const dims: [string,number,[number,number,number],[number,number,number]][] = [
      ["Length",l,[-l/2,-w/2-0.45,h],[l/2,-w/2-0.45,h]],
      ["Width",w,[l/2+0.45,-w/2,h],[l/2+0.45,w/2,h]],
      ["Deck height",h,[-l/2-0.45,-w/2,0],[-l/2-0.45,-w/2,h]],
    ];
    for(const [name,value,a,b] of dims) entities.add({id:`platform-dimension:${name}`,position:world((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2),
      polyline:{positions:[world(...a),world(...b)],width:2,material:Cesium.Color.fromCssColorString("#a9dcff"),depthFailMaterial:Cesium.Color.fromCssColorString("#a9dcff")},
      label:{text:`${name} ${Number(value.toFixed(3))} m`,font:"500 12px sans-serif",fillColor:Cesium.Color.WHITE,showBackground:true,backgroundColor:Cesium.Color.BLACK.withAlpha(0.8),pixelOffset:new Cesium.Cartesian2(name === "Width" ? 40 : name === "Deck height" ? -45 : 0,name === "Deck height" ? 12 : -16),distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,Math.max(l,w,h)*16),disableDepthTestDistance:Infinity}});
  }
  return { collection, bounds: spheres.length ? Cesium.BoundingSphere.fromBoundingSpheres(spheres) : null };
}
