"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function NewProjectDialog({ onClose, returnFocus }: { onClose: () => void; returnFocus: () => void }) {
  const router = useRouter();
  const dialog = useRef<HTMLFormElement>(null);
  const nameInput = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef(onClose);
  const focusRef = useRef(returnFocus);
  useEffect(() => { closeRef.current = onClose; focusRef.current = returnFocus; }, [onClose, returnFocus]);
  useEffect(() => {
    nameInput.current?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); if (!submitting.current) closeRef.current(); }
      if (event.key !== "Tab") return;
      const controls = dialog.current?.querySelectorAll<HTMLElement>("input:not([disabled]),button:not([disabled])");
      if (!controls?.length) return;
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", keyboard);
    return () => { window.removeEventListener("keydown", keyboard); focusRef.current(); };
  }, []);
  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || trimmed.length > 255 || submitting.current) return;
    submitting.current = true; setBusy(true); setError(null);
    try {
      const project = await api.post<Project>("/api/projects", { name: trimmed });
      router.push(`/projects/${project.id}/workspace`);
      closeRef.current();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Project could not be created. Please retry."); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onMouseDown={event => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <form ref={dialog} role="dialog" aria-modal="true" aria-labelledby="new-project-title" aria-busy={busy} onSubmit={create} onMouseDown={event => event.stopPropagation()} className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-[var(--shadow-lg)]">
      <h2 id="new-project-title" className="font-semibold text-foreground">New project</h2>
      <label className="mt-5 block text-sm text-foreground-secondary">Project name
        <input ref={nameInput} required maxLength={255} disabled={busy} value={name} onChange={e => setName(e.target.value)} className="mt-2 h-10 w-full rounded-xl border border-border bg-background px-3 text-foreground outline-none focus:border-foreground/40 focus-visible:ring-0" />
      </label>
      {error && <p role="alert" className="mt-3 text-sm text-destructive">{error}</p>}
      <div className="mt-6 flex justify-end gap-3">
        <button type="button" disabled={busy} onClick={onClose} className="rounded-xl border border-border px-4 py-2 text-sm">Cancel</button>
        <button type="submit" disabled={busy || !name.trim()} className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50">{busy ? "Creating…" : "Create Project"}</button>
      </div>
    </form>
  </div>;
}
