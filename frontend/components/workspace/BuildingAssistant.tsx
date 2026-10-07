"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { CheckCheck, Loader2, Sparkles, X } from "lucide-react";
import { api, formatApiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Plan = {
  id: number; parent_id: number | null; prompt: string; stale: boolean;
  base_revision_id: number | null; job_id: string | null; scenario_id: number | null;
  model: string; elevation_known: boolean;
  spec: {
    summary: string; floors: number; floor_height: number;
    footprint: { x: number; y: number; width: number; depth: number };
    rooms: { id: string; name: string; floor: number; x: number; y: number; width: number; depth: number }[];
    walls: { id: string; floor: number; start: [number, number]; end: [number, number]; thickness: number }[];
    openings: { id: string; kind: string; wall_id: string; offset: number; width: number; height: number; sill: number }[];
    columns: { x: number; y: number; size: number }[];
    beams: { start: [number, number]; end: [number, number]; width: number; depth: number }[];
    slab_thickness: number; foundation_width: number; foundation_depth: number; assumptions: string[];
  };
};

export default function BuildingAssistant({ projectId, boundaryKey, revisionId, dirty, generating, onStarted, onClose }: {
  projectId: number; boundaryKey: string; revisionId: number | null; dirty: boolean; generating: boolean;
  onStarted: (jobId: string, scenarioId?: number | null) => Promise<void>; onClose: () => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadedContext, setLoadedContext] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [floor, setFloor] = useState(0);
  const sequence = useRef({ version: 0 });
  const path = `/api/projects/${projectId}/ai/building-plans`;
  const contextKey = JSON.stringify([path, boundaryKey, revisionId]);
  const loading = loadedContext !== contextKey;
  useEffect(() => {
    const tracker = sequence.current;
    const seq = ++tracker.version;
    api.get<{ plans: Plan[] }>(path).then(result => {
      if (seq !== tracker.version) return;
      setPlans(result.plans);
      setPlan(current => result.plans.find(p => p.id === current?.id) ?? result.plans[0] ?? null);
      setError(null);
    }).catch(e => { if (seq === tracker.version) setError(formatApiErrorMessage(e)); })
      .finally(() => { if (seq === tracker.version) { setLoadedContext(contextKey); setBusy(false); } });
    return () => { tracker.version++; };
  }, [path, contextKey]);

  const unavailable = !boundaryKey || boundaryKey === "null" || dirty || generating || loading;
  const stale = !!plan && (plan.stale || plan.base_revision_id !== revisionId);
  const propose = async (revise: boolean) => {
    const seq = ++sequence.current.version;
    setBusy(true); setError(null);
    try {
      const next = await api.post<Plan>(revise && plan ? `${path}/${plan.id}/revisions` : path,
        { prompt: prompt.trim(), base_revision_id: revisionId });
      if (seq !== sequence.current.version) return;
      setPlan(next); setPlans(previous => [next, ...previous]); setPrompt(""); setFloor(0);
    } catch (e) { if (seq === sequence.current.version) setError(formatApiErrorMessage(e)); }
    finally { if (seq === sequence.current.version) setBusy(false); }
  };
  const build = async () => {
    if (!plan) return;
    setBusy(true); setError(null);
    try {
      const result = await api.post<{ job_id: string; scenario_id: number }>(`${path}/${plan.id}/build`, { approve: true });
      const submitted = { ...plan, job_id: result.job_id, scenario_id: result.scenario_id };
      setPlan(submitted);
      setPlans(previous => previous.map(p => p.id === plan.id ? submitted : p));
      await onStarted(result.job_id, result.scenario_id);
    } catch (e) { setError(formatApiErrorMessage(e)); }
    finally { setBusy(false); }
  };
  const spec = plan?.spec;
  const fp = spec?.footprint;
  return createPortal(<section aria-label="AI Building Assistant" className="fixed right-4 top-24 z-[80] max-h-[calc(100dvh-8rem)] w-[440px] max-w-[calc(100vw-2rem)] overflow-y-auto rounded-2xl border border-white/15 bg-background p-5 shadow-2xl">
    <header className="flex items-start justify-between gap-3">
      <div><h2 className="flex items-center gap-2 text-sm font-semibold"><Sparkles className="size-4 text-primary" />AI Building Assistant</h2><p className="mt-1 text-xs text-muted-foreground">Select your plot. Plan together. Build in 3D.</p></div>
      <Button variant="ghost" size="icon" aria-label="Close building assistant" onClick={onClose}><X className="size-4" /></Button>
    </header>
    <ol className="my-4 flex justify-between text-[11px] text-muted-foreground"><li>1 · Plot</li><li className={plan ? "text-primary" : ""}>2 · Review plan</li><li>3 · Build model</li></ol>
    {(!boundaryKey || boundaryKey === "null") && <p role="status" className="mb-3 text-xs text-amber-300">Use Site & drawing tools to draw and save a plot boundary first.</p>}
    {dirty && <p role="status" className="mb-3 text-xs text-amber-300">Save your model edits before creating or approving a plan.</p>}
    {generating && <p role="status" className="mb-3 text-xs text-primary">Building your model. Progress appears in the workspace.</p>}
    {error && <p role="alert" className="mb-3 rounded-lg border border-red-400/30 bg-red-400/10 p-3 text-xs">{error}</p>}
    {loading && <p role="status" className="text-xs">Loading saved plans…</p>}
    {!!plans.length && <label className="block text-xs">Saved proposals<select aria-label="Saved proposals" className="my-2 w-full rounded-md border border-border bg-background p-2" value={plan?.id ?? ""} disabled={busy} onChange={e => { setPlan(plans.find(p => p.id === Number(e.target.value)) ?? null); setFloor(0); }}>
      {plans.map(p => <option key={p.id} value={p.id}>Plan {p.id}{p.job_id ? " · Built / submitted" : " · Review"}</option>)}
    </select></label>}
    <label htmlFor="building-request" className="mb-2 block text-xs font-medium">{plan ? "Describe a new building or request changes" : "Describe your building"}</label>
    <textarea id="building-request" value={prompt} disabled={busy} onChange={e => setPrompt(e.target.value)} maxLength={6000} rows={3} className="w-full rounded-lg border border-border bg-background-secondary p-3 text-xs" placeholder="A two-floor house with three bedrooms, a kitchen, and parking…" />
    <div className="mt-2 flex gap-2">
      <Button size="sm" variant="outline" disabled={busy || unavailable || prompt.trim().length < 5} onClick={() => propose(false)}>Create plan</Button>
      {plan && <Button size="sm" variant="outline" disabled={busy || unavailable || prompt.trim().length < 5} onClick={() => propose(true)}>Request changes</Button>}
      {busy && <Loader2 role="status" aria-label="Working" className="size-5 animate-spin self-center text-primary" />}
    </div>
    {plan && spec && fp && <div className="mt-5 space-y-3 border-t border-border pt-4">
      <div><h3 className="text-sm font-semibold">Review plan {plan.id}</h3><p className="mt-1 text-xs leading-relaxed">{spec.summary}</p></div>
      <p className="text-xs text-muted-foreground">{spec.floors} floors · {fp.width} × {fp.depth} m footprint · {spec.floor_height} m floor height</p>
      <label className="block text-xs">Floor preview<select aria-label="Floor preview" value={floor} onChange={e => setFloor(Number(e.target.value))} className="ml-3 rounded border border-border bg-background px-2 py-1">{Array.from({ length: spec.floors }, (_, i) => <option key={i} value={i}>{i === 0 ? "Ground floor" : `Floor ${i + 1}`}</option>)}</select></label>
      <svg aria-label="Proposed floor layout" role="img" viewBox={`${fp.x-1} ${-fp.y-fp.depth-1} ${fp.width+2} ${fp.depth+2}`} className="h-52 w-full rounded-lg border border-border bg-background-secondary">
        <rect x={fp.x} y={-fp.y-fp.depth} width={fp.width} height={fp.depth} fill="none" stroke="#94a3b8" strokeWidth={0.07} />
        {spec.rooms.filter(r => r.floor === floor).map(r => <g key={r.id}><rect x={r.x} y={-r.y-r.depth} width={r.width} height={r.depth} fill="#72b99b" fillOpacity={0.15} stroke="#72b99b" strokeWidth={0.04} /><text x={r.x+r.width/2} y={-r.y-r.depth/2} textAnchor="middle" fill="currentColor" fontSize={Math.min(fp.width/30, 0.45)}>{r.name}</text></g>)}
        {spec.walls.filter(w => w.floor === floor).map(w => <line key={w.id} x1={w.start[0]} y1={-w.start[1]} x2={w.end[0]} y2={-w.end[1]} stroke="#d6d3c6" strokeWidth={w.thickness} />)}
        {spec.openings.map(o => {
          const wall = spec.walls.find(w => w.id === o.wall_id && w.floor === floor);
          if (!wall) return null;
          const length = Math.hypot(wall.end[0]-wall.start[0], wall.end[1]-wall.start[1]);
          const dx = (wall.end[0]-wall.start[0])/length, dy = (wall.end[1]-wall.start[1])/length;
          return <line key={o.id} x1={wall.start[0]+dx*o.offset} y1={-wall.start[1]-dy*o.offset} x2={wall.start[0]+dx*(o.offset+o.width)} y2={-wall.start[1]-dy*(o.offset+o.width)} stroke={o.kind === "door" ? "#daa05d" : "#78bdcf"} strokeWidth={wall.thickness*1.8} />;
        })}
        {spec.columns.map((c, i) => <rect key={i} x={c.x-c.size/2} y={-c.y-c.size/2} width={c.size} height={c.size} fill="#8eacc7" />)}
      </svg>
      <ul className="space-y-1 text-xs">{spec.rooms.filter(r => r.floor === floor).map(r => <li key={r.id}>{r.name} · {r.width} × {r.depth} m</li>)}</ul>
      <p className="text-xs text-muted-foreground">{spec.openings.length} doors / windows · {spec.columns.length} column positions · {spec.beams.length} beams per floor</p>
      <details className="text-xs"><summary className="cursor-pointer">Member dimensions and openings</summary><p className="mt-2">Slabs: {spec.slab_thickness} m. Foundations: {spec.foundation_width} m wide × {spec.foundation_depth} m deep.</p><ul className="mt-2 space-y-1">{spec.openings.map(o => <li key={o.id}>{o.kind} {o.id}: {o.width} × {o.height} m · wall {o.wall_id}</li>)}{spec.columns.map((c, i) => <li key={`column-${i}`}>Column {i+1}: {c.size} × {c.size} m at ({c.x}, {c.y}) m</li>)}{spec.beams.map((b, i) => <li key={`beam-${i}`}>Beam {i+1}: {b.width} × {b.depth} m · {Math.hypot(b.end[0]-b.start[0], b.end[1]-b.start[1]).toFixed(2)} m long</li>)}</ul></details>
      <div className="rounded-lg bg-amber-400/5 p-3 text-xs"><h4 className="font-medium">Assumptions to review</h4><ul className="mt-2 list-disc space-y-1 pl-4">{spec.assumptions.map((a, i) => <li key={i}>{a}</li>)}{!plan.elevation_known && <li>Survey elevation is unknown; the model uses a visual reference.</li>}<li>Conceptual architecture and frame. Approval here is not engineering approval.</li></ul></div>
      {stale && !plan.job_id && <p role="status" className="text-xs text-amber-300">The plot or saved model changed. Request changes to create a current plan.</p>}
      <Button className="w-full gap-2" disabled={busy || unavailable || stale || !!plan.job_id || !!prompt.trim()} onClick={build}><CheckCheck className="size-4" />{plan.job_id ? "Build submitted" : "Approve and build"}</Button>
      {!!prompt.trim() && <p className="text-xs text-muted-foreground">Submit or clear your draft request before approving this plan.</p>}
      {plan.job_id && <Button variant="outline" size="sm" onClick={() => onStarted(plan.job_id!, plan.scenario_id).catch(e => setError(formatApiErrorMessage(e)))}>Show build status</Button>}
      <p className="text-[10px] text-muted-foreground">Planned with Nebius · {plan.model}</p>
    </div>}
  </section>, document.body);
}
