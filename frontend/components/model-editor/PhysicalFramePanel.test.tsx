import {act,cleanup,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import PhysicalFramePanel from './PhysicalFramePanel';
import type {EditableModelEditor} from '@/hooks/useEditableModelEditor';

const {get,post}=vi.hoisted(()=>({get:vi.fn(),post:vi.fn()}));
vi.mock('@/lib/api',()=>({api:{get,post},formatApiErrorMessage:(error:Error)=>error.message}));
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();get.mockReset();post.mockReset();});

it('recovers saved input forms after an initial read failure without an edit or solver request',async()=>{
  vi.useFakeTimers();
  const document={components:[],metadata:{}};
  const editor={document,baseRevision:{id:7,document},selectedIds:[],dirty:false} as unknown as EditableModelEditor;
  const record={id:21,model_revision_id:7,status:'AWAITING_AUTHORIZATION',result:{
    inputs:{component_ids:[],sections:[],connections:[],supports:'both_column_bases_fixed',support_source:'Declared',load_n:1000,purpose:'VERIFICATION_ONLY',elements_per_member:2,units:'SI'},
    physical_to_analytical_graph:{component_ids:[],members:[],candidate_joints:[],origin_enu_m:[0,0,0],height_m:3,length_m:6,coordinate_mapping:'East-Up'},
  }};
  get.mockRejectedValueOnce(new TypeError('Read interrupted')).mockResolvedValue({records:[record]});
  render(<PhysicalFramePanel editor={editor} projectId={793}/>);
  await act(async()=>{await Promise.resolve();});
  expect(screen.getByText(/Saved analysis could not load/)).toBeInTheDocument();
  expect(screen.queryByText('Physical frame engineering inputs')).toBeNull();
  await act(async()=>{await vi.advanceTimersByTimeAsync(5000);});
  expect(screen.getByText('Physical frame engineering inputs')).toBeInTheDocument();
  expect(screen.getByLabelText('Assembly load N')).toHaveValue(1000);
  expect(screen.queryByText(/Saved analysis could not load/)).toBeNull();
  expect(post).not.toHaveBeenCalled();
});
