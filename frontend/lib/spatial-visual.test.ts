import {describe,it,expect} from 'vitest';
import fixtures from '../../docs/spatial-frame/demo.json';
import {spatialOverlay,type SpatialCase,type SpatialOptions} from './spatial-visual';
import {STRUCTURAL_MODES} from './structural-visual';
const c=fixtures[1].analysis.result.cases[2] as SpatialCase;
const opts:SpatialOptions={mode:'path',floor:0,force:'Mz',scale:30,original:true,fit:true,isolate:true};
describe('saved true spatial evidence projection',()=>{
 it('projects all seven modes without changing saved results',()=>{const original=JSON.stringify(c);for(const [mode] of STRUCTURAL_MODES){const o=spatialOverlay(c,{...opts,mode});expect(o.paths.length).toBeGreaterThan(0);expect(o.paths.every(p=>p.every(p=>p.length===3&&p.every(Number.isFinite)))).toBe(true);expect(o.paths.length).toBe(o.inspectionKeys.length);}expect(JSON.stringify(c)).toBe(original);});
 it('preserves actual E/N/U deformation and labels display magnification',()=>{const o=spatialOverlay(c,{...opts,mode:'deformation',scale:100});const s=c.members[0].samples[8];expect(o.paths[1][8]).toEqual(s.position.map((v,i)=>v+100*s.displacement[i]));expect(o.label).toContain('×100');expect(o.pathStyles?.[0]).toBe('reference');});
 it('filters and frames the chosen floor without rewriting geometry',()=>{const o=spatialOverlay(c,{...opts,floor:2});expect(o.focusComponentIds?.length).toBe(15);expect(o.paths.length).toBe(13+4);expect(o.fitPoints.every(p=>p[2]>=3)).toBe(true);});
 it('uses real six-component local forces with distinct diagram styling',()=>{for(const force of ['My','Mz','Vy','Vz','N','T'] as const){const o=spatialOverlay(c,{...opts,mode:'forces',force});expect(o.label).toContain(force);expect(o.label).toContain('±0.80 m');expect(o.pathStyles).toContain(['N','T'].includes(force)?'diagram-dashed':'diagram');expect(o.nodeMarkers[0].name).toContain(force);}});
 it('displays slab allocation without fabricated deformation or plate contours',()=>{const o=spatialOverlay(c,{...opts,mode:'slab'});expect(o.polygons.length).toBe(4);expect(o.nodeMarkers.some(m=>m.name.includes('one-way allocation only'))).toBe(true);const d=spatialOverlay(c,{...opts,mode:'deformation'});expect(d.componentIds.some(id=>id.startsWith('slab-'))).toBe(false);});
 it('retains unsupported foundation and connection warnings',()=>{expect(spatialOverlay(c,{...opts,mode:'foundation'}).nodeMarkers.some(m=>m.name.includes('NOT VERIFIED'))).toBe(true);expect(spatialOverlay(c,{...opts,mode:'warnings'}).nodeMarkers.every(m=>m.name.includes('NOT VERIFIED'))).toBe(true);});
});
