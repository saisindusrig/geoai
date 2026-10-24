import {act,renderHook,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {useState} from 'react';
import {useWorkspaceAssistant} from './useWorkspaceAssistant';
import type {EditableModelEditor} from './useEditableModelEditor';
import {api} from '@/lib/api';
import {matchesWorkspace,waitForWorkspace,outcome,type WorkspaceCommand} from '@/lib/workspace-assistant';
vi.mock('@/lib/api',()=>({api:{post:vi.fn()}}));afterEach(()=>{cleanup();vi.resetAllMocks();});
const command:WorkspaceCommand={kind:'workspace_action',actionId:'a'.repeat(64),projectId:1,projectName:'Test',revisionId:8,documentHash:'hash',operation:'select_components',componentIds:['beam'],validation:{name:'select_components',arguments:{project_id:1,component_ids:['beam']}}};
it('selects exact geometry and confirms only after the real editor selection updates',async()=>{
 vi.mocked(api.post).mockResolvedValue(command);
 renderHook(()=>{const [selectedIds,selectMany]=useState<string[]>([]);const editor={document:{project_id:1,components:[{id:'beam',name:'Beam',visible:true}]},baseRevision:{id:8},dirty:false,selectedIds,selectMany} as unknown as EditableModelEditor;useWorkspaceAssistant(editor,1);return selectedIds;});
 const confirmed=waitForWorkspace(command,1000);
 await act(async()=>window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:command})));
 expect(await confirmed).toMatchObject({ok:true,message:'Selected Beam.'});expect(api.post).toHaveBeenCalledOnce();
});
it('rejects stale and dirty commands before any frontend operation',async()=>{
 const selectMany=vi.fn();renderHook(()=>useWorkspaceAssistant({document:{project_id:1},baseRevision:{id:8},dirty:true,selectedIds:[],selectMany} as unknown as EditableModelEditor,1));
 const confirmed=waitForWorkspace(command,1000);act(()=>window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:command})));
 expect((await confirmed).ok).toBe(false);expect(selectMany).not.toHaveBeenCalled();expect(api.post).not.toHaveBeenCalled();
});
it('waits for a matching frontend acknowledgment and reports timeout honestly',async()=>{
 const waiting=waitForWorkspace(command,30);outcome({...command,actionId:'other'},true,'Unrelated');expect((await waiting).ok).toBe(false);
 expect(matchesWorkspace(command,2,8)).toBe(false);expect(matchesWorkspace(command,1,9)).toBe(false);expect(matchesWorkspace(command,1,8,true)).toBe(false);
});
it('confirms opening after an unrelated editor rerender while validation is pending',async()=>{
 let resolve!:(c:WorkspaceCommand)=>void;vi.mocked(api.post).mockImplementation(()=>new Promise(r=>{resolve=r;}));
 const open={...command,operation:'open_project' as const};
 const editor={document:{project_id:1},baseRevision:{id:8},dirty:false,selectedIds:[]} as unknown as EditableModelEditor;
 const {rerender}=renderHook(({value})=>useWorkspaceAssistant(value,1),{initialProps:{value:editor}});
 const confirmed=waitForWorkspace(open,1000);act(()=>window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:open})));
 rerender({value:{...editor}});await act(async()=>resolve(open));
 expect(await confirmed).toMatchObject({ok:true,message:'Opened Test · saved revision 8.'});
});
it('rejects a changed revision while validation is pending',async()=>{
 let resolve!:(c:WorkspaceCommand)=>void;vi.mocked(api.post).mockImplementation(()=>new Promise(r=>{resolve=r;}));
 const editor={document:{project_id:1},baseRevision:{id:8},dirty:false,selectedIds:[],selectMany:vi.fn()} as unknown as EditableModelEditor;
 const {rerender}=renderHook(({value})=>useWorkspaceAssistant(value,1),{initialProps:{value:editor}});
 const confirmed=waitForWorkspace(command,1000);act(()=>window.dispatchEvent(new CustomEvent('geoai:workspace-command',{detail:command})));
 rerender({value:{...editor,baseRevision:{...editor.baseRevision!,id:9}}});await act(async()=>resolve(command));
 expect((await confirmed).ok).toBe(false);expect(editor.selectMany).not.toHaveBeenCalled();
});
