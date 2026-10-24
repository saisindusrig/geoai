/** Read-only floor selection and graph tracing. No stiffness or force redistribution. */
import {spatialOverlay,type SpatialCase,type SpatialOptions} from './spatial-visual';
export type FloorEvidence={analysis_id:number;model_document_sha256:string;cases:{status:string;case_name:string;run_id:string;slabs:{id:string;floor:number;status:string;pressure_pa:number;area_m2:number;applied_downward_n:number;allocation_residual_n:number;strips:{beam_id:string;area_m2:number;line_load_n_m:number;downward_force_n:number;polygon:number[][]}[]}[];node_balances:{node_id:number;fixed:boolean;member_end_action_sum_enu:number[];applied_nodal_enu:number[];support_reaction_enu:number[];residual_enu:number[]}[];comparisons:Record<string,number>;capabilities:Record<string,boolean>;limitations:string[]}[]};
export type TraceEntity={key:string;label:string;kind:'slab'|'beam'|'column'|'load'|'joint'|'base';position:number[];componentId?:string;floor?:number;description:string};
export function floorOutline(c:SpatialCase,id:string){const slab=c.slabs.find(s=>s.id===id);if(!slab)return [];const [a,b]=slab.beams.map(id=>c.members.find(m=>m.id===id));if(!a||!b)return [];return [a.samples[0].position,a.samples.at(-1)!.position,b.samples.at(-1)!.position,b.samples[0].position];}
const center=(points:number[][])=>points.reduce((sum,p)=>sum.map((v,i)=>v+p[i]/points.length),[0,0,0]);
export function connectedEntities(c:SpatialCase){
 const entities=new Map<string,TraceEntity>(),next=new Map<string,string[]>();
 for(const n of c.nodes){const key=`node:${n.id}`;entities.set(key,{key,label:n.fixed?`Base N${n.id}`:`Joint N${n.id}`,kind:n.fixed?'base':'joint',position:n.position,description:n.fixed?'Prescribed fixed restraint; foundation/soil capacity NOT VERIFIED.':'Explicit shared six-DOF analytical node; connection capacity NOT VERIFIED.'});next.set(key,n.fixed?[]:c.members.filter(m=>m.nodes.includes(n.id)).map(m=>m.id));const f=c.case.nodal[n.id];if(f?.some(v=>v!==0)){const key=`load:node:${n.id}`;entities.set(key,{key,label:`N${n.id} applied load`,kind:'load',position:n.position,description:`E/N/U ${f.slice(0,3).map(v=>(v/1000).toFixed(2)).join('/')} kN; moments ${f.slice(3).map(v=>(v/1000).toFixed(2)).join('/')} kN·m.`});next.set(key,[`node:${n.id}`]);}}
 for(const m of c.members){entities.set(m.id,{key:m.id,label:m.id,kind:m.kind==='column'?'column':'beam',componentId:m.id,floor:m.floor,position:m.samples[8].position,description:'Whole saved-case end actions and section samples; no selected-load attribution.'});next.set(m.id,m.nodes.map(n=>`node:${n}`));if(m.uniform_global_n_m.some(v=>Math.abs(v)>1e-12)){const key=`load:beam:${m.id}`;entities.set(key,{key,label:`q · ${m.id}`,kind:'load',position:m.samples[8].position,componentId:m.id,floor:m.floor,description:`Saved E/N/U line load ${m.uniform_global_n_m.map(v=>(v/1000).toFixed(2)).join('/')} kN/m.`});next.set(key,[m.id]);}}
 for(const s of c.slabs){const polygon=floorOutline(c,s.id);if(!polygon.length)continue;const position=center(polygon);entities.set(s.id,{key:s.id,label:`${s.id} · LOAD-ONLY`,kind:'slab',position,componentId:s.id,floor:s.floor,description:'Reviewed one-way tributary load allocation only. No plate stiffness, diaphragm or slab deformation.'});next.set(s.id,s.beams);if(s.pressure_pa*c.case.slab_factor){const key=`load:slab:${s.id}`;entities.set(key,{key,label:`Pressure · ${s.id}`,kind:'load',position,componentId:s.id,floor:s.floor,description:`${(s.pressure_pa*c.case.slab_factor/1000).toFixed(2)} kPa saved uniform gravity pressure.`});next.set(key,[s.id]);}}
 return {entities,next};
}
/** Directed allocation at the slab; thereafter undirected shared-node frame connectivity.
 * Slabs can NEVER be intermediate structural links between beams. Fixed bases terminate.
 */
