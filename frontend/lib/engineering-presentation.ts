import type {EngineeringContext, EngineeringReply} from "./engineering-guidance";

export function currentSavedResult(context:EngineeringContext){
  return context.analyses.find(row=>row.type.startsWith("OPENSEES") && row.selectionMatch && !row.stale && row.status==="VERIFIED");
}

export function inputBlocker(context:EngineeringContext){
  const paths=context.missing.map(row=>row.path);
  const anchors=paths.some(path=>path.startsWith("anchors."));
  const contact=paths.some(path=>path.startsWith("contact_stiffness"));
  if(anchors && contact)return "The anchor properties and concrete-contact stiffness need supporting data.";
  if(anchors)return "The anchor properties still need supporting data.";
  if(contact)return "The concrete-contact stiffness still needs supporting data.";
  if(paths.some(path=>path.startsWith("saved_geometry")))return "The geometry needs a documented source before analysis can proceed.";
  return "Some required engineering inputs are missing. We can review them one task at a time.";
}

/** A reading view of existing saved evidence; never changes the stored response. */
export function naturalEngineeringResponse(text:string, context:EngineeringContext){
  if(context.stale || text.includes("STALE"))return "These values belong to a changed or earlier model. Save your changes and refresh the context before using them for a new analysis.";
  if(/cannot execute scripts|cannot.*certify safety/.test(text))return "I can explain saved evidence and guide you through supported inputs. I cannot run arbitrary scripts, certify safety or approve a design.";
  if(text.includes("Saved assessment identifies"))return `${inputBlocker(context)} I can guide you through the required inputs.`;
  const result=currentSavedResult(context);
  if(text.includes("Case ") && result){
    const transfer=result.transfer as {applied_kn?:number;area_m2?:number;loading?:{intensity_kn_m2?:number}}|undefined;
    if(transfer?.loading?.intensity_kn_m2!==undefined && transfer.applied_kn!==undefined)
      return `The saved slab load is ${transfer.loading.intensity_kn_m2} kN/m² over ${transfer.area_m2} m², giving ${transfer.applied_kn} kN in total. This is one-way load transfer, not slab plate or shell analysis.`;
    const cases=result.cases as {name:string}[]|undefined;
    return cases?.length ? `The saved analysis includes ${[...new Set(cases.map(row=>row.name))].join(", ")} load cases. Open the results to inspect their magnitudes, directions and units.` : "Open the saved results to inspect the applied loads and their sources.";
  }
  if(text.includes("Stored bending-moment samples") && result){
    const moment=result.moment_nm as {min:number;max:number}|undefined;
    if(moment)return `The saved bending moment ranges from ${(moment.min/1000).toFixed(6)} to ${(moment.max/1000).toFixed(6)} kN·m. You can inspect it in the existing diagram.`;
  }
  if(text.includes("CAD-generated components"))return `${context.drawingReferences.length} generated components are linked to saved drawing references. You can inspect their source outlines and model components together.`;
  if(text.includes("Geometry dimensions") && context.selected.length){
    const component=context.selected[0],geometry=component.geometry as {size?:number[]};
    return `${component.name} is a ${component.role}${geometry.size ? ` with saved local dimensions ${geometry.size.join(" × ")} m` : ""}. Its visual finish does not establish engineering material properties.`;
  }
  if(text.includes("Geometry changes require"))return "You can preview a dimension change in Inspect, then Apply and Save it. Existing analysis may become stale and must be reviewed before reuse.";
  if(text.includes("No current verified saved"))return "There is no current verified saved result for this selection. Select an analyzed member or review the engineering inputs.";
  if(text.includes("No missing-value assessment"))return "There is no saved input-readiness assessment for this selection. Review the engineering inputs before preparing an analysis.";
  return text.split("\n").filter(line=>!line.startsWith("Project ") && !line.startsWith("Engineering approval remains")).join("\n").trim();
}

export function primaryGuidanceAction(text:string, reply:EngineeringReply){
  if(reply.evidence.missing.length)return "inputs";
  if(reply.actions.includes("moment") && currentSavedResult(reply.evidence))return "moment";
  if(reply.actions.includes("drawing"))return "drawing";
  if(currentSavedResult(reply.evidence) && /load|result|moment/i.test(text))return "results";
  if(reply.evidence.selected?.length)return "inspect";
  return reply.actions.includes("inputs") ? "inputs" : reply.actions[0];
}

export const ACTION_LABELS:Record<string,string>={inputs:"Review required inputs",inspect:"Inspect component",results:"Open saved results",moment:"Show bending moment",drawing:"Inspect drawing sources"};

export function guidanceActionAvailable(action:string,reply:EngineeringReply){
  if(action==="inspect")return !!reply.evidence.selected?.length;
  if(action==="results" || action==="moment")return !!currentSavedResult(reply.evidence);
  return true;
}
