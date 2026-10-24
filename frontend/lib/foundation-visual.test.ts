import {describe,it,expect} from 'vitest';
import saved from '../../docs/foundation-system/api-results.json';
import {buildFoundationOverlay,FOUNDATION_MODES,foundationStatus,type FoundationData} from './foundation-visual';
const data=saved.reviewed_result.result.computed as FoundationData;
const input=saved.reviewed_result.result.inputs.inputs;
describe('saved foundation evidence display geometry',()=>{
 it('renders all seven modes with finite ENU geometry without mutating numerical evidence',()=>{
  const before=JSON.stringify(saved);
  for(const [mode] of FOUNDATION_MODES){
   const overlay=buildFoundationOverlay(data,input,mode,{alternative:saved.alternatives.scenarios[3]});
   expect(overlay.visualMode).toBe(mode);expect(overlay.paths.length).toBeGreaterThan(0);
   expect(overlay.paths.flat(2).every(Number.isFinite)).toBe(true);
   expect(overlay.paths.length).toBe(overlay.colors.length);expect(overlay.paths.length).toBe(overlay.inspectionKeys.length);
   expect(overlay.focusComponentIds).toEqual([data.geometry.footing_id,data.geometry.column_id]);
  }
  expect(JSON.stringify(saved)).toBe(before);
 });
 it('uses actual round bar radius, exact supported mat depths, spacing and full straight lengths',()=>{
  const o=buildFoundationOverlay(data,input,'reinforcement');
  expect(o.bars).toHaveLength(16);
  for(const [i,bar] of o.bars.entries()){
   expect(bar.radius).toBe(.01);expect(bar.start[2]).toBeCloseTo(i<8?-.365:-.345,12);
   expect(Math.hypot(...bar.end.map((v,j)=>v-bar.start[j]))).toBeCloseTo(1.05,12);
  }
  expect(o.bars[1].start[1]-o.bars[0].start[1]).toBeCloseTo(data.rc.layers[0].spacing_mm/1000,12);
  expect(o.nodeMarkers.some(m=>m.name.includes('971 mm required')&&m.name.includes('375 mm available'))).toBe(true);
  expect(buildFoundationOverlay(data,input,'reinforcement',{direction:'NS'}).bars).toHaveLength(8);
 });
 it('keeps required development reach separate from physical steel and points to exact saved failure',()=>{
  const o=buildFoundationOverlay(data,input,'reinforcement',{direction:'EW'}),E=data.geometry.center_east_north_m[0];
  expect(Math.max(...o.bars.flatMap(b=>[b.start[0],b.end[0]]))).toBeCloseTo(E+.525,12);
  expect(Math.max(...o.paths.flat().map(p=>p[0]))).toBeGreaterThan(E+1.12);
  expect(data.rc.layers[0].development.status).toBe('EXCEEDS_IMPLEMENTED_CHECK');
 });
 it('shows one pressure colour for the calculated uniform result and labels displacement exaggeration',()=>{
  const o=buildFoundationOverlay(data,input,'soil');
  expect(o.polygons).toHaveLength(1);expect(data.contact.pmin_pa).toBe(data.contact.pmax_pa);
  expect(o.nodeMarkers.map(m=>m.name).join(' ')).toContain('5.563 mm');
  expect(o.nodeMarkers.map(m=>m.name).join(' ')).toContain('×20');
 });
 it('uses saved one-way cuts and punching perimeter, with no invented resistance for disabled checks',()=>{
  const o=buildFoundationOverlay(data,input,'one-way');
  expect(o.nodeMarkers[0].name).toContain('15.300 kN');expect(o.nodeMarkers[1].name).toContain('18.900 kN');
  expect(foundationStatus(data.rc.layers[0].one_way)).toBe('Not supported');
  const selected=buildFoundationOverlay(data,input,'one-way',{direction:'NS'});
  expect(selected.nodeMarkers).toHaveLength(1);expect(selected.nodeMarkers[0].inspectionKey).toBe('one-way-NS');
  const punching=buildFoundationOverlay(data,input,'punching');
  expect(Math.abs(punching.paths[0][1][0]-punching.paths[0][0][0])*4000).toBeCloseTo(data.rc.punching.perimeter_mm,8);
 });
 it('shows footing self-weight as well as column action so gross service reactions balance',()=>{
  expect(data.actions.service_column_kn+data.actions.service_footing_weight_kn).toBeCloseTo(data.actions.service_gross_soil_kn,12);
  expect(buildFoundationOverlay(data,input,'loads').nodeMarkers.map(m=>m.name).join(' ')).toContain('Footing weight 16.20 kN');
 });
 it('ghosts only the selected validated alternative, never changing original dimensions or bars',()=>{
  const a=saved.alternatives.scenarios[5],o=buildFoundationOverlay(data,input,'alternatives',{alternative:a});
  expect(o.bars).toHaveLength(20);expect(o.nodeMarkers[0].name).toContain('UNSAVED');
  expect(data.geometry.footing_size_m).toEqual([1.2,1.2,.45]);
  const unsupported=buildFoundationOverlay(data,input,'alternatives',{alternative:{width_m:1.2,thickness_m:.1,status:'OUTSIDE_DOMAIN'}});
  expect(unsupported.bars).toHaveLength(0);expect(unsupported.polygons).toHaveLength(0);
 });
 it('maps only the four honest display statuses',()=>{
  expect(foundationStatus({status:'WITHIN_IMPLEMENTED_CHECK'})).toBe('Within implemented check');
  expect(foundationStatus({status:'EXCEEDS_IMPLEMENTED_CHECK'})).toBe('Exceeds implemented check');
  expect(foundationStatus({status:'DISABLED'})).toBe('Not supported');
  expect(foundationStatus()).toBe('Not verified');
 });
});
