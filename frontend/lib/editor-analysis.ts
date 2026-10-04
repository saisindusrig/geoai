import * as THREE from "three";
import { componentObject, releaseComponentObject } from "./sandbox-geometry";
import type { EditableModelDocument } from "./types";

export function sectionGeometry(doc: EditableModelDocument, east: number, north: number, heading: number) {
  const direction = new THREE.Vector3(Math.cos(heading * Math.PI / 180),Math.sin(heading * Math.PI / 180),0);
  const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(new THREE.Vector3(-direction.y,direction.x,0),new THREE.Vector3(east,north,0));
  const segments: { id:string; name:string; points:[number,number][] }[] = [];
  for (const item of doc.components) {
    if (!item.visible || item.geometry.kind === "asset_instance") continue;
    const object = componentObject(item); object.updateMatrixWorld(true);
    const mesh = object.children[0] as THREE.Mesh<THREE.BufferGeometry>;
    const positions = mesh.geometry.getAttribute("position"), indices = mesh.geometry.index;
    for (let offset=0;offset<(indices?.count ?? positions.count);offset+=3) {
      const vertices = [0,1,2].map(index=>new THREE.Vector3().fromBufferAttribute(positions,indices ? indices.getX(offset+index) : offset+index).applyMatrix4(mesh.matrixWorld));
      const intersections: THREE.Vector3[]=[];
      for (let index=0;index<3;index++) {
        const a=vertices[index], b=vertices[(index+1)%3];
        if (plane.distanceToPoint(a)*plane.distanceToPoint(b)>0) continue;
        const point=plane.intersectLine(new THREE.Line3(a,b),new THREE.Vector3());
        if (point && !intersections.some(previous=>previous.distanceTo(point)<1e-8)) intersections.push(point.clone());
      }
      if(intersections.length===2) segments.push({id:item.id,name:item.name,points:intersections.map(point=>[point.clone().sub(new THREE.Vector3(east,north,0)).dot(direction),point.z])});
    }
    releaseComponentObject(object);
  }
  return segments;
}
export function designElevationAt(doc: EditableModelDocument, east:number, north:number) {
  const ray = new THREE.Raycaster(new THREE.Vector3(east,north,1e6),new THREE.Vector3(0,0,-1));
  let top: number | null = null;
  for(const component of doc.components){
    if (!component.visible || component.geometry.kind === "asset_instance") continue;
    const object=componentObject(component);object.updateMatrixWorld(true);
    const hits=ray.intersectObject(object,true);
    if(hits.length && (top === null || hits[0].point.z>top)) top=hits[0].point.z;
    releaseComponentObject(object);
  }
  return top;
}

