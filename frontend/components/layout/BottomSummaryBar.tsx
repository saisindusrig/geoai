"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Box,
  ChevronUp,
  Clock,
  DollarSign,
  Layers,
  MapPin,
  Shovel,
  TrendingUp,
} from "lucide-react";
import { useState, useEffect } from "react";
import type { RefCallback } from "react";
import { SidebarSection } from "@/components/ui/collapsible-section";
import { cn, formatCurrency, formatQty } from "@/lib/utils";
import EngineeringDockPanel from "@/components/model-editor/EngineeringDockPanel";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { Project } from "@/lib/types";

export interface SummaryStats {
  totalCost?: number;
  cementBags?: number;
  steelKg?: number;
  excavationM3?: number;
  timelineMonths?: number;
  areaSqm?: number;
  riskScore?: number;
  currency?: string;
}

const ITEMS = [
  {
    key: "totalCost",
    label: "Cost",
    icon: DollarSign,
    accent: "text-primary",
    format: (v: number, c?: string) => formatCurrency(v, c),
  },
  {
    key: "cementBags",
    label: "Cement",
    icon: Box,
    accent: "text-accent",
    format: (v: number) => formatQty(v, "bags"),
  },
  {
    key: "steelKg",
    label: "Steel",
    icon: Layers,
    accent: "text-foreground-secondary",
    format: (v: number) => formatQty(v, "kg"),
  },
  {
    key: "excavationM3",
    label: "Excavation",
    icon: Shovel,
    accent: "text-warning",
    format: (v: number) => formatQty(v, "m³"),
  },
  {
    key: "timelineMonths",
    label: "Duration",
    icon: Clock,
    accent: "text-success",
    format: (v: number) => `~${v} mo`,
  },
  {
    key: "areaSqm",
    label: "Area",
    icon: MapPin,
    accent: "text-muted-foreground",
    format: (v: number) => formatQty(v, "m²"),
  },
  {
    key: "riskScore",
    label: "Risk",
    icon: TrendingUp,
    accent: "text-destructive",
    format: (v: number) => `${v}/10`,
  },
] as const;

function formatValue(
  key: string,
  raw: SummaryStats[keyof SummaryStats],
  stats: SummaryStats,
  format: (v: number, c?: string) => string,
) {
  if (raw == null || typeof raw !== "number") return "—";
  return key === "totalCost" ? format(raw, stats.currency) : format(raw);
}

