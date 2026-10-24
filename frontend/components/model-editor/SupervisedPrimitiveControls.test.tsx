import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import Controls from './SupervisedPrimitiveControls';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
import type {WorkspaceCommand} from '@/lib/workspace-assistant';
import fixture from '@/lib/__fixtures__/supervised-column.json';
import {api} from '@/lib/api';
vi.mock('@/lib/api',()=>({api:{post:vi.fn()}}));
afterEach(()=>{cleanup();vi.resetAllMocks();});
const command=()=>({...structuredClone(fixture),expiresAt:Date.now()+120000}) as unknown as WorkspaceCommand;
function editor(c:WorkspaceCommand){return {platformPreview:{proposal:c},document:{components:[]},baseRevision:{id:1},dirty:false,setPlatformPreview:vi.fn(),applyPrimitivePreview:vi.fn(),save:vi.fn()} as unknown as EditableModelEditor;}
function ready(c:WorkspaceCommand){act(()=>window.dispatchEvent(new CustomEvent('geoai:workspace-outcome',{detail:{actionId:c.actionId,ok:true}})));}
it('requires renderer confirmation before Apply and cancels without mutation',()=>{
 const c=command(),e=editor(c);render(<Controls editor={e}/>);
 expect(screen.getByRole('button',{name:'Apply column'})).toBeDisabled();
 fireEvent.click(screen.getByRole('button',{name:'Cancel proposal'}));expect(e.setPlatformPreview).toHaveBeenCalledWith(null);
 expect(screen.queryByRole('button',{name:'Apply column'})).toBeNull();expect(screen.getByRole('region',{name:'Supervised column review'})).toHaveAttribute('data-proposal-state','canceled');
 expect(api.post).not.toHaveBeenCalled();expect(e.applyPrimitivePreview).not.toHaveBeenCalled();expect(e.save).not.toHaveBeenCalled();
});
it('revalidates on explicit Apply and never saves automatically',async()=>{
 const c=command(),e=editor(c);vi.mocked(api.post).mockResolvedValue(c);const {rerender}=render(<Controls editor={e}/>);ready(c);
 fireEvent.click(screen.getByRole('button',{name:'Apply column'}));await waitFor(()=>expect(e.applyPrimitivePreview).toHaveBeenCalledExactlyOnceWith(c.actionId));expect(e.save).not.toHaveBeenCalled();
 rerender(<Controls editor={{...e,platformPreview:null,document:{components:[c.candidate]},dirty:true} as unknown as EditableModelEditor}/>);
 await screen.findByText('Column applied to the editor draft · not saved.');fireEvent.click(screen.getByRole('button',{name:'Save model revision'}));await waitFor(()=>expect(e.save).toHaveBeenCalledOnce());
 rerender(<Controls editor={{...e,platformPreview:null,document:{components:[c.candidate]},baseRevision:{id:2,document:{components:[]}},dirty:false} as unknown as EditableModelEditor}/>);
 expect(screen.queryByRole('button',{name:/^Saved$/})).toBeNull();
 rerender(<Controls editor={{...e,platformPreview:null,document:{components:[c.candidate]},baseRevision:{id:2,document:{components:[c.candidate]}},dirty:false} as unknown as EditableModelEditor}/>);
 await screen.findByText('Saved column in revision 2.');expect(screen.getByRole('button',{name:/^Saved$/})).toBeDisabled();
 expect(screen.queryByRole('button',{name:'Apply column'})).toBeNull();expect(screen.queryByRole('button',{name:'Cancel proposal'})).toBeNull();
});
it('expires a pending approval and removes its Apply control without a transaction',async()=>{
 const c={...command(),expiresAt:Date.now()+40},e=editor(c);render(<Controls editor={e}/>);ready(c);
 await waitFor(()=>expect(screen.getByRole('region',{name:'Supervised column review'})).toHaveAttribute('data-proposal-state','rejected_stale'));
 expect(e.setPlatformPreview).toHaveBeenCalledWith(null);expect(screen.queryByRole('button',{name:'Apply column'})).toBeNull();expect(e.applyPrimitivePreview).not.toHaveBeenCalled();expect(e.save).not.toHaveBeenCalled();
});
it('rejects remote freshness failure and retains the preview',async()=>{
 const c=command(),e=editor(c);vi.mocked(api.post).mockRejectedValue(Error('Saved revision changed'));render(<Controls editor={e}/>);ready(c);
 fireEvent.click(screen.getByRole('button',{name:'Apply column'}));await screen.findByRole('alert');expect(e.applyPrimitivePreview).not.toHaveBeenCalled();expect(e.save).not.toHaveBeenCalled();
});
it('does not apply if Cancel wins during async validation',async()=>{
 const c=command(),e=editor(c);let resolve!:(c:WorkspaceCommand)=>void;vi.mocked(api.post).mockImplementation(()=>new Promise(r=>{resolve=r;}));
 const {rerender}=render(<Controls editor={e}/>);ready(c);fireEvent.click(screen.getByRole('button',{name:'Apply column'}));
 fireEvent.click(screen.getByRole('button',{name:'Cancel proposal'}));rerender(<Controls editor={{...e,platformPreview:null}}/>);await act(async()=>resolve(c));expect(e.applyPrimitivePreview).not.toHaveBeenCalled();expect(e.save).not.toHaveBeenCalled();
});
