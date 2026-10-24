import {describe,it,expect} from 'vitest';
import p793 from '../../docs/structural-visual/project-793.json';
import p794 from '../../docs/structural-visual/project-794.json';
import {STRUCTURAL_MODES,buildStructuralOverlay,savedStructuralEvidence,structuralCases,selectedStructuralFrames,type StructuralRow} from './structural-visual';
// Raw immutable API fixtures include solver-internal inputs in subcases; the
// viewer deliberately uses the parent physical inputs when selecting a case.
const rows793=p793.rows as unknown as StructuralRow[],rows794=p794.rows as unknown as StructuralRow[];
const evidence=savedStructuralEvidence(rows793,[],103),slab=savedStructuralEvidence([],rows794,105);
const options={caseName:structuralCases(evidence)[0],scale:50,force:'moment' as const,original:true,isolate:true};
describe('saved structural evidence projection',()=>{
 it('rejects stale or other revision records and does not manufacture cases',()=>{
  expect(savedStructuralEvidence(rows793,[],104).frames).toEqual([]);
  expect(savedStructuralEvidence(rows793.map(r=>({...r,status:'STALE'})),[],103).frames).toEqual([]);
  expect(selectedStructuralFrames(evidence,'unknown')).toEqual([]);
  expect(structuralCases(evidence)).toEqual(['Linear sum','Horizontal','Gravity','Self weight']);
 });
 it('projects actual displacement using East/Up and preserved North at an explicit magnification',()=>{
  const frame=evidence.frames[0],g=frame.physical_to_analytical_graph!,sample=frame.elements![0].samples[3],o=buildStructuralOverlay(evidence,p793.components,'deformation',options);
  expect(o.paths[1][3]).toEqual([g.origin_enu_m[0]+sample.position_m[0]+50*sample.displacement_m[0],g.origin_enu_m[1],g.origin_enu_m[2]+sample.position_m[1]+50*sample.displacement_m[1]]);
  const doubled=buildStructuralOverlay(evidence,p793.components,'deformation',{...options,scale:100,original:false});
  expect(doubled.paths[0][3][0]-g.origin_enu_m[0]-sample.position_m[0]).toBeCloseTo(100*sample.displacement_m[0],12);
  expect(o.label).toContain('visual magnification');
 });
 it('retains signed saved member-force peaks and declared rigid arms only',()=>{
  const f=evidence.frames[0],o=buildStructuralOverlay(evidence,p793.components,'forces',options);
  const id=f.elements![0].component_id,samples=f.elements!.filter(e=>e.component_id===id).flatMap(e=>e.samples),peak=samples.reduce((a,b)=>Math.abs(a.moment_nm)>Math.abs(b.moment_nm)?a:b);
  expect(o.nodeMarkers.find(m=>m.componentId===id)?.name).toContain((peak.moment_nm/1000).toFixed(3));
  expect(o.nodeMarkers).toHaveLength(3);
  const path=buildStructuralOverlay(evidence,p793.components,'path',options);
  expect(path.nodeMarkers.filter(m=>m.name.includes('Declared rigid arm'))).toHaveLength(2);
  expect(path.arrowIndices).toEqual([]);
 });
 it('uses both actual slab support frames, saved tributary polygons and conserved force',()=>{
  expect(slab.frames).toHaveLength(2);const o=buildStructuralOverlay(slab,p794.components,'slab',{...options,caseName:structuralCases(slab)[0]});
  expect(o.polygons.map(p=>p.positions)).toEqual(slab.transfer!.strips.map(s=>s.polygon_enu_m));
  expect(slab.transfer!.strips.reduce((n,s)=>n+s.transferred_kn!,0)).toBeCloseTo(slab.transfer!.applied_kn!,8);
  expect(new Set(slab.frames.flatMap(f=>f.physical_to_analytical_graph!.component_ids)).size).toBe(6);
  expect(new Set(slab.frames.map(f=>f.physical_to_analytical_graph!.origin_enu_m[1])).size).toBe(2);
 });
 it('labels actual loads and reactions without assigning loads to excluded context',()=>{
  const o=buildStructuralOverlay(evidence,p793.components,'loads',options),f=evidence.frames[0];
  for(const r of f.reactions!)expect(o.nodeMarkers.some(m=>m.name.includes((r.fy_n/1000).toFixed(3))&&m.name.includes((r.moment_nm/1000).toFixed(3)))).toBe(true);
  expect(o.componentIds.every(id=>f.physical_to_analytical_graph!.component_ids.includes(id))).toBe(true);
  expect(o.arrowIndices.length).toBeGreaterThan(0);
 });
 it('never fabricates response, connections or soil fields for missing evidence',()=>{
  const e={frames:[],recordIds:[]};for(const mode of ['forces','deformation','slab','foundation'] as const){const o=buildStructuralOverlay(e,p793.components,mode,options);expect(o.paths).toEqual([]);expect(o.polygons).toEqual([]);}
  expect(buildStructuralOverlay(e,p793.components,'warnings',options).nodeMarkers.length).toBeGreaterThan(0);
 });
 it('all modes preserve source evidence and have finite display geometry',()=>{
  const before=JSON.stringify([evidence,slab,p793.components,p794.components]);
  for(const e of [evidence,slab])for(const [mode] of STRUCTURAL_MODES){const o=buildStructuralOverlay(e,p793.components,mode,{...options,caseName:structuralCases(e)[0]});expect(o.paths.flat(2).every(Number.isFinite)).toBe(true);}
  expect(JSON.stringify([evidence,slab,p793.components,p794.components])).toBe(before);
 });
});
