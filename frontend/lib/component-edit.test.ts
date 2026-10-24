import {describe,expect,it} from "vitest";
import {componentEditPatch} from "./component-edit";
import {componentDisplayName} from "./component-presentation";
import {displayMaterial} from "./display-material";
import type {EditableModelComponent} from "./types";

const member:EditableModelComponent={id:"stable-id",parent_id:null,name:"column-sw",category:"column",visible:true,locked:false,geometry:{kind:"box",size:[.3,.3,3.2]},transform:{position:[1,2,3],rotation_deg:[0,0,0],scale:[1,1,1]},material:{name:"Generated material",color:"#94A3B8",roughness:.75,metalness:0}};
describe("presentation and staged edit contracts",()=>{
  it("classifies finishes and names without changing declarations or geometry",()=>{
    const before=JSON.stringify(member);
    expect(componentDisplayName(member)).toBe("Column SW");
    expect(displayMaterial(member).finish).toBe("Steel-style column appearance");
    expect(JSON.stringify(member)).toBe(before);
  });
  it("does not submit unchanged fields through CAD authorization gates",()=>{
    const draft=structuredClone(member);draft.transform.position[0]=5;
    expect(Object.keys(componentEditPatch(member,draft))).toEqual(["transform"]);
    expect(componentEditPatch(member,structuredClone(member))).toEqual({});
  });
  it("submits multiple changed fields in one patch and leaves the source intact",()=>{
    const draft=structuredClone(member);draft.name="Support column";if(draft.geometry.kind==="box")draft.geometry.size[2]=4;
    expect(Object.keys(componentEditPatch(member,draft))).toEqual(["name","geometry"]);
    expect(member.name).toBe("column-sw");
  });
});
