"use client";
import {useEffect,useLayoutEffect,useRef} from 'react';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
import {api} from '@/lib/api';
import {matchesWorkspace,outcome,type WorkspaceCommand} from '@/lib/workspace-assistant';
import {isPrimitive,primitiveStatus} from '@/lib/primitive-status';
export function useWorkspaceAssistant(editor:EditableModelEditor,projectId?:number,previewActive=false){
 const pending=useRef<WorkspaceCommand|null>(null),alive=useRef(true);
 const latest=useRef({editor,projectId,previewActive});
 useLayoutEffect(()=>{latest.current={editor,projectId,previewActive};},[editor,projectId,previewActive]);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;pending.current=null;};},[]);
 useEffect(()=>{
  const receive=async(event:Event)=>{
   const command=(event as CustomEvent<WorkspaceCommand>).detail;
   if(!projectId||command.projectId!==projectId)return;
   if(command.expiresAt&&Date.now()>command.expiresAt){outcome(command,false,'Workspace command expired. No action performed.');return;}
   const cancelling=command.operation==='cancel_primitive_preview';
   if(!matchesWorkspace(command,projectId,editor.baseRevision?.id,!cancelling&&(editor.dirty||previewActive||!!editor.aiPreview||!!editor.platformPreview||!!editor.comparison))){outcome(command,false,'Workspace revision or draft changed. No action performed.');return;}
   try{
    const current=await api.post<WorkspaceCommand>('/api/assistant/workspace/validate',{page:`/projects/${projectId}/workspace`,project_id:projectId,revision_id:editor.baseRevision?.id,selected_ids:editor.selectedIds,dirty:editor.dirty,name:command.validation.name,arguments:command.validation.arguments,action_id:command.actionId});
    const live=latest.current,e=live.editor;
    if((command.expiresAt&&Date.now()>command.expiresAt)||!alive.current||current.actionId!==command.actionId||current.documentHash!==command.documentHash||!matchesWorkspace(command,live.projectId??0,e.baseRevision?.id,!cancelling&&(e.dirty||live.previewActive||!!e.aiPreview||!!e.platformPreview||!!e.comparison)))throw Error('Saved source changed.');
    if(cancelling){const p=e.platformPreview?.proposal;if(!p)throw Error('No temporary component preview is active. Applied or saved geometry was not removed.');primitiveStatus(p,'canceled','Canceled · temporary proposal removed. Nothing applied or saved.');e.setPlatformPreview(null);outcome(command,true,'Temporary component proposal cancelled. No model change was applied or saved.');return;}
    if(isPrimitive(command)){e.stagePrimitivePreview({...current,expiresAt:Date.now()+120000});return;}
    if(command.operation==='open_project'){outcome(command,true,`Opened ${command.projectName} · saved revision ${command.revisionId}.`);return;}
    if(command.operation==='select_components'){
     if(!command.componentIds.every(id=>editor.document?.components.some(c=>c.id===id&&c.visible)))throw Error('The requested component is hidden or absent in the editor.');
     pending.current=command;editor.selectMany(command.componentIds);window.dispatchEvent(new Event('geoai:selection-inspect'));return;
    }
    if(command.operation==='show_saved_result'){
     window.dispatchEvent(new Event('geoai:show-analysis'));
     // The guided panel can mount asynchronously; a bounded DOM observer only
     // delivers the exact command once the real receiver advertises readiness.
     let sent=false;
     const deliver=()=>{if(!sent&&document.querySelector('[data-guided-workspace-ready="true"]')){sent=true;window.dispatchEvent(new CustomEvent('geoai:workspace-result',{detail:command}));return true;}return false;};
     if(!deliver()){const observer=new MutationObserver(()=>{if(deliver())observer.disconnect();});observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-guided-workspace-ready']});window.setTimeout(()=>{observer.disconnect();if(!sent)outcome(command,false,'Saved results panel is unavailable. Open Analyze / Results manually.');},8000);}return;
    }
    window.dispatchEvent(new CustomEvent('geoai:workspace-camera',{detail:command}));
   }catch(e){outcome(command,false,e instanceof Error?e.message:'Workspace validation failed.');}
  };
  window.addEventListener('geoai:workspace-command',receive);
  return()=>{window.removeEventListener('geoai:workspace-command',receive);};
 },[editor,projectId,previewActive]);
 useEffect(()=>{const c=pending.current;if(c&&matchesWorkspace(c,projectId??0,editor.baseRevision?.id,editor.dirty)&&c.componentIds.length===editor.selectedIds.length&&c.componentIds.every(id=>editor.selectedIds.includes(id))){pending.current=null;outcome(c,true,`Selected ${c.componentIds.map(id=>editor.document?.components.find(v=>v.id===id)?.name||id).join(', ')}.`);}},[editor.selectedIds,editor.document,editor.baseRevision?.id,editor.dirty,projectId]);
}
