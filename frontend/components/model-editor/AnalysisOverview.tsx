"use client";
import {useEffect,useState} from "react";
import {api} from "@/lib/api";
import {requestEngineeringResult,type EngineeringContext} from "@/lib/engineering-guidance";
import {currentSavedResult,inputBlocker} from "@/lib/engineering-presentation";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";

export default function AnalysisOverview({editor,projectId}:{editor:EditableModelEditor;projectId:number}){
  const [context,setContext]=useState<EngineeringContext|null>(null),[error,setError]=useState(""),[refresh,setRefresh]=useState(0);
  const revision=editor.baseRevision?.id,selection=editor.selectedIds.join(",");
  useEffect(()=>{
    const changed=(event:Event)=>{if((event as CustomEvent<{projectId:number}>).detail?.projectId===projectId)setRefresh(v=>v+1);};
    window.addEventListener("geoai:engineering-inputs-saved",changed);
    return()=>window.removeEventListener("geoai:engineering-inputs-saved",changed);
  },[projectId]);
  useEffect(()=>{
    let active=true;
    queueMicrotask(()=>{if(active){setContext(null);setError("");}});
    void api.get<{context:EngineeringContext}>(`/api/projects/${projectId}/assistant/engineering-context?${revision ? `revision_id=${revision}&` : ""}selected_ids=${encodeURIComponent(selection)}&dirty=${editor.dirty}`).then(data=>{if(active)setContext(data.context);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[projectId,revision,selection,editor.dirty,refresh]);
  const open=(action:string)=>{
    const panel=document.getElementById("inspector-panel-analysis");
    const tools=panel?.querySelector<HTMLDetailsElement>("[data-analysis-tools]");if(tools)tools.open=true;
    const result=context && currentSavedResult(context);
    if(action==="results" && result && revision)requestEngineeringResult({analysisId:result.id,revisionId:revision,mode:result.moment_nm ? "moment" : "results"});
    else window.dispatchEvent(new CustomEvent("geoai:copilot-inputs",{detail:action}));
  };
  if(error)return <section aria-label="Analysis overview" className="space-y-3"><h2 className="text-base font-semibold">Analysis</h2><p role="alert" className="text-sm">{error}</p><button className="copilot-primary-action" onClick={()=>setRefresh(v=>v+1)}>Reload analysis status</button></section>;
  if(!context)return <section aria-label="Analysis overview"><h2 className="text-base font-semibold">Analysis</h2><p role="status" className="mt-3 text-sm text-muted-foreground">Reading saved analysis…</p></section>;
  const result=currentSavedResult(context),blocked=context.missing.length>0;
  const status=context.stale ? "Needs refresh" : result ? "Numerically verified" : blocked ? "Needs inputs" : context.drawingReferences.length ? "Geometry only" : "No saved result";
  const moment=result?.moment_nm as {min:number;max:number}|undefined;
  const transfer=result?.transfer as {applied_kn?:number;area_m2?:number}|undefined;
  return <section aria-label="Analysis overview" className="space-y-5 pb-5">
    <div><h2 className="text-base font-semibold">Analysis</h2><p className="mt-2 text-sm">{context.selected.length ? context.selected.map(c=>c.name).join(", ") : "Saved structural model"}</p></div>
    <div><p className={`text-xs font-medium ${result ? "text-primary" : "text-amber-200"}`}>{status}</p>
      <p className="mt-2 text-sm leading-relaxed">{context.stale ? "The model has changed. Save and refresh before using analysis for this draft." : result ? "Saved results are available for this model and selection." : blocked ? inputBlocker(context) : context.drawingReferences.length ? "The drawing defines model geometry. It does not establish structural sections, loads or material properties." : "Choose the relevant engineering inputs before preparing an analysis."}</p>
    </div>
    {!context.stale && moment && <div className="border-y border-border py-4"><p className="text-xs text-muted-foreground">Saved bending moment · kN·m</p><p className="mt-2 font-medium">{(moment.min/1000).toFixed(6)} to {(moment.max/1000).toFixed(6)}</p></div>}
    {!context.stale && transfer?.applied_kn!==undefined && <p className="text-sm">Slab load: {transfer.applied_kn} kN over {transfer.area_m2} m². One-way load transfer only.</p>}
    {blocked && <p className="text-xs text-muted-foreground">Work through the geometry source, contact model and anchor properties one task at a time.</p>}
    <button className="copilot-primary-action" disabled={context.stale} onClick={()=>open(result ? "results" : context.drawingReferences.length && !blocked ? "drawing" : "inputs")}>{result ? "View saved diagram" : context.drawingReferences.length && !blocked ? "Inspect drawing sources" : "Review required inputs"}</button>
    <p className="text-xs text-muted-foreground">Numerical verification is not structural design approval.{blocked && " Shear transfer and connection capacity remain unsupported where stated."}</p>
  </section>;
}
