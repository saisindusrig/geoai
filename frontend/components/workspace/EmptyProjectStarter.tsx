"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

export default function EmptyProjectStarter({ projectId, active, hasSite, children }: { projectId?: number; active: boolean; hasSite: boolean; children: ReactNode }) {
  const [status, setStatus] = useState<{ projectId: number; empty: boolean } | null>(null);
  const [dismissedProject, setDismissedProject] = useState<number | null>(null);
  const dismiss = () => {
    if (!projectId) return;
    setDismissedProject(projectId);
    try { sessionStorage.setItem(`geoai-starter-dismissed-${projectId}`, "true"); } catch { /* Session storage may be unavailable. */ }
  };
  useEffect(() => {
    const hide = () => {
      if (!projectId) return;
      setDismissedProject(projectId);
      try { sessionStorage.setItem(`geoai-starter-dismissed-${projectId}`, "true"); } catch { /* Best effort. */ }
    };
    window.addEventListener("geoai:assistant-opened", hide);
    return () => window.removeEventListener("geoai:assistant-opened", hide);
  }, [projectId]);
  useEffect(() => {
    if (!projectId || !active || hasSite) return;
    let live = true;
    api.get<{ isEmpty: boolean }>(`/api/projects/${projectId}/workspace-state`).then(result => {
      if (live) {
        try { if (sessionStorage.getItem(`geoai-starter-dismissed-${projectId}`)) setDismissedProject(projectId); } catch { /* Best effort. */ }
        setStatus({ projectId, empty: result.isEmpty });
      }
    }).catch(() => { if (live) setStatus({ projectId, empty: false }); });
    return () => { live = false; };
  }, [projectId, active, hasSite]);
  if (!projectId || !active || hasSite || status?.projectId !== projectId || !status.empty || dismissedProject === projectId) return children;
  const start = (event: string) => {
    dismiss();
    window.dispatchEvent(new CustomEvent(event));
  };
  return <><section aria-label="Empty project starter" className="pointer-events-auto space-y-3 rounded-xl border border-border bg-background/95 p-4 shadow-lg backdrop-blur-md">
    <div className="flex items-center justify-between gap-3"><p className="text-sm font-medium">Start anywhere.</p><button type="button" aria-label="Dismiss first-run actions" className="text-xs text-muted-foreground hover:text-foreground" onClick={dismiss}>Dismiss</button></div>
    <p className="text-xs leading-relaxed text-muted-foreground">Describe what you want to build, select a site on the map, draw an area or route, or import site information.</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className="rounded border border-border px-3 py-2 text-xs text-primary" onClick={() => start("geoai:open-copilot")}>Ask GeoAI</button>
      <button type="button" className="rounded border border-border px-3 py-2 text-xs" onClick={() => start("geoai:open-drawing")}>Draw / select site</button>
    </div>
  </section>{children}</>;
}
