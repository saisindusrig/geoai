"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { ArrowLeft, GitCompare, Pin } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import ChartCard from "@/components/project-results/ChartCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import { StatusPill } from "@/components/project-results/StatusPill";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import ScenarioComparePanel from "@/components/workspace/ScenarioComparePanel";
import { useProjectData } from "@/hooks/useProjectData";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format-display";
import { CHART } from "@/lib/chart-theme";
import { formatCurrency } from "@/lib/utils";
import type { ScenarioCompareResult, ScenarioSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

type Filter = "all" | "latest" | "completed";

const pinStorageKey = (projectId: number) => `project-${projectId}-pinned-scenario`;

export default function ScenarioComparePage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, scenarioSummaries, loading, error, load, summaryStats, selectScenario } =
    useProjectData(projectId);
  const [filter, setFilter] = useState<Filter>("completed");
  const [selectedCompare, setSelectedCompare] = useState<number[]>([]);
  const [compareResult, setCompareResult] = useState<ScenarioCompareResult | null>(null);
  const [comparing, setComparing] = useState(false);
  const [pinVersion, setPinVersion] = useState(0);

  const pinnedId = useMemo(() => {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(pinStorageKey(projectId));
    return raw ? Number(raw) : null;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- pinVersion bumps after pin toggle
  }, [projectId, pinVersion]);

  const filtered = useMemo(() => {
    let list = [...scenarioSummaries];
    if (filter === "completed") list = list.filter((s) => s.status === "completed");
    if (filter === "latest")
      list = list.sort((a, b) => +new Date(b.created_at ?? 0) - +new Date(a.created_at ?? 0)).slice(0, 3);
    return list;
  }, [scenarioSummaries, filter]);

  const completed = useMemo(
    () => scenarioSummaries.filter((s) => s.status === "completed"),
    [scenarioSummaries],
  );

  const chartData = useMemo(() => {
    const durationById = new Map(
      (compareResult?.rows ?? []).map((r) => [r.scenario_id, r.duration_months ?? 0]),
    );
    return completed.map((s) => ({
      name: s.name.length > 14 ? `${s.name.slice(0, 12)}…` : s.name,
      cost: s.cost_total ?? 0,
      cement: s.materials_summary?.concrete_m3 ?? 0,
      steel: (s.materials_summary?.steel_kg ?? 0) / 1000,
      duration: durationById.get(s.scenario_id) ?? s.duration_months ?? 0,
    }));
  }, [completed, compareResult]);

  const bestCost = useMemo(() => {
    if (chartData.length === 0) return null;
    const costs = chartData.map((d) => d.cost).filter((c) => c > 0);
    return costs.length ? Math.min(...costs) : null;
  }, [chartData]);

  const toggleCompare = (id: number) => {
    setSelectedCompare((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 4) return prev;
      return [...prev, id];
    });
  };

  const togglePin = (id: number) => {
    const key = pinStorageKey(projectId);
    if (pinnedId === id) localStorage.removeItem(key);
    else localStorage.setItem(key, String(id));
    setPinVersion((v) => v + 1);
  };

  const runCompare = useCallback(async () => {
    if (selectedCompare.length < 2) return;
    setComparing(true);
    try {
      const result = await api.post<ScenarioCompareResult>(
        `/api/projects/${projectId}/scenarios/compare`,
        { scenario_ids: selectedCompare },
      );
      setCompareResult(result);
    } finally {
      setComparing(false);
    }
  }, [projectId, selectedCompare]);

  if (loading) return <ProjectLoading message="Loading scenarios…" />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats} maxWidth="max-w-[1400px]">
      <ResultPageHeader
        title="Scenario Comparison"
        subtitle="Compare cost, validation, geometry modes, and warnings across design runs."
        status={completed.length >= 2 ? "Ready to compare" : "Need more scenarios"}
        statusVariant={completed.length >= 2 ? "success" : "warning"}
        actions={
          <div className="flex flex-wrap gap-2">
            {selectedCompare.length >= 2 && (
              <Button size="sm" className="gap-1.5" disabled={comparing} onClick={runCompare}>
                <GitCompare className="h-3.5 w-3.5" />
                Compare {selectedCompare.length}
              </Button>
            )}
            <Link href={`/projects/${projectId}/workspace`}>
              <Button variant="secondary" size="sm" className="gap-1.5">
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Studio
              </Button>
            </Link>
          </div>
        }
      />

      <div className="flex flex-wrap gap-2">
        {(
          [
            { id: "completed" as const, label: "Completed" },
            { id: "latest" as const, label: "Latest" },
            { id: "all" as const, label: "All" },
          ] as const
        ).map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setFilter(id)}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-[11px] font-medium transition-all",
              filter === id
                ? "border-[rgba(59,130,246,0.4)] bg-[rgba(59,130,246,0.15)] text-primary"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {completed.length < 2 ? (
        <GlassCard className="p-10">
          <EmptyState
            icon={GitCompare}
            title="Generate another design scenario"
            description="Create at least two completed scenarios with different parameters to compare alternatives."
          />
          <div className="mt-6 flex justify-center">
            <Link href={`/projects/${projectId}/workspace`}>
              <Button size="sm">Open AI Design Studio</Button>
            </Link>
          </div>
        </GlassCard>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { title: "Cost (medium)", key: "cost" as const, format: (v: number) => formatCurrency(v) },
              { title: "Concrete (m³)", key: "cement" as const, format: (v: number) => v.toLocaleString("en-IN") },
              { title: "Steel (tonnes)", key: "steel" as const, format: (v: number) => v.toFixed(1) },
              { title: "Duration (mo)", key: "duration" as const, format: (v: number) => v.toFixed(1) },
            ].map(({ title, key, format }) => (
              <ChartCard key={key} title={title} height="h-44 sm:h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 9, fill: CHART.tick }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 9, fill: CHART.tick }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => format(Number(v))} contentStyle={CHART.tooltip} />
                    <Bar dataKey={key} fill={CHART.accent} radius={[4, 4, 0, 0]} maxBarSize={36} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            ))}
          </div>

          <GlassCard className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="data-table w-full min-w-[720px]">
                <thead>
                  <tr>
                    <th className="sticky left-0 z-10 bg-background-secondary min-w-[140px]">Metric</th>
                    {completed.map((s) => (
                      <th key={s.scenario_id} className="min-w-[160px]">
                        <span className="block truncate">{s.name}</span>
                        <StatusPill label={s.status} variant={s.status === "completed" ? "success" : "warning"} className="mt-1" />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      label: "Cost",
                      get: (s: ScenarioSummary) => s.cost_total,
                      format: (v: number | null | undefined) => (v != null ? formatCurrency(v) : "—"),
                      best: "min" as const,
                    },
                    {
                      label: "Validation score",
                      get: (s: ScenarioSummary) => s.validation_score,
                      format: (v: number | null | undefined) => (v != null ? String(v) : "—"),
                      best: "max" as const,
                    },
                    {
                      label: "Validation status",
                      get: (s: ScenarioSummary) => s.validation_status,
                      format: (v: string | null | undefined) => v ?? "—",
                    },
                    {
                      label: "Length (m)",
                      get: (s: ScenarioSummary) => s.length_m,
                      format: (v: number | null | undefined) => (v != null ? String(v) : "—"),
                    },
                    {
                      label: "Lanes / width",
                      get: (s: ScenarioSummary) =>
                        [s.lanes != null ? `${s.lanes} ln` : null, s.width_m != null ? `${s.width_m}m` : null]
                          .filter(Boolean)
                          .join(" · ") || null,
                      format: (v: string | null) => v ?? "—",
                    },
                    {
                      label: "Max grade %",
                      get: (s: ScenarioSummary) => s.max_grade_percent,
                      format: (v: number | null | undefined) => (v != null ? v.toFixed(1) : "—"),
                    },
                    {
                      label: "Geometry / elevation",
                      get: (s: ScenarioSummary) => `${s.geometry_mode ?? "—"} / ${s.elevation_mode ?? "—"}`,
                      format: (v: string) => v,
                    },
                    {
                      label: "Warnings",
                      get: (s: ScenarioSummary) => s.warning_count ?? 0,
                      format: (v: number) => String(v),
                      best: "min" as const,
                    },
                  ].map((row) => {
                    const values = completed.map((s) => row.get(s));
                    const numeric = values.filter((v): v is number => typeof v === "number");
                    const bestVal =
                      "best" in row && row.best === "min" && numeric.length
                        ? Math.min(...numeric)
                        : "best" in row && row.best === "max" && numeric.length
                          ? Math.max(...numeric)
                          : null;
                    return (
                      <tr key={row.label}>
                        <td className="sticky left-0 z-10 bg-background-secondary text-xs font-medium text-muted-foreground">
                          {row.label}
                        </td>
                        {completed.map((s, i) => {
                          const raw = values[i];
                          const display = row.format(raw as never);
                          const isBest = typeof raw === "number" && bestVal != null && raw === bestVal;
                          return (
                            <td
                              key={s.scenario_id}
                              className={cn("text-xs font-data", isBest && "text-[#34D399] font-semibold")}
                            >
                              {display}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}

      {filtered.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((s) => {
            const isBest = s.cost_total != null && bestCost != null && s.cost_total === bestCost;
            const checked = selectedCompare.includes(s.scenario_id);
            const isPinned = pinnedId === s.scenario_id;
            return (
              <GlassCard
                key={s.scenario_id}
                className={cn(
                  "p-4",
                  isBest && "border-[rgba(16,185,129,0.35)]",
                  isPinned && "border-[rgba(59,130,246,0.35)]",
                )}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleCompare(s.scenario_id)}
                      className="mt-1 shrink-0"
                      title="Include in compare"
                    />
                    <h3 className="text-sm font-semibold text-foreground truncate">{s.name}</h3>
                  </div>
                  <StatusPill label={s.status} variant={s.status === "completed" ? "success" : "warning"} />
                </div>
                <p className="text-[11px] text-muted-foreground mb-3">{formatDateTime(s.created_at ?? "")}</p>
                <dl className="grid grid-cols-2 gap-2 text-[11px] mb-3">
                  <div>
                    <dt className="text-muted-foreground">Cost</dt>
                    <dd className="font-data font-medium text-foreground">
                      {s.cost_total != null ? formatCurrency(s.cost_total, s.cost_currency) : "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Validation</dt>
                    <dd className="font-data font-medium text-foreground">
                      {s.validation_status ?? "—"}
                      {s.validation_score != null ? ` (${s.validation_score})` : ""}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Steel</dt>
                    <dd className="font-data text-foreground-secondary">
                      {s.materials_summary?.steel_kg?.toLocaleString("en-IN") ?? "—"} kg
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Warnings</dt>
                    <dd className="font-data text-foreground-secondary">{s.warning_count ?? 0}</dd>
                  </div>
                </dl>
                <p className="text-[11px] text-muted-foreground line-clamp-2 mb-3">
                  {s.generation_mode ?? "—"} · {s.geometry_mode ?? "—"} / {s.elevation_mode ?? "—"}
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    className="flex-1 h-8 text-[11px]"
                    onClick={() => void selectScenario(s)}
                  >
                    View in studio
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className={cn("h-8 px-2", isPinned && "text-primary")}
                    title={isPinned ? "Unpin scenario" : "Pin scenario"}
                    onClick={() => togglePin(s.scenario_id)}
                  >
                    <Pin className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </GlassCard>
            );
          })}
        </div>
      )}

      {compareResult && (
        <ScenarioComparePanel
          result={compareResult}
          summaries={scenarioSummaries}
          onClose={() => setCompareResult(null)}
        />
      )}
    </ProjectResultShell>
  );
}
