// @vitest-environment jsdom
import {act,cleanup,fireEvent,render,screen,waitFor} from "@testing-library/react";
import {afterEach,expect,it,vi} from "vitest";
import ConnectionInputsPanel from "./ConnectionInputsPanel";
import {api} from "@/lib/api";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";
vi.mock("@/lib/api",()=>({api:{get:vi.fn(),post:vi.fn()},formatApiErrorMessage:(e:Error)=>e.message}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it("keeps an early navigation request until the exact saved record loads, selects the correct anchor, and never edits",async()=>{
  HTMLElement.prototype.scrollIntoView=vi.fn();
  const evidence={category:null,reference:"",method:"",applicability:"",reviewed_by:""};
  const quantity={value:null,evidence};
  const anchors=["A1","A2"].map(id=>({id,material:"",geometry_and_material_evidence:evidence,tension_load_path:"",diameter_m:quantity,effective_embedment_m:quantity,tensile_area_m2:quantity,steel_modulus_pa:quantity,axial_stiffness_n_m:quantity,max_valid_tension_n:quantity,max_valid_opening_m:quantity}));
  const inputs={anchors,saved_geometry_evidence:evidence,mechanical_evidence:evidence,concrete_material:"",contact_model_justification:"",reference_plane_assumption:"",rigid_plate:false,homogeneous_contact:false,fixed_anchor_ground:false,zero_pretension:false,shear_excluded:false,engineer_input_review:false};
  const actual={source_interface_analysis_id:1,source_revision_id:93,source_evidence_sha256:"saved",geometry:{column_base_enu_m:[0,0,0],objects:[]},actual_anchor_local_positions:[],demand:{compression_n:30000,horizontal_shear_east_n:10000,moment_about_negative_north_nm:11000,solver_version:"3.8.0",run_id:"saved"}};
  let release!:()=>void;
  const gate=new Promise<void>(resolve=>{release=resolve;});
  vi.mocked(api.get).mockImplementation(async path=>{
    await gate;
    return path.includes("/audit") ? {actual,template:inputs,assessment:{status:"BLOCKED",missing:[]},anchor_fields:{},contact_fields:{},flags:{}} : {records:[{id:354,model_revision_id:93,status:"BLOCKED",result:{inputs,assessment:{status:"BLOCKED",missing:[]},actual_project_audit:actual,input_sha256:"exact"}}]};
  });
  const editor={baseRevision:{id:93,document:{}},document:{},dirty:false} as unknown as EditableModelEditor;
  render(<ConnectionInputsPanel editor={editor} projectId={788}/>);
  act(()=>window.dispatchEvent(new CustomEvent("geoai:connection-input",{detail:{projectId:788,revisionId:93,recordId:354,path:"anchors.A2.material"}})));
  await act(async()=>release());
  await waitFor(()=>expect(screen.getByLabelText("Anchor material identification")).toHaveFocus());
  expect(screen.getByLabelText("Actual anchor to inspect")).toHaveValue("1");
  expect(screen.getByText("Saved input #354 · anchors.A2.material")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Engineering task"),{target:{value:"review"}});
  expect(screen.getByRole("button",{name:"Run authorized actual contact calculation"})).toBeDisabled();
  expect(api.post).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Engineering task"),{target:{value:"anchor:A2"}});
  act(()=>window.dispatchEvent(new CustomEvent("geoai:connection-input",{detail:{projectId:788,revisionId:93,recordId:353,path:"anchors.A1.material"}})));
  await waitFor(()=>expect(screen.getByText(/This saved input record has been replaced/)).toBeInTheDocument());
  expect(screen.getByLabelText("Actual anchor to inspect")).toHaveValue("1");
});
