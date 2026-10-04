import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import EngineeringDockPanel from "./EngineeringDockPanel";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { Project } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";

const get=vi.fn(),post=vi.fn();
vi.mock("@/lib/api",()=>({api:{get:(...args:unknown[])=>get(...args),post:(...args:unknown[])=>post(...args)},formatApiErrorMessage:(error:Error)=>error.message}));
const project={id:5,alignment_geojson:{type:"LineString",coordinates:[[0,0],[.01,0]]}} as Project;
const editor={document:{components:[{id:"deck",name:"Deck",category:"deck",visible:true,geometry:{kind:"box",size:[10,6,2]},transform:{position:[0,0,5],rotation_deg:[0,0,0],scale:[1,1,1]},material:{color:"#fff",roughness:1,metalness:0}}]},baseRevision:{id:12,revision_number:2},dirty:false,select:vi.fn(),validateDraft:vi.fn().mockResolvedValue({})} as unknown as EditableModelEditor;
beforeEach(()=>{get.mockReset();post.mockReset();get.mockImplementation((url:string)=>Promise.resolve(url.endsWith("evidence")?{readiness:"VISUAL_REFERENCE"}:[]));useProjectStore.setState({undergroundView:false});});
describe("engineering dock",()=>{
  it("shows unsupported quantities as unavailable and real readiness",async()=>{
    render(<EngineeringDockPanel project={project} editor={editor}/>);
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("tab",{name:"VALIDATION"}));
    await screen.findByText("Readiness: VISUAL_REFERENCE");
    expect(screen.getByText(/No engineering clearance/)).toBeVisible();
  });
  it("sections rendered geometry, applies view-only clipping and restores clipping on unmount",()=>{
    const events:unknown[]=[];const listener=(event:Event)=>events.push((event as CustomEvent).detail);window.addEventListener("geoai:analysis-clip",listener);
    const view=render(<EngineeringDockPanel project={project} editor={editor} initialTab="SECTION"/>);
    expect(screen.getByRole("img",{name:"Design cross section"}).querySelectorAll("polyline").length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Analysis clipping"),{target:{value:"horizontal"}});
    expect(events.at(-1)).toEqual({mode:"horizontal",value:0,size:50});
    fireEvent.click(screen.getByLabelText("Underground view"));expect(useProjectStore.getState().undergroundView).toBe(true);
    view.unmount();expect(events.at(-1)).toEqual({mode:"off",value:0,size:50});window.removeEventListener("geoai:analysis-clip",listener);
  });
  it("keeps failed terrain profiles explicit instead of adding fabricated stations",async()=>{
    post.mockRejectedValue(new Error("Authoritative terrain required"));
    render(<EngineeringDockPanel project={project} editor={editor} initialTab="PROFILE"/>);
    fireEvent.click(screen.getByRole("button",{name:"Create terrain profile"}));
    await waitFor(()=>expect(screen.getByRole("alert")).toHaveTextContent("Authoritative terrain required"));
    expect(screen.queryByRole("img",{name:"Alignment terrain profile"})).toBeNull();
    expect(post).toHaveBeenCalledWith("/api/projects/5/engineering/analyses/profile",{model_revision_id:12,station_interval_m:20});
  });
});
