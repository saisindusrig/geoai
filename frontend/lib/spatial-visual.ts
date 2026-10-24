/** Display projection only: every response value comes from saved native solver evidence. */
import type {StructuralOverlay,StructuralMode} from './structural-visual';
import {diagramRibbons} from './structural-display';
export type SpatialSample={position:number[];displacement:number[];N:number;Vy:number;Vz:number;My:number;Mz:number;T:number};
export type SpatialMember={id:string;nodes:number[];floor:number;kind:string;axes:number[][];length_m:number;end_forces:number[];uniform_global_n_m:number[];samples:SpatialSample[]};
export type SpatialSlab={id:string;floor:number;beams:string[];width_m:number;pressure_pa:number};
export type SpatialCase={status:string;run_id:string;case:{name:string;nodal:Record<string,number[]>;slab_factor:number};nodes:{id:number;position:number[];fixed:boolean;displacement:number[];reaction:number[]}[];members:SpatialMember[];slabs:SpatialSlab[];comparisons:Record<string,number>;limitations:string[]};
export type SpatialRecord={id:number;status:string;model_revision_id:number;result:{cases?:SpatialCase[];proposal_sha256?:string;input_sha256?:string;model_document_sha256:string;limitations:string[];benchmark_gate?:{status:string};evidence_sha256?:string}};
export type SpatialOptions={mode:StructuralMode;floor:number;force:'N'|'Vy'|'Vz'|'My'|'Mz'|'T';scale:number;original:boolean;selectedId?:string;fit:boolean;isolate:boolean};
export function spatialOverlay(c:SpatialCase,opts:SpatialOptions):StructuralOverlay{
 const members=c.members.filter(m=>!opts.floor||m.floor===opts.floor),slabs=c.slabs.filter(s=>!opts.floor||s.floor===opts.floor),ids=[...members.map(m=>m.id),...slabs.map(s=>s.id)];
 const o:StructuralOverlay={mode:'structural-visual',visualMode:opts.mode,paths:[],colors:[],componentIds:[],inspectionKeys:[],pathStyles:[],arrowIndices:[],nodeMarkers:[],polygons:[],fit:opts.fit,fitPoints:members.flatMap(m=>[m.samples[0].position,m.samples.at(-1)!.position]),overlayThroughSolids:true,selectedComponentId:opts.selectedId,displayOpacity:Object.fromEntries(ids.map(id=>[id,id.startsWith('slab-')?.12:.25])),label:'Spatial linear frame · saved N m rad · no safety approval',fitPitch:-28,fitHeadingOffset:.6};
 if(opts.isolate)o.focusComponentIds=ids;
 const line=(p:number[][],id:string,color:string,style='response',arrow=false)=>{if(!p.every(x=>x.length===3&&x.every(Number.isFinite)))return;if(arrow)o.arrowIndices.push(o.paths.length);o.paths.push(p);o.colors.push(color);o.componentIds.push(id);o.inspectionKeys.push(id);o.pathStyles!.push(style);};
 const mark=(name:string,position:number[],id:string)=>o.nodeMarkers.push({name,position,componentId:id,inspectionKey:id});
 const arrow=(p:number[],f:number[],id:string,text:string,color:string)=>{const norm=Math.hypot(...f);if(!norm)return;const tail=p.map((v,i)=>v-f[i]/norm*.8);line([tail,p],id,color,'response',true);mark(text,tail,id);};
 const peak=Math.max(1,...members.flatMap(m=>m.samples.map(s=>Math.abs(s[opts.force])))),magnification=Number.isFinite(opts.scale)?Math.max(1,Math.min(1000,opts.scale)):1;
 for(const m of members){
  const p=m.samples.map(s=>s.position);
  if(['path','slab','loads','foundation','warnings'].includes(opts.mode))line(p,m.id,opts.mode==='warnings'?'#ffbd69':'#65d7bf');
  if(opts.mode==='deformation'){
   if(opts.original)line(p,m.id,'#91a1ae','reference');
   const deformed=m.samples.map(s=>s.position.map((v,i)=>v+magnification*s.displacement[i]));line(deformed,m.id,'#60a5fa');
   const i=m.samples.reduce((best,s,i,ss)=>Math.hypot(...s.displacement)>Math.hypot(...ss[best].displacement)?i:best,0);
   mark(`${m.id} · |u| ${(Math.hypot(...m.samples[i].displacement)*1000).toFixed(3)} mm (actual)`,deformed[i],m.id);
  }
  if(opts.mode==='forces'){
   const bending=['My','Mz'].includes(opts.force),shear=['Vy','Vz'].includes(opts.force),color=bending?'#ffbd69':shear?'#63ddff':'#dca0ff';
   const axis=m.axes[['My','Vz','T'].includes(opts.force)?2:1],diagram=m.samples.map(s=>s.position.map((v,i)=>v+axis[i]*s[opts.force]/peak*.8));
   line(p,m.id,'#91a1ae','reference');line(diagram,m.id,color,bending||shear?'diagram':'diagram-dashed');
   for(let i=0;i<p.length;i+=shear?2:8)line([p[i],diagram[i]],m.id,color,'ordinate');
   if(bending)for(const positions of diagramRibbons(p,diagram,m.samples.map(s=>s[opts.force])))o.polygons.push({positions,color,alpha:.16,componentId:m.id});
   const s=m.samples.reduce((a,b)=>Math.abs(b[opts.force])>Math.abs(a[opts.force])?b:a);mark(`${m.id} · ${opts.force} ${(s[opts.force]/1000).toFixed(3)} ${bending||opts.force==='T'?'kN·m':'kN'}`,s.position,m.id);
  }
  if(opts.mode==='loads'){
   const q=m.uniform_global_n_m;for(const i of [0,8,16])if(Math.hypot(...q))arrow(p[i],q,m.id,i===8?`Uniform gravity ${(Math.hypot(...q)/1000).toFixed(2)} kN/m`:'','#ffe18a');
  }
  if(opts.mode==='warnings')mark(`${m.id} · rigid centreline joints; capacity NOT VERIFIED`,p[0],m.id);
 }
 if(['loads','foundation','path'].includes(opts.mode))for(const n of c.nodes){const m=members.find(m=>m.nodes.includes(n.id));if(!m)continue;const f=c.case.nodal[n.id];if(opts.mode==='loads'&&f){arrow(n.position,f.slice(0,3),m.id,`N${n.id} · E/N/U ${f.slice(0,3).map(v=>(v/1000).toFixed(2)).join('/')} kN`,'#ffe18a');if(Math.hypot(...f.slice(3)))mark(`N${n.id} applied M E/N/U ${f.slice(3).map(v=>(v/1000).toFixed(2)).join('/')} kN·m`,n.position,m.id);}if(n.fixed){arrow(n.position,n.reaction.slice(0,3),m.id,`Fixed base N${n.id} · E/N/U ${n.reaction.slice(0,3).map(v=>(v/1000).toFixed(2)).join('/')} kN`,'#65d7bf');if(opts.mode==='foundation')mark('Prescribed fixed base · soil/foundation transfer NOT VERIFIED',n.position,m.id);}}
 if(opts.mode==='slab'||opts.mode==='path')for(const s of slabs){const [a,b]=s.beams.map(id=>c.members.find(m=>m.id===id)!);const polygon=[a.samples[0].position,a.samples.at(-1)!.position,b.samples.at(-1)!.position,b.samples[0].position];o.polygons.push({positions:polygon,color:'#65cfe8',componentId:s.id,alpha:.22});const center=polygon.reduce((sum,p)=>sum.map((v,i)=>v+p[i]/4),[0,0,0]);mark(`${s.id} · ${(s.pressure_pa*c.case.slab_factor/1000).toFixed(2)} kPa · one-way allocation only`,center,s.id);for(const m of [a,b])line([center,m.samples[8].position],s.id,'#65cfe8','response',true);}
 o.label+=opts.mode==='deformation'?` · computed displacement ×${magnification} visual magnification`:opts.mode==='forces'?` · ${opts.force} · ±0.80 m diagram offset = ±${(peak/1000).toPrecision(4)} ${['My','Mz','T'].includes(opts.force)?'kN·m':'kN'}; not deformation`:'';
 return o;
}
