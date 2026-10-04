import {describe,expect,it} from "vitest";
import {compareDocuments} from "./revision-comparison";
import type {EditableModelDocument} from "./types";
const doc={components:[{id:"a",name:"Pier",transform:{position:[1,2,3],rotation_deg:[0,0,0],scale:[1,1,1]},geometry:{kind:"box",size:[1,1,1]} }]} as EditableModelDocument;
describe("immutable revision comparison",()=>{
  it("reports exact changes without altering either revision",()=>{const after=structuredClone(doc);after.components[0].transform.position=[3,2,4];after.components[0].transform.rotation_deg[2]=15;after.components[0].geometry={kind:"box",size:[2,1,1]};const before=JSON.stringify(doc),current=JSON.stringify(after);expect(compareDocuments(doc,after)[0]).toMatchObject({status:"MODIFIED",position:[2,0,1],heading:15,scale:[0,0,0],geometryChanged:true});expect(JSON.stringify(doc)).toBe(before);expect(JSON.stringify(after)).toBe(current);});
  it("distinguishes added, removed and unchanged objects",()=>{expect(compareDocuments(doc,doc)[0].status).toBe("UNCHANGED");expect(compareDocuments(doc,{...doc,components:[]})[0].status).toBe("REMOVED");expect(compareDocuments({...doc,components:[]},doc)[0].status).toBe("ADDED");});
});
