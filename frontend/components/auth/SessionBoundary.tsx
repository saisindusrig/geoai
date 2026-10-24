"use client";

import { Fragment, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { firebaseMode, isAuthConfiguration, prepareFirebase, sessionRevision, subscribeSession } from "@/lib/firebase-auth";
import { useProjectStore } from "@/stores/projectStore";
import { useToastStore } from "@/lib/toast";

/** Remount account-scoped views and reset the existing store on identity changes. */
export default function SessionBoundary({ children }: { children: React.ReactNode }) {
  const [epoch, setEpoch] = useState(sessionRevision);
  const [state, setState] = useState<"checking" | "ready" | "unavailable">("checking");
  useEffect(() => {
    let active = true;
    const stop = subscribeSession(() => {
      useProjectStore.setState(useProjectStore.getInitialState(), true);
      useToastStore.setState({ toasts: [] });
      if (firebaseMode()) {
        // Account-specific view caches only; retain original offline sandbox drafts.
        try {
          Object.keys(localStorage).filter(key => /^(geoai-map-bookmarks-|geoai:analysis-guided:|project-\d+-)/.test(key))
            .forEach(key => localStorage.removeItem(key));
        } catch { /* In-memory stores and stale-response guards still clear. */ }
      }
      if (active) setEpoch(sessionRevision());
    });
    void api.get<unknown>("/api/auth/config").then(async config => {
      if (!active) return;
      if (!isAuthConfiguration(config)) throw new Error("Invalid authentication configuration");
      await prepareFirebase(config);
      if (active) setState("ready");
    }).catch(() => { if (active) setState("unavailable"); });
    return () => { active = false; stop(); };
  }, []);
  if (state !== "ready") return <div className="p-6 text-sm text-muted-foreground" role="status">{state === "checking" ? "Checking authentication configuration…" : "Authentication configuration unavailable. Reload to try again."}</div>;
  if (firebaseMode() && typeof window !== "undefined" && /(?:[?&](?:local|demo)=1)|\/projects\/999999\/workspace/.test(window.location.pathname + window.location.search)) {
    return <div className="p-6 text-sm text-muted-foreground" role="status">Local development workspaces are unavailable in Firebase mode. Open an authorized project from the dashboard.</div>;
  }
  // Preserve the login's pending/error state while the SDK changes identities.
  // Protected account views still remount on every session revision.
  return <Fragment key={typeof window !== "undefined" && window.location.pathname === "/login" ? "login" : epoch}>{children}</Fragment>;
}
