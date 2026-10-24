"use client";
import {useWorkspaceAssistant} from "@/hooks/useWorkspaceAssistant";
import { DownloadButton } from "@/components/ui/download-button";
import RCFlexurePanel from "./RCFlexurePanel";
import FoundationSystemPanel from "./FoundationSystemPanel";
import SecondaryAnalysisTools from "./SecondaryAnalysisTools";
import StructuralVisualPanel from "./StructuralVisualPanel";
import SpatialVisualPanel from "./SpatialVisualPanel";
import CoupledFloorPanel from "./CoupledFloorPanel";
import GuidedAnalysisWorkflow from "./GuidedAnalysisWorkflow";
import FootingFlexurePanel from "./FootingFlexurePanel";
import RectangularBearingPanel from "./RectangularBearingPanel";
import AnalysisOverview from "./AnalysisOverview";
import BearingCapacityPanel from "@/components/model-editor/BearingCapacityPanel";
import SoilProfilePanel from "@/components/model-editor/SoilProfilePanel";
import SoilContactPanel from "@/components/model-editor/SoilContactPanel";
import FootingTransportPanel from "@/components/model-editor/FootingTransportPanel";
import CadSoilPanel from "@/components/model-editor/CadSoilPanel";

import { useEffect, useRef, useState } from "react";
import {
  Bot, Check, Download, History,
  Layers3, MousePointer2, Move3D, Redo2, RotateCw, Save,
  Scale3D, Sparkles, Undo2, X, ShieldCheck, TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import SceneLayersPanel from "@/components/model-editor/SceneLayersPanel";
import PlatformAttachmentsPanel from "@/components/model-editor/PlatformAttachmentsPanel";
import OpenSeesBenchmarkPanel from "@/components/model-editor/OpenSeesBenchmarkPanel";
import PhysicalColumnAnalysisPanel from "@/components/model-editor/PhysicalColumnAnalysisPanel";
import CadFrameAuditPanel from '@/components/model-editor/CadFrameAuditPanel';
import DrawingCadPanel from '@/components/model-editor/DrawingCadPanel';
import EngineeringStudyPanel from "@/components/model-editor/EngineeringStudyPanel";
import ConnectionInputsPanel from "@/components/model-editor/ConnectionInputsPanel";
import AnchorContact3DPanel from "@/components/model-editor/AnchorContact3DPanel";
import AnchorContactPanel from "@/components/model-editor/AnchorContactPanel";
import FoundationInterfacePanel from "@/components/model-editor/FoundationInterfacePanel";
import SlabTransferPanel from "@/components/model-editor/SlabTransferPanel";
import PhysicalFramePanel from "@/components/model-editor/PhysicalFramePanel";
import ElasticFramePanel from "@/components/model-editor/ElasticFramePanel";
import { componentDisplayName, componentRole } from "@/lib/component-presentation";
import { displayMaterial } from "@/lib/display-material";
import { componentEditPatch } from "@/lib/component-edit";
import type { EditableModelComponent } from "@/lib/types";
import { attachmentOf } from "@/lib/platform-attachments";
import PlatformParametersPanel from "@/components/model-editor/PlatformParametersPanel";
import ComponentIdentity from "@/components/model-editor/ComponentIdentity";
import ExperimentalCadReview from "@/components/model-editor/ExperimentalCadReview";
import PersistentAssistant from "@/components/workspace/PersistentAssistant";
import { publishAssistantContext, type ToolResult } from "@/lib/site-assistant";
import EmptyProjectStarter from "@/components/workspace/EmptyProjectStarter";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

import { compareDocuments } from "@/lib/revision-comparison";
import { toast, toastPromise } from "@/lib/toast";
import { cn, formatCurrency, formatQty } from "@/lib/utils";

const TABS = [
  { id: "layers", label: "Layers", icon: Layers3 },
  { id: "properties", label: "Inspect", icon: MousePointer2 },
  { id: "revisions", label: "History", icon: History },
  { id: "analysis", label: "Analysis", icon: ShieldCheck },
  { id: "layout", label: "Review", icon: ShieldCheck },
  { id: "copilot", label: "Assistant", icon: Bot },
];

export function NumberField({ label, value, onChange, step = 0.1, positive = false, disabled = false }: { label: string; value: number; onChange: (value: number) => void; step?: number; positive?: boolean; disabled?: boolean }) {
  const displayValue = (v:number) => Number(v.toFixed(6)).toString();
  const [draft, setDraft] = useState(displayValue(value));
  const [touched,setTouched]=useState(false);
  const [error, setError] = useState<string | null>(null);
  const confirm = () => {
    if(!touched)return;
    const next = Number(draft);
    if (!draft.trim() || !Number.isFinite(next) || positive && next <= 0) { setError(positive ? "Enter a value greater than zero." : "Enter a finite number."); return; }
    setError(null);
    setTouched(false);
    if (next !== value) onChange(next);
  };
  return <label className="space-y-1 text-[10px] text-muted-foreground"><span>{label}</span><Input aria-label={label} aria-invalid={!!error} disabled={disabled} className="h-8 px-2 font-data text-xs" type="text" inputMode="decimal" data-step={step} value={draft} onChange={event => {setTouched(true);setDraft(event.target.value);}} onBlur={confirm} onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); if (event.key === "Escape") { setDraft(displayValue(value)); setTouched(false); setError(null); event.stopPropagation(); } }} />{error && <span role="alert" className="block text-destructive">{error}</span>}</label>;
}

function VectorEditor({ label, values, onChange, disabled, positive, names = ["X", "Y", "Z"] }: { label: string; values: [number, number, number]; onChange: (values: [number, number, number]) => void; disabled?: boolean; positive?: boolean; names?: string[] }) {
  return <div className="space-y-1.5"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</p><div className="grid grid-cols-3 gap-1.5">{names.map((axis,index) => <NumberField key={`${axis}-${values[index]}`} label={`${label} ${axis}`} value={values[index]} disabled={disabled} positive={positive} onChange={value => { const next = [...values] as [number,number,number]; next[index] = value; onChange(next); }} />)}</div></div>;
}
export function PropertiesPanel({ editor }: { editor: EditableModelEditor }) {
  const component = editor.selected;
  if (!component) return <div className="space-y-3 p-4"><p>Select a component</p><p className="text-xs text-muted-foreground">Click a member in the viewport or choose it from Layers.</p><Button size="sm" variant="secondary" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:layer-action",{detail:"restore"}))}>Restore visibility</Button></div>;
  if (attachmentOf(component)) return <div className="space-y-3 p-3"><p className="text-xs">{componentDisplayName(component)}</p><p className="text-xs text-muted-foreground">Open Assembly tools and parameters above, then Edit selected attachment. Generated parts move with their assembly; individual edits would disconnect it.</p><details><summary>Identity and source references</summary><ComponentIdentity component={component} document={editor.document} /></details></div>;
  return <ComponentEditForm key={JSON.stringify(component)} component={component} editor={editor} />;
}

