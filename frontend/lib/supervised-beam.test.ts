import {expect,it} from 'vitest';
import * as THREE from 'three';
import fixture from './__fixtures__/supervised-beam.json';
import cases from './__fixtures__/beam-transform-cases.json';
import {primitiveDocument} from './supervised-primitive';
import {boxFrame} from './editor-transform';
import {componentObject,releaseComponentObject} from './sandbox-geometry';
import {documentFromGeometrySpec} from './editable-model';
import type {Project} from './types';
import type {WorkspaceCommand} from './workspace-assistant';
const command=()=>({...structuredClone(fixture),expiresAt:Date.now()+120000}) as unknown as WorkspaceCommand;
const doc=()=>documentFromGeometrySpec({id:7,project_type:'building',center_lat:13,center_lng:77} as Project,12,{objects:[{kind:'box',name:'Existing',layer:'column',size:[.4,.4,3],center:[-2,0,1.5]}]});
it('uses the real box renderer transform for endpoint and cross-section agreement',()=>{
 const c=command(),d=doc(),before=structuredClone(d),next=primitiveDocument(c,d,1),v=next.components[1];
 expect(d).toEqual(before);expect(next.components[0]).toEqual(d.components[0]);
 const frame=boxFrame(v),object=componentObject(v);object.updateMatrixWorld(true);
 expect(frame.start.toArray()).toEqual(expect.arrayContaining([expect.closeTo(0,8),expect.closeTo(0,8),expect.closeTo(3,8)]));
 expect(frame.end.toArray()).toEqual([expect.closeTo(4,8),expect.closeTo(2,8),expect.closeTo(4,8)]);
 expect(frame.length).toBeCloseTo(Math.sqrt(21),8);
 const endpoints=[-1,1].map(sign=>new THREE.Vector3(sign*frame.length/2,0,0).applyMatrix4(object.matrixWorld).toArray());
 expect(endpoints[0]).toEqual(frame.start.toArray());expect(endpoints[1]).toEqual(frame.end.toArray());
 expect(v.quantity?.included).toBe(false);releaseComponentObject(object);
});
it('rejects mismatched endpoint evidence, wrong revision and duplicate component IDs',()=>{
 const c=command();c.candidate!.transform.position[0]+=.1;expect(()=>primitiveDocument(c,doc(),1)).toThrow('exact endpoints');
 expect(()=>primitiveDocument(command(),doc(),2)).toThrow();
 const d=primitiveDocument(command(),doc(),1);expect(()=>primitiveDocument(command(),d,1)).toThrow();
});

it('agrees with backend transforms for horizontal, oblique, vertical and reversed endpoint order',()=>{
 for(const data of cases){
  const c=command();c.candidate!.geometry={kind:'box',size:data.size as [number,number,number]};c.candidate!.transform={position:data.position as [number,number,number],rotation_deg:data.rotation_deg as [number,number,number],scale:[1,1,1]};c.candidate!.metadata!.beam=data;
  const actual=primitiveDocument(c,doc(),1).components[1],object=componentObject(actual);object.updateMatrixWorld(true);
  for(const [i,sign] of [-1,1].entries()){
   const endpoint=new THREE.Vector3(sign*data.length_m/2,0,0).applyMatrix4(object.matrixWorld).toArray();
   endpoint.forEach((v,j)=>expect(v).toBeCloseTo(data.endpoints_enu_m[i][j],7));
  }
  releaseComponentObject(object);
 }
});