export function routesToBases(c:SpatialCase,start:string){const {entities,next}=connectedEntities(c);if(!entities.has(start))return [];const visited=new Set([start]),queue=[[start]],routes:string[][]=[];for(let i=0;i<queue.length;i++){const path=queue[i],key=path.at(-1)!;if(entities.get(key)?.kind==='base'){routes.push(path);continue;}for(const other of next.get(key)??[]){if(!entities.has(other)||visited.has(other))continue;visited.add(other);queue.push([...path,other]);}}return routes;}
export type FloorOptions=SpatialOptions&{surfaces?:boolean;labels?:'selection'|'overview'|'all';inspectionKey?:string;trace?:string[];animate?:boolean};
export function floorOverlay(c:SpatialCase,opts:FloorOptions,evidence?:FloorEvidence['cases'][number]){
 const o=spatialOverlay(c,opts),floorIds=new Set(c.slabs.map(s=>s.id)),graph=connectedEntities(c),selectedKey=opts.inspectionKey??opts.selectedId;
 o.floorSystem=true;
 // A lateral-only case has no slab gravity arrows; geometry is still selectable.
 const suppressed=new Set(o.arrowIndices.filter(i=>{const slab=c.slabs.find(s=>s.id===o.componentIds[i]);return slab&&slab.pressure_pa*c.case.slab_factor===0;}));
 if(suppressed.size){const keep=o.paths.map((_,i)=>i).filter(i=>!suppressed.has(i)),oldArrows=new Set(o.arrowIndices);o.paths=keep.map(i=>o.paths[i]);o.colors=keep.map(i=>o.colors[i]);o.componentIds=keep.map(i=>o.componentIds[i]);o.inspectionKeys=keep.map(i=>o.inspectionKeys[i]);o.pathStyles=keep.map(i=>o.pathStyles![i]);o.arrowIndices=keep.flatMap((old,i)=>oldArrows.has(old)?[i]:[]);}
 const add=(positions:number[][],id:string,key:string,color:string,arrow=false,style='response')=>{if(arrow)o.arrowIndices.push(o.paths.length);o.paths.push(positions);o.colors.push(color);o.componentIds.push(id);o.inspectionKeys.push(key);o.pathStyles!.push(style);};
 const marker=(name:string,position:number[],componentId:string,inspectionKey:string)=>o.nodeMarkers.push({name,position,componentId,inspectionKey});
 const arrow=(p:number[],vector:number[],id:string,key:string,text:string,color:string)=>{const norm=Math.hypot(...vector);if(!norm)return;const tail=p.map((v,i)=>v-vector[i]/norm*.65);add([tail,p],id,key,color,true);if(text)marker(text,tail,id,key);};
 // Stable, undeformed floor surfaces remain explicitly LOAD-ONLY in every mode.
 o.polygons=o.polygons.filter(p=>!floorIds.has(p.componentId));o.nodeMarkers=o.nodeMarkers.filter(p=>!floorIds.has(p.componentId));
 for(const s of c.slabs.filter(s=>!opts.floor||s.floor===opts.floor)){
  const polygon=floorOutline(c,s.id);if(!polygon.length)continue;
  o.displayOpacity![s.id]=0;
  if(opts.surfaces!==false){o.polygons.push({positions:polygon,color:selectedKey===s.id?'#aaf4ff':s.floor%2?'#64b5dd':'#a1a9ee',componentId:s.id,inspectionKey:s.id,alpha:selectedKey===s.id?.32:opts.mode==='deformation'?.08:.18});marker(`F${s.floor} · ${s.id.split('-').at(-1)} · LOAD-ONLY`,center(polygon),s.id,s.id);o.displayOpacity![s.id]=0;}
  const saved=evidence?.slabs.find(e=>e.id===s.id);
  if(saved&&opts.surfaces!==false&&['path','slab'].includes(opts.mode))for(const strip of saved.strips)o.polygons.push({positions:strip.polygon,color:strip.beam_id===s.beams[0]?'#54d8c8':'#79b4ff',componentId:s.id,inspectionKey:s.id,alpha:.12});
 }
 // Make each real load/reaction independently inspectable rather than aliasing its beam.
 if(opts.mode==='loads'){
  const remove=new Set(o.arrowIndices),keep=o.paths.map((_,i)=>i).filter(i=>!remove.has(i));o.paths=keep.map(i=>o.paths[i]);o.colors=keep.map(i=>o.colors[i]);o.componentIds=keep.map(i=>o.componentIds[i]);o.inspectionKeys=keep.map(i=>o.inspectionKeys[i]);o.pathStyles=keep.map(i=>o.pathStyles![i]);o.arrowIndices=[];o.nodeMarkers=o.nodeMarkers.filter(m=>floorIds.has(m.componentId));
  for(const m of c.members.filter(m=>!opts.floor||m.floor===opts.floor)){const key=`load:beam:${m.id}`;for(const i of [4,8,12])arrow(m.samples[i].position,m.uniform_global_n_m,m.id,key,i===8?`q ${(Math.hypot(...m.uniform_global_n_m)/1000).toFixed(2)} kN/m`:'','#ffe18a');}
  for(const n of c.nodes){const m=c.members.find(m=>m.nodes.includes(n.id)&&(!opts.floor||m.floor===opts.floor));if(!m)continue;const f=c.case.nodal[n.id];if(f){arrow(n.position,f.slice(0,3),m.id,`load:node:${n.id}`,`N${n.id} · ${f.slice(0,3).map(v=>(v/1000).toFixed(2)).join('/')} kN`,'#ffe18a');if(Math.hypot(...f.slice(3)))marker(`N${n.id} moment ${f.slice(3).map(v=>(v/1000).toFixed(2)).join('/')} kN·m`,n.position,m.id,`load:node:${n.id}`);}if(n.fixed)arrow(n.position,n.reaction.slice(0,3),m.id,`node:${n.id}`,`Base N${n.id} · ${(n.reaction[2]/1000).toFixed(2)} kN Up`,'#65d7bf');}
 }
 for(let i=0;i<o.paths.length;i++)if(floorIds.has(o.componentIds[i])&&o.arrowIndices.includes(i))o.inspectionKeys[i]=`load:slab:${o.componentIds[i]}`;
 // A highlighted route is connectivity, with no invented individual-load force shares.
 const trace=opts.trace??[];
 if(evidence?.status==='VERIFIED'&&trace.length&&opts.mode!=='deformation'){
  for(let i=1;i<trace.length;i++){if(!(graph.next.get(trace[i-1])??[]).includes(trace[i]))continue;const a=graph.entities.get(trace[i-1]),b=graph.entities.get(trace[i]);if(!a||!b)continue;const member=c.members.find(m=>m.id===a.componentId||m.id===b.componentId);if(opts.floor&&member&&member.floor!==opts.floor)continue;const id=b.componentId??a.componentId??'',pa=a.position,pb=b.position;if(Math.hypot(...pa.map((v,i)=>v-pb[i]))>1e-9)add([pa,pb],id,b.key,'#ed90ff',true);}
  for(const key of trace){const m=c.members.find(m=>m.id===key);if(m&&(!opts.floor||m.floor===opts.floor))add(m.samples.map(s=>s.position),m.id,m.id,'#ed90ff');}
 }
 // At most a few labels by default; source values remain available on selection.
 const policy=opts.labels??'selection';if(policy!=='all'){
  const selected=o.nodeMarkers.filter(m=>m.inspectionKey===selectedKey||m.componentId===opts.selectedId),floors=o.nodeMarkers.filter(m=>m.name.includes('LOAD-ONLY')&&!selected.includes(m)),overview=policy==='overview'?o.nodeMarkers.filter(m=>!selected.includes(m)&&!floors.includes(m)).slice(0,4):[];
  o.nodeMarkers=[...selected.slice(0,3),...floors,...overview];
 }
 const entity=selectedKey?graph.entities.get(selectedKey):undefined;
 if(entity&&!o.nodeMarkers.some(m=>m.inspectionKey===entity.key))marker(`${entity.label} · ${entity.kind==='base'?'restraint only':entity.kind==='slab'?'LOAD-ONLY':'selected saved evidence'}`,entity.position,entity.componentId??'',entity.key);
 if(policy==='selection'&&o.nodeMarkers.length>7)o.nodeMarkers=[...o.nodeMarkers.filter(m=>m.inspectionKey===selectedKey),...o.nodeMarkers.filter(m=>m.name.includes('LOAD-ONLY')&&m.inspectionKey!==selectedKey),...o.nodeMarkers.filter(m=>m.inspectionKey!==selectedKey&&!m.name.includes('LOAD-ONLY'))].slice(0,7);
 if(opts.animate&&opts.mode==='deformation'){
  o.animation={periodSeconds:4,basePaths:o.paths.map((p,i)=>o.pathStyles?.[i]==='reference'?p:(c.members.find(m=>m.id===o.componentIds[i]&&m.samples.length===p.length)?.samples.map(s=>s.position)??p))};
  o.label+=' · STATIC CASE interpolation 0→1→0; not dynamic analysis';
 }
 return o;
}