function ComponentEditForm({component, editor}: {component: EditableModelComponent; editor: EditableModelEditor}) {
  const [draft, setDraft] = useState(() => structuredClone(component));
  const [previewing, setPreviewing] = useState(false);
  const [resetVersion,setResetVersion]=useState(0);
  const [formError,setFormError]=useState<string|null>(null);
  const fieldsValid=(button:HTMLButtonElement)=>{const invalid=button.closest('[aria-label="Component edit form"]')?.querySelector('[aria-invalid="true"]');setFormError(invalid ? "Correct the invalid fields before Preview or Apply, or Cancel to discard pending values." : null);return !invalid;};
  const patch = componentEditPatch(component, draft);
  const changed = Object.keys(patch).length > 0;
  const disabled = component.locked || !!editor.comparison || !!editor.platformPreview;
  const cad = component.geometry.kind === "cad_mesh";
  useEffect(() => () => { window.dispatchEvent(new CustomEvent("geoai:component-preview", {detail:null})); }, []);
  useEffect(() => {
    const receive = (event: Event) => {
      const proposal = (event as CustomEvent<ToolResult>).detail;
      if (proposal.componentId !== component.id || proposal.revisionId !== editor.baseRevision?.id || editor.dirty || disabled || JSON.stringify(component.transform.position) !== JSON.stringify(proposal.before) || !proposal.after || proposal.after.length !== 3 || !proposal.after.every(v => Number.isFinite(v) && Math.abs(v) <= 100000)) return;
      const candidate = structuredClone(component);
      candidate.transform.position = proposal.after as [number, number, number];
      setDraft(candidate); setPreviewing(true);
      window.dispatchEvent(new CustomEvent("geoai:component-preview", { detail: candidate }));
      window.dispatchEvent(new CustomEvent("geoai:assistant-preview-status", { detail: "Visual preview shown. Review in 3D, then explicitly Apply and Save model in the editor. No model has been saved." }));
    };
    window.addEventListener("geoai:assistant-preview-ready", receive);
    return () => window.removeEventListener("geoai:assistant-preview-ready", receive);
  }, [component, editor, disabled]);
  useEffect(() => {
    const cancel = (event: Event) => {
      if (!previewing || (event as CustomEvent<ToolResult>).detail?.componentId !== component.id) return;
      setDraft(structuredClone(component)); setPreviewing(false); setFormError(null);
      window.dispatchEvent(new CustomEvent("geoai:component-preview", {detail:null}));
    };
    window.addEventListener("geoai:assistant-preview-cancel", cancel);
    return () => window.removeEventListener("geoai:assistant-preview-cancel", cancel);
  }, [component, previewing]);
  const update = (value: Partial<EditableModelComponent>) => {
    setDraft(current => ({...current, ...value}));
    setPreviewing(false);
    window.dispatchEvent(new CustomEvent("geoai:component-preview", {detail:null}));
  };
  const updateTransform = (key: "position" | "rotation_deg" | "scale", value: [number,number,number]) => update({transform:{...draft.transform,[key]:value}});
  const box = draft.geometry.kind === "box" || draft.geometry.kind === "extrusion" ? draft.geometry : null;
  const clearPreview = () => {setPreviewing(false);window.dispatchEvent(new CustomEvent("geoai:component-preview", {detail:null}));};
  return <div key={resetVersion} className="space-y-4 p-3" aria-label="Component edit form">
    <h3 className="text-sm font-semibold">Edit component</h3>{editor.selectedIds?.length > 1 && <p className="text-xs text-muted-foreground">Fields edit {componentDisplayName(component)} only. Viewport transform tools move the selected group.</p>}
    <p className="text-xs text-muted-foreground">Local axes: East / North / Up · metres. Changes remain pending until Apply, then Save model.</p>
    {disabled && <p role="status" className="text-xs text-amber-200">Editing unavailable while locked or reviewing a preview.</p>}
    {cad && <p className="text-xs text-muted-foreground">CAD source geometry is read-only. Position and rotation retain the existing authorization gates.</p>}
    <label className="block text-xs">Component name<Input aria-label="Component name" value={draft.name} disabled={disabled} onChange={e=>update({name:e.target.value})} /></label>
    {box && <VectorEditor disabled={disabled || cad} positive label="Dimensions · metres" values={box.size} onChange={size=>update({geometry:{...box,size}})} />}
    <VectorEditor disabled={disabled} names={["East","North","Up"]} label="Position · metres" values={draft.transform.position} onChange={v=>updateTransform("position",v)} />
    <VectorEditor disabled={disabled} label="Rotation · degrees" values={draft.transform.rotation_deg} onChange={v=>updateTransform("rotation_deg",v)} />
    <details><summary className="text-xs">Scale and appearance</summary><div className="mt-3 space-y-3">
      <VectorEditor disabled={disabled || cad} positive label="Scale" values={draft.transform.scale} onChange={v=>updateTransform("scale",v)} />
      <label className="block text-xs">Appearance name<Input aria-label="Appearance name" disabled={disabled || cad} value={draft.material.name} onChange={e=>update({material:{...draft.material,name:e.target.value}})} /></label>
      <label className="flex items-center gap-2 text-xs">Appearance color<input aria-label="Appearance color" disabled={disabled || cad} type="color" value={draft.material.color} onChange={e=>update({material:{...draft.material,color:e.target.value}})} /></label>
      <p className="text-xs text-muted-foreground">Illustrative finish only. These fields do not declare strength or solver properties.</p>
    </div></details>
    {formError && <p role="alert" className="text-xs text-destructive">{formError}</p>}
    <p role="status" className="text-xs">{previewing ? "Edit preview · not applied" : changed ? "Pending changes · not applied" : "No pending changes"}</p>
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="secondary" disabled={disabled || !changed} onClick={event=>{if(!fieldsValid(event.currentTarget))return;window.dispatchEvent(new CustomEvent("geoai:component-preview",{detail:draft}));setPreviewing(true);}}>Preview</Button>
      <Button size="sm" disabled={disabled || !changed} onClick={event=>{if(!fieldsValid(event.currentTarget))return;clearPreview();editor.updateComponent(component.id,patch);}}>Apply</Button>
      <Button size="sm" variant="secondary" disabled={disabled} onClick={()=>{clearPreview();setFormError(null);setResetVersion(v=>v+1);setDraft(structuredClone(component));}}>Cancel</Button>
    </div>
    <details><summary className="text-xs">Identity and source references</summary><ComponentIdentity component={component} document={editor.document} /></details>
  </div>;
}

function EmptyEditor({ editor }: { editor: EditableModelEditor }) {
  return <div className="space-y-3 p-3"><div className="rounded-sm border border-primary/20 bg-primary/5 p-3"><div className="flex items-center gap-2"><Layers3 className="h-4 w-4 text-primary" /><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-primary">Reference model</p></div><p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">This model contains visual geometry only. Generate a design to unlock component selection, semantic layers, and editable engineering elements.</p>{editor.loading && <span className="mt-2 block text-[10px] text-muted-foreground">Loading model document…</span>}</div><p className="px-1 text-[11px] leading-relaxed text-muted-foreground">Use the map controls to inspect terrain and project context in the meantime.</p></div>;
}

