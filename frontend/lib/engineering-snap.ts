import * as THREE from "three";
import type { EditableModelDocument } from "./types";
import { transformMatrix } from "./editor-transform";

export function engineeringSnapTargets(doc:EditableModelDocument,excluded:string[]){
  const targets=[{name:"Project origin",point:new THREE.Vector3()}];
  for(const item of doc.components){
    if(!item.visible || excluded.includes(item.id) || item.geometry.kind==="asset_instance")continue;
    targets.push({name:item.name,point:new THREE.Vector3(...item.transform.position)});
    if(item.geometry.kind==="cylinder" || item.geometry.kind==="sweep"){
      for(const [name,point] of [["start",item.geometry.start],["end",item.geometry.end]] as const)targets.push({name:`${item.name} ${name}`,point:new THREE.Vector3(...point).applyMatrix4(transformMatrix(item.transform))});
    }
  }
  return targets;
}
/** Project the target onto the permitted axes; snapping never unlocks a constrained axis. */
export function snapTranslationToTargets(pivot:THREE.Vector3,delta:THREE.Vector3,axes:THREE.Vector3[],targets:ReturnType<typeof engineeringSnapTargets>,tolerance:number){
  let best:{delta:THREE.Vector3;name:string;distance:number}|null=null;
  for(const target of targets){
    const offset=target.point.clone().sub(pivot);
    const projected=axes.reduce((sum,axis)=>sum.addScaledVector(axis,offset.dot(axis)),new THREE.Vector3());
    if(projected.distanceTo(offset)>tolerance)continue;
    const distance=projected.distanceTo(delta);
    if(distance<=tolerance && (!best || distance<best.distance))best={delta:projected,name:target.name,distance};
  }
  return best;
}
