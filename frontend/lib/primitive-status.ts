import type {WorkspaceCommand} from './workspace-assistant';
export type PrimitivePhase='preview_pending'|'canceled'|'applied_unsaved'|'saved'|'rejected_stale';
export type PrimitiveStatus={actionId:string;projectId:number;phase:PrimitivePhase;message:string;revisionId?:number};
export const isPrimitive=(c:WorkspaceCommand)=>c.operation==='prepare_primitive_preview'||c.operation==='prepare_beam_preview';
export function primitiveStatus(c:WorkspaceCommand,phase:PrimitivePhase,message:string,revisionId?:number){
 window.dispatchEvent(new CustomEvent<PrimitiveStatus>('geoai:primitive-status',{detail:{actionId:c.actionId,projectId:c.projectId,phase,message,revisionId}}));
}
