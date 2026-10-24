"use client";
import {requirementPlan, type EngineeringContext, type MissingRequirement} from "@/lib/engineering-guidance";

export default function MissingEngineeringInputs({evidence, disabled, onOpen}: {evidence:EngineeringContext;disabled:boolean;onOpen:(row:MissingRequirement)=>void}) {
  const plan=requirementPlan(evidence.missing);
  if(!plan.length)return null;
  const next=plan.find(row=>!row.prerequisite) ?? plan[0];
  const components=[...new Set(plan.map(row=>row.component))];
  return <section aria-label="Missing engineering requirements" className="space-y-3 text-xs">
    <p className="text-muted-foreground">Next: {next.component} · {next.label}</p>
    <button className="copilot-primary-action" disabled={disabled} onClick={()=>onOpen(next)}>Review required inputs</button>
    <details><summary className="cursor-pointer">Advanced requirements</summary>
      <p className="my-2 font-medium">{evidence.missingTotal ?? plan.length} saved requirements · {components.length} task groups</p>
      {evidence.missingTotal===undefined&&<p>Earlier snapshot: the total may be incomplete. Ask again for the current assessment.</p>}
      <p className="my-2 text-muted-foreground">Suggested entry order, not a safety ranking. All saved requirements remain mandatory. Source details follow the source declaration; engineer review comes last.</p>
      {components.map(component=><details key={component} className="my-2"><summary className="cursor-pointer">{component} ({plan.filter(row=>row.component===component).length})</summary>
        {plan.filter(row=>row.component===component).map(row=><div key={`${row.recordId}:${row.path}`} className="my-2 border-l border-border pl-2">
          <p>Step {row.priority} · {row.label}</p><p>{row.reason}</p>
          {row.prerequisite&&<p className="text-muted-foreground">First declare: {row.prerequisite.replaceAll("_"," ")}</p>}
          <button className="underline disabled:opacity-40" disabled={disabled} onClick={()=>onOpen(row)}>Open input</button>
          <details><summary>Saved reference</summary><p className="break-all">Record {row.recordId} · {row.path}</p></details>
        </div>)}
      </details>)}
      {(evidence.missingTotal ?? plan.length)>plan.length&&<p>Showing {plan.length}; open the saved assessment for the complete list.</p>}
    </details>
  </section>;
}
