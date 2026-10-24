import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {describe,it,expect,vi,beforeEach,afterEach} from 'vitest';
import UnequalFrameComparisonPanel from './UnequalFrameComparisonPanel';
const get=vi.hoisted(()=>vi.fn());
vi.mock('@/lib/api',()=>({api:{get},formatApiErrorMessage:(e:Error)=>e.message}));
const baseline={project_id:791,analysis_id:384,revision_id:100,column_heights_m:[3.2,3.2]};
const comparison={status:'COMPARABLE_EXPLICIT_SYNTHETIC_CASES',explanation:'Original unequal geometry compared with declared equal case',unequal:{...baseline,analysis_id:400,revision_id:101},equal:baseline,heads:[],reactions:[],external_horizontal_load_moment_nm:{unequal:64600,equal:64000}};
describe('saved unequal comparison applicability',()=>{
 beforeEach(()=>{get.mockReset();});
 afterEach(()=>{cleanup();});
 it('removes an old comparison when active solver result changes and blocks unmatched baseline',async()=>{
  get.mockImplementation((url:string)=>Promise.resolve(url.includes('comparison-baselines')?{baselines:url.includes('analysis_id=400')?[baseline]:[]}:comparison));
  const view=render(<UnequalFrameComparisonPanel projectId={792} analysisId={400} valid/>);
  await waitFor(()=>expect(screen.getByRole('option',{name:/Project 791/})).toBeTruthy());fireEvent.change(screen.getByLabelText('Equal frame baseline'),{target:{value:'384'}});fireEvent.click(screen.getByRole('button',{name:'Compare saved equal-height case'}));
  await waitFor(()=>expect(screen.getByLabelText('Saved geometry response comparison')).toBeTruthy());
  view.rerender(<UnequalFrameComparisonPanel projectId={792} analysisId={401} valid/>);
  expect(screen.queryByLabelText('Saved geometry response comparison')).toBeNull();await waitFor(()=>expect((screen.getByRole('button',{name:'Compare saved equal-height case'}) as HTMLButtonElement).disabled).toBe(true));
 });
 it('hides verified comparison values when the engineering result becomes stale',async()=>{
  get.mockImplementation((url:string)=>Promise.resolve(url.includes('comparison-baselines')?{baselines:[baseline]}:comparison));
  const view=render(<UnequalFrameComparisonPanel projectId={792} analysisId={400} valid/>);await waitFor(()=>expect(screen.getByRole('option',{name:/Project 791/})).toBeTruthy());fireEvent.change(screen.getByLabelText('Equal frame baseline'),{target:{value:'384'}});fireEvent.click(screen.getByRole('button',{name:'Compare saved equal-height case'}));await waitFor(()=>expect(screen.getByLabelText('Saved geometry response comparison')).toBeTruthy());
  view.rerender(<UnequalFrameComparisonPanel projectId={792} analysisId={400} valid={false}/>);expect(screen.queryByLabelText('Saved geometry response comparison')).toBeNull();expect(screen.getByText('STALE — comparison blocked')).toBeTruthy();
 });
});
