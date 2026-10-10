import {describe, expect, it, vi, afterEach} from "vitest";
import {validateCadMesh,loadCadMeshes,cadBufferGeometry} from "./cad-mesh";
import {applyTransformDelta, defaultTransformSettings} from "./editor-transform";
import * as THREE from "three";
import type {EditableModelComponent,EditableModelDocument} from "./types";
import {webcrypto} from "node:crypto";

describe("CAD render boundary", () => {
  afterEach(()=>vi.unstubAllGlobals());
  const mesh={positions:[[0,0,0],[1,0,0],[0,1,0]],triangles:[[0,1,2]],units:"m"};
  async function reference(){
    const bytes=new TextEncoder().encode(JSON.stringify(mesh));
    const hash=[...new Uint8Array(await webcrypto.subtle.digest("SHA-256",bytes))].map(v=>v.toString(16).padStart(2,"0")).join("");
    const geometry={kind:"cad_mesh" as const,catalog_id:100,mesh_hash:hash,brep_hash:hash,definition_hash:hash,bounds_m:[0,0,0,1,1,0] as [number,number,number,number,number,number]};
    const document={project_id:1,components:[{geometry}]} as unknown as EditableModelDocument;
    vi.stubGlobal("crypto",webcrypto);
    return {bytes,geometry,document};
  }
  it("renders authorized hash-verified triangles around the component pivot and reauthorizes cached bytes",async()=>{
    const {bytes,geometry,document}=await reference();
    const fetch=vi.fn().mockResolvedValue(new Response(bytes));
    vi.stubGlobal("fetch",fetch);
    await loadCadMeshes(document);
    const buffer=cadBufferGeometry(geometry);
    expect(Array.from(buffer.getAttribute("position").array)).toEqual([-.5,-.5,0,.5,-.5,0,-.5,.5,0]);
    expect(Array.from(buffer.index!.array)).toEqual([0,1,2]);
    buffer.dispose();
    fetch.mockResolvedValue(new Response(null,{status:403}));
    await expect(loadCadMeshes(document)).rejects.toThrow(/unauthorized/);
    expect(fetch).toHaveBeenCalledTimes(2);
  });
  it("rejects changed artifact bytes rather than rendering a fallback mesh",async()=>{
    const {document}=await reference();
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue(new Response(JSON.stringify({...mesh,units:"mm"}))));
    await expect(loadCadMeshes(document)).rejects.toThrow(/hash mismatch/);
  });
  it("rejects malformed triangles, invalid units and nonfinite positions", () => {
    const mesh = {positions:[[0,0,0],[1,0,0],[0,1,0]], triangles:[[0,1,2]], units:"m"};
    expect(validateCadMesh(mesh)).toEqual(mesh);
    expect(() => validateCadMesh({...mesh,triangles:[[0,1,3]]})).toThrow();
    expect(() => validateCadMesh({...mesh,units:"mm"})).toThrow();
    expect(() => validateCadMesh({...mesh,positions:[[NaN,0,0],[1,0,0],[0,1,0]]})).toThrow();
  });
  it("allows rigid translation and rejects CAD scaling", () => {
    const component = {id:"beam",locked:false,geometry:{kind:"cad_mesh"},transform:{position:[0,0,0],rotation_deg:[0,0,0],scale:[1,1,1]}} as EditableModelComponent;
    const settings = {...defaultTransformSettings, mode:"translate" as const};
    expect(applyTransformDelta([component],settings,new THREE.Vector3(1,0,0),1)[0].transform.position).toEqual([1,0,0]);
    expect(() => applyTransformDelta([component],{...settings,mode:"scale"},new THREE.Vector3(),2)).toThrow(/parametric/);
  });
});
