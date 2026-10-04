import * as THREE from "three";
export type AnalysisClip = { mode: "off" | "horizontal" | "vertical" | "box" | "terrain"; value:number; size:number };
export function clipPlanes(clip: AnalysisClip) {
  if(clip.mode === "off" || clip.mode === "terrain") return [];
  if(clip.mode === "horizontal") return [new THREE.Plane(new THREE.Vector3(0,0,1),-clip.value)];
  if(clip.mode === "vertical") return [new THREE.Plane(new THREE.Vector3(1,0,0),-clip.value)];
  return [0,1,2].flatMap(index=>[new THREE.Plane(new THREE.Vector3().setComponent(index,1),clip.size/2),new THREE.Plane(new THREE.Vector3().setComponent(index,-1),clip.size/2)]);
}
/** Clip triangles in document coordinates, leaving the source document untouched. */
export function clipGeometry(source:THREE.BufferGeometry,matrix:THREE.Matrix4,planes:THREE.Plane[]) {
  const geometry=source.index ? source.toNonIndexed() : source.clone(); geometry.applyMatrix4(matrix);
  const positions=geometry.getAttribute("position"), normals=geometry.getAttribute("normal");
  const output:number[]=[], outputNormals:number[]=[];
  for(let offset=0;offset<positions.count;offset+=3){
    let polygon=[0,1,2].map(index=>({p:new THREE.Vector3().fromBufferAttribute(positions,offset+index),n:new THREE.Vector3().fromBufferAttribute(normals,offset+index)}));
    for(const plane of planes){
      const next:typeof polygon=[];
      polygon.forEach((a,index)=>{const b=polygon[(index+1)%polygon.length], da=plane.distanceToPoint(a.p),db=plane.distanceToPoint(b.p);if(da>=0)next.push(a);if((da>=0)!==(db>=0)){const t=da/(da-db);next.push({p:a.p.clone().lerp(b.p,t),n:a.n.clone().lerp(b.n,t).normalize()});}});
      polygon=next;
    }
    for(let index=1;index<polygon.length-1;index++)for(const vertex of [polygon[0],polygon[index],polygon[index+1]]){output.push(...vertex.p.toArray());outputNormals.push(...vertex.n.toArray());}
  }
  geometry.dispose();
  return new THREE.BufferGeometry().setAttribute("position",new THREE.Float32BufferAttribute(output,3)).setAttribute("normal",new THREE.Float32BufferAttribute(outputNormals,3));
}
