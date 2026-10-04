"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { CheckCircle2, Circle, Clock, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import MetricCard from "@/components/project-results/MetricCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import { StatusPill } from "@/components/project-results/StatusPill";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { useProjectData } from "@/hooks/useProjectData";
import { cn } from "@/lib/utils";

export default function TimelinePage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, design, calc, summaryStats, loading, error, load } = useProjectData(projectId);

  const sequence = useMemo(
    () => design?.construction_sequence ?? [],
    [design?.construction_sequence],
  );
  const timeline = calc?.timeline;
  const months = timeline?.estimated_months_medium as number | undefined;
  const timelineNote = typeof timeline?.note === "string" ? timeline.note : null;

  const phaseMonths = useMemo(() => {
    if (!months || sequence.length === 0) return [];
    const perPhase = months / sequence.length;
    return sequence.map(() => Math.round(perPhase * 10) / 10);
  }, [months, sequence]);

  if (loading) return <ProjectLoading />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const downloadTimeline = () => {
    if (!design) return;
    const payload = {
      project: project.name,
      disclaimer: "Preliminary planning only — not for construction approval",
      timeline,
      construction_sequence: sequence,
      required_permissions: design.required_permissions,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${project.name.replace(/\s+/g, "-").toLowerCase()}-timeline.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats} maxWidth="max-w-5xl">
      <ResultPageHeader
        title="Construction Timeline"
        subtitle="Preliminary construction sequence and duration estimate."
        status={design ? undefined : "Pending design"}
        actions={
          design ? (
            <Button variant="secondary" size="sm" className="gap-2" onClick={downloadTimeline}>
              <Download className="h-3.5 w-3.5" />
              Download Timeline
            </Button>
          ) : undefined
        }
      />

      {!design && (
        <GlassCard className="p-8">
          <EmptyState
            icon={Clock}
            title="No timeline yet"
            description="Generate a design to see the construction sequence and duration estimates."
          />
        </GlassCard>
      )}

      {design && (
        <>
          <div className="grid sm:grid-cols-3 gap-3">
            <MetricCard label="Duration (low)" value={timeline?.estimated_months_low != null ? `${timeline.estimated_months_low}` : "—"} unit="months" />
            <MetricCard label="Duration (medium)" value={months != null ? `${months}` : "—"} unit="months — planning default" highlight />
            <MetricCard label="Duration (high)" value={timeline?.estimated_months_high != null ? `${timeline.estimated_months_high}` : "—"} unit="months" />
          </div>

          <GlassCard className="p-4 sm:p-6">
            <div className="flex items-center gap-2 mb-6">
              <h3 className="text-sm font-semibold text-foreground">Construction sequence</h3>
              <StatusPill label="Preliminary" variant="warning" />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
              <div className="space-y-0">
                {sequence.map((step, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-full border",
                          i === 0
                            ? "border-primary/40 bg-primary/10 text-primary"
                            : "border-border bg-background-secondary text-muted-foreground",
                        )}
                      >
                        {i < sequence.length - 1 ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : (
                          <Circle className="h-4 w-4" />
                        )}
                      </div>
                      {i < sequence.length - 1 && (
                        <div className="w-px flex-1 bg-[rgba(148,163,184,0.2)] min-h-[20px]" />
                      )}
                    </div>
                    <div className="pb-5 pt-0.5 flex-1">
                      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Phase {i + 1}</p>
                      <p className="text-sm font-medium text-foreground mt-0.5">{step}</p>
                      {phaseMonths[i] != null && (
                        <p className="text-[11px] text-muted-foreground mt-0.5 font-data">~{phaseMonths[i]} months</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="hidden lg:block rounded-lg border border-border bg-background-secondary/80 p-4">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-3">Gantt preview</p>
                <div className="space-y-2">
                  {sequence.map((step, i) => {
                    const widthPct = months
                      ? Math.min(95, ((phaseMonths[i] ?? months / sequence.length) / months) * 100)
                      : Math.min(95, 35 + (i + 1) * (55 / Math.max(sequence.length, 1)));
                    return (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-[9px] text-muted-foreground w-4 shrink-0">{i + 1}</span>
                      <div className="flex-1 h-5 rounded bg-[rgba(148,163,184,0.08)] overflow-hidden">
                        <div
                          className="h-full rounded bg-primary/70"
                          style={{ width: `${widthPct}%` }}
                          title={step}
                        />
                      </div>
                    </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </GlassCard>

          {design.required_permissions.length > 0 && (
            <GlassCard className="p-4 sm:p-5">
              <h3 className="text-sm font-semibold text-foreground mb-3">Required permissions & surveys</h3>
              <ul className="space-y-2">
                {design.required_permissions.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-accent mt-0.5" />
                    {p}
                  </li>
                ))}
              </ul>
            </GlassCard>
          )}

          <p className="text-[11px] leading-relaxed text-muted-foreground border-l-2 border-[rgba(245,158,11,0.4)] pl-3">
            {timelineNote ??
              "Timeline excludes approval delays, monsoon impact, land acquisition, and utility shifting unless explicitly modeled."}
          </p>
        </>
      )}
    </ProjectResultShell>
  );
}
