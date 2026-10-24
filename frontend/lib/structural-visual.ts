/** Read-only projection of saved solver evidence. No stiffness or response calculation. */
import {diagramRibbons} from './structural-display';
import type {RecordRow} from '@/components/model-editor/PhysicalFramePanel';
import {buildFoundationOverlay,type FoundationData} from './foundation-visual';
export const STRUCTURAL_MODES=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
export type StructuralMode=typeof STRUCTURAL_MODES[number][0];
export type FrameResult=RecordRow['result'];
export type StructuralRow={id:number;model_revision_id:number;status:string;result:FrameResult&{model_document_sha256?:string;frames?:{beam_id:string;result:FrameResult}[];transfer?:Transfer;reaction_total_kn?:number;reaction_balance_error_kn?:number}};
export type Transfer={slab_id:string;applied_kn?:number;transferred_kn?:number;conservation_error_kn?:number;strips:{beam_id:string;beam_name:string;line_load_kn_m?:number;transferred_kn?:number;polygon_enu_m:number[][]}[]};
export type VisualComponent={id:string;name:string;category:string;transform:{position:number[]}};
export type StructuralOverlay={mode:string;paths:number[][][];colors:string[];componentIds:string[];inspectionKeys:string[];nodeMarkers:{name:string;position:number[];componentId:string;inspectionKey:string}[];polygons:{positions:number[][];basePositions?:number[][];color:string;componentId:string;alpha:number;inspectionKey?:string}[];arrowIndices:number[];overlayThroughSolids:boolean;fit:boolean;fitPoints:number[][];focusComponentIds?:string[];fitPitch?:number;fitHeadingOffset?:number;displayOpacity?:Record<string,number>;label:string;visualMode:string;pathStyles?:string[];selectedComponentId?:string;floorSystem?:boolean;animation?:{basePaths:number[][][];periodSeconds:number}};
export type StructuralEvidence={frames:FrameResult[];transfer?:Transfer;foundation?:{data:FoundationData;cover_mm:number};recordIds:number[]};
export function savedStructuralEvidence(frameRows:StructuralRow[],slabRows:StructuralRow[],revision:number):StructuralEvidence{
 const valid=(r:StructuralRow)=>r.model_revision_id===revision&&r.status==='VERIFIED';
 const slab=slabRows.find(r=>valid(r)&&r.result.frames?.length&&r.result.frames.every(f=>f.result.solver_version&&f.result.elements?.length));
 if(slab)return {frames:slab.result.frames!.map(f=>f.result),transfer:slab.result.transfer,recordIds:[slab.id]};
 const frame=frameRows.find(r=>valid(r)&&r.result.solver_version&&r.result.elements?.length);
 return {frames:frame?[frame.result]:[],recordIds:frame?[frame.id]:[]};
}
export function structuralCases(e:StructuralEvidence){return [...new Set(e.frames.flatMap(f=>[f.case_name??'Saved case',...(f.load_case_results??[]).map(c=>c.case_name??'Saved case')]))];}
export function selectedStructuralFrames(e:StructuralEvidence,caseName:string){return e.frames.flatMap(f=>{if((f.case_name??'Saved case')===caseName)return [f];const c=f.load_case_results?.find(c=>c.case_name===caseName);return c?[{...f,...c,inputs:f.inputs,physical_to_analytical_graph:f.physical_to_analytical_graph}]:[];});}
const finite=(p:number[])=>p.length===3&&p.every(Number.isFinite);
export function buildStructuralOverlay(e:StructuralEvidence,components:VisualComponent[],mode:StructuralMode,opts:{caseName:string;scale:number;force:'moment'|'shear'|'axial';original:boolean;isolate:boolean;selectedId?:string;fit?:boolean}):StructuralOverlay{
 const displayScale=Number.isFinite(opts.scale)?Math.max(1,Math.min(10000,opts.scale)):1;
 if(mode==='foundation'&&e.foundation){const f=buildFoundationOverlay(e.foundation.data,{cover_mm:e.foundation.cover_mm},'soil',{fit:opts.fit});return {...f,selectedComponentId:opts.selectedId,mode:'structural-visual',visualMode:mode,arrowIndices:[],inspectionKeys:f.paths.map(()=>e.foundation!.data.geometry.footing_id),nodeMarkers:f.nodeMarkers.map(m=>({...m,componentId:e.foundation!.data.geometry.footing_id,inspectionKey:e.foundation!.data.geometry.footing_id})),polygons:f.polygons.map(p=>({...p,inspectionKey:e.foundation!.data.geometry.footing_id,alpha:p.alpha??.3}))};}
 const o:StructuralOverlay={mode:'structural-visual',visualMode:mode,paths:[],colors:[],componentIds:[],inspectionKeys:[],nodeMarkers:[],polygons:[],arrowIndices:[],overlayThroughSolids:true,fit:opts.fit!==false,fitPoints:[],pathStyles:[],selectedComponentId:opts.selectedId,label:STRUCTURAL_MODES.find(m=>m[0]===mode)![1]};
 const frames=selectedStructuralFrames(e,opts.caseName),ids=new Set(frames.flatMap(f=>f.physical_to_analytical_graph?.component_ids??[]));if(e.transfer)ids.add(e.transfer.slab_id);
 o.displayOpacity=Object.fromEntries([...ids].map(id=>[id,id===e.transfer?.slab_id ? .15 : .32]));
 if(['path','slab','foundation','warnings'].includes(mode)){o.fitPitch=-32;o.fitHeadingOffset=2.4;}
 if(opts.isolate)o.focusComponentIds=[...ids];
 const line=(p:number[][],id:string,color:string,arrow=false,style='response')=>{if(p.length<2||!p.every(finite))return;if(arrow)o.arrowIndices.push(o.paths.length);o.paths.push(p);o.componentIds.push(id);o.inspectionKeys.push(id);o.colors.push(color);o.pathStyles!.push(style);};
 const mark=(name:string,p:number[],id:string)=>{if(finite(p))o.nodeMarkers.push({name,position:p,componentId:id,inspectionKey:id});};
 const vector=(p:number[],d:number[],id:string,label:string,color='#ffe18a')=>{const L=Math.hypot(...d);if(!L)return;const tail=p.map((v,i)=>v-d[i]/L*.65);line([tail,p],id,color,true);if(label)mark(label,tail,id);};
 for(const f of frames){
  const g=f.physical_to_analytical_graph;if(!g)continue;const enu=(p:number[])=>[g.origin_enu_m[0]+p[0],g.origin_enu_m[1],g.origin_enu_m[2]+p[1]];
  o.fitPoints.push(...(g.node_positions_m??[]).map(enu));
  const marked=new Set<string>();
  const samples=(f.elements??[]).flatMap(el=>el.samples),value=(s:typeof samples[number])=>opts.force==='moment'?s.moment_nm:opts.force==='shear'?s.shear_n:s.axial_n,max=Math.max(1,...samples.map(s=>Math.abs(value(s))));
  for(const el of f.elements??[]){if(el.samples.length<2)continue;const p=el.samples.map(s=>enu(s.position_m)),id=el.component_id;
   if(mode==='path'||mode==='warnings')line(p,id,'#65d7bf');
   if(mode==='deformation'){
    if(opts.original)line(p,id,'#91a1ae',false,'reference');
    const scale=displayScale;
    line(el.samples.map(s=>enu([s.position_m[0]+scale*s.displacement_m[0],s.position_m[1]+scale*s.displacement_m[1]])),id,'#60a5fa');
    const peak=(f.elements??[]).filter(e=>e.component_id===id).flatMap(e=>e.samples).reduce((a,b)=>Math.hypot(...b.displacement_m)>Math.hypot(...a.displacement_m)?b:a);if(!marked.has(id))mark(`${g.members.find(m=>m.component_id===id)?.name??id} · |u|max ${(Math.hypot(...peak.displacement_m)*1000).toPrecision(4)} mm`,enu([peak.position_m[0]+scale*peak.displacement_m[0],peak.position_m[1]+scale*peak.displacement_m[1]]),id);
   }
   if(mode==='forces'){
    const a=el.samples[0].position_m,b=el.samples.at(-1)!.position_m,dx=b[0]-a[0],dz=b[1]-a[1],L=Math.hypot(dx,dz);if(!L)continue;
    const color=opts.force==='moment'?'#ffbd69':opts.force==='shear'?'#63ddff':'#dca0ff';
    const diagram=el.samples.map(s=>enu([s.position_m[0]-dz/L*value(s)/max*.75,s.position_m[1]+dx/L*value(s)/max*.75]));
    line(p,id,'#91a1ae',false,'reference');line(diagram,id,color,false,opts.force==='axial'?'diagram-dashed':'diagram');
    // Display ordinates reference existing signed samples; no response is recomputed.
    for(let i=0;i<p.length;i+=opts.force==='shear'?4:8)line([p[i],diagram[i]],id,color,false,'ordinate');
    if(opts.force!=='shear')for(const positions of diagramRibbons(p,diagram,el.samples.map(value)))o.polygons.push({positions,color,componentId:id,alpha:.16});
    const peak=(f.elements??[]).filter(e=>e.component_id===id).flatMap(e=>e.samples).reduce((a,b)=>Math.abs(value(b))>Math.abs(value(a))?b:a);if(!marked.has(id))mark(`${opts.force} ${ (value(peak)/1000).toFixed(3)} ${opts.force==='moment'?'kN·m':'kN'} · signed sample peak`,enu(peak.position_m),id);
   }
   marked.add(id);
  }
  if(mode==='path'||mode==='warnings'||mode==='deformation')for(const j of g.connection_offsets??[]){
   const declared=f.inputs?.connections.find(c=>c.column_id===j.column_id&&c.beam_id===j.beam_id&&c.beam_endpoint===j.beam_endpoint),approved=declared?.behavior==='rigid_offset'&&declared.idealization_approved;
   if(mode!=='deformation'){line([enu(j.column_top_m),enu(j.beam_end_m)],j.beam_id,approved?'#ff83e1':'#ff6575');mark(approved?'Declared rigid arm · capacity unverified':'Unverified transfer',enu(j.column_top_m),j.column_id);}
   else{const t=f.rigid_offset_transfers?.find(t=>t.node===j.retained_node_id&&t.component_id===j.beam_id),n=f.nodes?.find(n=>n.id===j.retained_node_id);if(t&&n)line([enu(j.column_top_m.map((v,i)=>v+displayScale*n.displacement_m[i])),enu(j.beam_end_m.map((v,i)=>v+displayScale*t.physical_end_displacement_si[i]))],j.beam_id,'#ff83e1');}
  }
  if(mode==='loads'){
   for(const [tag,load] of Object.entries(f.applied_loads?.nodal_loads_si??{})){const xy=g.node_positions_m?.[Number(tag)-1],member=g.members.find(m=>m.node_ids.includes(Number(tag)));if(!xy||!member)continue;for(const i of [0,1])if(load[i])vector(enu(xy),i===0?[load[i],0,0]:[0,0,load[i]],member.component_id,`Node ${tag} ${i?'Up':'East'} ${(load[i]/1000).toFixed(3)} kN`);if(load[2])mark(`Applied moment ${(load[2]/1000).toFixed(3)} kN·m about −North`,enu(xy),member.component_id);}
   for(const m of g.members){const q=f.applied_loads?.uniform_global_by_component_n_per_m?.[m.component_id],el=f.elements?.filter(el=>el.component_id===m.component_id).flatMap(el=>el.samples);if(!q||!el?.length)continue;for(const t of [0,.5,1]){const a=el[0].position_m,b=el.at(-1)!.position_m,xy=a.map((v,i)=>v+(b[i]-v)*t);for(const i of [0,1])if(q[i])vector(enu(xy),i===0?[q[i],0,0]:[0,0,q[i]],m.component_id,t===.5?`${m.name} q${i?'Up':'East'} ${(q[i]/1000).toFixed(3)} kN/m`:'');}}
   for(const r of f.reactions??[]){const xy=g.node_positions_m?.[r.node-1],m=g.members.find(m=>m.node_ids.includes(r.node));if(!xy||!m)continue;vector(enu(xy),[r.fx_n,0,r.fy_n],m.component_id,`R${r.node} East ${(r.fx_n/1000).toFixed(3)} / Up ${(r.fy_n/1000).toFixed(3)} kN\nM−N ${(r.moment_nm/1000).toFixed(3)} kN·m`,'#65d7bf');}
  }
 }
 if((mode==='slab'||mode==='path')&&e.transfer)for(const strip of e.transfer.strips){o.polygons.push({positions:strip.polygon_enu_m,color:'#65cfe8',componentId:e.transfer.slab_id,alpha:.28});const p=strip.polygon_enu_m.reduce((sum,p)=>sum.map((v,i)=>v+p[i]/strip.polygon_enu_m.length),[0,0,0]);mark(`${strip.beam_name} · q ${strip.line_load_kn_m?.toFixed(3)} kN/m\nTransferred ${strip.transferred_kn?.toFixed(3)} kN`,p,strip.beam_id);const beam=components.find(c=>c.id===strip.beam_id);if(beam)line([p,beam.transform.position],strip.beam_id,'#65d7bf',true);}
 if(mode==='warnings'||mode==='foundation')for(const c of components.filter(c=>['column','beam','slab','footing','foundation','base_plate','connection'].includes(c.category))){if(!ids.has(c.id)||['footing','foundation','base_plate','connection'].includes(c.category))mark(`${c.name} · ${ids.has(c.id)?'Connection capacity unverified':'No current verified solver transfer'}`,c.transform.position,c.id);}
 o.label+=mode==='deformation'?` · displacement ×${opts.scale} (visual magnification) · grey original / lime deformed`:mode==='forces'?` · ${opts.force==='moment'?'kN·m':'kN'} · diagram offset normalized, not geometry`:mode==='path'?' · declared analytical topology, arrows do not encode force direction':' · saved numerical evidence only';
 return o;
}

