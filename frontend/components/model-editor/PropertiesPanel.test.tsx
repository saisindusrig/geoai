import {render,screen,cleanup} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {afterEach,describe,expect,it,vi} from "vitest";
import {PropertiesPanel} from "./ProfessionalModelEditor";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";
import type {EditableModelComponent} from "@/lib/types";
afterEach(cleanup);
const component:EditableModelComponent={id:"beam",parent_id:null,name:"Test beam",category:"beam",visible:true,locked:false,geometry:{kind:"box",size:[3,.2,.3]},transform:{position:[0,0,1],rotation_deg:[0,0,0],scale:[1,1,1]},material:{name:"Concept steel",color:"#94A3B8",roughness:.5,metalness:0}};
describe("staged inspector edits",()=>{
  it("previews without committing, then applies all fields once",async()=>{
    const update=vi.fn();const preview=vi.fn();window.addEventListener("geoai:component-preview",preview);
    const editor={selected:component,document:null,updateComponent:update} as unknown as EditableModelEditor;
    const user=userEvent.setup();render(<PropertiesPanel editor={editor}/>);
    await user.clear(screen.getByLabelText("Dimensions · metres X"));await user.type(screen.getByLabelText("Dimensions · metres X"),"4");await user.tab();
    await user.clear(screen.getByLabelText("Position · metres East"));await user.type(screen.getByLabelText("Position · metres East"),"2");await user.tab();
    await user.click(screen.getByRole("button",{name:"Preview"}));expect(update).not.toHaveBeenCalled();expect(preview.mock.lastCall?.[0].detail.geometry.size[0]).toBe(4);
    await user.click(screen.getByRole("button",{name:"Apply"}));expect(update).toHaveBeenCalledTimes(1);expect(Object.keys(update.mock.calls[0][1])).toEqual(["transform","geometry"]);
    window.removeEventListener("geoai:component-preview",preview);
  });
  it("cancel discards pending edits without creating an undo operation",async()=>{
    const update=vi.fn();const user=userEvent.setup();render(<PropertiesPanel editor={{selected:component,document:null,updateComponent:update} as unknown as EditableModelEditor}/>);
    await user.clear(screen.getByLabelText("Dimensions · metres X"));await user.type(screen.getByLabelText("Dimensions · metres X"),"4");await user.tab();
    await user.click(screen.getByRole("button",{name:"Cancel"}));expect(update).not.toHaveBeenCalled();expect(screen.getByLabelText("Dimensions · metres X")).toHaveValue("3");expect(screen.getByRole("button",{name:"Apply"})).toBeDisabled();
  });
  it("blocks a partial Apply with invalid fields and Cancel resets those fields",async()=>{
    const update=vi.fn();const user=userEvent.setup();render(<PropertiesPanel editor={{selected:component,document:null,updateComponent:update} as unknown as EditableModelEditor}/>);
    await user.clear(screen.getByLabelText("Dimensions · metres X"));await user.type(screen.getByLabelText("Dimensions · metres X"),"4");await user.tab();
    await user.clear(screen.getByLabelText("Dimensions · metres Y"));await user.type(screen.getByLabelText("Dimensions · metres Y"),"-1");await user.tab();
    await user.click(screen.getByRole("button",{name:"Apply"}));expect(update).not.toHaveBeenCalled();expect(screen.getByText(/Correct the invalid fields/)).toBeVisible();
    await user.click(screen.getByRole("button",{name:"Cancel"}));expect(screen.getByLabelText("Dimensions · metres Y")).toHaveValue("0.2");expect(screen.getByRole("button",{name:"Apply"})).toBeDisabled();
  });
});
it("assistant Cancel removes only an active matching visual preview without applying", async()=>{
 const update=vi.fn(),preview=vi.fn();const editor={selected:component,document:null,updateComponent:update,baseRevision:{id:8},dirty:false} as unknown as EditableModelEditor;
 window.addEventListener('geoai:component-preview',preview);
 render(<PropertiesPanel editor={editor}/>);
 const {act}=await import('@testing-library/react');
 act(()=>window.dispatchEvent(new CustomEvent('geoai:assistant-preview-ready',{detail:{componentId:'beam',revisionId:8,before:[0,0,1],after:[2,0,1]}})));
 expect(screen.getByLabelText('Position · metres East')).toHaveValue('2');
 act(()=>window.dispatchEvent(new CustomEvent('geoai:assistant-preview-cancel',{detail:{componentId:'other'}})));
 expect(screen.getByLabelText('Position · metres East')).toHaveValue('2');
 act(()=>window.dispatchEvent(new CustomEvent('geoai:assistant-preview-cancel',{detail:{componentId:'beam'}})));
 expect(screen.getByLabelText('Position · metres East')).toHaveValue('0');expect(preview.mock.lastCall?.[0].detail).toBeNull();expect(update).not.toHaveBeenCalled();
 window.removeEventListener('geoai:component-preview',preview);
});
