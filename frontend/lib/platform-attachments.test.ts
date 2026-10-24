import {describe,expect,it} from "vitest";
import fixture from "./__fixtures__/maintenance-platform.json";
import type {EditableModelDocument} from "./types";
import {previewPlatform,readPlatform} from "./parametric-platform";
import {ATTACHMENT_DEFAULTS,attachmentOf,attachments,previewAttachment,validateAttachments,type AttachmentKind} from "./platform-attachments";
import {componentObject,releaseComponentObject} from "./sandbox-geometry";
const prefix="industrial-platform-5x3:";
const initial=()=>previewPlatform(structuredClone(fixture) as unknown as EditableModelDocument,{...readPlatform(fixture as unknown as EditableModelDocument)!,length:5,width:3,height:3});
function add(doc:EditableModelDocument,kind:AttachmentKind,id:string=kind,refs=kind==="stairs"?[prefix+"platform-deck"]:kind==="brace"?[prefix+"column-sw",prefix+"column-nw"]:kind==="connection"?[prefix+"column-sw",prefix+"beam-south"]:[prefix+"column-sw"],p=ATTACHMENT_DEFAULTS[kind]){return previewAttachment(doc,{id,kind,refs,parameters:{...p}});}
function body(doc:EditableModelDocument,id:string){return doc.components.find(c=>attachmentOf(c)===id)!;}
describe("connected platform assemblies",()=>{
  it.each(["foundation","base_plate","brace","stairs","connection"] as AttachmentKind[])("generates selectable editable real %s geometry without changing its source",kind=>{
    const source=initial(),snapshot=JSON.stringify(source),doc=add(source,kind);
    expect(JSON.stringify(source)).toBe(snapshot);expect(validateAttachments(doc)).toEqual([]);expect(attachments(doc)).toHaveLength(1);
    for(const c of doc.components.filter(attachmentOf)) {const object=componentObject(c);expect(object.children).toHaveLength(1);expect(c.quantity?.included).toBe(false);expect(c.metadata?.engineering_status).toBe("conceptual_unverified");releaseComponentObject(object);}
  });
  it("stacks column, plate and footing with touching surfaces and keeps footing under edits",()=>{
    let doc=add(add(initial(),"foundation"),"base_plate");const column=doc.components.find(c=>c.id===prefix+"column-sw")!;
    const plate=body(doc,"base_plate"),foot=body(doc,"foundation");if(column.geometry.kind!=="box"||plate.geometry.kind!=="box"||foot.geometry.kind!=="box")throw Error();
    const base=column.transform.position[2]-column.geometry.size[2]/2;
    expect(plate.transform.position[2]+plate.geometry.size[2]/2).toBeCloseTo(base);expect(foot.transform.position[2]+foot.geometry.size[2]/2).toBeCloseTo(plate.transform.position[2]-plate.geometry.size[2]/2);
    doc=add(doc,"base_plate","base_plate",undefined,{...ATTACHMENT_DEFAULTS.base_plate,thickness:.05});expect(body(doc,"foundation").transform.position[2]).toBeCloseTo(-.05-.45/2);
    doc=previewAttachment(doc,null,"base_plate");expect(body(doc,"foundation").transform.position[2]).toBeCloseTo(-.45/2);expect(validateAttachments(doc)).toEqual([]);
  });
  it("connects brace endpoints exactly to column base and opposite column top",()=>{
    const doc=add(initial(),"brace"),brace=body(doc,"brace");if(brace.geometry.kind!=="cylinder")throw Error();
    const a=doc.components.find(c=>c.id===prefix+"column-sw")!,b=doc.components.find(c=>c.id===prefix+"column-nw")!;
    expect(brace.geometry.start.slice(0,2)).toEqual(a.transform.position.slice(0,2).map((v,i)=>v-doc.components.find(c=>c.id===prefix+"platform-deck")!.transform.position[i]));expect(brace.geometry.start[2]).toBeCloseTo(0);expect(brace.geometry.end[2]).toBeCloseTo(2.6);expect(b.transform.position[2]).toBeCloseTo(1.3);
  });
  it("uses equal risers, deck-edge contact and continuous stringers beneath every tread",()=>{
    const doc=add(initial(),"stairs"),treads=doc.components.filter(c=>c.id.startsWith("platform-addon:stairs:tread-"));expect(treads).toHaveLength(17);
    const rise=3/17,deck=doc.components.find(c=>c.id===prefix+"platform-deck")!,last=treads.at(-1)!,stringer=doc.components.find(c=>c.id==="platform-addon:stairs:stringer-1")!;
    if(last.geometry.kind!=="box"||stringer.geometry.kind!=="cylinder"||deck.geometry.kind!=="box")throw Error();
    expect(last.transform.position[2]+last.geometry.size[2]/2).toBeCloseTo(3);
    expect(last.transform.position[1]+last.geometry.size[1]/2).toBeCloseTo(deck.transform.position[1]-deck.geometry.size[1]/2);
    for(const [i,tread] of treads.entries()){if(tread.geometry.kind!=="box")throw Error();expect(tread.transform.position[2]+tread.geometry.size[2]/2).toBeCloseTo((i+1)*rise);const y=tread.transform.position[1]-deck.transform.position[1];const g=stringer.geometry;const lineZ=g.start[2]+(y-g.start[1])*(g.end[2]-g.start[2])/(g.end[1]-g.start[1]);expect(lineZ).toBeCloseTo(tread.transform.position[2]-tread.geometry.size[2]/2);}
  });
  it("regenerates all attachments on length, width, height and column size changes",()=>{
    let doc=initial();for(const kind of Object.keys(ATTACHMENT_DEFAULTS) as AttachmentKind[])doc=add(doc,kind);
    const ids=doc.components.map(c=>c.id),next=previewPlatform(doc,{...readPlatform(doc)!,length:6,width:4,height:3.6,columnWidth:.35,columnDepth:.4});
    expect(validateAttachments(next)).toEqual([]);expect(body(next,"foundation").transform.position[0]).not.toBe(body(doc,"foundation").transform.position[0]);expect(next.components.filter(c=>attachmentOf(c)==="stairs")).toHaveLength(22);expect(next.components.map(c=>c.id)).toEqual(expect.arrayContaining(ids));
  });
  it("preserves appearance, hidden state, unrelated components and parameter identities",()=>{
    let doc=add(initial(),"foundation");body(doc,"foundation").visible=false;body(doc,"foundation").material.color="#abcdef";doc.components.push({...structuredClone(doc.components[0]),id:"unrelated"});
    doc=previewPlatform(doc,{...readPlatform(doc)!,length:7});expect(body(doc,"foundation").visible).toBe(false);expect(body(doc,"foundation").material.color).toBe("#abcdef");expect(doc.components.some(c=>c.id==="unrelated")).toBe(true);
  });
  it("handles common rotation and translated base plane",()=>{
    const doc=initial();for(const c of doc.components){c.transform.rotation_deg[2]=45;c.transform.position[2]+=2;}
    const next=add(add(doc,"foundation"),"stairs");expect(validateAttachments(next)).toEqual([]);expect(body(next,"foundation").transform.position[2]).toBeCloseTo(2-.45/2);
  });
  it.each([0,-1,NaN,Infinity,501])("rejects invalid dimension %s",v=>expect(()=>add(initial(),"foundation","a",undefined,{...ATTACHMENT_DEFAULTS.foundation,width:v})).toThrow());
  it("rejects missing, duplicate, wrong-category and disconnected references",()=>{
    expect(()=>add(initial(),"brace","a",[prefix+"column-sw",prefix+"column-sw"])).toThrow("distinct");
    expect(()=>add(initial(),"foundation","a",["missing"])).toThrow("missing");
    expect(()=>add(initial(),"foundation","a",[prefix+"beam-south"])).toThrow("column reference");
    expect(()=>add(initial(),"connection","a",[prefix+"column-sw",prefix+"beam-north"])).toThrow("touch");
    expect(()=>add(add(initial(),"foundation"),"foundation","another")).toThrow("already");
  });
  it("rejects impossible footprints, brace diameter and stair dimensions",()=>{
    expect(()=>add(initial(),"foundation","a",undefined,{...ATTACHMENT_DEFAULTS.foundation,width:.1})).toThrow("footprint");
    expect(()=>add(initial(),"brace","a",undefined,{radius:1})).toThrow("diameter");
    const invalid:Record<string,number>[]=[{width:10},{maxRiser:.001},{treadThickness:.5},{stringerRadius:1}];
    for(const p of invalid)expect(()=>add(initial(),"stairs","a",undefined,{...ATTACHMENT_DEFAULTS.stairs,...p})).toThrow();
  });
  it("respects lock constraints on dependent regeneration and deletion",()=>{
    const doc=add(initial(),"foundation");body(doc,"foundation").locked=true;
    expect(()=>previewPlatform(doc,{...readPlatform(doc)!,length:6})).toThrow("Unlock");expect(()=>previewAttachment(doc,null,"foundation")).toThrow("Unlock");
    expect(()=>add(doc,"base_plate")).toThrow("Unlock");
  });
  it("rejects detached, missing, orphan and tampered geometry",()=>{
    const doc=add(initial(),"stairs");body(doc,"stairs").transform.position[0]+=1;expect(validateAttachments(doc)).not.toEqual([]);
    const missing=add(initial(),"stairs");missing.components=missing.components.filter(c=>c.id!=="platform-addon:stairs:tread-2");expect(validateAttachments(missing)).not.toEqual([]);
    const orphan=add(initial(),"foundation");orphan.generator_parameters.platform_attachments={version:1,items:[]};expect(validateAttachments(orphan)).not.toEqual([]);
    const bad=add(initial(),"foundation");bad.components.find(c=>c.id===prefix+"column-sw")!.transform.scale[0]=2;expect(validateAttachments(bad)).not.toEqual([]);
  });
  it("deletes the whole stair assembly with no orphan treads or stringers",()=>{const doc=add(initial(),"stairs"),next=previewAttachment(doc,null,"stairs");expect(next.components).toHaveLength(9);expect(attachments(next)).toEqual([]);expect(doc.components.length).toBeGreaterThan(9);});
});
