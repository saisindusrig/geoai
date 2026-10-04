import { describe,expect,it } from "vitest";
import { measurementClassification,measurementValues,type MeasurementPoint } from "./engineering-measurement";
const a: MeasurementPoint = {longitude:77,latitude:12,elevation:500,source:"Survey",dataset:2,version:4,horizontalReference:"EPSG:4326",verticalReference:"ELLIPSOIDAL",status:"VALID",classification:"SURVEY_DERIVED"};
describe("measurement evidence",()=>{
  it("retains unknown elevation instead of zero",()=>{const b={...a,longitude:77.001,elevation:null,classification:"UNKNOWN" as const};expect(measurementValues("distance",[a,b])).toMatchObject({vertical_delta_m:null,distance_m:null,grade_percent:null});expect(measurementClassification([a,b])).toBe("UNKNOWN");});
  it("calculates 3D distance and slope from resolved samples",()=>{const b={...a,longitude:77.001,elevation:510};const result=measurementValues("distance",[a,b]);expect(result.vertical_delta_m).toBe(10);expect(result.distance_m).toBeGreaterThan(result.horizontal_m!);expect(result.grade_percent).toBeGreaterThan(0);expect(a.version).toBe(4);});
  it("public terrain never promotes a mixed measurement",()=>{expect(measurementClassification([a,{...a,classification:"VISUAL_REFERENCE"}])).toBe("VISUAL_REFERENCE");});
  it("blocks mixed vertical references and zero-run slope",()=>{expect(measurementValues("clearance",[a,{...a,verticalReference:"EGM96"}]).clearance_m).toBeNull();expect(measurementValues("slope",[a,a]).grade_percent).toBeNull();});
  it("requires three area vertices",()=>{expect(measurementValues("area",[a,a]).area_m2).toBeNull();expect(measurementValues("area",[a,{...a,longitude:77.001},{...a,latitude:12.001}]).area_m2).toBeGreaterThan(0);});
});
