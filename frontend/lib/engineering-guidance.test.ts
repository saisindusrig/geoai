// @vitest-environment jsdom
import {describe,it,expect} from "vitest";
import {requestEngineeringResult,takeEngineeringResult,requirementPlan,conciseResponse} from "./engineering-guidance";
describe("saved diagram navigation gates",()=>{
  it("only consumes an exact valid analysis and revision, once",()=>{
    requestEngineeringResult({analysisId:421,revisionId:103,mode:"moment"});
    expect(takeEngineeringResult(420,103,true)).toBeNull();
    expect(takeEngineeringResult(421,102,true)).toBeNull();
    expect(takeEngineeringResult(421,103,false)).toBeNull();
    expect(takeEngineeringResult(421,103,true)?.mode).toBe("moment");
    expect(takeEngineeringResult(421,103,true)).toBeNull();
  });
});

it("orders geometry before review and identifies source prerequisites without losing rows",()=>{
  const rows=[
    {path:"engineer_input_review",reason:"Review",recordId:354,group:"Assumptions"},
    {path:"anchors.A.material",reason:"Declare material",recordId:354,group:"Materials"},
    {path:"saved_geometry_evidence.reference",reason:"Supply reference",recordId:354,group:"Geometry"},
    {path:"saved_geometry_evidence",reason:"Choose source",recordId:354,group:"Geometry"},
  ];
  const result=requirementPlan(rows);
  expect(result).toHaveLength(4);
  expect(result.find(row=>!row.prerequisite)?.path).toBe("saved_geometry_evidence");
  expect(result.find(row=>row.path.endsWith(".reference"))?.prerequisite).toBe("saved_geometry_evidence");
  expect(result.at(-1)?.path).toBe("engineer_input_review");
  expect(result.find(row=>row.path==="anchors.A.material")?.component).toBe("Anchor · A");
  expect(rows[0].path).toBe("engineer_input_review");
});

it("never collapses stale qualifications or cuts a numerical line",()=>{
  expect(conciseResponse("STALE " + "saved values ".repeat(100))).toBeNull();
  expect(conciseResponse("A very long numeric row " + "1234 ".repeat(150))).toBeNull();
  const text="Project 793\n\nSaved analysis 421\nCase Gravity: explicit declaration\nNode 2: -1 kN\n"+"Source evidence ".repeat(70);
  expect(conciseResponse(text)).toContain("Node 2: -1 kN");
});
