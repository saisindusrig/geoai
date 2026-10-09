"use client";

import { useEffect, useState } from "react";
import {
  Bot, Check, Download, History,
  Layers3, MousePointer2, Move3D, Redo2, RotateCw, Save,
  Scale3D, Sparkles, Undo2, X, ShieldCheck, TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import SceneLayersPanel from "@/components/model-editor/SceneLayersPanel";
import ComponentIdentity from "@/components/model-editor/ComponentIdentity";
import PersistentAssistant from "@/components/workspace/PersistentAssistant";
import EmptyProjectStarter from "@/components/workspace/EmptyProjectStarter";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

import { compareDocuments } from "@/lib/revision-comparison";
import { toast, toastPromise } from "@/lib/toast";
import { cn, formatCurrency, formatQty } from "@/lib/utils";

const TABS = [
  { id: "layers", label: "Layers", icon: Layers3 },
  { id: "properties", label: "Inspect", icon: MousePointer2 },
  { id: "revisions", label: "History", icon: History },
  { id: "layout", label: "Checks", icon: ShieldCheck },
  { id: "copilot", label: "Assistant", icon: Bot },
];

export function NumberField({ label, value, onChange, step = 0.1, positive = false, disabled = false }: { label: string; value: number; onChange: (value: number) => void; step?: number; positive?: boolean; disabled?: boolean }) {
  const [draft, setDraft] = useState(String(value));
  const [error, setError] = useState<string | null>(null);
  const confirm = () => {
    const next = Number(draft);
    if (!draft.trim() || !Number.isFinite(next) || positive && next <= 0) { setError(positive ? "Enter a value greater than zero." : "Enter a finite number."); return; }
    setError(null);
    if (next !== value) onChange(next);
  };
  return <label className="space-y-1 text-[10px] text-muted-foreground"><span>{label}</span><Input aria-label={label} aria-invalid={!!error} disabled={disabled} className="h-8 px-2 font-data text-xs" type="text" inputMode="decimal" data-step={step} value={draft} onChange={event => setDraft(event.target.value)} onBlur={confirm} onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); if (event.key === "Escape") { setDraft(String(value)); setError(null); event.stopPropagation(); } }} />{error && <span role="alert" className="block text-destructive">{error}</span>}</label>;
}

