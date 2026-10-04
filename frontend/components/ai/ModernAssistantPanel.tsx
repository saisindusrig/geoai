"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  ArrowUp,
  Bot,
  ChevronDown,
  Circle,
  PanelRightClose,
  Paperclip,
  Sparkles,
  Zap,
} from "lucide-react";
import { BRAND_COPILOT, BRAND_NAME } from "@/components/landing/landing-theme";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiUrl, streamChat } from "@/lib/api";
import type { CopilotAction, DesignOutput } from "@/lib/types";
import { cn, formatCurrency } from "@/lib/utils";
import BlenderLayerPanel from "@/components/map/BlenderLayerPanel";
import { useWorkspaceMap } from "@/components/layout/WorkspaceMapContext";
import { PanelResizeHandle } from "@/components/ui/panel-resize-handle";
import { useVerticalSplitResize } from "@/hooks/usePointerResize";
import { useProjectStore } from "@/stores/projectStore";

interface ChatEntry {
  role: "user" | "assistant";
  text: string;
  design?: DesignOutput | null;
  cardType?: ResponseCardType;
  actions?: CopilotAction[];
  warnings?: string[];
  provider?: string;
}

type ResponseCardType =
  | "site-analysis"
  | "risk"
  | "materials"
  | "cost"
  | "design"
  | "timeline";

interface Props {
  projectId: number;
  design?: DesignOutput | null;
  onApplyParameters: (params: Record<string, unknown>) => void;
  onRegenerate: (params: Record<string, unknown>) => void;
  onRunSiteAnalysis?: () => Promise<void>;
  currentParameters?: Record<string, unknown> | null;
}

function inferCardType(text: string): ResponseCardType | undefined {
  const t = text.toLowerCase();
  if (t.includes("risk") || t.includes("constraint")) return "risk";
  if (t.includes("cement") || t.includes("steel") || t.includes("material")) return "materials";
  if (t.includes("cost") || t.includes("₹") || t.includes("cr")) return "cost";
  if (t.includes("month") || t.includes("timeline") || t.includes("duration")) return "timeline";
  if (t.includes("design") || t.includes("flyover") || t.includes("building")) return "design";
  if (t.includes("site") || t.includes("analysis")) return "site-analysis";
  return undefined;
}

function actionLabel(action: CopilotAction): string {
  switch (action.type) {
    case "update_parameters":
      return "Apply parameter changes";
    case "run_site_analysis":
      return "Run site analysis";
    case "generate_design":
      return "Generate preliminary design";
    case "show_layer":
      return `Show layer: ${String(action.payload.layer ?? "layer")}`;
    case "download":
      return `Download ${String(action.payload.export ?? "file")}`;
    default:
      return "Confirm action";
  }
}

function actionDescription(action: CopilotAction): string {
  if (action.type === "update_parameters") {
    const keys = Object.keys(action.payload);
    if (!keys.length) return "Merge suggested parameters into the workspace.";
    return keys.map((k) => `${k}: ${String(action.payload[k])}`).join(" · ");
  }
  if (action.type === "run_site_analysis") {
    return "Analyze boundary/alignment for elevation, OSM context, and risks.";
  }
  if (action.type === "generate_design") {
    return "Queue design generation with current parameters (BOQ from backend calculators).";
  }
  return "Review and confirm before applying.";
}

