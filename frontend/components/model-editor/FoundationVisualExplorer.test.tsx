import {render,screen,fireEvent,cleanup,act} from '@testing-library/react';
import {afterEach,describe,it,expect,vi} from 'vitest';
import saved from '../../../docs/foundation-system/api-results.json';
import FoundationVisualExplorer from './FoundationVisualExplorer';
import type {FoundationData,FoundationOverlay} from '@/lib/foundation-visual';
afterEach(cleanup);
const props={data:saved.reviewed_result.result.computed as FoundationData,cover:75,stale:false,alternatives:[],onCompare:vi.fn(),onReviewAlternative:vi.fn(),busy:false};
describe('foundation visual-first controls',()=>{
 it('changes modes and inspects labels without requests or data changes',()=>{
  const before=JSON.stringify(saved),events:FoundationOverlay[]=[];
  const receive=(e:Event)=>events.push((e as CustomEvent).detail);window.addEventListener('geoai:elastic-results',receive);
  const fetchSpy=vi.spyOn(globalThis,'fetch');render(<FoundationVisualExplorer {...props}/>);
  expect(screen.getByLabelText('Foundation visual analysis')).toHaveAttribute('data-mode','reinforcement');
  fireEvent.click(screen.getByRole('button',{name:'Loads and reactions'}));expect(events.at(-1)?.visualMode).toBe('loads');
  fireEvent.click(screen.getByRole('button',{name:'Punching shear'}));expect(events.at(-1)?.visualMode).toBe('punching');
  act(()=>{window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key:'drawing-cad:some-structural-component'}}));});
  expect(screen.getByLabelText('Foundation visual analysis')).toHaveAttribute('data-mode','punching');
  act(()=>{window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key:'anchorage-NS'}}));});
  expect(events.at(-1)?.bars).toHaveLength(8);
  expect(screen.getByLabelText('Foundation visual analysis')).toHaveAttribute('data-mode','reinforcement');
  expect(fetchSpy).not.toHaveBeenCalled();expect(JSON.stringify(saved)).toBe(before);
  fetchSpy.mockRestore();window.removeEventListener('geoai:elastic-results',receive);
 });
 it('clears overlays and disables all modes when results become stale',()=>{
  const events:unknown[]=[];const receive=(e:Event)=>events.push((e as CustomEvent).detail);window.addEventListener('geoai:elastic-results',receive);
  const {rerender}=render(<FoundationVisualExplorer {...props}/>);rerender(<FoundationVisualExplorer {...props} stale/>);
  expect(screen.getByRole('button',{name:'Soil pressure and settlement'})).toBeDisabled();
  expect(events.at(-1)).toEqual({clearMode:'foundation-integrated'});window.removeEventListener('geoai:elastic-results',receive);
 });
 it('changes concrete opacity only as temporary display state and restores it on unmount',()=>{
  const events:unknown[]=[];const receive=(e:Event)=>events.push((e as CustomEvent).detail);window.addEventListener('geoai:foundation-appearance',receive);
  const {unmount}=render(<FoundationVisualExplorer {...props}/>);expect(events.at(-1)).toEqual({[props.data.geometry.footing_id]:.2});
  fireEvent.click(screen.getByLabelText('Transparent foundation concrete'));expect(events.at(-1)).toEqual({[props.data.geometry.footing_id]:1});
  unmount();expect(events.at(-1)).toEqual({});window.removeEventListener('geoai:foundation-appearance',receive);
 });
});
