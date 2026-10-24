"use client";

import { useEffect, useState } from "react";
import { api, formatApiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

type Result = {
  run_id: string; status: string; solver_version?: string; error?: string;
  model_document_sha256: string; input_file_sha256: string; inputs_sha256: string;
  solver: { name: string; executable_sha256: string };
  inputs: { elements: number; load_factor: number; solver_units: string };
  values_si?: { column_shortening_m: number; spring_settlement_m: number; total_displacement_m: number; compression_stress_pa: number; reaction_n: number };
  nodes?: { id: number; z_m: number; displacement_m: number }[];
  elements?: { id: number; axial_force_n: number }[];
  force_residual_n?: number;
  comparisons?: Record<string, {relative_error: number; passed: boolean}>;
  verification_suite?: { status: string; cases: { status: string }[] };
};
type Analysis = { id: number; model_revision_id: number; status: string; result: Result };
const fields = [
  ["column_shortening_m", "Column shortening", 1000, "mm"],
  ["spring_settlement_m", "Spring settlement", 1000, "mm"],
  ["total_displacement_m", "Head displacement", 1000, "mm"],
  ["compression_stress_pa", "Axial compression stress", 1e-6, "MPa"],
  ["reaction_n", "Upward ground reaction", .001, "kN"],
] as const;

export default function OpenSeesBenchmarkPanel({ editor, projectId }: { editor: EditableModelEditor; projectId: number }) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [elements, setElements] = useState(1), [factor, setFactor] = useState(1), [units, setUnits] = useState("SI");
  const [busy, setBusy] = useState(false), [error, setError] = useState<string | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  useEffect(() => {
    let active = true;
    void api.get<{solver: {available?: boolean}; analyses: Analysis[]}>(`/api/projects/${projectId}/engineering/opensees`).then(data => {
      if (!active) return;
      setAvailable(data.solver.available !== false);
      const row = data.analyses[0] ?? null;
      setAnalysis(row);
      if (row) {setElements(row.result.inputs.elements);setFactor(row.result.inputs.load_factor);setUnits(row.result.inputs.solver_units);}
    }).catch(reason => {if (active) setError(formatApiErrorMessage(reason));});
    return () => {active = false;};
  }, [projectId]);
  const result = analysis?.result;
  const changedInputs = !!result && (elements !== result.inputs.elements || factor !== result.inputs.load_factor || units !== result.inputs.solver_units);
  const changedModel = !!analysis && (editor.dirty || !!editor.platformPreview || !!editor.aiPreview || analysis.model_revision_id !== editor.baseRevision?.id);
  const stale = analysis?.status === "STALE" || changedInputs || changedModel;
  const run = async () => {
    if (!editor.baseRevision) return;
    setBusy(true);setError(null);
    try {setAnalysis(await api.post<Analysis>(`/api/projects/${projectId}/engineering/opensees`, {model_revision_id: editor.baseRevision.id, elements, load_factor: factor, units}));}
    catch (reason) {setError(formatApiErrorMessage(reason));}
    finally {setBusy(false);}
  };
  const download = async (filename: string) => {
    try {
      const data = await api.get<{contents: string}>(`/api/projects/${projectId}/engineering/opensees/${analysis!.id}/artifacts/${filename}`);
      const url = URL.createObjectURL(new Blob([data.contents], {type: "text/plain"}));
      const anchor = document.createElement("a");anchor.href = url;anchor.download = filename;anchor.click();URL.revokeObjectURL(url);
    } catch (reason) {setError(formatApiErrorMessage(reason));}
  };
  const values = result?.values_si;
  return <section aria-label="OpenSees axial benchmark" className="space-y-3 border border-border p-3">
    <h3 className="text-xs font-semibold">OpenSees · axial column benchmark</h3>
    <p className="text-[10px] text-amber-200">Design-code checks DISABLED · Engineering approval DISABLED. Numerical verification is not structural adequacy.</p>
    <p className="text-[11px] leading-relaxed text-muted-foreground">Isolated 3 m steel column + prescribed vertical soil spring. Linked to this project revision for provenance; this does not analyze the platform, anchors or footing.</p>
    <p className="text-[10px] text-muted-foreground">L = 3 m · A = 0.01 m² · E = 200 GPa · k = 100 MN/m. Centered compression; no self-weight, bending or buckling. Plate and footing rigid; anchors inactive.</p>
    <div className="grid grid-cols-3 gap-2 text-[10px]">
      <label>Elements<select aria-label="OpenSees elements" disabled={busy} className="mt-1 w-full border border-border bg-background p-1" value={elements} onChange={e=>setElements(Number(e.target.value))}>{[1,2,4].map(n=><option key={n} value={n}>{n}</option>)}</select></label>
      <label>Compression<select aria-label="OpenSees load" disabled={busy} className="mt-1 w-full border border-border bg-background p-1" value={factor} onChange={e=>setFactor(Number(e.target.value))}>{[.5,1,2].map(n=><option key={n} value={n}>{100*n} kN</option>)}</select></label>
      <label>Solver units<select aria-label="OpenSees units" disabled={busy} className="mt-1 w-full border border-border bg-background p-1" value={units} onChange={e=>setUnits(e.target.value)}><option>SI</option><option>N-mm</option></select></label>
    </div>
    <Button size="sm" variant="secondary" className="w-full" onClick={()=>void run()} disabled={busy || available !== true || !editor.baseRevision || editor.dirty || !!editor.platformPreview || !!editor.aiPreview || !!editor.comparison}>{busy ? "Running OpenSees + verification…" : "Run OpenSees benchmark"}</Button>
    {!editor.baseRevision || editor.dirty ? <p className="text-[10px] text-muted-foreground">Save the model revision before running.</p> : null}
    {available === false && <p role="alert" className="text-xs text-destructive">Local OpenSees executable unavailable. No simulated results.</p>}
    {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
    {analysis && <div className="space-y-2">
      <p role="status" className={stale ? "text-xs text-amber-200" : "text-xs text-primary"}>{stale ? "STALE · model or engineering inputs changed. Re-run before use." : `${result!.status} · numerical benchmark only`}</p>
      <p className="text-[10px] text-muted-foreground">Result revision #{analysis.model_revision_id} · OpenSees {result!.solver_version ?? "version unavailable"} · {result!.inputs.elements} elements · {result!.inputs.solver_units} · {result!.inputs.load_factor*100} kN</p>
      {result!.error && <p role="alert" className="text-xs text-destructive">{result!.error}</p>}
      {values && result!.status === "VERIFIED" && <>
        <dl aria-label="Computed OpenSees results" className="space-y-1 text-[11px]">{fields.map(([key,label,scale,unit])=><div key={key} className="flex justify-between gap-2"><dt>{label}</dt><dd className="font-data">{(values[key]*scale).toFixed(5)} {unit}</dd></div>)}</dl>
        <svg aria-label="Computed axial displacement diagram" viewBox="0 0 280 230" className="w-full border border-border text-primary">
          <text x="8" y="16" fontSize="10" fill="currentColor">Computed displacement · deformation ×100</text>
          <line x1="90" x2="90" y1="35" y2="175" stroke="currentColor" strokeDasharray="4 3" opacity=".5" />
          <polyline points={(result!.nodes ?? []).filter(n=>n.id!==1).map(n=>`130,${175-n.z_m*45-n.displacement_m*100*45}`).join(" ")} fill="none" stroke="currentColor" strokeWidth="3" />
          {(result!.nodes ?? []).filter(n=>n.id!==1).map(n=><g key={n.id}><circle cx="130" cy={175-n.z_m*45-n.displacement_m*100*45} r="3" fill="currentColor"/><text x="142" y={178-n.z_m*45-n.displacement_m*100*45} fontSize="9" fill="currentColor">{(-n.displacement_m*1000).toFixed(4)} mm ↓</text></g>)}
          <path d="M130 175 l-7 5 14 5 -14 5 14 5 -7 5" fill="none" stroke="currentColor"/><line x1="65" x2="190" y1="203" y2="203" stroke="currentColor"/>
          <text x="8" y="220" fontSize="10" fill="currentColor">Reaction {(values.reaction_n/1000).toFixed(3)} kN ↑ · z in metres</text>
        </svg>
        <p className="text-[10px] text-muted-foreground">Nodal displacement shown downward positive; solver uses upward positive. Dashed line: undeformed column, offset for clarity.</p>
        <p className="text-[10px]">{result!.elements?.map(e=>`Element ${e.id}: ${(e.axial_force_n/1000).toFixed(3)} kN`).join(" · ")} (negative = compression)</p>
        <p className="text-[10px]">Equilibrium residual {result!.force_residual_n?.toExponential(3)} N · Suite {result!.verification_suite?.status}: {result!.verification_suite?.cases.length} actual solver cases</p>
      </>}
      <details className="text-[10px]"><summary>Solver provenance and artifacts</summary><p className="mt-2 break-all">Run {result!.run_id}</p><p className="break-all">Executable SHA-256 {result!.solver.executable_sha256}</p><p className="break-all">Model SHA-256 {result!.model_document_sha256}</p><p className="break-all">Input SHA-256 {result!.input_file_sha256}</p><div className="mt-2 flex flex-wrap gap-2">{["model.tcl","nodes.tsv","forces.tsv","summary.tsv","stdout.txt","stderr.txt","manifest.json"].map(name=><button key={name} className="text-primary underline" onClick={()=>void download(name)}>{name}</button>)}</div></details>
    </div>}
  </section>;
}