export default function BottomSummaryBar({
  stats,
  loading,
  variant = "bar",
  onCreditsContainerChange,
  editor,
  project,
}: {
  stats: SummaryStats;
  loading?: boolean;
  variant?: "bar" | "sidebar";
  onCreditsContainerChange?: RefCallback<HTMLDivElement>;
  editor?: EditableModelEditor;
  project?: Project;
}) {
  const [expanded, setExpanded] = useState(false);
  const [dockTab,setDockTab]=useState("QUANTITIES");
  useEffect(()=>{const open=(event:Event)=>{setDockTab((event as CustomEvent<string>).detail ?? "QUANTITIES");setExpanded(true);};window.addEventListener("geoai:open-dock",open);return()=>window.removeEventListener("geoai:open-dock",open);},[]);
  const params = useParams<{ id?: string }>();
  const projectId = params?.id;
  const metricHref = (key: string) => {
    if (!projectId) return null;
    if (key === "totalCost") return `/projects/${projectId}/cost`;
    if (key === "cementBags" || key === "steelKg" || key === "excavationM3") return `/projects/${projectId}/estimate`;
    if (key === "timelineMonths") return `/projects/${projectId}/timeline`;
    if (key === "riskScore") return `/projects/${projectId}/analysis`;
    return `/projects/${projectId}/workspace`;
  };

  if (variant === "sidebar") {
    const hasData = ITEMS.some(({ key }) => {
      const raw = stats[key as keyof SummaryStats];
      return raw != null && typeof raw === "number";
    });

    return (
      <SidebarSection title="Quantity estimate">
        {!hasData && !loading ? (
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            BOQ estimate appears after generation.
          </p>
        ) : (
          <div className={cn("space-y-2", loading && "opacity-60")}>
            <ul className="space-y-1.5">
              {ITEMS.map(({ key, label, icon: Icon, accent, format }) => {
                const raw = stats[key as keyof SummaryStats];
                const value = loading ? "…" : formatValue(key, raw, stats, format);
                return (
                  <li
                    key={key}
                    className="flex items-center justify-between gap-2 rounded-lg border border-border bg-background-secondary/50 px-2 py-1.5 text-[11px]"
                    title={`${label}: ${value}`}
                  >
                    <span className="flex items-center gap-1.5 min-w-0 text-muted-foreground">
                      <Icon className={cn("h-3.5 w-3.5 shrink-0", accent)} aria-hidden />
                      <span className="truncate">{label}</span>
                    </span>
                    <span className="font-data font-medium text-foreground shrink-0">{value}</span>
                  </li>
                );
              })}
            </ul>
            {projectId && (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  href={`/projects/${projectId}/estimate`}
                  className="flex h-7 items-center justify-center rounded-lg border border-border bg-background-secondary text-[10px] text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
                >
                  View BOQ
                </Link>
                <Link
                  href={`/projects/${projectId}/cost`}
                  className="flex h-7 items-center justify-center rounded-lg border border-border bg-background-secondary text-[10px] text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
                >
                  Cost Analysis
                </Link>
              </div>
            )}
          </div>
        )}
      </SidebarSection>
    );
  }

  return (
    <div
      role="region"
      aria-label="Engineering dock"
      className={cn(
        "shrink-0 border-t border-white/10 bg-[#101410]/95 px-3 py-2 backdrop-blur-xl",
        loading && "opacity-60",
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <button type="button" onClick={() => setExpanded((value) => !value)} className="flex shrink-0 items-center gap-2 text-left" title={expanded ? "Collapse engineering dock" : "Expand engineering dock"}>
          <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Engineering dock</span>
          <ChevronUp className={cn("size-3.5 text-primary transition-transform", !expanded && "rotate-180")} />
        </button>
        {ITEMS.map((item) => {
          const { key, label, icon: Icon, accent, format } = item;
          const raw = stats[key as keyof SummaryStats];
          const value = loading ? "…" : formatValue(key, raw, stats, format);
          const href = metricHref(key);
          const chip = (
            <div
              className="flex items-center gap-1.5 rounded-lg border border-border bg-card/80 px-2.5 py-1 transition-colors hover:bg-surface-hover"
              title={`${label}: ${value}`}
            >
              <Icon className={cn("h-3 w-3 shrink-0", accent)} />
              <span className="hidden text-[9px] text-muted-foreground xl:inline">{label}</span>
              <span className="font-data text-[11px] font-medium whitespace-nowrap text-foreground">
                {value}
              </span>
            </div>
          );

          return (
            <div key={key} className="flex items-center shrink-0">
              {editor ? <button onClick={() => setExpanded(true)} title={`Expand ${label} analysis`}>{chip}</button> : href ? <Link href={href}>{chip}</Link> : chip}
            </div>
          );
        })}
      </div>
      {onCreditsContainerChange && <div hidden ref={onCreditsContainerChange} aria-label="Map source attribution" className="workspace-map-attribution min-w-0 basis-full text-[9px]" />}
      </div>
      {expanded && editor && project ? <EngineeringDockPanel key={dockTab} initialTab={dockTab} editor={editor} project={project}/> : expanded && (
        <div className="mt-3 grid grid-cols-4 gap-2 border-t border-white/10 pt-3">
          <div className="col-span-2 rounded-lg border border-border bg-black/10 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Quantities</p><p className="mt-1 text-xs text-muted-foreground">Values are calculated from the current project summary when available.</p></div>
          <div className="rounded-lg border border-border bg-black/10 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Profile</p><p className="mt-1 text-xs text-muted-foreground">Open the alignment view to inspect terrain and grade.</p></div>
          <div className="rounded-lg border border-border bg-black/10 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Risks</p><p className="mt-1 text-xs text-muted-foreground">No additional risk findings are available here.</p></div>
        </div>
      )}
    </div>
  );
}


