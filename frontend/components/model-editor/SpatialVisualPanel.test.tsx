import {render,screen,fireEvent,cleanup,waitFor,act} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import SpatialVisualPanel from './SpatialVisualPanel';
import demo from '../../../docs/spatial-frame/demo.json';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
const {get,post}=vi.hoisted(()=>({get:vi.fn(),post:vi.fn()}));
vi.mock('@/lib/api',()=>({api:{get,post},formatApiErrorMessage:(e:Error)=>e.message}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const fixture=demo[1],member=fixture.fixture.inputs.members[0];
function editor(){return {baseRevision:{id:fixture.fixture.model_revision_id},document:{components:fixture.fixture.inputs.members.map(m=>({id:m.id,name:m.id,category:m.kind,transform:{position:[0,0,0]}})),metadata:{spatial_frame_review:{input:fixture.fixture.inputs}}},selectedIds:[],selectMany:vi.fn(),dirty:false} as unknown as EditableModelEditor;}
it('keeps case, floor, magnification and component selection read-only',async()=>{
 get.mockResolvedValue({records:[fixture.analysis]});const ed=editor();render(<SpatialVisualPanel editor={ed} projectId={fixture.fixture.project_id}/>);await screen.findByLabelText('Spatial load case');
 fireEvent.click(screen.getByRole('button',{name:'Deformed versus original'}));fireEvent.change(screen.getByLabelText('Spatial displacement magnification'),{target:{value:'150'}});fireEvent.change(screen.getByLabelText('Spatial floor'),{target:{value:'2'}});fireEvent.change(screen.getByLabelText('Spatial load case'),{target:{value:fixture.analysis.result.cases[2].case.name}});
 act(()=>window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key:member.id}})));expect(ed.selectMany).toHaveBeenCalledWith([member.id]);expect(get).toHaveBeenCalledTimes(2);expect(post).not.toHaveBeenCalled();
});
it('hides stale numerical values and overlays during a draft',async()=>{
 get.mockResolvedValue({records:[fixture.analysis]});const ed=editor();ed.selectedIds=[member.id];const {rerender}=render(<SpatialVisualPanel editor={ed} projectId={fixture.fixture.project_id}/>);await screen.findByRole('article',{name:'Selected spatial evidence'});
 const events:unknown[]=[];const receive=(e:Event)=>events.push((e as CustomEvent).detail);window.addEventListener('geoai:elastic-results',receive);rerender(<SpatialVisualPanel editor={{...ed,dirty:true}} projectId={fixture.fixture.project_id}/>);
 expect(screen.queryByRole('article',{name:'Selected spatial evidence'})).toBeNull();expect(screen.getByRole('button',{name:'Beam and column forces'})).toBeDisabled();expect(events.at(-1)).toEqual({clearMode:'structural-visual'});expect(post).not.toHaveBeenCalled();window.removeEventListener('geoai:elastic-results',receive);
});
it('rejects stale saved evidence rather than inferring a response',async()=>{
 get.mockResolvedValue({records:[{...fixture.analysis,status:'STALE'}]});render(<SpatialVisualPanel editor={editor()} projectId={fixture.fixture.project_id}/>);await waitFor(()=>expect(screen.getByRole('region',{name:'Spatial structural engineering'})).toHaveAttribute('data-blocked','false'));expect(screen.queryByLabelText('Spatial load case')).toBeNull();expect(screen.getByText(/No current verified spatial result/)).toBeVisible();expect(post).not.toHaveBeenCalled();
});


