// @vitest-environment jsdom
import {cleanup,fireEvent,render,screen,waitFor} from "@testing-library/react";
import {afterEach,expect,it,vi} from "vitest";
import AnalysisOverview from "./AnalysisOverview";
import {api} from "@/lib/api";
import {takeEngineeringResult} from "@/lib/engineering-guidance";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";
vi.mock("@/lib/api",()=>({api:{get:vi.fn()}}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const editor={baseRevision:{id:103},selectedIds:[],dirty:false} as unknown as EditableModelEditor;
it("shows a numerical summary with units and routes to its exact saved diagram",async()=>{
  vi.mocked(api.get).mockResolvedValue({context:{selected:[],missing:[],drawingReferences:[],stale:false,analyses:[{id:421,type:"OPENSEES_PHYSICAL_FRAME",status:"VERIFIED",stale:false,selectionMatch:true,moment_nm:{min:-28809.726,max:24756.664}}]}});
  render(<AnalysisOverview editor={editor} projectId={793}/>);
  expect(await screen.findByText("Numerically verified")).toBeInTheDocument();
  expect(screen.getByText("-28.809726 to 24.756664")).toBeInTheDocument();
  expect(screen.getByText(/not structural design approval/)).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"View saved diagram"}));
  expect(takeEngineeringResult(421,103,true)).toEqual({analysisId:421,revisionId:103,mode:"moment"});
  fireEvent(window,new CustomEvent("geoai:engineering-inputs-saved",{detail:{projectId:788}}));
  expect(api.get).toHaveBeenCalledTimes(1);
  fireEvent(window,new CustomEvent("geoai:engineering-inputs-saved",{detail:{projectId:793}}));
  await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(2));
});
it("keeps blocked and stale contexts from appearing verified",async()=>{
  vi.mocked(api.get).mockResolvedValue({context:{selected:[],missing:[{path:"anchors.A.material"},{path:"contact_stiffness_n_m3.value"}],drawingReferences:[],analyses:[],stale:false}});
  const view=render(<AnalysisOverview editor={editor} projectId={788}/>);
  expect(await screen.findByText("Needs inputs")).toBeInTheDocument();expect(screen.queryByText("Numerically verified")).not.toBeInTheDocument();
  expect(screen.getByRole("button",{name:"Review required inputs"})).toBeEnabled();
  vi.mocked(api.get).mockResolvedValue({context:{selected:[],missing:[],drawingReferences:[],analyses:[],stale:true}});
  view.rerender(<AnalysisOverview editor={{...editor,dirty:true}} projectId={788}/>);
  expect(await screen.findByText("Needs refresh")).toBeInTheDocument();expect(screen.getByRole("button",{name:"Review required inputs"})).toBeDisabled();
});
