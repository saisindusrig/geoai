import {describe,it,expect} from "vitest";
import fixture from "./__fixtures__/maintenance-platform.json";
import {readPlatform,previewPlatform} from "./parametric-platform";
import type {EditableModelDocument} from "./types";
const doc=fixture as unknown as EditableModelDocument;
const parameters={...readPlatform(doc)!,length:6,width:4,height:3.6,slabThickness:0.25,beamWidth:0.35,beamDepth:0.3,columnWidth:0.4,columnDepth:0.45};
describe("coordinated conceptual platform",()=>{
  it("preserves source, identities and unrelated objects while joining all nine members",()=>{
    const before=JSON.stringify(doc), next=previewPlatform(doc,parameters);
    expect(JSON.stringify(doc)).toBe(before);expect(next.components.map(c=>c.id)).toEqual(doc.components.map(c=>c.id));
    const get=(name:string)=>next.components.find(c=>c.name===name)!;
    const box=(name:string)=>{const c=get(name);if(c.geometry.kind!=="box")throw Error();return {p:c.transform.position,s:c.geometry.size};};
    const deck=box("platform-deck"), north=box("beam-north"), east=box("beam-east"), column=box("column-ne");
    expect(deck.s).toEqual([6,4,.25]);
    expect(deck.p[2]-deck.s[2]/2).toBeCloseTo(north.p[2]+north.s[2]/2);
    expect(north.p[2]-north.s[2]/2).toBeCloseTo(column.p[2]+column.s[2]/2);
    expect(east.p[1]+east.s[1]/2).toBeCloseTo(north.p[1]-north.s[1]/2);
    for(const c of next.components.filter(c=>c.name.startsWith("column"))) {expect(c.transform.position[2]).toBeCloseTo(3.05/2);expect(c.metadata?.engineering_status).toBe("conceptual_unverified");}
    const extra=structuredClone(doc);extra.components.push({...structuredClone(doc.components[0]),id:"other",name:"Other"});
    expect(previewPlatform(extra,parameters).components.at(-1)).toEqual(extra.components.at(-1));
  });
  it.each([0,-1,NaN,Infinity])("rejects invalid dimension %s",value=>expect(()=>previewPlatform(doc,{...parameters,length:value})).toThrow("greater than zero"));
  it("rejects impossible spans and deck stack",()=>{expect(()=>previewPlatform(doc,{...parameters,width:.3})).toThrow("clear span");expect(()=>previewPlatform(doc,{...parameters,height:.4})).toThrow("Deck height");});
  it("respects locks, missing members, scales and base planes",()=>{
    const locked=structuredClone(doc);locked.components[0].locked=true;expect(()=>previewPlatform(locked,parameters)).toThrow("Unlock");
    const missing=structuredClone(doc);missing.components.pop();expect(()=>previewPlatform(missing,parameters)).toThrow("nine-member");
    const scaled=structuredClone(doc);scaled.components[0].transform.scale[0]=2;expect(()=>previewPlatform(scaled,parameters)).toThrow("unit scale");
    const uneven=structuredClone(doc);uneven.components.find(c=>c.name==="column-sw")!.transform.position[2]+=.2;expect(()=>previewPlatform(uneven,parameters)).toThrow("bases");
  });
  it("preserves a common rotated and translated assembly",()=>{const rotated=structuredClone(doc);for(const c of rotated.components)c.transform.rotation_deg[2]=90;const next=previewPlatform(rotated,parameters);const north=next.components.find(c=>c.name==="beam-north")!;const deck=next.components.find(c=>c.name==="platform-deck")!;expect(north.transform.position[0]-deck.transform.position[0]).toBeCloseTo(-1.775);});
});
