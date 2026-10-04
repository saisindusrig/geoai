import {describe,expect,it} from "vitest";
import * as THREE from "three";
import {snapTranslationToTargets,engineeringSnapTargets} from "./engineering-snap";
import type {EditableModelDocument} from "./types";
describe("engineering geometry snapping",()=>{
  it("keeps unconstrained axes unchanged and rejects distant geometry",()=>{
    const targets=[{name:"Pier",point:new THREE.Vector3(5,0,0)},{name:"Reference",point:new THREE.Vector3(5,4,0)}];
    const result=snapTranslationToTargets(new THREE.Vector3(),new THREE.Vector3(4.8,0,0),[new THREE.Vector3(1,0,0)],targets,.5);
    expect(result?.name).toBe("Pier");expect(result?.delta.toArray()).toEqual([5,0,0]);
    expect(snapTranslationToTargets(new THREE.Vector3(),new THREE.Vector3(2,0,0),[new THREE.Vector3(1,0,0)],targets,.5)).toBeNull();
  });
  it("uses transformed design endpoints and excludes selected and external geometry",()=>{
    const doc={components:[{id:"pipe",name:"Pipe",visible:true,geometry:{kind:"sweep",start:[0,0,0],end:[5,0,0],radius_m:1},transform:{position:[2,0,0],rotation_deg:[0,0,90],scale:[1,1,1]}}]} as EditableModelDocument;
    const targets=engineeringSnapTargets(doc,[]);expect(targets.at(-1)?.point.x).toBeCloseTo(2);expect(targets.at(-1)?.point.y).toBeCloseTo(5);
    expect(engineeringSnapTargets(doc,["pipe"])).toHaveLength(1);
  });
});
