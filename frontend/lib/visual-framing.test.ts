import {expect,it} from 'vitest';
import * as C from 'cesium';
import {frameEntities,projectedRange} from './visual-framing';
it('fits every actual corner in both image axes at front, side, top and isometric angles',()=>{
 const points=[-4,4].flatMap(x=>[-2,2].flatMap(y=>[-1.8,1.8].map(z=>[x,y,z])));
 for(const [h,p] of [[0,-Math.PI/2],[Math.PI,0],[Math.PI*1.5,0],[.45,-.52]])for(const aspect of [.65,1.6,2.1]){
  const d=projectedRange(points,h,p,Math.PI/3,aspect),c=Math.cos(h),s=Math.sin(h),cp=Math.cos(p),sp=Math.sin(p);
  for(const [x,y,z] of points){const depth=d-(-cp*s*x-cp*c*y-sp*z);expect(depth).toBeGreaterThan(0);expect(Math.abs(c*x-s*y)/depth).toBeLessThan(Math.tan(Math.PI/6)*aspect);expect(Math.abs(sp*s*x+sp*c*y+cp*z)/depth).toBeLessThan(Math.tan(Math.PI/6));}
  expect(projectedRange(points.map(p=>p.map(v=>v*2)),h,p,Math.PI/3,aspect)).toBeCloseTo(d*2);
 }
});
it('focuses by declared display roles without changing any entity visibility or identities',()=>{
 const origin=C.Cartesian3.fromDegrees(77,12),enu=C.Transforms.eastNorthUpToFixedFrame(origin),entities=new C.EntityCollection();
 for(const [id,x,structural] of [['frame',0,true],['context',100,false]] as const)entities.add({id:`editable:${id}`,properties:{structuralPresentation:structural,previewCorners:[[x-1,-1,0],[x+1,1,3]].map(p=>{const v=C.Matrix4.multiplyByPoint(enu,new C.Cartesian3(...p as [number,number,number]),new C.Cartesian3());return [v.x,v.y,v.z];})}});
 const before=entities.values.map(e=>[e.id,e.show]),fallback=new C.BoundingSphere(origin,10);
 const all=frameEntities(C,entities.values,fallback,.45,-.5,Math.PI/3,1.5),focus=frameEntities(C,entities.values,fallback,.45,-.5,Math.PI/3,1.5,e=>!!e.properties?.getValue(C.JulianDate.now()).structuralPresentation);
 expect(focus.range).toBeLessThan(all.range/5);expect(entities.values.map(e=>[e.id,e.show])).toEqual(before);
});
