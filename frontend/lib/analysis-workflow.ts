/** UI routing/status only. Numerical checks and authorization stay on existing APIs. */
import type {EditableModelDocument} from './types';
export type AnalysisFamily='structure'|'floors'|'foundation';
export type AnalysisMethod='frame'|'slab'|'spatial'|'coupled'|'foundation';
export type WorkflowStep='select'|'inputs'|'analyze'|'results';
export const WORKFLOW_STEPS=['select','inputs','analyze','results'] as const;
export const FAMILY_LABELS={structure:'Structural analysis',floors:'Slabs and floor systems',foundation:'Foundations and soil'};
export type AnalysisRow={id:number;model_revision_id?:number;type?:string;status:string;result:Record<string,unknown>};
export const endpoint=(method:AnalysisMethod)=>({frame:'assembly',slab:'slab-transfer',spatial:'spatial-frame',coupled:'coupled-floor',foundation:'foundation-system'}[method]);
export function methodFor(family:AnalysisFamily,doc?:EditableModelDocument|null):AnalysisMethod{
 const m=doc?.metadata;if(family==='foundation')return 'foundation';if(m?.coupled_floor_review)return 'coupled';if(m?.spatial_frame_review)return 'spatial';return family==='floors'?'slab':'frame';
}
export type ResultIdentity={id:number;project_id:number;model_revision_id:number;method:AnalysisMethod;status:string;load_cases:string[];model_document_sha256:string;current?:boolean};
export type MethodCapability={status:'SUPPORTED'|'MISSING_INPUTS'|'UNSUPPORTED'|'STALE';reason:string;can_review:boolean;current_results:ResultIdentity[];history:ResultIdentity[]};
export type CapabilityResponse={project_id:number;model_revision_id:number;model_document_sha256:string;methods:Record<AnalysisMethod,MethodCapability>};
export function availability(family:AnalysisFamily,doc?:EditableModelDocument|null,capabilities?:CapabilityResponse){
 const capability=capabilities?.methods[methodFor(family,doc)];
 return {available:!!capability&&capability.status!=='UNSUPPORTED',reason:capability?.reason??'Backend capability information unavailable. Read saved status before continuing.',status:capability?.status??'UNSUPPORTED'};
}
export function isCurrentResult(row:AnalysisRow,rid?:number,identity?:ResultIdentity,projectId?:number,method?:AnalysisMethod){
 return !!identity&&identity.id===row.id&&identity.project_id===projectId&&identity.method===method&&identity.model_revision_id===rid&&(row.model_revision_id===undefined||row.model_revision_id===rid)&&identity.status===row.status&&identity.load_cases.length>0&&(method==='foundation'||row.result.model_document_sha256===identity.model_document_sha256);
}
export function resultLabel(row?:AnalysisRow){return row?.type==='FOUNDATION_SYSTEM_RESULT'?'Bounded checks available':row?'Numerically verified':'Not verified';}
export function loadViewState(key:string){
 try{const value=JSON.parse(localStorage.getItem(key)??'null');if(!value||!['structure','floors','foundation'].includes(value.family)||!WORKFLOW_STEPS.includes(value.step))return null;return value as {family:AnalysisFamily;step:WorkflowStep;mode:string;caseName:string;resultId?:number};}catch{return null;}
}
