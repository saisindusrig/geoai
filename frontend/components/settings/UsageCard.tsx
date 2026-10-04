"use client";

import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { UsageMetric, UsageSummary } from "@/lib/types";

function UsageBar({ label, metric }: { label: string; metric: UsageMetric }) {
  const unlimited = metric.unlimited || metric.max == null || metric.max === 0;
  const current = metric.current ?? 0;
  const max = metric.max ?? 0;
  const ratio = unlimited ? 0 : max === 0 ? 1 : current / max;
  const pct = unlimited ? 100 : Math.min(100, Math.round(ratio * 100));
  const tone = unlimited ? "bg-primary/35" : ratio >= 1 ? "bg-destructive" : ratio >= 0.8 ? "bg-warning" : "bg-primary";
  const value = unlimited ? "Unlimited" : `${current.toLocaleString()} / ${max.toLocaleString()}`;
  const over = !unlimited && current > max;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className={`font-mono text-xs ${over ? "text-destructive" : "text-foreground"}`}>{value}</span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function UsageCard() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<UsageSummary>("/api/usage/summary")
      .then(setSummary)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <Card float className="h-full">
      <CardHeader className="flex-row items-start gap-3 space-y-0">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/15">
          <BarChart3 className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <CardTitle>Plan & usage</CardTitle>
            {summary && (
              <Badge variant="primary" className="capitalize">
                {summary.plan}
              </Badge>
            )}
          </div>
          <CardDescription>Daily limits and project quotas for your account</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!summary && !error && <p className="text-sm text-muted-foreground">Loading usage…</p>}
        {summary && (
          <>
            <UsageBar label="Projects" metric={summary.projects} />
            <UsageBar label="Generations today" metric={summary.generations_today} />
            <UsageBar label="AI plans today" metric={summary.llm_plans_today} />
            <UsageBar label="Exports today" metric={summary.exports_today} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
