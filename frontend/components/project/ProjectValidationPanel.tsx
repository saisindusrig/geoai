"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import AccuracyBadge from "@/components/survey/AccuracyBadge";
import { SidebarStatChip, SidebarStatusCard } from "@/components/layout/SidebarStatusCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { AccuracyTier, ProjectValidation } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function ProjectValidationPanel({
  projectId,
  compact,
  className,
}: {
  projectId: number;
  compact?: boolean;
  className?: string;
  /** @deprecated Details are always visible in compact mode */
  defaultDetailsOpen?: boolean;
}) {
  const [validation, setValidation] = useState<ProjectValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<ProjectValidation>(`/api/projects/${projectId}/validation`);
      setValidation(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation unavailable");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  if (loading) {
    return (
      <SidebarStatusCard title="Readiness" className={className}>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Checking…
        </div>
      </SidebarStatusCard>
    );
  }

  if (error || !validation) {
    return (
      <SidebarStatusCard title="Readiness" className={className}>
        <p className="text-[11px] text-muted-foreground">{error ?? "Could not load"}</p>
        <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2 w-full" onClick={() => void load()}>
          Retry
        </Button>
      </SidebarStatusCard>
    );
  }

  const tier = validation.accuracy_tier as AccuracyTier;
  const passedCount = validation.checks.filter((c) => c.passed).length;
  const failedChecks = validation.checks.filter((c) => !c.passed);
  const topIssues = failedChecks.slice(0, 2);
  const nextStep = validation.recommended_next_steps[0];
  const progress = validation.checks.length
    ? Math.round((passedCount / validation.checks.length) * 100)
    : 0;

  const body = (
    <>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between gap-2 text-[10px]">
          <span className="text-muted-foreground">
            {passedCount}/{validation.checks.length} checks complete
          </span>
          <span className="font-data text-foreground-secondary">{progress}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.08]">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              validation.ready_for_design ? "bg-[#10B981]" : "bg-gradient-to-r from-[#F59E0B] to-[#3B82F6]",
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex gap-1">
        <SidebarStatChip label="Design" ok={validation.ready_for_design} />
        <SidebarStatChip label="BOQ" ok={validation.ready_for_boq} />
        <SidebarStatChip label="Export" ok={validation.ready_for_export} />
      </div>

      <div className="flex flex-wrap items-center gap-1 text-[10px]">
        {validation.database_mode === "sqlite" && (
          <span className="rounded-full border border-warning/25 bg-warning/10 px-2 py-0.5 text-warning shrink-0">
            Limited GIS mode
          </span>
        )}
        {!validation.ready_for_design && (
          <span className="rounded-full border border-[rgba(245,158,11,0.25)] bg-[rgba(245,158,11,0.1)] px-2 py-0.5 text-[#FCD34D]">
            Action needed
          </span>
        )}
      </div>

      {topIssues.length > 0 && (
        <ul className="space-y-1">
          {topIssues.map((c) => (
            <li key={c.id} className="flex gap-1.5 text-[10px] leading-snug">
              {c.severity === "error" ? (
                <AlertTriangle className="h-3 w-3 shrink-0 text-destructive mt-0.5" />
              ) : (
                <Circle className="h-3 w-3 shrink-0 text-warning mt-0.5" />
              )}
              <span className="text-muted-foreground line-clamp-2">{c.detail}</span>
            </li>
          ))}
        </ul>
      )}

      {failedChecks.length === 0 && (
        <div className="flex items-center gap-1.5 text-[10px] text-[#4ADE80]">
          <CheckCircle2 className="h-3 w-3 shrink-0" />
          All checks passed
        </div>
      )}

      {nextStep && (
        <div className="space-y-1.5 border-t border-border/50 pt-2">
          <p className="text-[10px] text-primary/90 leading-snug">Next: {nextStep}</p>
          <div className="grid grid-cols-1 gap-1">
            {["Import survey DEM", "Draw alignment", "Run site analysis"].map((label) => (
              <button
                key={label}
                type="button"
                className="h-6 rounded-md border border-[rgba(148,163,184,0.14)] bg-white/[0.03] px-2 text-left text-[10px] text-foreground-secondary hover:bg-surface-hover"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );

  if (compact) {
    return (
      <SidebarStatusCard
        title="Readiness"
        trailing={<AccuracyBadge tier={tier} compact />}
        className={className}
      >
        {body}
      </SidebarStatusCard>
    );
  }

  return (
    <Card className={cn("border-border/80", className)}>
      <CardHeader className="p-4 pb-2 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-semibold">Readiness</span>
          <AccuracyBadge tier={tier} compact />
        </div>
        {body}
      </CardHeader>
      <CardContent className="p-4 pt-0">
        <p className="text-[10px] text-muted-foreground border-l-2 border-primary pl-2 leading-snug">
          {validation.disclaimer}
        </p>
      </CardContent>
    </Card>
  );
}
