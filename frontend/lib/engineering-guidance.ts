export type EngineeringContext = {
  projectId:number;projectName:string;revisionId:number|null;revisionNumber:number|null;latestRevisionId:number|null;
  stale:boolean;editorDirty:boolean;analysisVersionHash?:string;documentHash:string|null;notice:string;groups:string[];
  selected:{id:string;name:string;role:string;geometry:unknown;transform:unknown;appearance:unknown;engineeringStatus:string;cadSource:unknown}[];
  drawingReferences:{componentId:string;name:string;sourceEntityId:string;sourceHash:string;geometryHash:string}[];
  missingTotal?:number;missing:{group:string;path:string;reason:string;recordId:number}[];
  analyses:{id:number;type:string;revisionId:number;status:string;stale:boolean;selectionMatch?:boolean;memberIds?:string[];evidenceHash:string;[key:string]:unknown}[];
};
export type EngineeringReply={mode:string;requestedModel:string;actualModel:string|null;producer:string;evidence:EngineeringContext;actions:string[]};
export const GUIDANCE_MODELS=["zai-org/GLM-5.3-Flash","zai-org/GLM-5.3"] as const;

export type ResultNavigation={analysisId:number;revisionId:number;mode:"moment"|"results"};
let pending:ResultNavigation|null=null;
export function requestEngineeringResult(value:ResultNavigation){pending=value;window.dispatchEvent(new Event("geoai:copilot-result"));}
export function takeEngineeringResult(analysisId:number,revisionId:number,valid:boolean){
  if(!valid || pending?.analysisId!==analysisId || pending.revisionId!==revisionId)return null;
  const value=pending;pending=null;return value;
}

export type MissingRequirement = EngineeringContext["missing"][number];
export function requirementPlan(rows: MissingRequirement[]) {
  const paths = new Set(rows.map(row => `${row.recordId}:${row.path}`));
  return rows.map((row, index) => {
    const parts = row.path.split(".");
    const anchor = parts[0] === "anchors" ? parts[1] : null;
    const field = anchor ? parts.slice(2).join(".") : row.path;
    const root = field.split(".")[0];
    const component = anchor ? `Anchor · ${anchor}` : root === "saved_geometry_evidence" ? "Connection geometry" : /contact|pressure|concrete/.test(root) ? "Plate / concrete contact" : "Connection assumptions";
    const parent = row.path.slice(0, row.path.lastIndexOf("."));
    const prerequisite = paths.has(`${row.recordId}:${parent}`) ? parent : null;
    const priority = root === "saved_geometry_evidence" ? 1 : root === "engineer_input_review" ? 4 : /evidence|reference|reviewed_by|applicability|method/.test(field) ? 3 : 2;
    return {...row, component, label: field==="saved_geometry_evidence" ? "Geometry source" : field.replaceAll("_", " ").replaceAll(".", " · "), priority, prerequisite, index};
  }).sort((a,b) => a.priority-b.priority || a.index-b.index);
}

/** Presentation only: retain the complete persisted response in a disclosure. */
export function conciseResponse(text: string, evidence?:EngineeringContext) {
  if(!text.includes("STALE") && text.includes("Saved assessment identifies") && evidence?.missingTotal!==undefined)
    return `${evidence.missingTotal} required inputs remain in this saved assessment. Start with the next requirement; analysis remains blocked.`;
  if(!text.includes("STALE") && text.includes("Case ") && evidence){
    const result=evidence.analyses.find(row=>row.type.startsWith("OPENSEES") && row.selectionMatch && !row.stale && row.status==="VERIFIED");
    const cases=result?.cases as {name:string}[]|undefined;
    if(result && cases?.length){
      const transfer=result.transfer as {applied_kn?:number;area_m2?:number;loading?:{intensity_kn_m2?:number}}|undefined;
      const slab=transfer?.loading?.intensity_kn_m2!==undefined && transfer.applied_kn!==undefined ? ` Saved slab pressure ${transfer.loading.intensity_kn_m2} kN/m²; total applied ${transfer.applied_kn} kN over ${transfer.area_m2} m². One-way load transfer only.` : "";
      return `Saved analysis #${result.id}: ${[...new Set(cases.map(row=>row.name))].join(", ")}.${slab} Expand the saved explanation for magnitudes, directions, units and source assumptions.`;
    }
  }
  const lines = text.split("\n").map(line=>line.trim()).filter(Boolean);
  const content = lines.filter(line=>!line.startsWith("Project ") && !line.startsWith("Engineering approval remains"));
  const summary = content.slice(0, 3).join("\n");
  // Never silently cut a numerical line or hide a stale-context qualification.
  return text.includes("STALE") || text.length < 550 || summary.length > 650 ? null : summary;
}
