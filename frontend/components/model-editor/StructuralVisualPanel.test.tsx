import {render,screen,fireEvent,cleanup,waitFor,act} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import StructuralVisualPanel from './StructuralVisualPanel';
import saved from '../../../docs/structural-visual/project-793.json';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
const get=vi.hoisted(()=>vi.fn());
vi.mock('@/lib/api',()=>({api:{get},formatApiErrorMessage:(e:Error)=>e.message}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
function editor(){return {baseRevision:{id:103},document:{components:saved.components,metadata:{}},selectedIds:[],selectMany:vi.fn(),dirty:false} as unknown as EditableModelEditor;}
function setup(){get.mockImplementation((url:string)=>Promise.resolve({records:url.includes('/assembly')?saved.rows:[]}));}
it('uses read-only saved evidence and keeps mode, case and scale changes out of requests',async()=>{
 setup();const ed=editor(),select=ed.selectMany;render(<StructuralVisualPanel editor={ed} projectId={793}/>);
 await waitFor(()=>expect(screen.getByRole('button',{name:'Deformed versus original'})).toBeEnabled());expect(get).toHaveBeenCalledTimes(2);
 fireEvent.click(screen.getByRole('button',{name:'Deformed versus original'}));fireEvent.change(screen.getByLabelText('Displacement magnification'),{target:{value:'200'}});fireEvent.change(screen.getByLabelText('Structural saved load case'),{target:{value:'Gravity'}});
 expect(screen.getByText('Visual displacement magnification ×200')).toBeVisible();expect(get).toHaveBeenCalledTimes(2);
 act(()=>window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key:saved.components[0].id}})));expect(select).toHaveBeenCalledWith([saved.components[0].id]);
});
it('hides saved numbers and clears display during an unsaved geometry draft',async()=>{
 setup();const ed=editor();ed.selectedIds=[saved.rows[0].result.elements![0].component_id];const {rerender}=render(<StructuralVisualPanel editor={ed} projectId={793}/>);
 await screen.findByText(/Available saved planar samples/);const events:unknown[]=[];const receive=(e:Event)=>events.push((e as CustomEvent).detail);window.addEventListener('geoai:elastic-results',receive);
 rerender(<StructuralVisualPanel editor={{...ed,dirty:true}} projectId={793}/>);expect(screen.getByRole('button',{name:'Beam and column forces'})).toBeDisabled();expect(screen.getByText('Saved evidence hidden while draft or preview is active.')).toBeVisible();expect(events.at(-1)).toEqual({clearMode:'structural-visual'});window.removeEventListener('geoai:elastic-results',receive);
});
it('restores the full structure without calling the model commit API',async()=>{
 setup();const ed=editor(),commit=vi.fn();ed.commit=commit;render(<StructuralVisualPanel editor={ed} projectId={793}/>);await waitFor(()=>expect(screen.getByRole('button',{name:'Frame view'})).toBeEnabled());
 fireEvent.click(screen.getByRole('button',{name:'Restore full structure'}));expect(screen.getByLabelText('Isolate analyzed structural system')).not.toBeChecked();expect(commit).not.toHaveBeenCalled();
});