export default function ModernAssistantPanel({
  projectId,
  design,
  onApplyParameters,
  onRegenerate,
  onRunSiteAnalysis,
  currentParameters,
}: Props) {
  const [pendingActions, setPendingActions] = useState<CopilotAction[]>([]);
  const [history, setHistory] = useState<ChatEntry[]>([
    {
      role: "assistant",
      text: `${BRAND_COPILOT} ready. Ask for site analysis, parameter suggestions, or help regenerating a preliminary design.`,
      cardType: "design",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [useMapContext, setUseMapContext] = useState(true);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const scrollRef = useRef<HTMLDivElement>(null);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const { size: layersHeight, onResizePointerDown } = useVerticalSplitResize({
    storageKey: "geoai-copilot-layers-height",
    defaultSize: 240,
    minSize: 120,
    minOtherSize: 220,
    containerRef: splitContainerRef,
  });
  const toggleLayer = useProjectStore((s) => s.toggleLayer);
  const layers = useProjectStore((s) => s.layers);
  const { onToggleCopilotPanel, copilotPanelVisible } = useWorkspaceMap();

  const hasUserMessages = history.some((e) => e.role === "user");

  const SUGGESTED_PROMPTS = [
    "Suggest flyover parameters",
    "Run site analysis",
    "How can I reduce cost?",
    "Regenerate design",
    "What are the main risks?",
    "Estimate construction timeline",
    "Explain BOQ",
  ] as const;

  const applyPrompt = (text: string) => {
    setInput(text);
  };

  const confirmAction = async (action: CopilotAction) => {
    if (action.type === "update_parameters") {
      onApplyParameters(action.payload);
    } else if (action.type === "generate_design") {
      onRegenerate(currentParameters ?? action.payload ?? {});
    } else if (action.type === "run_site_analysis" && onRunSiteAnalysis) {
      await onRunSiteAnalysis();
    } else if (action.type === "show_layer" && action.payload.layer === "excavation" && !layers.excavation) {
      toggleLayer("excavation");
    } else if (action.type === "download" && action.payload.export) {
      window.open(apiUrl(`/api/projects/${projectId}/exports/${action.payload.export}`), "_blank");
    }
    setPendingActions((prev) => prev.filter((a) => a !== action));
  };

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setHistory((h) => [...h, { role: "user", text }]);
    setBusy(true);
    setPendingActions([]);
    const streamIdx = history.length + 1;
    setHistory((h) => [...h, { role: "assistant", text: "", cardType: inferCardType(text) }]);

    try {
      let fullReply = "";
      const result = await streamChat(projectId, text, (chunk) => {
        fullReply += chunk;
        setHistory((h) =>
          h.map((entry, i) => (i === streamIdx ? { ...entry, text: fullReply } : entry)),
        );
      });

      const actions = result.actions?.length
        ? result.actions
        : result.action
          ? [result.action]
          : [];

      setHistory((h) =>
        h.map((entry, i) =>
          i === streamIdx
            ? {
                ...entry,
                text: fullReply || result.message || "",
                design: design ?? undefined,
                cardType: inferCardType(fullReply || result.message || ""),
                actions,
                warnings: result.warnings,
                provider: result.provider,
              }
            : entry,
        ),
      );

      if (actions.length) setPendingActions(actions);
    } catch (e) {
      setHistory((h) =>
        h
          .filter((_, i) => i !== streamIdx)
          .concat({
            role: "assistant",
            text: `Error: ${e instanceof Error ? e.message : e}`,
          }),
      );
    } finally {
      setBusy(false);
      setTimeout(() => scrollRef.current?.scrollTo({ top: 99999, behavior: "smooth" }), 50);
    }
  };

  return (
    <div
      ref={splitContainerRef}
      className="flex flex-col h-full rounded-none bg-background-secondary"
    >
      <div className="shrink-0 overflow-hidden" style={{ height: layersHeight }}>
        <BlenderLayerPanel design={design} />
      </div>

      <PanelResizeHandle orientation="horizontal" onPointerDown={onResizePointerDown} />

      <div className="flex flex-1 min-h-0 flex flex-col min-w-0 bg-background">
        <div className="shrink-0 border-b border-border px-3 py-2.5">
          <div className="flex items-center justify-between gap-2">
          <div className="flex items-center justify-center gap-2 min-w-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-[rgba(34,211,238,0.25)] bg-[rgba(34,211,238,0.1)]">
              <Sparkles className="h-3.5 w-3.5 text-accent shrink-0" />
            </div>
            <div className="min-w-0">
              <p className="text-[13px] font-semibold text-foreground">{BRAND_COPILOT}</p>
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <Circle className="h-2 w-2 fill-[#10B981] text-[#10B981]" />
                Local Ollama / Cloud LLM
              </p>
            </div>
          </div>
          {copilotPanelVisible && (
            <button
              type="button"
              onClick={onToggleCopilotPanel}
              className="shrink-0 p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              title="Hide Copilot panel"
              aria-label="Hide Copilot panel"
            >
              <PanelRightClose className="h-4 w-4" />
            </button>
          )}
          </div>
          <button
            type="button"
            onClick={() => setUseMapContext((v) => !v)}
            className={cn(
              "mt-2 flex h-7 w-full items-center justify-between rounded-lg border px-2 text-[10px] transition-all",
              useMapContext
                ? "border-[var(--primary)] bg-[rgba(59,130,246,0.1)] text-foreground-secondary"
                : "border-[rgba(148,163,184,0.14)] bg-white/[0.03] text-muted-foreground",
            )}
          >
            Use current map view as context
            <span className="font-data">{useMapContext ? "On" : "Off"}</span>
          </button>
        </div>

        <div ref={scrollRef} className="relative flex-1 min-h-0 overflow-y-auto overscroll-contain scrollbar-thin-dark">
          {!hasUserMessages ? (
            <div className="flex min-h-full flex-col items-center justify-center px-5 py-8 text-center">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 border border-primary/25">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <p className="text-[15px] font-medium text-foreground mb-2">Ask about this design workspace</p>
              <p className="text-[13px] leading-relaxed text-muted-foreground max-w-[260px] mb-5">
                Ask about site risks, BOQ, design parameters, construction sequence, or cost reduction.
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-[280px]">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => applyPrompt(prompt)}
                    className="rounded-full border border-[rgba(148,163,184,0.2)] bg-background-secondary px-3 py-1.5 text-[11px] text-foreground-secondary hover:border-primary/35 hover:bg-primary/10 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-full px-3 py-4 space-y-5">
              <AnimatePresence initial={false}>
                {history.map((entry, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.18 }}
                    className={cn(
                      "flex w-full",
                      entry.role === "user" ? "justify-end" : "justify-start",
                    )}
                  >
                    {entry.role === "user" ? (
                  <div className="max-w-[88%] rounded-[1.25rem] border border-primary/20 bg-primary/10 px-4 py-2.5 text-[13px] leading-relaxed text-foreground">
                        {entry.text}
                      </div>
                    ) : (
                      <div className="max-w-full space-y-2 min-w-0">
                        {entry.provider && entry.provider !== "fallback" && (
                          <Badge variant="outline" className="text-[10px]">
                            {entry.provider}
                          </Badge>
                        )}
                        <div className="text-[13px] leading-[1.65] text-foreground/90 whitespace-pre-wrap">
                          {expanded[i] !== false || entry.text.length < 400
                            ? entry.text
                            : `${entry.text.slice(0, 400)}…`}
                          {entry.text.length > 400 && (
                            <button
                              type="button"
                              onClick={() => setExpanded((e) => ({ ...e, [i]: !e[i] }))}
                              className="flex items-center gap-1 mt-2 text-[12px] text-muted-foreground hover:text-foreground"
                            >
                              {expanded[i] === false ? "Show more" : "Show less"}
                              <ChevronDown
                                className={cn("h-3 w-3", expanded[i] !== false && "rotate-180")}
                              />
                            </button>
                          )}
                        </div>
                        {entry.warnings && entry.warnings.length > 0 && (
                          <div className="rounded-lg border border-warning/30 bg-warning/5 px-3 py-2 text-[11px] text-warning-text space-y-1">
                            {entry.warnings.map((w, wi) => (
                              <p key={wi}>{w}</p>
                            ))}
                          </div>
                        )}
                        {entry.actions && entry.actions.length > 0 && i === history.length - 1 && (
                          <div className="space-y-2">
                            {entry.actions.map((action, ai) => (
                              <ActionCard
                                key={ai}
                                action={action}
                                onConfirm={() => void confirmAction(action)}
                              />
                            ))}
                          </div>
                        )}
                        {design?.calculated && i === history.length - 1 && (
                          <DesignSummaryCard
                            design={design}
                            projectId={projectId}
                            onRegenerate={onRegenerate}
                          />
                        )}
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {busy && (
                <div className="flex items-center gap-1.5 py-1">
                  <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                  <span className="h-2 w-2 rounded-full bg-accent animate-pulse [animation-delay:150ms]" />
                  <span className="h-2 w-2 rounded-full bg-accent animate-pulse [animation-delay:300ms]" />
                  <span className="ml-2 text-[11px] text-muted-foreground">{BRAND_NAME} is analyzing workspace context…</span>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="shrink-0 space-y-2 border-t border-border bg-[rgba(5,7,10,0.92)] px-3 pb-3 pt-3">
          {pendingActions.length > 0 && (
            <div className="rounded-xl border border-accent/25 bg-info-muted px-3 py-2 text-[11px] space-y-2">
              <p className="font-medium text-accent flex items-center gap-1">
                <Zap className="h-3 w-3" />
                Suggested actions — confirm to apply
              </p>
              {pendingActions.map((action, i) => (
                <div key={i} className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground truncate">{actionLabel(action)}</span>
                  <Button
                    size="sm"
                    className="h-7 text-[11px] shrink-0"
                    onClick={() => void confirmAction(action)}
                  >
                    Confirm
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="relative flex items-end gap-2 rounded-[1.35rem] border border-border bg-background-secondary px-3 py-2 shadow-sm focus-within:border-primary/45 focus-within:ring-1 focus-within:ring-primary/20">
            <button
              type="button"
              className="mb-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-surface-hover hover:text-foreground"
              title="Attach workspace context"
            >
              <Paperclip className="h-3.5 w-3.5" />
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              placeholder={`Message ${BRAND_COPILOT}…`}
              rows={1}
              disabled={busy}
              className="flex-1 min-h-[24px] max-h-28 resize-none bg-transparent text-[13px] leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none py-1"
            />
            <Button
              type="button"
              size="icon"
              disabled={busy || !input.trim()}
              onClick={() => void send()}
              className={cn(
                "h-8 w-8 shrink-0 rounded-full transition-opacity",
                input.trim() ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-muted text-muted-foreground",
              )}
              aria-label="Send message"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ActionCard({
  action,
  onConfirm,
}: {
  action: CopilotAction;
  onConfirm: () => void;
}) {
  return (
    <Card className="border-[rgba(34,211,238,0.2)] bg-[rgba(15,23,42,0.5)] p-3 space-y-2 shadow-none">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-medium text-foreground">{actionLabel(action)}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">{actionDescription(action)}</p>
        </div>
        <Badge variant="warning" className="shrink-0 text-[9px]">
          Confirm
        </Badge>
      </div>
      <Button size="sm" className="h-7 text-[11px] w-full" onClick={onConfirm}>
        Apply this action
      </Button>
    </Card>
  );
}

function DesignSummaryCard({
  design,
  projectId,
  onRegenerate,
}: {
  design: DesignOutput;
  projectId: number;
  onRegenerate: (p: Record<string, unknown>) => void;
}) {
  const calc = design.calculated;
  if (!calc) return null;

  return (
    <Card className="border-border/60 bg-muted/20 p-3 space-y-2 text-left shadow-none">
      <p className="text-[10px] font-semibold text-accent">Calculated summary</p>
      <div className="grid grid-cols-2 gap-2 text-[11px] font-data">
        <div className="rounded-md bg-card px-2 py-1.5 border border-border">
          <p className="text-muted-foreground text-[10px]">Cost (mid)</p>
          <p className="font-medium">{formatCurrency(calc.cost_summary.total_medium, calc.cost_summary.currency)}</p>
        </div>
        <div className="rounded-md bg-card px-2 py-1.5 border border-border">
          <p className="text-muted-foreground text-[10px]">Timeline</p>
          <p className="font-medium">~{calc.timeline.estimated_months_medium} mo</p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button size="sm" className="flex-1 gap-1 text-[11px] h-7" onClick={() => onRegenerate({})}>
          Regenerate <ArrowRight className="h-3 w-3" />
        </Button>
        <a
          href={`/projects/${projectId}/estimate`}
          className="inline-flex flex-1 h-7 items-center justify-center rounded-md btn-glass text-[11px] font-medium"
        >
          View BOQ
        </a>
      </div>
    </Card>
  );
}
