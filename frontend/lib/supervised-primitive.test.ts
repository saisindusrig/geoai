import {expect,it} from 'vitest';
import {primitiveDocument} from './supervised-primitive';
import fixture from './__fixtures__/supervised-column.json';
import {documentFromGeometrySpec} from './editable-model';
import type {Project} from './types';
import type {WorkspaceCommand} from './workspace-assistant';
const document=()=>documentFromGeometrySpec({id:7,project_type:'building',center_lat:13,center_lng:77} as Project,12,{objects:[{kind:'box',name:'Original',layer:'column',size:[1,1,3],center:[0,0,1.5]}]});
const command=()=>({...structuredClone(fixture),expiresAt:Date.now()+120000}) as unknown as WorkspaceCommand;
it('preserves existing components and appends explicit metric geometry only',()=>{
 const d=document(),before=structuredClone(d),next=primitiveDocument(command(),d,1);
 expect(d).toEqual(before);expect(next.components[0]).toEqual(d.components[0]);expect(next.components[1].transform.position).toEqual([3,0,1.5]);expect(next.components[1].quantity?.included).toBe(false);
});
it('rejects wrong project/revision, duplicate IDs and protected CAD/assembly sources',()=>{
 const c=command(),d=document();
 expect(()=>primitiveDocument(c,d,2)).toThrow();expect(()=>primitiveDocument({...c,projectId:9},d,1)).toThrow();
 expect(()=>primitiveDocument(c,{...d,components:[...d.components,c.candidate!]},1)).toThrow();
 for(const change of [{locked:true},{metadata:{parametric_platform:true}},{parent_id:'parent'}])expect(()=>primitiveDocument(c,{...d,components:[{...d.components[0],...change}]},1)).toThrow('Protected');
});
it('rejects nonpositive geometry and non-upright orientation',()=>{
 const c=command();c.candidate!.geometry={kind:'box',size:[0,.5,3]};expect(()=>primitiveDocument(c,document(),1)).toThrow();
 const tilted=command();tilted.candidate!.transform.rotation_deg=[15,0,0];expect(()=>primitiveDocument(tilted,document(),1)).toThrow();
});