function RevisionsPanel({ editor }: { editor: EditableModelEditor }) {
  const [older,setOlder]=useState(editor.revisions[1]?.id ?? editor.baseRevision?.id ?? 0);
  const [newer,setNewer]=useState(editor.baseRevision?.id ?? 0);
  const [error,setError]=useState<string|null>(null),[busy,setBusy]=useState(false);
  const compare=async()=>{
    setBusy(true);setError(null);
    try {const [previous,current]=await Promise.all([editor.revisionDocument(older),editor.revisionDocument(newer)]);editor.setComparison({previous,current,mode:"overlay"});}
    catch(reason){setError(String(reason));}finally{setBusy(false);}
  };
  const differences=editor.comparison ? compareDocuments(editor.comparison.previous,editor.comparison.current) : [];
  return <div className="space-y-3 p-3">
    <p className="text-[11px] text-muted-foreground">Compare immutable revisions. Restore geometry is a separate, reversible edit.</p>
    {error && <p role="alert" className="text-xs text-amber-200">{error}</p>}
    <div className="grid grid-cols-2 gap-2">{([["Revision A",older,setOlder],["Revision B",newer,setNewer]] as const).map(([label,value,set])=><label key={label} className="text-[10px]">{label}<select aria-label={label} className="mt-1 h-8 w-full border border-border bg-background" value={value} onChange={event=>set(Number(event.target.value))}>{editor.revisions.map(revision=><option key={revision.id} value={revision.id}>v{revision.revision_number}</option>)}</select></label>)}</div>
    <Button size="sm" disabled={busy || !older || !newer} onClick={()=>void compare()}>Compare</Button>
    {editor.comparison && <><div className="flex gap-2">{(["previous","current","overlay"] as const).map(mode=><button key={mode} aria-pressed={editor.comparison?.mode===mode} className="text-[10px] capitalize text-primary" onClick={()=>editor.setComparison({...editor.comparison!,mode})}>{mode}</button>)}<button className="ml-auto text-[10px]" onClick={()=>editor.setComparison(null)}>Close compare</button></div><p className="text-[10px] text-muted-foreground">{differences.filter(item=>item.status==="ADDED").length} added · {differences.filter(item=>item.status==="REMOVED").length} removed · {differences.filter(item=>item.status==="MODIFIED").length} modified</p>{differences.filter(item=>item.status!=="UNCHANGED").map(item=><button key={item.id} className="block w-full border-b border-white/10 py-2 text-left text-[10px]" onClick={()=>editor.select(item.id)}>{item.name} · {item.status}{item.position && <span className="mt-1 block text-muted-foreground">Δ East {item.position[0].toFixed(3)} · North {item.position[1].toFixed(3)} · Up {item.position[2].toFixed(3)} m · Heading {item.heading?.toFixed(2)}° · Scale {item.scale?.map(value=>value.toFixed(3)).join(" / ")}{item.geometryChanged && " · GEOMETRY CHANGED"}</span>}</button>)}</>}
    {editor.revisions.map(revision=><div key={revision.id} className="border-l border-white/15 py-2 pl-3"><p className="text-xs">v{revision.revision_number} · {revision.source.replaceAll("_"," ")}</p><p className="mt-1 text-[10px] text-muted-foreground">{new Date(revision.created_at).toLocaleString()}</p><button className="mt-1 text-[10px] text-primary" onClick={()=>{setOlder(revision.id);}}>Use as previous</button><button className="ml-3 text-[10px] text-muted-foreground" disabled={busy} onClick={()=>{setBusy(true);void editor.revisionDocument(revision.id).then(document=>{editor.setComparison(null);editor.commit(document);}).catch(reason=>setError(String(reason))).finally(()=>setBusy(false));}}>Restore geometry</button></div>)}
    {!editor.revisions.length && <p className="text-xs text-muted-foreground">Save a revision to begin history.</p>}
  </div>;
}
function CopilotPanel({ editor }: { editor: EditableModelEditor }) {
  const [prompt, setPrompt] = useState("");
  const [working, setWorking] = useState(false);
  const run = async () => {
    if (!prompt.trim()) return;
    setWorking(true);
    try { await editor.previewAiEdit(prompt); } catch (error) { toast("AI edit preview failed", { variant: "error", description: String(error) }); } finally { setWorking(false); }
  };
  return <div className="flex h-full flex-col"><div className="flex-1 space-y-3 overflow-y-auto p-3"><div className="rounded-none border border-primary/25 bg-primary/5 p-3"><div className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-primary" /><p className="text-xs font-semibold">Engineering Assistant</p></div><p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">Review project evidence and checks, or prepare a semantic design proposal. Only Apply changes geometry.</p><div className="mt-3 flex flex-wrap gap-2"><button className="text-[10px] text-primary" onClick={()=>{void editor.validateDraft().catch(error=>toast("Checks failed",{variant:"error",description:String(error)}));}}>Check maximum supplied grade</button><button className="text-[10px] text-primary" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:open-dock",{detail:"PROFILE"}))}>Create terrain profile</button><button className="text-[10px] text-primary" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:open-dock",{detail:"VALIDATION"}))}>Check bridge clearances</button><button className="text-[10px] text-primary" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:open-site-data"))}>Inspect survey readiness</button><button className="text-[10px] text-primary" onClick={()=>setPrompt("Reduce pier count while keeping span below 45 m")}>Reduce pier count</button></div>{editor.layoutValidation?.violations.map((issue,index)=><p key={index} className="mt-2 text-[10px] text-amber-200">{issue.message} · {issue.action}</p>)}</div>{editor.aiPreview && <div className="rounded-none border border-accent/35 bg-accent/5 p-3"><p className="text-xs font-semibold">Proposal ready</p>{editor.aiPreview.patch.map(patch=><p key={patch.component_id} className="mt-1 text-[10px]">{editor.document?.components.find(component=>component.id===patch.component_id)?.name ?? patch.component_id} · {Object.keys(patch.changes).join(", ")}</p>)}{editor.aiPreview.warnings.map((warning,index)=><p key={index} className="mt-1 text-[10px] text-amber-200">{warning}</p>)}<p className="mt-1 text-[11px] text-muted-foreground">{editor.aiPreview.patch.length} component change{editor.aiPreview.patch.length === 1 ? "" : "s"} · save required after acceptance</p>{editor.aiPreview.validation_errors.length > 0 && <p className="mt-2 text-[10px] text-destructive">{editor.aiPreview.validation_errors.join(" · ")}</p>}<div className="mt-3 grid grid-cols-2 gap-2"><Button size="sm" onClick={editor.acceptAiPreview} disabled={editor.aiPreview.validation_errors.length > 0 || !editor.aiPreview.patch.length || editor.dirty}><Check className="h-3.5 w-3.5" />Apply proposal</Button><Button size="sm" variant="secondary" onClick={editor.rejectAiPreview}><X className="h-3.5 w-3.5" />Cancel</Button></div></div>}{editor.impact && <div className="grid grid-cols-2 gap-2"><div className="rounded-sm border border-border p-2"><p className="text-[9px] uppercase text-muted-foreground">Estimated cost</p><p className="mt-1 font-data text-xs">{formatCurrency(editor.impact.total_cost_estimate, editor.impact.currency)}</p></div><div className="rounded-sm border border-border p-2"><p className="text-[9px] uppercase text-muted-foreground">Concrete</p><p className="mt-1 font-data text-xs">{formatQty(editor.impact.quantities.concrete_m3, "m³")}</p></div></div>}</div><div className="border-t border-border p-3"><textarea className="min-h-20 w-full resize-none rounded-none border border-border bg-background p-3 text-xs outline-none focus:border-primary" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Describe an engineering edit to review…" /><Button className="mt-2 w-full" size="sm" onClick={run} disabled={working || !editor.baseRevision || editor.dirty}><Bot className="h-3.5 w-3.5" />{working ? "Preparing preview…" : "Prepare proposal"}</Button></div></div>;
}

