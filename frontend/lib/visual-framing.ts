import type * as Cesium from 'cesium';
/** Perspective fit of actual corners, rather than an oversized union of member spheres. */
export function projectedRange(points:number[][],heading:number,pitch:number,fov:number,aspect:number){
 const c=Math.cos(heading),s=Math.sin(heading),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const right=[c,-s,0],up=[sp*s,sp*c,cp],toward=[-cp*s,-cp*c,-sp];
 const dot=(a:number[],b:number[])=>a.reduce((v,x,i)=>v+x*b[i],0);
 const tv=Math.tan(fov/2),th=tv*Math.max(.25,aspect);
 return Math.max(.5,...points.map(p=>dot(p,toward)+1.16*Math.max(Math.abs(dot(p,right))/th,Math.abs(dot(p,up))/tv)));
}
/** Camera-only operation. No visibility or document mutations. */
export function frameEntities(C:typeof Cesium,entities:Cesium.Entity[],fallback:Cesium.BoundingSphere,heading:number,pitch:number,fov:number,aspect:number,filter?:(entity:Cesium.Entity)=>boolean){
 const now=C.JulianDate.now();
 const points=entities.filter(e=>e.show&&e.id.startsWith('editable:')&&(!filter||filter(e))).flatMap(e=>{
  const corners=e.properties?.getValue(now)?.previewCorners as number[][]|undefined;
  return corners?.map(p=>new C.Cartesian3(...p as [number,number,number]))??[];
 });
 if(!points.length)return {sphere:fallback,range:Math.max(1.5,fallback.radius*3.4)};
 const bounds=C.BoundingSphere.fromPoints(points),enu=C.Transforms.eastNorthUpToFixedFrame(bounds.center),inverse=C.Matrix4.inverseTransformation(enu,new C.Matrix4());
 const local=points.map(p=>{const v=C.Matrix4.multiplyByPoint(inverse,p,new C.Cartesian3());return [v.x,v.y,v.z];});
 const center=[0,1,2].map(i=>(Math.min(...local.map(p=>p[i]))+Math.max(...local.map(p=>p[i])))/2);
 const target=C.Matrix4.multiplyByPoint(enu,new C.Cartesian3(...center as [number,number,number]),new C.Cartesian3());
 return {sphere:new C.BoundingSphere(target,bounds.radius),range:projectedRange(local.map(p=>p.map((v,i)=>v-center[i])),heading,pitch,fov,aspect)};
}
