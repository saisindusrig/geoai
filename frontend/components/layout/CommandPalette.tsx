"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  Bot,
  FileText,
  Map,
  Search,
  Sparkles,
  Workflow,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Command {
  id: string;
  label: string;
  group: string;
  icon: React.ComponentType<{ className?: string }>;
  run: () => void;
}

interface Props {
  projectId?: number;
  onAnalyze?: () => void;
  onGenerate?: () => void;
}

export default function CommandPalette({ projectId, onAnalyze, onGenerate }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  const go = useCallback((path: string) => {
    router.push(path);
    setOpen(false);
  }, [router]);

  const commands: Command[] = [
    { id: "dash", label: "Dashboard", group: "Navigate", icon: Workflow, run: () => go("/dashboard") },
    ...(projectId
      ? [
          { id: "map", label: "Site Selection Map", group: "Navigate", icon: Map, run: () => go(`/projects/${projectId}/map`) },
          { id: "workspace", label: "AI Design Studio", group: "Navigate", icon: Sparkles, run: () => go(`/projects/${projectId}/workspace`) },
          { id: "estimate", label: "BOQ / Estimate", group: "Navigate", icon: BarChart3, run: () => go(`/projects/${projectId}/estimate`) },
          { id: "report", label: "Reports & Export", group: "Navigate", icon: FileText, run: () => go(`/projects/${projectId}/report`) },
          { id: "copilot", label: "Open AI Copilot panel", group: "Actions", icon: Bot, run: () => { setOpen(false); document.dispatchEvent(new CustomEvent("geoai:open-copilot")); } },
          ...(onAnalyze ? [{ id: "analyze", label: "Run Site Analysis", group: "Actions", icon: Search, run: () => { onAnalyze(); setOpen(false); } }] : []),
          ...(onGenerate ? [{ id: "generate", label: "Generate Design", group: "Actions", icon: Sparkles, run: () => { onGenerate(); setOpen(false); } }] : []),
        ]
      : []),
  ];

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()),
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQuery("");
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] modal-overlay"
            onClick={() => setOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -8 }}
            className="fixed left-1/2 top-[15%] z-[101] w-full max-w-lg -translate-x-1/2 panel-elevated rounded-xl border border-border shadow-2xl overflow-hidden"
          >
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Jump to page or run action…"
                className="flex-1 bg-transparent text-sm outline-none"
              />
              <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-border text-muted-foreground">Esc</kbd>
            </div>
            <ul className="max-h-64 overflow-y-auto py-1">
              {filtered.map((cmd) => {
                const Icon = cmd.icon;
                return (
                  <li key={cmd.id}>
                    <button
                      type="button"
                      onClick={cmd.run}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-primary/10 text-left"
                    >
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      <span className="flex-1">{cmd.label}</span>
                      <span className="text-[10px] text-muted-foreground">{cmd.group}</span>
                    </button>
                  </li>
                );
              })}
              {filtered.length === 0 && (
                <li className="px-3 py-4 text-sm text-muted-foreground text-center">No matches</li>
              )}
            </ul>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export function CommandPaletteHint({ className }: { className?: string }) {
  return (
    <span className={cn("text-[10px] text-muted-foreground", className)}>
      <kbd className="px-1 py-0.5 rounded border border-border">⌘K</kbd> commands
    </span>
  );
}