function LayoutIntelligencePanel({ editor }: { editor: EditableModelEditor }) {
  const [reviewed,setReviewed]=useState<string[]>([]);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadIntelligence = editor.loadLayoutIntelligence;
  useEffect(() => {
    let cancelled = false;
    void loadIntelligence().catch((reason) => { if (!cancelled) setError(String(reason)); });
    return () => { cancelled = true; };
  }, [loadIntelligence]);
  const validation = editor.layoutValidation;
  const approve = async () => {
    setWorking(true);
    try { await editor.approveLayout(); toast("Geometry review recorded", { variant: "success" }); }
    catch (error) { toast("Approval blocked", { variant: "error", description: String(error) }); }
    finally { setWorking(false); }
  };
  const checkDraft = async () => {
    setWorking(true);
    setError(null);
    try { await editor.validateDraft(); }
    catch (reason) { setError(String(reason)); }
    finally { setWorking(false); }
  };
  if (!editor.document) return <div className="p-4 text-xs text-muted-foreground">Generate or open a layout to configure project rules.</div>;
  return <div className="space-y-3 p-3">
    {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
    <section className="space-y-2 border border-border p-3" aria-label="Project rule values">
      <p className="text-xs font-semibold">Project rule values</p>
      <p className="text-[11px] leading-relaxed text-muted-foreground">Geometry screening only. Loads, stresses, deflection, foundations, connections and code compliance are not analyzed here.</p>
      {([
        ["min_member_spacing_m", "Support spacing · m", 1],
        ["max_slope_percent", "Maximum supplied slope · %", 12],
        ["max_dimension_m", "Maximum component dimension · m", 500],
      ] as const).map(([key, label, fallback]) => <label key={key} className="block text-[10px] text-muted-foreground">{label}
        <Input type="number" min={0} step={0.1} className="mt-1 h-8" value={editor.document?.structural_layout?.rule_preset?.[key] ?? fallback} onChange={(event) => editor.updateRulePreset(key, event.target.valueAsNumber)} />
      </label>)}
      <Button size="sm" className="w-full" disabled={working} onClick={checkDraft}>Check current draft</Button>
      <p className="text-[10px] text-muted-foreground">Preset changes are saved with the next revision. Slope checks use supplied component slope values.</p>
    </section>
    <section className={cn("rounded-none border p-3", validation?.passed ? "border-success/40 bg-success/5" : "border-warning/40 bg-warning/5")}>
      <div className="flex items-center gap-2"><ShieldCheck className="size-4 text-primary" /><p className="text-xs font-semibold">Structural rule preset</p></div>
      <p className="mt-1 text-[11px] text-muted-foreground">{validation ? (validation.passed ? "Implemented spacing, supplied-slope, and dimension checks pass." : `${validation.violations.length} blocking issue${validation.violations.length === 1 ? "" : "s"} found.`) : "Check the current draft to see rule results."}</p>
      {validation?.violations.map((item) => {const key=`${JSON.stringify(editor.document)}:${item.rule}:${item.component_id}`;return <div key={key} className="mt-2 flex gap-2 text-[10px] text-warning"><TriangleAlert className="mt-0.5 size-3.5 shrink-0" /><span><strong>WARNING · {item.message}</strong><br />{item.action}<span className="mt-1 flex gap-3"><button onClick={()=>{editor.select(item.component_id ?? null);window.dispatchEvent(new CustomEvent("geoai:locate-component",{detail:item.component_id}));}}>Locate</button><button onClick={()=>{editor.select(item.component_id ?? null);window.dispatchEvent(new CustomEvent("geoai:inspect-component"));}}>Inspect</button><button onClick={()=>setReviewed(previous=>[...previous,key])} disabled={reviewed.includes(key)}>{reviewed.includes(key)?"Reviewed in session":"Mark reviewed"}</button></span></span></div>;})}
      <Button className="mt-3 w-full" size="sm" onClick={approve} disabled={working || !editor.baseRevision || editor.dirty || !validation?.passed}><ShieldCheck className="size-3.5" />{working ? "Working…" : "Record geometry review"}</Button>
    </section>
    <section className="rounded-none border border-border p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Saved layout baseline</p>
      {editor.alternatives.map((option) => <div key={option.id} className="mt-2 rounded-sm border border-border bg-black/10 p-2">
        <p className="text-xs font-medium">{option.name}</p>
        <p className="mt-1 text-[10px] text-muted-foreground">{editor.impact && option.estimated_cost != null ? `Estimated cost: ${formatCurrency(option.estimated_cost, editor.impact.currency)}` : "Cost not evaluated for this concept."}</p>
        <p className="mt-1 text-[10px] text-muted-foreground">Constructability and alternative ranking have not been evaluated.</p>
      </div>)}
      <Button className="mt-3 w-full" size="sm" variant="secondary" disabled={!editor.baseRevision || editor.dirty} onClick={() => {
        void editor.exportAnalysisPackage().catch((error) => toast("Analysis export blocked", { variant: "error", description: String(error) }));
      }}><Download className="size-3.5" />Export analysis package</Button>
      <p className="mt-2 text-[10px] text-muted-foreground">Geometry review only. Engineering approval and design-code checks are disabled; this review cannot approve FEA, connections or foundations.</p>
    </section>
    <section className="space-y-2 border border-border p-3" aria-label="External analysis review">
      <p className="text-xs font-semibold">External analysis review</p>
      <label className="block text-[10px] text-muted-foreground">Import analysis result JSON
        <input className="mt-2 block w-full text-xs" type="file" accept=".json,application/json" disabled={!editor.baseRevision || editor.dirty || working} onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (!file) return;
          setWorking(true);
          setError(null);
          void editor.importAnalysisResults(file).catch((reason) => setError(String(reason))).finally(() => setWorking(false));
        }} />
      </label>
      <p className="text-[10px] text-muted-foreground">Results must identify this revision and its exported document hash. Imported findings are read-only.</p>
      {editor.analysisResults.map((result) => <article key={result.id} className="space-y-2 border-t border-border pt-2">
        <p className="text-xs font-semibold">{result.solver}</p><p className="text-[11px]">{result.summary}</p>
        {result.findings.map((finding, index) => <button key={index} type="button" className="block w-full text-left text-[11px] hover:text-primary" onClick={() => editor.select(finding.component_id)}>
          {finding.status.toUpperCase()} · {finding.message}
        </button>)}
      </article>)}
    </section>
  </div>;
}

