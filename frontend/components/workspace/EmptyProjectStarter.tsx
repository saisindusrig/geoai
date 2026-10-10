"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

export default function EmptyProjectStarter({ projectId, active, hasSite, children }: { projectId?: number; active: boolean; hasSite: boolean; children: ReactNode }) {
  const [empty, setEmpty] = useState(false);
  useEffect(() => {
    if (!projectId || !active || hasSite) return;
    let live = true;
    api.get<{ isEmpty: boolean }>(`/api/projects/${projectId}/workspace-state`).then(result => { if (live) setEmpty(result.isEmpty); }).catch(() => { if (live) setEmpty(false); });
    return () => { live = false; };
  }, [projectId, active, hasSite]);
  if (!projectId || hasSite || !empty) return children;
  return <section aria-label="Empty project starter" className="pointer-events-auto space-y-3 rounded-xl border border-border bg-background/95 p-4 shadow-lg backdrop-blur-md">
    <p className="text-sm font-medium">Start anywhere.</p>
    <p className="text-xs leading-relaxed text-muted-foreground">Describe what you want to build, select a site on the map, draw an area or route, or import site information.</p>
    <div className="flex flex-wrap gap-2">
      <button className="rounded border border-border px-3 py-2 text-xs text-primary" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-copilot"))}>Ask GeoAI</button>
      <button className="rounded border border-border px-3 py-2 text-xs" onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-drawing"))}>Draw / select site</button>
    </div>
  </section>;
}
