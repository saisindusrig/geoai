/** Projection of native saved shell displacements; no plate/stress calculation. */
import {spatialOverlay,type SpatialCase,type SpatialOptions} from './spatial-visual';
export type CoupledCase=Omit<SpatialCase,'nodes'>&{shells:{id:number;nodes:number[]}[];center_uz_m:number;mesh:number;validation:{status:string;checks:Record<string,number>};nodes:(SpatialCase['nodes'][number]&{applied:number[]})[];formulation:{thickness_m:number;pressure_pa:number;offset_m:number;diaphragm:boolean};evidence_sha256:string;interface_actions:Record<string,number[]>};
export function coupledOverlay(c:CoupledCase,opts:SpatialOptions&{animate:boolean;surfaces:boolean;inspection:string}){
 const o=spatialOverlay(c,opts);o.floorSystem=true;o.displayOpacity={...o.displayOpacity,'coupled-panel':0};if(o.focusComponentIds)o.focusComponentIds.push('coupled-panel');
 o.nodeMarkers=o.nodeMarkers.filter(n=>n.componentId===opts.selectedId).slice(0,2);
 const nodes=new Map(c.nodes.map(n=>[n.id,n])),peak=Math.max(...c.nodes.map(n=>Math.abs(n.displacement[2])),1e-12),scale=Math.max(1,Math.min(1000,Number.isFinite(opts.scale)?opts.scale:1));
 if(opts.surfaces&&opts.mode!=='forces')for(const shell of c.shells){
  const ns=shell.nodes.map(id=>nodes.get(id)!),base=ns.map(n=>n.position),positions=ns.map(n=>n.position.map((v,i)=>v+(opts.mode==='deformation'?scale*n.displacement[i]:0))),mean=ns.reduce((v,n)=>v+n.displacement[2]/4,0),ratio=Math.min(1,Math.abs(mean)/peak),color=opts.mode==='slab'||opts.mode==='deformation'?`rgb(${Math.round(50+205*ratio)},${Math.round(190-120*ratio)},${Math.round(240-180*ratio)})`:'#65cfe8';
  o.polygons.push({positions,basePositions:base,color,componentId:'coupled-panel',inspectionKey:`shell:${shell.id}`,alpha:.66});
  if(opts.inspection===`shell:${shell.id}`)o.nodeMarkers.push({name:`Shell ${shell.id} · mean nodal Uz ${(mean*1000).toFixed(4)} mm`,position:positions.reduce((s,p)=>s.map((v,i)=>v+p[i]/4),[0,0,0]),componentId:'coupled-panel',inspectionKey:`shell:${shell.id}`});
 }
 if(opts.mode==='path'||opts.mode==='slab')for(const position of [[2,0,3],[4,2,3],[2,4,3],[0,2,3]]){
  const n=c.nodes.find(n=>n.position.every((v,i)=>Math.abs(v-position[i])<1e-9)),f=n?c.interface_actions[String(n.id)]:undefined;if(!f||Math.hypot(...f.slice(0,3))<1e-8)continue;
  const norm=Math.hypot(...f.slice(0,3)),tail=position.map((v,i)=>v-.45*f[i]/norm),member=c.members.find(m=>m.nodes.includes(n!.id));o.arrowIndices.push(o.paths.length);o.paths.push([tail,position]);o.colors.push('#ffe18a');o.componentIds.push(member?.id??'coupled-panel');o.inspectionKeys.push(member?.id??'coupled-panel');o.pathStyles?.push('response');
 }
 if(opts.mode==='loads'){
  const total=c.nodes.reduce((v,n)=>v+n.applied[2],0);o.arrowIndices.push(o.paths.length);o.paths.push([[2,2,4],[2,2,3]]);o.colors.push('#ffe18a');o.componentIds.push('coupled-panel');o.inspectionKeys.push('coupled-panel');o.pathStyles?.push('response');o.nodeMarkers.push({name:`Shell pressure total ${(total/1000).toFixed(1)} kN · no tributary loads`,position:[2,2,4],componentId:'coupled-panel',inspectionKey:'coupled-panel'});
 }
 if(opts.animate&&opts.mode==='deformation')o.animation={basePaths:o.paths.map((p,i)=>{const id=o.componentIds[i],m=c.members.find(m=>m.id===id);return m&&o.pathStyles?.[i]!=='reference'?m.samples.map(s=>s.position):p;}),periodSeconds:4};
 o.label=`Synthetic one-storey shell–frame · ${opts.mode==='deformation'?`actual displacement ×${scale}`:'saved native results'} · no capacity/approval`;
 return o;
}