function ObjectSummary({ editor }: { editor: EditableModelEditor }) {
  const c = editor.selected;
  if (!c) return null;
  const declaration=(c.metadata?.drawing_cad as {input?:{material_name?:string;material_source?:string}}|undefined)?.input;
  const dims = c.geometry.kind === "box" || c.geometry.kind === "extrusion" ? c.geometry.size.map((v,i)=>(v*c.transform.scale[i]).toFixed(3)).join(" × ")+" m" : c.geometry.kind === "cylinder" || c.geometry.kind === "sweep" ? `Radius ${c.geometry.radius_m} m` : "Source geometry · see drawing";
  return <section aria-label="Object summary" className="space-y-3 border-b border-border p-4">
    <div><h3 className="text-base font-semibold">{componentDisplayName(c)}</h3><p className="text-xs capitalize text-muted-foreground">{componentRole(c)} · {c.locked ? "Locked" : "Editable"}{editor.selectedIds.length > 1 && ` · ${editor.selectedIds.length} selected`}</p></div>
    <dl className="space-y-2 text-xs"><div><dt className="text-muted-foreground">Dimensions · metres</dt><dd>{dims}</dd></div><div><dt className="text-muted-foreground">Position · East / North / Up · m</dt><dd>{c.transform.position.map(v=>v.toFixed(3)).join(" / ")}</dd></div><div><dt className="text-muted-foreground">Orientation · X / Y / Z · degrees</dt><dd>{c.transform.rotation_deg.map(v=>v.toFixed(1)).join(" / ")}</dd></div><div><dt className="text-muted-foreground">Geometry source</dt><dd>{c.metadata?.drawing_cad ? `Reviewed CAD entity ${(c.metadata.drawing_cad as {source_entity_id?:string}).source_entity_id??'not recorded'}` : c.metadata?.parametric_attachment ? 'Parametric assembly · generated attachment' : c.metadata?.sourceObjectId ? `Generated source: ${String(c.metadata.sourceObjectId)}` : 'Saved geometry · source evidence not recorded'}</dd></div><div><dt className="text-muted-foreground">Material verification</dt><dd>Unverified · appearance is not engineering evidence{declaration?.material_name ? ' · declaration supplied, independent validation not established' : ' · engineering properties missing here'}</dd></div><div><dt className="text-muted-foreground">Stable component ID</dt><dd className="break-all">{c.id}</dd></div><div><dt className="text-muted-foreground">Appearance finish · illustrative</dt><dd>{displayMaterial(c).finish}</dd></div><div><dt className="text-muted-foreground">Declared engineering material</dt><dd>{declaration?.material_name || "Not declared in this visual component. Review Analysis inputs."}</dd></div></dl>
    {declaration?.material_source && <details><summary className="text-xs">Material declaration source</summary><p className="text-xs text-muted-foreground">{declaration.material_source}</p></details>}
    <p className="text-xs">{editor.dirty ? "Draft · unsaved" : editor.baseRevision ? `Saved v${editor.baseRevision.revision_number}` : "Needs Inputs"} · Engineering Unverified</p>
    <div className="flex flex-wrap gap-2"><Button size="sm" variant="secondary" onClick={()=>window.dispatchEvent(new Event("geoai:fit-selection"))}>Fit selection</Button><Button size="sm" variant="secondary" disabled={c.locked || !!attachmentOf(c)} onClick={()=>document.querySelector('[aria-label="Component edit form"]')?.scrollIntoView({block:"nearest"})}>Edit</Button><Button size="sm" variant="secondary" onClick={()=>window.dispatchEvent(new Event("geoai:show-analysis"))}>Existing analysis</Button>{['Isolate','Hide','Restore visibility'].map(label=><Button key={label} size="sm" variant="secondary" disabled={!!editor.comparison||!!editor.platformPreview} onClick={()=>window.dispatchEvent(new CustomEvent('geoai:layer-action',{detail:label==='Isolate'?'isolate':label==='Hide'?'hide':'restore'}))}>{label}</Button>)}</div>
    {!!c.metadata?.references && <details><summary className="text-xs">View connections / references</summary><p className="mt-2 text-xs text-muted-foreground">Assembly links only · connection capacity is not certified.</p><ComponentIdentity component={c} document={editor.document} /></details>}
  </section>;
}

