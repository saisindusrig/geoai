import {expect,it} from "vitest";
import {modelFitRange} from "./model-framing";
it("frames a sphere in both dimensions with a margin and scales with geometry",()=>{
  const radius=5,fov=Math.PI/3;
  for(const aspect of [.5,1,2]){
    const distance=modelFitRange(radius,fov,aspect);
    const limitingAngle=Math.min(fov/2,Math.atan(Math.tan(fov/2)*aspect));
    expect(distance*Math.sin(limitingAngle)).toBeGreaterThan(radius);
    expect(modelFitRange(radius*2,fov,aspect)).toBeCloseTo(distance*2);
  }
  expect(modelFitRange(0,fov,1)).toBeGreaterThan(0);
  expect(modelFitRange(radius,fov,.5)).toBeGreaterThan(modelFitRange(radius,fov,2));
});
