"use client";

import Link from "next/link";
import { Monitor } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useWorkspaceDevice } from "@/hooks/useWorkspaceDevice";

export default function DesktopWorkspaceGate({ required, projectId, projectName, returnPath, children }: {
  required: boolean; projectId: number | null; projectName?: string; returnPath: string; children: ReactNode;
}) {
  const device = useWorkspaceDevice();
  const [admitted, setAdmitted] = useState(false);
  useEffect(() => {
    let cancelled = false;
    if (required && device === "desktop") queueMicrotask(() => { if (!cancelled) setAdmitted(true); });
    return () => { cancelled = true; };
  }, [required, device]);

  if (!required) return children;
  const available = device === "desktop" && admitted;
  return <>
    {!available && <main id="main-content" className="desktop-required-screen flex min-h-dvh w-full flex-col items-center justify-center overflow-y-auto bg-background p-6 text-center">
      <div className="w-full max-w-lg space-y-5">
        <Monitor aria-hidden="true" className="mx-auto size-10 text-primary" />
        {device === "checking" ? <p role="status">Checking workspace compatibility…</p> : <>
          <h1 className="text-2xl font-semibold">Desktop Required</h1>
          <p className="text-sm leading-6 text-muted-foreground">StruvoCivil&apos;s 3D engineering workspace is designed for desktop use. Open this project on a desktop or laptop for the complete engineering experience.</p>
        </>}
        {projectId && <p className="break-words text-sm text-foreground">{projectName ?? `Project #${projectId}`}</p>}
        <Link href={`/dashboard?returnTo=${encodeURIComponent(returnPath)}`} className="inline-flex min-h-11 items-center justify-center border border-primary bg-primary px-5 py-3 font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary">Back to Dashboard</Link>
        <p className="text-xs leading-5 text-muted-foreground">Your project link is retained when you return to the dashboard. Desktop editing requires a wide screen and a mouse or trackpad.</p>
      </div>
    </main>}
    {/* Keep an already opened desktop session mounted during resize to retain drafts/undo. */}
    {admitted && <div hidden={!available} inert={!available} className={available ? "contents" : "hidden"}>{children}</div>}
  </>;
}