export function ProfessionalModelPanel({ editor, projectId, siteGeometry, showStarter = true, separateAssistant = false, onInspectorOpenChange }: { editor: EditableModelEditor; projectId?: number; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null; showStarter?: boolean; separateAssistant?: boolean; onInspectorOpenChange?: (open: boolean) => void }) {
  const [tab, setTabState] = useState<string | null>(separateAssistant ? null : "layers");
  const [componentPreviewActive, setComponentPreviewActive] = useState(false);
  useWorkspaceAssistant(editor,projectId,componentPreviewActive);
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("geoai:inspector-view", { detail: separateAssistant ? tab : tab ?? "layers" }));
  }, [tab, separateAssistant]);
  useEffect(() => {
    const close = () => { if (separateAssistant) setTabState(null); };
    window.addEventListener("geoai:presentation", close);
    return () => window.removeEventListener("geoai:presentation", close);
  }, [separateAssistant]);
  useEffect(() => {
    const track = (event: Event) => setComponentPreviewActive(!!(event as CustomEvent).detail);
    window.addEventListener("geoai:component-preview", track);
    return () => { window.removeEventListener("geoai:component-preview", track); publishAssistantContext({ project_id: null, revision_id: null, selected_ids: [], dirty: false }); };
  }, []);
  const pendingNavigation=useRef<string|{action:string;projectId:number;revisionId:number;recordId:number;path:string}|null>(null);
  useEffect(() => {
    publishAssistantContext({ project_id: projectId ?? null, revision_id: editor.baseRevision?.id ?? null, selected_ids: editor.selectedIds, dirty: editor.dirty || componentPreviewActive || !!editor.aiPreview || !!editor.platformPreview || !!editor.comparison });
  }, [projectId, editor.baseRevision?.id, editor.selectedIds, editor.dirty, componentPreviewActive, editor.aiPreview, editor.platformPreview, editor.comparison]);
  useEffect(() => {
    const preview = async (event: Event) => {
      const proposal = (event as CustomEvent<ToolResult>).detail;
      const report = (message: string) => window.dispatchEvent(new CustomEvent("geoai:assistant-preview-status", { detail: message }));
      if (proposal.projectId !== projectId || proposal.revisionId !== editor.baseRevision?.id || editor.dirty || editor.comparison || editor.platformPreview || editor.aiPreview) { report("Preview rejected: editor state has changed. Request a fresh preview."); return; }
      const original = editor.document?.components.find(c => c.id === proposal.componentId);
      if (!original || original.locked || attachmentOf(original)) { report("Preview rejected: select an unlocked independent object."); return; }
      // Verify the server-pinned component and entire saved document before display.
      try {
        const { api } = await import("@/lib/api");
        const latest = await api.post<{ project: { documentHash: string; stale: boolean } }>("/api/assistant/context", { page: `/projects/${projectId}/workspace`, project_id: projectId, revision_id: proposal.revisionId, selected_ids: [proposal.componentId], dirty: false });
        if (latest.project.stale || latest.project.documentHash !== proposal.documentHash || JSON.stringify(original.transform.position) !== JSON.stringify(proposal.before)) { report("Preview rejected: saved source changed. Request a fresh preview."); return; }
        editor.selectMany([original.id]); setTabState("properties");
        // Wait for the existing inspector to mount; no model mutation is dispatched.
        let count = 0;
        const deliver = () => { if (document.querySelector('[aria-label="Component edit form"]')) window.dispatchEvent(new CustomEvent("geoai:assistant-preview-ready", { detail: proposal })); else if (++count < 30) window.setTimeout(deliver, 50); else report("Inspector unavailable. Open Inspect and request the preview again."); };
        window.setTimeout(deliver, 50);
      } catch { report("Saved source verification failed. Retry manually; no model change applied."); }
    };
    window.addEventListener("geoai:assistant-position-preview", preview);
    return () => window.removeEventListener("geoai:assistant-position-preview", preview);
  }, [projectId, editor]);
  useEffect(()=>{const selected=()=>{setTabState("properties");};window.addEventListener("geoai:selection-inspect",selected);return()=>window.removeEventListener("geoai:selection-inspect",selected);},[]);
  useEffect(()=>{const inspect=(event:Event)=>{
    const target=(event as CustomEvent<{projectId:number;revisionId:number;componentIds:string[]}>).detail;
    if(target){if(target.projectId!==projectId || target.revisionId!==editor.baseRevision?.id || editor.dirty || !target.componentIds.every(id=>editor.document?.components.some(c=>c.id===id)))return;editor.selectMany(target.componentIds);}
    setTabState("properties");};window.addEventListener("geoai:inspect-component",inspect);return()=>window.removeEventListener("geoai:inspect-component",inspect);},[editor,projectId]);
  useEffect(() => { const assistant = () => setTabState(separateAssistant ? null : "copilot"); window.addEventListener("geoai:open-copilot", assistant); return () => window.removeEventListener("geoai:open-copilot", assistant); }, [separateAssistant]);
  useEffect(() => {
    const layers = () => setTabState("layers"), analysis = () => setTabState("analysis"), review = () => setTabState("layout");
    window.addEventListener("geoai:show-layers", layers); window.addEventListener("geoai:show-analysis", analysis); window.addEventListener("geoai:show-review", review);
    return () => { window.removeEventListener("geoai:show-layers", layers); window.removeEventListener("geoai:show-analysis", analysis); window.removeEventListener("geoai:show-review", review); };
  }, []);
  const setTab = (next: string) => {
    setTabState(current => separateAssistant && current === next ? null : next);
  };
  useEffect(() => { onInspectorOpenChange?.(separateAssistant && tab !== null); }, [tab, separateAssistant, onInspectorOpenChange]);
  useEffect(()=>{
    let stopPending=()=>{};
    const navigate=(event:Event)=>{
      stopPending();
      const target=(event as CustomEvent<NonNullable<typeof pendingNavigation.current>>).detail;
      if(typeof target!=="string" && (target.projectId!==projectId || target.revisionId!==editor.baseRevision?.id || editor.dirty))return;
      const action=typeof target==="string" ? target : target.action;
      pendingNavigation.current=target;
      const panel=document.getElementById("inspector-panel-analysis");
      if(!panel)return;
      pendingNavigation.current=null;
      if(panel.querySelector('[aria-label="Guided Analysis"]')){
        if(typeof target==="string" && action==="inputs"){window.dispatchEvent(new CustomEvent("geoai:guided-navigation",{detail:{step:"inputs"}}));return;}
        window.dispatchEvent(new CustomEvent("geoai:guided-navigation",{detail:{advanced:true}}));
      }
      const openDestination=()=>{
        const drawing=panel.querySelector('[aria-label="Reviewed drawing to parametric 3D"]');
        if(action==="drawing" && drawing){
          for(let ancestor=drawing.parentElement;ancestor && ancestor!==panel;ancestor=ancestor.parentElement)if(ancestor instanceof HTMLDetailsElement)ancestor.open=true;
          drawing.scrollIntoView({block:"start"});return true;
        }
        const connection=panel.querySelector('[aria-label="Real connection engineering inputs"]');
        if(action==="inputs" && connection){
          if(typeof target!=="string" && !connection.querySelector("input"))return false;
          for(let ancestor=connection.parentElement;ancestor && ancestor!==panel;ancestor=ancestor.parentElement)if(ancestor instanceof HTMLDetailsElement)ancestor.open=true;
          if(typeof target!=="string")window.dispatchEvent(new CustomEvent("geoai:connection-input",{detail:target}));
          connection.scrollIntoView({block:"start"});return true;}
        const details=Array.from(panel.querySelectorAll("details"));
        const slab=details.find(d=>d.querySelector("summary")?.textContent==="Saved slab, supports and explicit engineering inputs");
        const frame=details.find(d=>d.querySelector("summary")?.textContent?.includes("Physical frame engineering inputs"));
        const frameScope=!!panel.querySelector('[aria-label="CAD frame geometry and source audit"]');
        const detail=action==="inputs" ? (frameScope?frame:slab??frame) : action==="drawing" ? details.find(d=>d.querySelector("summary")?.textContent==="Reviewed CAD geometry and source drawing") : undefined;
        if(!detail)return false;
        detail.open=true;
        for(let ancestor=detail.parentElement;ancestor && ancestor!==panel;ancestor=ancestor.parentElement)if(ancestor instanceof HTMLDetailsElement)ancestor.open=true;
        detail.scrollIntoView({block:"start"});
        return true;
      };
      // Saved forms arrive asynchronously; keep navigation until the target mounts.
      if(openDestination() || !["inputs","drawing"].includes(action))return;
      const observer=new MutationObserver(()=>{if(openDestination())stopPending();});
      const timer=window.setTimeout(()=>stopPending(),15000);
      stopPending=()=>{observer.disconnect();window.clearTimeout(timer);};
      observer.observe(panel,{childList:true,subtree:true});
    };
    window.addEventListener("geoai:copilot-inputs",navigate);
    return()=>{stopPending();window.removeEventListener("geoai:copilot-inputs",navigate);};
  },[editor.baseRevision?.id,editor.dirty,projectId]);
  const activeTab = tab ?? "layers";
  useEffect(()=>{
    if(activeTab==="analysis" && pendingNavigation.current)window.dispatchEvent(new CustomEvent("geoai:copilot-inputs",{detail:pendingNavigation.current}));
  },[activeTab]);
  useEffect(()=>{if(activeTab === "properties")document.getElementById("inspector-panel-properties")?.scrollTo({top:0});},[activeTab,editor.selected?.id]);
  useEffect(() => {window.dispatchEvent(new CustomEvent("geoai:analysis-workspace",{detail:{active:activeTab === "analysis" && tab !== null}}));return()=>{window.dispatchEvent(new CustomEvent("geoai:analysis-workspace",{detail:{active:false}}));};},[activeTab,tab]);
  useEffect(() => { if (activeTab === "copilot") window.dispatchEvent(new Event("geoai:assistant-opened")); }, [activeTab]);
  return <div className={separateAssistant ? "workspace-inspector absolute inset-y-0 right-0 z-40 flex w-full bg-background-secondary" : "flex h-full min-h-0 flex-col bg-background-secondary"}>
    <div className={separateAssistant ? (tab ? (activeTab === "analysis" ? "flex min-w-0 flex-1 min-h-0 flex-col border-l border-border shadow-xl" : "flex min-w-0 flex-1 min-h-0 flex-col border-l border-border shadow-xl") : "hidden") : "contents"}>
    <div className="shrink-0 border-b border-white/10 p-3">
      {editor.editError && <p role="alert" className="mb-2 text-xs text-destructive">{editor.editError}</p>}
      {separateAssistant && <div className="mb-2 flex items-center justify-between"><span className="text-xs font-medium">{TABS.find(item => item.id === activeTab)?.label}</span><button type="button" aria-label="Close inspector" className="p-1 text-muted-foreground" onClick={() => setTabState(null)}><X className="size-4" /></button></div>}
      {!separateAssistant && <Button size="sm" className="mb-2 w-full" disabled={!editor.dirty || editor.saving || !editor.canPersist || !!editor.platformPreview} onClick={() => { void editor.save().catch(() => undefined); }}>{editor.saving ? "Saving…" : "Save 3D model revision"}</Button>}
      {editor.saveError && <p role="alert" className="text-xs text-destructive">{editor.saveError} · Model draft retained; retry saving.</p>}
      <ExperimentalCadReview editor={editor} projectId={projectId} />{!separateAssistant && (<div role="tablist" aria-label="Inspector views" className="grid grid-cols-6 gap-1">{TABS.map(({ id, label, icon: Icon }) => <button key={id} role="tab" id={`inspector-tab-${id}`} aria-controls={`inspector-panel-${id}`} aria-selected={activeTab === id} onClick={() => setTab(id)} className={cn("flex min-w-0 flex-col items-center gap-1 border-b-2 border-transparent px-1 py-2 text-[10px] transition", activeTab === id ? "border-primary font-semibold text-primary" : "text-muted-foreground hover:text-foreground")}><Icon className="size-3.5" />{label}</button>)}</div>)}
    </div>
    <div role="tabpanel" id={`inspector-panel-${activeTab}`} aria-labelledby={`inspector-tab-${activeTab}`} className={`min-h-0 flex-1 ${activeTab === "copilot" ? "overflow-hidden" : "overflow-y-auto"}`}><div className={activeTab === "layers" ? "" : "hidden"}>{editor.document ? <SceneLayersPanel editor={editor} /> : <EmptyProjectStarter projectId={projectId} active={showStarter && activeTab === "layers"} hasSite={!!siteGeometry}><EmptyEditor editor={editor} /></EmptyProjectStarter>}</div>{activeTab === "properties" && <><ObjectSummary editor={editor} /><details className="px-3"><summary>Assembly tools and parameters</summary><PlatformAttachmentsPanel editor={editor} /><PlatformParametersPanel editor={editor} /></details><PropertiesPanel editor={editor} /></>}{activeTab === "revisions" && <RevisionsPanel editor={editor} />}{activeTab === "analysis" && projectId && <GuidedAnalysisWorkflow key={`${projectId}:${editor.baseRevision?.id}`} editor={editor} projectId={projectId}>{editor.document?.metadata?.foundation_system?<details><summary>Whole-structure evidence and unsupported transfers</summary><StructuralVisualPanel editor={editor} projectId={projectId}/></details>:editor.document?.metadata?.coupled_floor_review?<CoupledFloorPanel editor={editor} projectId={projectId}/>:editor.document?.metadata?.spatial_frame_review?<SpatialVisualPanel editor={editor} projectId={projectId}/>:<StructuralVisualPanel editor={editor} projectId={projectId}/>}{!editor.document?.metadata?.foundation_system&&<details><summary>Analysis overview and input guidance</summary><AnalysisOverview editor={editor} projectId={projectId}/></details>}{(projectId===804||!!editor.document?.metadata?.foundation_system)&&<FoundationSystemPanel editor={editor} projectId={projectId}/>}<SecondaryAnalysisTools lazy foundation={!!editor.document?.metadata?.foundation_system}>{!!editor.baseRevision && !editor.document?.metadata?.drawing_review && <details><summary>Import and review a drawing reference</summary><EngineeringStudyPanel editor={editor} projectId={projectId} track="drawing" /></details>}{!!editor.document?.metadata?.rc_flexure_review&&!editor.document?.metadata?.foundation_system&&<RCFlexurePanel editor={editor} projectId={projectId}/>} {!!editor.document?.metadata?.footing_flexure_review&&<FootingFlexurePanel editor={editor} projectId={projectId}/>} {editor.document?.metadata?.finite_bearing_review?<><RectangularBearingPanel editor={editor} projectId={projectId}/><details><summary>Existing infinite-strip benchmark</summary><BearingCapacityPanel editor={editor} projectId={projectId}/></details></>:!!editor.document?.metadata?.bearing_capacity_review&&<BearingCapacityPanel editor={editor} projectId={projectId} />}{!!editor.document?.metadata?.soil_profile_review&&<SoilProfilePanel editor={editor} projectId={projectId} />}{!!editor.document?.metadata?.soil_contact_review&&<SoilContactPanel editor={editor} projectId={projectId} />}{!!editor.document?.metadata?.footing_transport_review&&<FootingTransportPanel editor={editor} projectId={projectId} />}{!!editor.document?.metadata?.cad_soil_path_review&&<CadSoilPanel editor={editor} projectId={projectId} />}<p className="mb-3 text-xs text-muted-foreground">Open saved results below to inspect diagrams. Numerical verification covers only the stated model; material grades, connection capacity and design approval require their own evidence.</p><div className="mb-3 flex flex-wrap gap-2">{[["Slab transfer and saved results",!editor.document?.metadata?.cad_slab_path_review],["Frame analysis and saved results",!editor.document?.metadata?.cad_frame_review]].filter(([,available])=>available).map(([label])=><button key={String(label)} className="rounded border border-border px-2 py-1 text-xs text-primary" onClick={event=>{const panel=event.currentTarget.closest('[role="tabpanel"]');for(const detail of panel?.querySelectorAll("details")??[]){if(["Analysis tasks and saved results",label].includes(detail.querySelector("summary")?.textContent??""))detail.open=true;}Array.from(panel?.querySelectorAll("summary")??[]).find(s=>s.textContent===label)?.scrollIntoView({block:"start"});}}>{String(label).replace(" and saved results"," results")}</button>)}</div>{!!editor.document?.metadata?.drawing_review&&<><>{editor.document?.metadata?.cad_frame_review?<>{!!editor.document?.metadata?.cad_slab_path_review&&<SlabTransferPanel editor={editor} projectId={projectId} />}<CadFrameAuditPanel editor={editor} projectId={projectId} /><PhysicalFramePanel editor={editor} projectId={projectId} /><details><summary>Reviewed CAD geometry and source drawing</summary><DrawingCadPanel editor={editor} projectId={projectId} /></details></>:<DrawingCadPanel editor={editor} projectId={projectId} />}</><details className="mt-4"><summary>Original drawing import and engineer corrections</summary><EngineeringStudyPanel editor={editor} projectId={projectId} track="drawing" /></details></>}{!!editor.document?.metadata?.engineering_method_review&&<EngineeringStudyPanel editor={editor} projectId={projectId} track="strength" />}{!!editor.document?.metadata?.real_engineering_input_review&&<ConnectionInputsPanel editor={editor} projectId={projectId} />}<details><summary className="mb-3 cursor-pointer text-sm">Analysis tasks and saved results</summary>{!!editor.document?.metadata?.anchor_contact_3d_review&&<AnchorContact3DPanel editor={editor} projectId={projectId} />}{!!editor.document?.metadata?.anchor_contact_review&&<AnchorContactPanel editor={editor} projectId={projectId} />}<details><summary>Foundation inputs and contact evidence</summary><FoundationInterfacePanel editor={editor} projectId={projectId} /></details>{!editor.document?.metadata?.cad_slab_path_review&&<details><summary>Slab transfer and saved results</summary><SlabTransferPanel editor={editor} projectId={projectId} /></details>}{!editor.document?.metadata?.cad_frame_review&&<details><summary>Frame analysis and saved results</summary><PhysicalFramePanel editor={editor} projectId={projectId} /></details>}</details></SecondaryAnalysisTools></GuidedAnalysisWorkflow>}{activeTab === "layout" && <><details className="p-3 pb-0"><summary>Advanced numerical verification tools</summary>{projectId && <><button className="mb-3 text-primary" onClick={()=>setTab("analysis")}>Open Engineering Analysis</button><ElasticFramePanel editor={editor} projectId={projectId} /><PhysicalColumnAnalysisPanel editor={editor} projectId={projectId} /><div className="mt-3"><OpenSeesBenchmarkPanel editor={editor} projectId={projectId} /></div></>}</details><LayoutIntelligencePanel editor={editor} /></>}{activeTab === "copilot" && (projectId ? <PersistentAssistant key={projectId} projectId={projectId} siteGeometry={siteGeometry} selectedIds={editor.selectedIds} revisionId={editor.baseRevision?.id ?? null} dirty={editor.dirty || !!editor.platformPreview || !!editor.aiPreview || !!editor.comparison} /> : <CopilotPanel editor={editor} />)}</div>
    </div>
    {separateAssistant && <div role="tablist" aria-label="Inspector views" aria-orientation="vertical" onKeyDown={event => {
      const items = TABS.filter(item => item.id !== "copilot");
      const index = items.findIndex(item => `inspector-tab-${item.id}` === (event.target as HTMLElement).id);
      if (index < 0 || !["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? items.length - 1 : (index + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      setTabState(items[next].id);
      document.getElementById(`inspector-tab-${items[next].id}`)?.focus();
    }} className="flex h-full w-11 shrink-0 flex-col items-center gap-1 border-l border-border bg-background py-3">
      {TABS.filter(item => item.id !== "copilot").map(({ id, label, icon: Icon }) => <button type="button" key={id} role="tab" id={`inspector-tab-${id}`} aria-controls={`inspector-panel-${id}`} aria-selected={tab === id} aria-label={label} title={label} onClick={() => setTab(id)} className={cn("flex w-9 flex-col items-center gap-2 rounded py-3 text-[10px]", tab === id ? "bg-white/10 text-foreground" : "text-muted-foreground hover:bg-white/5 hover:text-foreground")}><Icon className="size-4" /><span style={{ writingMode: "vertical-rl" }}>{label}</span></button>)}

    </div>}

  </div>;
}

export function ProfessionalAssistantPanel({ editor, projectId, siteGeometry }: { editor: EditableModelEditor; projectId: number; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null }) {
  useEffect(() => { window.dispatchEvent(new Event("geoai:assistant-opened")); }, []);
  return <div className="relative flex h-full min-h-0 flex-col"><button type="button" aria-label="Close Assistant" title="Close Assistant" className="absolute right-3 top-2 z-10 rounded p-1 text-muted-foreground hover:text-foreground" onClick={() => window.dispatchEvent(new Event("geoai:toggle-copilot"))}><X className="size-4" /></button><div role="tablist" aria-label="AI conversation" className="shrink-0 px-3 pt-2"><button type="button" role="tab" aria-selected="true" className="flex items-center gap-2 text-xs text-muted-foreground" onClick={() => window.dispatchEvent(new Event("geoai:assistant-opened"))}><Bot className="size-3.5" />Assistant</button></div><div className="min-h-0 flex-1"><PersistentAssistant projectId={projectId} siteGeometry={siteGeometry} selectedIds={editor.selectedIds} revisionId={editor.baseRevision?.id ?? null} dirty={editor.dirty || !!editor.platformPreview || !!editor.aiPreview || !!editor.comparison} /></div></div>;
}

export function ProfessionalCadToolbar({ editor, projectId }: { editor: EditableModelEditor; projectId: number }) {
  const save = () => toastPromise(editor.save(), { loading: "Validating and saving model…", success: "Model revision saved", error: "Could not save model revision" });
  const tools = [{ id: "select", icon: MousePointer2, label: "Select" }, { id: "translate", icon: Move3D, label: "Move" }, { id: "rotate", icon: RotateCw, label: "Rotate" }, { id: "scale", icon: Scale3D, label: "Scale" }] as const;
  return <div className="flex w-full items-center gap-1 overflow-x-auto py-0.5"><div className="flex items-center gap-1 rounded-none border border-border bg-black/20 p-1">{tools.map(({ id, icon: Icon, label }) => <Button key={id} variant={editor.tool === id ? "accent" : "ghost"} size="sm" className="h-8 px-2" onClick={() => editor.setTool(id)} title={label}><Icon className="h-3.5 w-3.5" /><span className="hidden xl:inline">{label}</span></Button>)}</div><div className="mx-1 h-6 w-px bg-border" /><Button variant="ghost" size="icon" className="h-8 w-8" onClick={editor.undo} disabled={!editor.canUndo} title="Undo"><Undo2 className="h-4 w-4" /></Button><Button variant="ghost" size="icon" className="h-8 w-8" onClick={editor.redo} disabled={!editor.canRedo} title="Redo"><Redo2 className="h-4 w-4" /></Button><div className="mx-1 h-6 w-px bg-border" />{editor.selectedIds.length > 0 && <><div className="flex items-center gap-1 rounded-none border border-border bg-black/20 p-1"><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(0, -editor.snapMeters)}>X−</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(0, editor.snapMeters)}>X+</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(1, -editor.snapMeters)}>Y−</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(1, editor.snapMeters)}>Y+</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(2, editor.snapMeters)}>Z+</Button>{editor.tool === "rotate" && <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.transformSelected("rotate", 15)}>15°</Button>}{editor.tool === "scale" && <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.transformSelected("scale", 1.1)}>110%</Button>}</div></>}<label className="ml-auto flex items-center gap-1.5 text-[10px] text-muted-foreground">Snap<Input className="h-8 w-16 px-2 text-xs" type="number" min={0.01} step={0.1} value={editor.snapMeters} onChange={(event) => editor.setSnapMeters(Math.max(0.01, Number(event.target.value)))} />m</label><DownloadButton variant="secondary" size="sm" className="h-8" path={`/api/projects/${projectId}/exports/model.glb${editor.baseRevision ? `?revision_id=${editor.baseRevision.id}` : ""}`} filename={`project-${projectId}-model.glb`} disabled={!editor.baseRevision}><Download className="h-3.5 w-3.5" />Export</DownloadButton><Button size="sm" className="h-8" onClick={save} disabled={!editor.dirty || editor.saving || !editor.canPersist || !!editor.platformPreview}><Save className="h-3.5 w-3.5" />{editor.saving ? "Saving…" : "Save revision"}</Button></div>;
}




