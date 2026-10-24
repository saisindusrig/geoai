import type {EditableModelComponent,EditableModelDocument,StructuralElementType} from './types';
import type {WorkspaceCommand} from './workspace-assistant';
import {boxFrame} from './editor-transform';

export function boxComponent(category:StructuralElementType,id:string,size:[number,number,number],position:[number,number,number]):EditableModelComponent{
 return {id,parent_id:null,name:category.replaceAll('_',' '),category,visible:true,locked:false,geometry:{kind:'box',size},transform:{position,rotation_deg:[0,0,0],scale:[1,1,1]},material:{name:'Conceptual component',color:'#60A5FA',roughness:.75,metalness:0},quantity:{included:!['zone','grid','site_boundary','construction_phase'].includes(category)}};
}
export function primitiveDocument(command:WorkspaceCommand,doc:EditableModelDocument,revisionId?:number){
 const c=command.candidate;
 const beam=command.operation==='prepare_beam_preview',kind=beam?'beam':'column';
 if(!['prepare_primitive_preview','prepare_beam_preview'].includes(command.operation)||!command.expiresAt||Date.now()>command.expiresAt||command.projectId!==doc.project_id||command.revisionId!==revisionId||doc.units!=='metric')throw Error('Proposal expired or saved revision changed. Request a fresh proposal.');
 if(doc.components.some(v=>v.locked||v.parent_id||!['box','cylinder'].includes(v.geometry.kind)||Object.keys(v.metadata??{}).some(k=>k.startsWith('parametric_')||k.includes('cad')))||Object.keys(doc.metadata??{}).some(k=>/cad|drawing|parametric/.test(k)))throw Error('Protected CAD or assembly model. Use its existing reviewed tools.');
 if(!c||!new RegExp(`^assistant-${kind}:[a-f0-9]{24}$`).test(c.id)||doc.components.some(v=>v.id===c.id)||c.category!==kind||c.parent_id!==null||c.locked||!c.visible||c.geometry.kind!=='box'||c.geometry.size?.length!==3||!c.geometry.size.every(v=>Number.isFinite(v)&&v>=.01&&v<=100)||c.transform.position.length!==3||!c.transform.position.every(v=>Number.isFinite(v)&&Math.abs(v)<=10000)||c.transform.rotation_deg.length!==3||(!beam&&c.transform.rotation_deg.slice(0,2).some(v=>v!==0))||!c.transform.rotation_deg.every(v=>Number.isFinite(v)&&Math.abs(v)<=360)||JSON.stringify(c.transform.scale)!=='[1,1,1]'||c.quantity?.included!==false||c.metadata?.source!=='assistant_supervised_primitive'||c.metadata?.provenance!=='user_dimensions_conceptual')throw Error('Unsupported or invalid component proposal. No editor change was made.');
 if(beam){
  const meta=c.metadata.beam as {endpoints_enu_m?:number[][];length_m?:number}|undefined,frame=boxFrame(c);
  const points=meta?.endpoints_enu_m;
  if(!points||points.length!==2||points.some(p=>!Array.isArray(p)||p.length!==3||p.some(v=>!Number.isFinite(v)||Math.abs(v)>10000))||!Number.isFinite(meta?.length_m)||Math.abs(frame.length-meta!.length_m!)>1e-7||[frame.start,frame.end].some((p,i)=>p.toArray().some((v,j)=>Math.abs(v-points[i][j])>1e-7)))throw Error('Beam transform does not match its exact endpoints. Nothing applied.');
 }
 return {...doc,components:[...doc.components,structuredClone(c)]};
}