export type GroundAnalysisSample = { status:string;elevation:number|null;source:string;terrain_version_id:number|null;vertical_reference:{type?:string}|null;failure_reason?:string };
export type AnalysisPlacement = {longitude:number;latitude:number;elevation:number;offset:number;heading:number;status:string;vertical_reference:{type?:string}|null};
export async function sampleSection(doc:EditableModelDocument,placement:AnalysisPlacement,east:number,north:number,heading:number,halfWidth:number,interval:number,sample:(longitude:number,latitude:number)=>Promise<GroundAnalysisSample>){
  if(![east,north,heading,halfWidth,interval].every(Number.isFinite) || interval<=0 || halfWidth<0 || halfWidth*2/interval>1000)throw new Error("Choose a finite section extent and positive interval with at most 1,000 samples.");
  if(placement.status!=="VALID" || placement.vertical_reference?.type!=="ELLIPSOIDAL")throw new Error("Section terrain requires a valid, resolved placement.");
  const C=await import("cesium"),angle=placement.heading*Math.PI/180,sectionAngle=heading*Math.PI/180;
  const frame=C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(placement.longitude,placement.latitude,placement.elevation+placement.offset));
  const inverse=C.Matrix4.inverse(frame,new C.Matrix4()),rows=[];
  for(let offset=-halfWidth;offset<=halfWidth;offset+=interval){
    const x=east+offset*Math.cos(sectionAngle),y=north+offset*Math.sin(sectionAngle);
    const coordinate=C.Cartographic.fromCartesian(C.Matrix4.multiplyByPoint(frame,new C.Cartesian3(x*Math.cos(angle)-y*Math.sin(angle),x*Math.sin(angle)+y*Math.cos(angle),0),new C.Cartesian3()));
    const longitude=C.Math.toDegrees(coordinate.longitude),latitude=C.Math.toDegrees(coordinate.latitude),ground=await sample(longitude,latitude);
    const resolved=ground.status==="VALID" && ground.elevation!==null && ground.vertical_reference?.type==="ELLIPSOIDAL";
    const elevation=resolved?C.Matrix4.multiplyByPoint(inverse,C.Cartesian3.fromDegrees(longitude,latitude,ground.elevation!),new C.Cartesian3()).z:null;
    const design=designElevationAt(doc,x,y);
    rows.push({offset,longitude,latitude,elevation,design,difference:elevation!==null&&design!==null?design-elevation:null,source:ground.source,version:ground.terrain_version_id,status:resolved?"VALID":ground.status});
  }
  return rows;
}
export async function designProfile<T extends {longitude:number;latitude:number;chainage_m:number;proposed_elevation_m:number|null;grade_percent:number|null}>(doc:EditableModelDocument,placement:AnalysisPlacement,stations:T[]){
  if(placement.status!=="VALID" || placement.vertical_reference?.type!=="ELLIPSOIDAL")return stations.map(station=>({...station,proposed_elevation_m:null,grade_percent:null}));
  const C=await import("cesium");
  const frame=C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(placement.longitude,placement.latitude,placement.elevation+placement.offset));
  const inverse=C.Matrix4.inverse(frame,new C.Matrix4());
  const angle=placement.heading*Math.PI/180;
  const result=stations.map(station=>{
    const point=C.Matrix4.multiplyByPoint(inverse,C.Cartesian3.fromDegrees(station.longitude,station.latitude,placement.elevation+placement.offset),new C.Cartesian3());
    const east=point.x*Math.cos(angle)+point.y*Math.sin(angle),north=-point.x*Math.sin(angle)+point.y*Math.cos(angle);
    const top=designElevationAt(doc,east,north);
    const elevation=top===null?null:C.Cartographic.fromCartesian(C.Matrix4.multiplyByPoint(frame,new C.Cartesian3(point.x,point.y,top),new C.Cartesian3())).height;
    return {...station,proposed_elevation_m:elevation,grade_percent:null as number|null};
  });
  return result.map((station,index)=>{
    const previous=result[index-1],run=previous?station.chainage_m-previous.chainage_m:0;
    return {...station,grade_percent:run>0 && station.proposed_elevation_m!==null && previous.proposed_elevation_m!==null ? (station.proposed_elevation_m-previous.proposed_elevation_m)/run*100:null};
  });
}
export async function analyseSupports(doc:EditableModelDocument,placement:AnalysisPlacement,sample:(longitude:number,latitude:number)=>Promise<GroundAnalysisSample>) {
  if(placement.status !== "VALID" || placement.vertical_reference?.type !== "ELLIPSOIDAL") throw new Error("Resolve and accept an ellipsoidal model placement before clearance analysis.");
  const C=await import("cesium");
  const frame=C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(placement.longitude,placement.latitude,placement.elevation+placement.offset));
  const angle=placement.heading*Math.PI/180;
  const world=(x:number,y:number,z:number)=>C.Cartographic.fromCartesian(C.Matrix4.multiplyByPoint(frame,new C.Cartesian3(x*Math.cos(angle)-y*Math.sin(angle),x*Math.sin(angle)+y*Math.cos(angle),z),new C.Cartesian3()));
  const deckDoc={...doc,components:doc.components.filter(item=>item.visible && /deck/.test(item.category))};
  const results=[];
  for(const support of doc.components.filter(item=>item.visible && /pier|support/.test(item.category))){
    if(support.geometry.kind === "asset_instance")continue;
    const object=componentObject(support);object.updateMatrixWorld(true);
    const bounds=new THREE.Box3().setFromObject(object),center=bounds.getCenter(new THREE.Vector3());releaseComponentObject(object);
    const ray=new THREE.Raycaster(new THREE.Vector3(center.x,center.y,1e6),new THREE.Vector3(0,0,-1));
    let bottom:number|null=null;
    for(const component of deckDoc.components){if(component.geometry.kind === "asset_instance")continue;const mesh=componentObject(component);mesh.updateMatrixWorld(true);mesh.traverse(child=>{if(child instanceof THREE.Mesh)child.material.side=THREE.DoubleSide;});const hits=ray.intersectObject(mesh,true);if(hits.length){const z=Math.min(...hits.map(hit=>hit.point.z));bottom=bottom===null?z:Math.min(bottom,z);}releaseComponentObject(mesh);}
    const anchor=world(center.x,center.y,0),longitude=C.Math.toDegrees(anchor.longitude),latitude=C.Math.toDegrees(anchor.latitude);
    const ground=await sample(longitude,latitude);
    const deck=bottom===null?null:world(center.x,center.y,bottom).height;
    const resolved=ground.status === "VALID" && ground.elevation!==null && ground.vertical_reference?.type === "ELLIPSOIDAL" && deck!==null;
    const clearance=resolved?deck!-ground.elevation!:null;
    results.push({id:support.id,name:support.name,longitude,latitude,ground:ground.elevation,foundation:world(center.x,center.y,bounds.min.z).height,deck,clearance,source:ground.source,version:ground.terrain_version_id,status:ground.status === "STALE"?"STALE":!resolved?"UNKNOWN":clearance!<0?"POTENTIAL_CONFLICT":"OK"});
  }
  return results;
}
