import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import RectangularBearingPanel,{finiteFixture} from './RectangularBearingPanel';
import {api} from '@/lib/api';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';
vi.mock('@/lib/api',()=>({api:{get:vi.fn(),post:vi.fn()},formatApiErrorMessage:(e:Error)=>e.message}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('stales results and clears only its diagram on input edits, requiring fresh authorization',async()=>{
 const inputs={model_revision_id:1,benchmark:finiteFixture},computed={factors:{Nc:Math.PI+2,sc:1.2},area_m2:1.44,ultimate_gross_kpa:308.495559215,ultimate_resistance_kn:444.2336,strength_only_allowable_gross_kpa:102.831853,strength_only_allowable_kn:148.077868,applied_pressure_kpa:69.444444};
 vi.mocked(api.get).mockResolvedValue({records:[{id:2,type:'BEARING_RESULT',status:'VERIFIED_SYNTHETIC',result:{inputs,computed}},{id:1,type:'BEARING_PROPOSAL',status:'AWAITING_AUTHORIZATION',result:{inputs,proposal_sha256:'a'.repeat(64)}}]});
 render(<RectangularBearingPanel projectId={802} editor={{baseRevision:{id:1},dirty:false} as EditableModelEditor}/>);
 await screen.findByText(/Ultimate resistance: 308.495559/);const show=screen.getByRole('button',{name:'Show finite footing and illustrative mechanism'});expect(show).toBeEnabled();
 const event=vi.fn();window.addEventListener('geoai:elastic-results',event);fireEvent.change(screen.getByLabelText('Total vertical load kN'),{target:{value:'200'}});
 expect(screen.getByRole('article',{name:'Finite bearing results'})).toHaveTextContent('STALE');expect(show).toBeDisabled();expect(screen.getByLabelText('Authorize finite bearing benchmark')).toBeDisabled();expect(event.mock.calls.at(-1)?.[0].detail).toEqual({clearMode:'finite-bearing-schematic'});
 vi.mocked(api.post).mockImplementation(()=>new Promise(()=>{}));fireEvent.click(screen.getByRole('button',{name:'Preview finite bearing proposal'}));await waitFor(()=>expect(screen.getByLabelText('Total vertical load kN')).toBeDisabled());window.removeEventListener('geoai:elastic-results',event);
});