function VectorEditor({ label, values, onChange, disabled, positive, names = ["X", "Y", "Z"] }: { label: string; values: [number, number, number]; onChange: (values: [number, number, number]) => void; disabled?: boolean; positive?: boolean; names?: string[] }) {
  return <div className="space-y-1.5"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</p><div className="grid grid-cols-3 gap-1.5">{names.map((axis,index) => <NumberField key={`${axis}-${values[index]}`} label={`${label} ${axis}`} value={values[index]} disabled={disabled} positive={positive} onChange={value => { const next = [...values] as [number,number,number]; next[index] = value; onChange(next); }} />)}</div></div>;
}
function PropertiesPanel({ editor }: { editor: EditableModelEditor }) {
  const component = editor.selected;
  if (!component) return <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center"><MousePointer2 className="h-7 w-7 text-primary" /><p className="text-sm font-medium">Select a component</p><p className="text-xs leading-relaxed text-muted-foreground">Pick an object on the map or choose it from Layers to edit its engineering properties.</p></div>;
  const updateTransform = (key: "position" | "rotation_deg" | "scale", value: [number, number, number]) => editor.updateComponent(component.id, { transform: { ...component.transform, [key]: value } });
  const boxGeometry = component.geometry.kind === "box" || component.geometry.kind === "extrusion" ? component.geometry : null;
  return (
    <div className="space-y-4 p-3">
      <ComponentIdentity component={component} document={editor.document} />
      <p className="text-[10px] text-muted-foreground">LOCAL ENU · Pivot {editor.pivotMode} · {editor.selectedIds.length} selected · {editor.document?.components.filter(item => editor.selectedIds.includes(item.id) && item.locked).length} locked</p>
      {component.locked && <p role="status" className="text-xs text-amber-200">OBJECT LOCKED · Unlock to edit.</p>}
      <div className="space-y-1"><p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Selected component</p><Input value={component.name} disabled={component.locked} onChange={(event) => editor.updateComponent(component.id, { name: event.target.value })} /></div>
      <div className="grid grid-cols-2 gap-2 text-[10px]"><div className="rounded-sm border border-border bg-black/15 p-2"><span className="text-muted-foreground">Category</span><p className="mt-1 font-medium">{component.category}</p></div><div className="rounded-sm border border-border bg-black/15 p-2"><span className="text-muted-foreground">Geometry</span><p className="mt-1 font-medium">{component.geometry.kind}</p></div></div>
      <VectorEditor disabled={component.locked} names={["East", "North", "Up"]} label="Position · metres" values={component.transform.position} onChange={(value) => updateTransform("position", value)} />
      <VectorEditor disabled={component.locked} label="Rotation · degrees" values={component.transform.rotation_deg} onChange={(value) => updateTransform("rotation_deg", value)} />
      <VectorEditor disabled={component.locked} positive label="Scale" values={component.transform.scale} onChange={(value) => updateTransform("scale", value)} />
      {boxGeometry && <VectorEditor disabled={component.locked} positive label="Dimensions · metres" values={boxGeometry.size} onChange={(size) => editor.updateComponent(component.id, { geometry: { ...boxGeometry, size } })} />}
      <div className="space-y-1"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Material</p><div className="flex items-center gap-2"><input type="color" className="h-9 w-12 rounded border border-border bg-transparent" value={component.material.color} onChange={(event) => editor.updateComponent(component.id, { material: { ...component.material, color: event.target.value } })} /><Input value={component.material.name} onChange={(event) => editor.updateComponent(component.id, { material: { ...component.material, name: event.target.value } })} /></div></div>
    </div>
  );
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
    try { await editor.approveLayout(); toast("Structural layout approved", { variant: "success" }); }
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
      <Button className="mt-3 w-full" size="sm" onClick={approve} disabled={working || !editor.baseRevision || editor.dirty || !validation?.passed}><ShieldCheck className="size-3.5" />{working ? "Working…" : "Engineer approve saved revision"}</Button>
    </section>
    <section className="rounded-none border border-border p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Saved layout baseline</p>
      {editor.alternatives.map((option) => <div key={option.id} className="mt-2 rounded-sm border border-border bg-black/10 p-2">
        <p className="text-xs font-medium">{option.name}</p>
        <p className="mt-1 text-[10px] text-muted-foreground">Estimated cost: {formatCurrency(option.estimated_cost ?? 0, editor.impact?.currency ?? "INR")}</p>
        <p className="mt-1 text-[10px] text-muted-foreground">Constructability and alternative ranking have not been evaluated.</p>
      </div>)}
      <Button className="mt-3 w-full" size="sm" variant="secondary" disabled={!editor.baseRevision || editor.dirty} onClick={() => {
        void editor.exportAnalysisPackage().catch((error) => toast("Analysis export blocked", { variant: "error", description: String(error) }));
      }}><Download className="size-3.5" />Export analysis package</Button>
      <p className="mt-2 text-[10px] text-muted-foreground">Engineer approval is required. Verify loads, connections and design codes in specialist software.</p>
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

export function ProfessionalModelPanel({ editor, projectId, siteGeometry }: { editor: EditableModelEditor; projectId?: number; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null }) {
  const [tab, setTabState] = useState("layers");
  useEffect(()=>{const inspect=()=>setTabState("properties");window.addEventListener("geoai:inspect-component",inspect);return()=>window.removeEventListener("geoai:inspect-component",inspect);},[]);
  useEffect(() => { const assistant = () => setTabState("copilot"); window.addEventListener("geoai:open-copilot", assistant); return () => window.removeEventListener("geoai:open-copilot", assistant); }, []);
  const setTab = (next: string) => {
    setTabState(next);
  };
  const activeTab = tab;
  return <div className="flex h-full min-h-0 flex-col bg-background-secondary">
    <div className="shrink-0 border-b border-white/10 p-3">
      <div role="tablist" aria-label="Inspector views" className="grid grid-cols-5 gap-1">{TABS.map(({ id, label, icon: Icon }) => <button key={id} role="tab" id={`inspector-tab-${id}`} aria-controls={`inspector-panel-${id}`} aria-selected={activeTab === id} onClick={() => setTab(id)} className={cn("flex min-w-0 flex-col items-center gap-1 border-b-2 border-transparent px-1 py-2 text-[10px] transition", activeTab === id ? "border-primary font-semibold text-primary" : "text-muted-foreground hover:text-foreground")}><Icon className="size-3.5" />{label}</button>)}</div>
    </div>
    <div role="tabpanel" id={`inspector-panel-${activeTab}`} aria-labelledby={`inspector-tab-${activeTab}`} className="min-h-0 flex-1 overflow-y-auto"><div className={activeTab === "layers" ? "" : "hidden"}>{editor.document ? <SceneLayersPanel editor={editor} /> : <EmptyProjectStarter projectId={projectId} active={activeTab === "layers"} hasSite={!!siteGeometry}><EmptyEditor editor={editor} /></EmptyProjectStarter>}</div>{activeTab === "properties" && <PropertiesPanel editor={editor} />}{activeTab === "revisions" && <RevisionsPanel editor={editor} />}{activeTab === "layout" && <LayoutIntelligencePanel editor={editor} />}{activeTab === "copilot" && (projectId ? <PersistentAssistant key={projectId} projectId={projectId} siteGeometry={siteGeometry} selectedIds={editor.selectedIds} revisionId={editor.baseRevision?.id ?? null} dirty={editor.dirty} /> : <CopilotPanel editor={editor} />)}</div>
  </div>;
}

export function ProfessionalCadToolbar({ editor, projectId }: { editor: EditableModelEditor; projectId: number }) {
  const save = () => toastPromise(editor.save(), { loading: "Validating and saving model…", success: "Model revision saved", error: "Could not save model revision" });
  const tools = [{ id: "select", icon: MousePointer2, label: "Select" }, { id: "translate", icon: Move3D, label: "Move" }, { id: "rotate", icon: RotateCw, label: "Rotate" }, { id: "scale", icon: Scale3D, label: "Scale" }] as const;
  return <div className="flex w-full items-center gap-1 overflow-x-auto py-0.5"><div className="flex items-center gap-1 rounded-none border border-border bg-black/20 p-1">{tools.map(({ id, icon: Icon, label }) => <Button key={id} variant={editor.tool === id ? "accent" : "ghost"} size="sm" className="h-8 px-2" onClick={() => editor.setTool(id)} title={label}><Icon className="h-3.5 w-3.5" /><span className="hidden xl:inline">{label}</span></Button>)}</div><div className="mx-1 h-6 w-px bg-border" /><Button variant="ghost" size="icon" className="h-8 w-8" onClick={editor.undo} disabled={!editor.canUndo} title="Undo"><Undo2 className="h-4 w-4" /></Button><Button variant="ghost" size="icon" className="h-8 w-8" onClick={editor.redo} disabled={!editor.canRedo} title="Redo"><Redo2 className="h-4 w-4" /></Button><div className="mx-1 h-6 w-px bg-border" />{editor.selectedIds.length > 0 && <><div className="flex items-center gap-1 rounded-none border border-border bg-black/20 p-1"><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(0, -editor.snapMeters)}>X−</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(0, editor.snapMeters)}>X+</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(1, -editor.snapMeters)}>Y−</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(1, editor.snapMeters)}>Y+</Button><Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.nudgeSelected(2, editor.snapMeters)}>Z+</Button>{editor.tool === "rotate" && <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.transformSelected("rotate", 15)}>15°</Button>}{editor.tool === "scale" && <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => editor.transformSelected("scale", 1.1)}>110%</Button>}</div></>}<label className="ml-auto flex items-center gap-1.5 text-[10px] text-muted-foreground">Snap<Input className="h-8 w-16 px-2 text-xs" type="number" min={0.01} step={0.1} value={editor.snapMeters} onChange={(event) => editor.setSnapMeters(Math.max(0.01, Number(event.target.value)))} />m</label><Button variant="secondary" size="sm" className="h-8" onClick={() => window.open(`/api/projects/${projectId}/exports/model.glb${editor.baseRevision ? `?revision_id=${editor.baseRevision.id}` : ""}`, "_blank")} disabled={!editor.baseRevision}><Download className="h-3.5 w-3.5" />Export</Button><Button size="sm" className="h-8" onClick={save} disabled={!editor.dirty || editor.saving || !editor.canPersist}><Save className="h-3.5 w-3.5" />{editor.saving ? "Saving…" : "Save revision"}</Button></div>;
}


