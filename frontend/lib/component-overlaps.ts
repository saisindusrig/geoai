import * as THREE from 'three';
import {componentObject,releaseComponentObject} from './sandbox-geometry';
import type {EditableModelComponent} from './types';
/** Geometric envelopes only: never interpret overlap as connectivity or capacity. */
export function componentOverlaps(components:EditableModelComponent[]){
 const boxes=components.flatMap(c=>{try{const o=componentObject(c);o.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(o);releaseComponentObject(o);return [{c,box}];}catch{return [];}});
 const result:{a:string;b:string;kind:'duplicate'|'envelope overlap'}[]=[];
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
  const a=boxes[i],b=boxes[j];if(!a.box.intersectsBox(b.box))continue;
  const size=a.box.clone().intersect(b.box).getSize(new THREE.Vector3());if(Math.min(size.x,size.y,size.z)<1e-6)continue;
  result.push({a:a.c.id,b:b.c.id,kind:JSON.stringify([a.c.geometry,a.c.transform])===JSON.stringify([b.c.geometry,b.c.transform])?'duplicate':'envelope overlap'});
 }
 return result;
}
