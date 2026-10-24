import {describe,expect,it} from "vitest";
import {naturalEngineeringResponse,inputBlocker,guidanceActionAvailable} from "./engineering-presentation";
import type {EngineeringContext,EngineeringReply} from "./engineering-guidance";
const context={selected:[],stale:false,missing:[],drawingReferences:[],analyses:[]} as unknown as EngineeringContext;
describe("minimal saved-evidence presentation",()=>{
  it("explains actual missing properties without a field-count dump",()=>{
    const c={...context,missing:[{path:"anchors.A.material"},{path:"contact_stiffness_n_m3.value"}]} as EngineeringContext;
    expect(inputBlocker(c)).toContain("anchor properties and concrete-contact stiffness");
    const answer=naturalEngineeringResponse("Saved assessment identifies missing required information: 233",c);
    expect(answer).toContain("guide you");expect(answer).not.toContain("233");
  });
  it("keeps saved numerical precision and units, but suppresses current interpretation when stale",()=>{
    const c={...context,analyses:[{id:421,revisionId:103,evidenceHash:"saved",type:"OPENSEES_PHYSICAL_FRAME",status:"VERIFIED",selectionMatch:true,stale:false,moment_nm:{min:-28809.726,max:24756.664}}]} as EngineeringContext;
    expect(naturalEngineeringResponse("Stored bending-moment samples",c)).toContain("-28.809726 to 24.756664 kN·m");
    expect(naturalEngineeringResponse("Stored bending-moment samples",{...c,stale:true})).not.toContain("28.809726");
    expect(guidanceActionAvailable("moment",{evidence:{...c,analyses:c.analyses.map(row=>({...row,stale:true}))}} as EngineeringReply)).toBe(false);
  });
  it("keeps the supported slab idealization and unsupported approval boundary explicit",()=>{
    const c={...context,analyses:[{id:301,revisionId:86,evidenceHash:"saved",type:"OPENSEES_SLAB_TRANSFER",status:"VERIFIED",selectionMatch:true,stale:false,transfer:{loading:{intensity_kn_m2:5},area_m2:24,applied_kn:120}}]} as EngineeringContext;
    const text=naturalEngineeringResponse("Case Slab tributary",c);
    expect(text).toContain("5 kN/m²");expect(text).toContain("120 kN");expect(text).toContain("not slab plate or shell analysis");
    expect(naturalEngineeringResponse("This chat cannot execute scripts",context)).toContain("cannot run arbitrary scripts, certify safety or approve a design");
  });
});
