"use client";

import { X, Ruler } from "lucide-react";

const modes: Record<string, { title: string; metric: string; supporting: [string, string][] }> = {
  distance: { title: "Distance", metric: "distance m", supporting: [["horizontal m", "Horizontal"], ["vertical delta m", "Elevation change"]] },
  height: { title: "Elevation", metric: "elevation m", supporting: [] },
  slope: { title: "Slope", metric: "grade percent", supporting: [["angle deg", "Angle"], ["horizontal m", "Horizontal"]] },
  area: { title: "Area", metric: "area m2", supporting: [] },
  clearance: { title: "Clearance", metric: "clearance m", supporting: [["horizontal m", "Horizontal separation"]] },
};

export default function MeasurementResult({ readout, mode, onClear }: { readout: string; mode: string; onClear: () => void }) {
  const [summary, ...details] = readout.split("\n");
  const parts = summary.split(" · ");
  const values = new Map(parts.slice(1).map(part => { const index = part.indexOf(": "); return [part.slice(0, index), part.slice(index + 2)]; }));
  const config = modes[mode] ?? modes.distance;
  const value = values.get(config.metric);
  const classification = parts[0];
  const source = classification === "VISUAL_REFERENCE" ? "Visual estimate" : classification === "SURVEY_DERIVED" ? "Survey derived" : classification === "ENGINEERING_RESULT" ? "Design geometry" : "Unverified";
  const waiting = !value || value === "Unknown";
  return <section aria-label="Measurement result" className="absolute bottom-16 right-3 z-50 w-[260px] max-w-[calc(100%-7rem)] rounded-xl border border-white/15 bg-[#0d1712]/95 p-4 shadow-xl backdrop-blur-md">
    <header className="flex items-center justify-between"><span className="flex items-center gap-2 text-xs font-medium text-[#dce7dd]"><Ruler size={14} className="text-primary" />{config.title}</span><button type="button" aria-label="Clear measurement" onClick={onClear} className="rounded p-1 text-muted-foreground hover:text-foreground"><X size={14} /></button></header>
    <div role="status" aria-live="polite" className="my-3">
      <p className="text-[28px] font-semibold leading-tight tracking-tight text-foreground tabular-nums">{waiting ? "—" : value}</p>
      {waiting && <p className="mt-2 text-xs text-muted-foreground">{value === "Unknown" ? mode === "area" ? "Pick at least three points." : "Elevation data is unavailable for this surface." : summary.includes("Sampling") ? "Sampling terrain…" : summary.includes("could not") || summary.includes("Could not") ? "Try another surface point." : mode === "height" ? "Pick a surface point." : "Pick the next point."}</p>}
    </div>
    {!waiting && config.supporting.map(([key, label]) => values.has(key) && <div key={key} className="flex justify-between gap-3 border-t border-white/10 py-2 text-[11px]"><span className="text-muted-foreground">{label}</span><span className="text-foreground tabular-nums">{values.get(key) === "Unknown" ? "Unavailable" : values.get(key)}</span></div>)}
    {value && <span className="mt-1 inline-block rounded bg-white/5 px-2 py-1 text-[10px] text-muted-foreground">{source}</span>}
    {details.length > 0 && <details className="mt-3 border-t border-white/10 pt-2 text-[10px] text-muted-foreground"><summary className="cursor-pointer hover:text-foreground">Source details</summary><div className="mt-2 max-h-28 space-y-2 overflow-y-auto break-words">{details.map((detail, index) => <p key={index}>{detail.replaceAll("VISUAL_REFERENCE", "Visual estimate").replaceAll("dataset unavailable · version unavailable · ", "")}</p>)}</div></details>}
  </section>;
}
