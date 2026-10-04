"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Download, TrendingUp } from "lucide-react";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import ChartCard from "@/components/project-results/ChartCard";
import MetricCard from "@/components/project-results/MetricCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import ScenarioSelector from "@/components/scenarios/ScenarioSelector";
import { StatusPill } from "@/components/project-results/StatusPill";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { useProjectData } from "@/hooks/useProjectData";
import { api, apiUrl } from "@/lib/api";
import { pctDiff } from "@/lib/format-display";
import { CHART } from "@/lib/chart-theme";
import { formatCurrency } from "@/lib/utils";

const PHASES = ["all", "foundation", "structure", "road", "pipeline", "finishing"] as const;
const CAT_COLORS = CHART.colors;

export default function CostDashboardPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, scenarios, scenarioSummaries, scenario, selectScenario, estimate, calc, summaryStats, loading, error, load } =
    useProjectData(projectId);
  const [phase, setPhase] = useState<(typeof PHASES)[number]>("all");
  const [scenarioEstimate, setScenarioEstimate] = useState(estimate);

  const scenarioId = scenario?.id;

  useEffect(() => {
    let cancelled = false;
    const qs = scenarioId ? `?scenario_id=${scenarioId}` : "";
    api
      .getOptional<typeof estimate>(`/api/projects/${projectId}/estimates${qs}`)
      .then((e) => {
        if (!cancelled) setScenarioEstimate(e);
      })
      .catch(() => {
        if (!cancelled) setScenarioEstimate(null);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, scenarioId, estimate]);

  const activeEstimate = scenarioEstimate ?? estimate;
  const activeCalc = scenario?.design_output_json?.calculated ?? calc;

  const filteredItems = useMemo(() => {
    if (!activeEstimate) return [];
    if (phase === "all") return activeEstimate.line_items;
    return activeEstimate.line_items.filter(
      (i) => i.category.toLowerCase().includes(phase) || i.item_name.toLowerCase().includes(phase),
    );
  }, [activeEstimate, phase]);

  const categoryData = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of filteredItems) {
      map.set(item.category, (map.get(item.category) ?? 0) + item.quantity * item.rate);
    }
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [filteredItems]);

  const costBreakdown = useMemo(() => {
    if (!activeCalc?.cost_summary) return [];
    const c = activeCalc.cost_summary;
    return [
      { name: "Direct", value: c.direct_cost },
      { name: "Contingency", value: c.contingency },
      { name: "Design/Survey", value: c.design_survey_approval },
    ].filter((x) => x.value > 0);
  }, [activeCalc]);

  const largestDriver = useMemo(() => {
    if (categoryData.length === 0) return null;
    const top = [...categoryData].sort((a, b) => b.value - a.value)[0];
    return top;
  }, [categoryData]);

  const lineSubtotal = useMemo(
    () => filteredItems.reduce((s, i) => s + i.quantity * i.rate, 0),
    [filteredItems],
  );

  if (loading) return <ProjectLoading />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const cost = activeCalc?.cost_summary;

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats}>
      <ResultPageHeader
        title="Cost Analysis"
        subtitle="Compare low, medium, and high preliminary cost estimates by category."
        status={activeEstimate ? undefined : "Pending design"}
        actions={
          activeEstimate ? (
            <a href={apiUrl(`/api/projects/${projectId}/exports/csv`)}>
              <Button size="sm" variant="secondary" className="gap-1.5">
                <Download className="h-3.5 w-3.5" />
                Export Cost Summary
              </Button>
            </a>
          ) : undefined
        }
      />

      <div className="max-w-xs">
        <ScenarioSelector
          projectId={projectId}
          scenarios={scenarios}
          selectedId={scenario?.id ?? null}
          onSelect={(s) => {
            const summary = scenarioSummaries.find((x) => x.scenario_id === s.id);
            if (summary) void selectScenario(summary);
          }}
        />
      </div>

      {!activeEstimate && (
        <GlassCard className="p-8">
          <EmptyState
            title="No cost data yet"
            description="Generate a design first to see cost breakdowns and charts."
          />
        </GlassCard>
      )}

      {activeEstimate && (
        <>
          <div className="overflow-x-auto scrollbar-none -mx-1 px-1">
            <Tabs
              tabs={PHASES.map((p) => ({
                id: p,
                label: p === "all" ? "All Phases" : p.charAt(0).toUpperCase() + p.slice(1),
              }))}
              active={phase}
              onChange={(id) => setPhase(id as typeof phase)}
              className="min-w-max"
            />
          </div>

          {cost && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <MetricCard
                label="Low estimate"
                value={formatCurrency(cost.total_low, cost.currency)}
                unit={pctDiff(cost.total_low, cost.total_medium) ? `${pctDiff(cost.total_low, cost.total_medium)} vs medium` : undefined}
              />
              <MetricCard
                label="Medium estimate"
                value={formatCurrency(cost.total_medium, cost.currency)}
                unit="Default planning estimate"
                highlight
              />
              <MetricCard
                label="High estimate"
                value={formatCurrency(cost.total_high, cost.currency)}
                unit={pctDiff(cost.total_medium, cost.total_high) ? `${pctDiff(cost.total_medium, cost.total_high)} vs medium` : undefined}
              />
            </div>
          )}

          {largestDriver && (
            <GlassCard className="flex items-center gap-3 px-4 py-3">
              <TrendingUp className="h-4 w-4 text-accent shrink-0" />
              <p className="text-sm text-muted-foreground">
                Largest cost driver:{" "}
                <span className="font-medium text-foreground">{largestDriver.name}</span>
                <span className="font-data text-primary ml-2">
                  {formatCurrency(largestDriver.value, cost?.currency)}
                </span>
              </p>
            </GlassCard>
          )}

          <div className="grid gap-6 lg:grid-cols-2 lg:items-stretch">
            <ChartCard title="Cost by category" subtitle="Amount in INR">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: CHART.tick }} axisLine={false} tickLine={false} />
                  <YAxis
                    tick={{ fontSize: 9, fill: CHART.tick }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => (v >= 1e7 ? `${(v / 1e7).toFixed(1)}Cr` : `${(v / 1e5).toFixed(0)}L`)}
                  />
                  <Tooltip contentStyle={CHART.tooltip} formatter={(v) => formatCurrency(Number(v), cost?.currency)} />
                  <Bar dataKey="value" fill={CHART.primary} radius={[6, 6, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Cost composition" subtitle="Direct, contingency & approvals">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={costBreakdown}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="45%"
                    innerRadius={48}
                    outerRadius={72}
                    paddingAngle={2}
                  >
                    {costBreakdown.map((_, i) => (
                      <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={CHART.tooltip} formatter={(v) => formatCurrency(Number(v), cost?.currency)} />
                  <Legend
                    wrapperStyle={{ fontSize: 11, color: CHART.tick }}
                    formatter={(value, entry) => {
                      const val = (entry.payload as { value: number })?.value;
                      const total = costBreakdown.reduce((s, x) => s + x.value, 0);
                      const pct = total ? Math.round((val / total) * 100) : 0;
                      return `${value} (${pct}%)`;
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <GlassCard className="overflow-hidden">
            <div className="border-b border-border px-4 py-3 flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">Line items</h3>
              <StatusPill label="Preliminary" variant="warning" />
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full min-w-[640px]">
                <thead>
                  <tr>
                    {["Item", "Category", "Qty", "Rate", "Amount"].map((h, i) => (
                      <th key={h} className={i >= 2 ? "text-right" : undefined}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item, i) => {
                    const catIdx = categoryData.findIndex((c) => c.name === item.category);
                    return (
                      <tr key={i}>
                        <td>
                          <span className="inline-flex items-center gap-2">
                            <span
                              className="h-2 w-2 rounded-full shrink-0"
                              style={{ background: CAT_COLORS[catIdx >= 0 ? catIdx % CAT_COLORS.length : 0] }}
                            />
                            {item.item_name}
                          </span>
                        </td>
                        <td className="text-xs text-muted-foreground">{item.category}</td>
                        <td className="text-right font-data text-xs">
                          {item.quantity.toLocaleString("en-IN")} {item.unit}
                        </td>
                        <td className="text-right font-data text-xs">{item.rate.toLocaleString("en-IN")}</td>
                        <td className="text-right font-medium font-data">
                          {(item.quantity * item.rate).toLocaleString("en-IN")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot className="border-t border-border bg-background/95">
                  <tr className="font-semibold text-foreground">
                    <td colSpan={4} className="text-right py-2.5">
                      Subtotal
                    </td>
                    <td className="text-right py-2.5 font-data text-primary">
                      {lineSubtotal.toLocaleString("en-IN")}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </ProjectResultShell>
  );
}
