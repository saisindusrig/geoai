import {describe,expect,it} from "vitest";
import * as THREE from "three";
import {sectionGeometry,designElevationAt,designProfile,analyseSupports,sampleSection} from "./editor-analysis";
import {clipGeometry,clipPlanes} from "./editor-clipping";
import type {EditableModelDocument} from "./types";
const doc={components:[{id:"deck",name:"Deck",category:"deck",visible:true,locked:false,geometry:{kind:"box",size:[10,6,2]},transform:{position:[0,0,5],rotation_deg:[0,0,0],scale:[1,1,1]},material:{color:"#fff",roughness:1,metalness:0}}]} as EditableModelDocument;
describe("non-destructive scene analysis",()=>{
  it("sections actual transformed geometry and leaves the document unchanged",()=>{const before=JSON.stringify(doc);const section=sectionGeometry(doc,0,0,0);expect(section.length).toBeGreaterThan(0);expect(section.flatMap(item=>item.points.map(point=>point[1]))).toContain(6);expect(JSON.stringify(doc)).toBe(before);expect(sectionGeometry(doc,0,20,0)).toEqual([]);});
  it("finds actual design top and preserves unknown outside geometry",()=>{expect(designElevationAt(doc,0,0)).toBeCloseTo(6);expect(designElevationAt(doc,50,50)).toBeNull();});
  it("clips triangles at the precise plane without changing source geometry",()=>{const source=new THREE.BoxGeometry(10,10,10);const count=source.getAttribute("position").count;const clipped=clipGeometry(source,new THREE.Matrix4(),clipPlanes({mode:"horizontal",value:1,size:10}));const positions=clipped.getAttribute("position");for(let index=0;index<positions.count;index++)expect(positions.getZ(index)).toBeGreaterThanOrEqual(1);expect(source.getAttribute("position").count).toBe(count);source.dispose();clipped.dispose();});
  it("section box supplies all six planes and Off restores source geometry",()=>{expect(clipPlanes({mode:"box",value:0,size:10})).toHaveLength(6);expect(clipPlanes({mode:"off",value:0,size:10})).toEqual([]);});
  it("profiles the actual placed model and keeps stations outside geometry unknown",async()=>{
    const stations=[{longitude:0,latitude:0,chainage_m:0,proposed_elevation_m:null,grade_percent:null},{longitude:.01,latitude:0,chainage_m:1000,proposed_elevation_m:null,grade_percent:null}];
    const placement={longitude:0,latitude:0,elevation:100,offset:0,heading:0,status:"VALID",vertical_reference:{type:"ELLIPSOIDAL"}};
    const result=await designProfile(doc,placement,stations);
    expect(result[0].proposed_elevation_m).toBeCloseTo(106);expect(result[1].proposed_elevation_m).toBeNull();expect(result[1].grade_percent).toBeNull();
    expect((await designProfile(doc,{...placement,status:"REVIEW_REQUIRED"},stations))[0].proposed_elevation_m).toBeNull();
  });
  it("samples support centers and computes clearance against the actual deck underside",async()=>{
    const support={...doc.components[0],id:"pier",name:"Pier",category:"pier",geometry:{kind:"box" as const,size:[1,1,4] as [number,number,number]},transform:{position:[0,0,2] as [number,number,number],rotation_deg:[0,0,0] as [number,number,number],scale:[1,1,1] as [number,number,number]}};
    const placement={longitude:0,latitude:0,elevation:100,offset:0,heading:0,status:"VALID",vertical_reference:{type:"ELLIPSOIDAL"}};
    const rows=await analyseSupports({...doc,components:[...doc.components,support]},placement,async()=>({status:"VALID",elevation:99,source:"Survey",terrain_version_id:4,vertical_reference:{type:"ELLIPSOIDAL"}}));
    expect(rows[0].deck).toBeCloseTo(104);expect(rows[0].clearance).toBeCloseTo(5);expect(rows[0].foundation).toBeCloseTo(100);expect(rows[0].version).toBe(4);expect(rows[0].status).toBe("OK");
    const unknown=await analyseSupports({...doc,components:[support]},placement,async()=>({status:"UNKNOWN",elevation:null,source:"NONE",terrain_version_id:null,vertical_reference:null}));
    expect(unknown[0].clearance).toBeNull();expect(unknown[0].status).toBe("UNKNOWN");
  });
  it("compares actual section ground and geometry without filling unknown terrain",async()=>{
    const placement={longitude:0,latitude:0,elevation:100,offset:0,heading:0,status:"VALID",vertical_reference:{type:"ELLIPSOIDAL"}};
    const rows=await sampleSection(doc,placement,0,0,0,0,10,async()=>({status:"VALID",elevation:102,source:"Survey",terrain_version_id:4,vertical_reference:{type:"ELLIPSOIDAL"}}));
    expect(rows[0].elevation).toBeCloseTo(2);expect(rows[0].design).toBeCloseTo(6);expect(rows[0].difference).toBeCloseTo(4);expect(rows[0].version).toBe(4);
    const unknown=await sampleSection(doc,placement,0,0,0,0,10,async()=>({status:"UNKNOWN",elevation:null,source:"NONE",terrain_version_id:null,vertical_reference:null}));
    expect(unknown[0].elevation).toBeNull();expect(unknown[0].difference).toBeNull();
    await expect(sampleSection(doc,placement,0,0,0,50,0,async()=>{throw new Error("Must not sample");})).rejects.toThrow("positive interval");
  });
});
