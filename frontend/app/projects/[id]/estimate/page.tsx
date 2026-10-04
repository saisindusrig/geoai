"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Box, Download, GitCompare, Layers, Save, Package, Shovel } from "lucide-react";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import ScenarioSelector from "@/components/scenarios/ScenarioSelector";
import ChartCard from "@/components/project-results/ChartCard";
import CostRangeCards from "@/components/project-results/CostRangeCards";
import MetricCard from "@/components/project-results/MetricCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { useProjectData } from "@/hooks/useProjectData";
import { api, apiUrl } from "@/lib/api";
import { CHART } from "@/lib/chart-theme";
import { toastPromise } from "@/lib/toast";
import type { LineItem, QuantityEstimate } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

const PHASES = ["all", "foundation", "structure", "road", "pipeline", "finishing"] as const;

export default function EstimatePage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, scenarios, scenarioSummaries, scenario, selectScenario, summaryStats, loading, error, load } =
    useProjectData(projectId);
  const [estimate, setEstimate] = useState<QuantityEstimate | null>(null);
  const [items, setItems] = useState<LineItem[]>([]);
  const [dirty, setDirty] = useState(false);
  const [loadErr, setLoadErr] = useState("");
  const [phase, setPhase] = useState<(typeof PHASES)[number]>("all");

  const scenarioId = scenario?.id;

  useEffect(() => {
    let cancelled = false;
    const qs = scenarioId ? `?scenario_id=${scenarioId}` : "";
    api
      .getOptional<QuantityEstimate>(`/api/projects/${projectId}/estimates${qs}`)
      .then((e) => {
        if (!cancelled) {
          setEstimate(e);
          setItems(e?.line_items ?? []);
          setLoadErr("");
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setLoadErr(String(e instanceof Error ? e.message : e));
          setEstimate(null);
          setItems([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, scenarioId]);

  const filteredItems = useMemo(() => {
    if (phase === "all") return items;
    return items.filter(
      (i) => i.category.toLowerCase().includes(phase) || i.item_name.toLowerCase().includes(phase),
    );
  }, [items, phase]);

  const categorySubtotals = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of filteredItems) {
      map.set(item.category, (map.get(item.category) ?? 0) + item.quantity * item.rate);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [filteredItems]);

  const footerTotal = useMemo(
    () => filteredItems.reduce((s, i) => s + i.quantity * i.rate, 0),
    [filteredItems],
  );

  const materialChart = useMemo(() => {
    if (!estimate) return [];
    return [
      { name: "Cement", value: estimate.cement_bags, unit: "bags" },
      { name: "Steel", value: estimate.steel_kg / 1000, unit: "t" },
      { name: "Concrete", value: estimate.concrete_m3, unit: "m³" },
      { name: "Excavation", value: estimate.excavation_m3, unit: "m³" },
    ];
  }, [estimate]);

  const updateItem = (i: number, field: "quantity" | "rate", value: number) => {
    setItems((prev) =>
      prev.map((item, idx) => (idx === i ? { ...item, [field]: value, amount: 0 } : item)),
    );
    setDirty(true);
  };

  const save = async () => {
    if (!estimate) return;
    await toastPromise(
      api.put<QuantityEstimate>(
        `/api/projects/${projectId}/estimates/${estimate.id}/line-items`,
        { line_items: items },
      ),
      { loading: "Saving BOQ…", success: "BOQ saved" },
    ).then((updated) => {
      setEstimate(updated);
      setItems(updated.line_items);
      setDirty(false);
    });
  };

  const calc = scenario?.design_output_json?.calculated;
  const cost = calc?.cost_summary;

  if (loading) return <ProjectLoading />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats}>
      <ResultPageHeader
        title="Material Estimation & BOQ"
        subtitle="Preliminary quantity takeoff and bill of quantities for the selected design scenario."
        status={estimate ? "Completed" : "Pending design"}
        statusVariant={estimate ? "success" : "warning"}
        actions={
          <>
            {dirty && (
              <Button size="sm" className="gap-1.5 " onClick={save}>
                <Save className="h-3.5 w-3.5" />
                Save BOQ
              </Button>
            )}
            <Link href={`/projects/${projectId}/scenarios`}>
              <Button size="sm" variant="secondary" className="gap-1.5">
                <GitCompare className="h-3.5 w-3.5" />
                Compare
              </Button>
            </Link>
            <a href={apiUrl(`/api/projects/${projectId}/exports/csv`)}>
              <Button size="sm" variant="secondary" className="gap-1.5">
                <Download className="h-3.5 w-3.5" />
                Export CSV
              </Button>
            </a>
          </>
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

      {loadErr && (
        <GlassCard className="p-6">
          <EmptyState
            icon={Package}
            title="No BOQ available yet"
            description={`${loadErr} — generate a design in AI Design Studio first.`}
          />
        </GlassCard>
      )}

      {estimate && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <MetricCard label="Concrete" value={estimate.concrete_m3.toLocaleString("en-IN")} unit="m³" icon={Layers} />
            <MetricCard label="Cement" value={estimate.cement_bags.toLocaleString("en-IN")} unit="bags" icon={Box} />
            <MetricCard label="Steel" value={estimate.steel_kg.toLocaleString("en-IN")} unit="kg" icon={Layers} />
            <MetricCard label="Excavation" value={estimate.excavation_m3.toLocaleString("en-IN")} unit="m³" icon={Shovel} />
            <MetricCard
              label="Total Cost"
              value={formatCurrency(estimate.total_cost_estimate, cost?.currency)}
              highlight
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2 lg:items-stretch">
            <ChartCard title="Material quantities" subtitle="Preliminary takeoff by material type">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={materialChart} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: CHART.tick }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: CHART.tick }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={CHART.tooltip}
                    formatter={(v, _n, p) => {
                      const unit = (p?.payload as { unit?: string })?.unit ?? "";
                      return [`${Number(v).toLocaleString("en-IN")} ${unit}`, "Qty"];
                    }}
                  />
                  <Bar dataKey="value" fill={CHART.accent} radius={[6, 6, 0, 0]} maxBarSize={48} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {cost ? (
              <CostRangeCards
                low={cost.total_low}
                medium={cost.total_medium}
                high={cost.total_high}
                currency={cost.currency}
              />
            ) : (
              <GlassCard className="p-6 flex items-center justify-center">
                <p className="text-sm text-muted-foreground">Cost range appears after design generation.</p>
              </GlassCard>
            )}
          </div>

          <GlassCard className="overflow-hidden">
            <div className="border-b border-border px-4 py-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Bill of quantities</h3>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Rates are preliminary — replace with project-specific schedule of rates.
                </p>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full min-w-[880px]">
                <thead>
                  <tr>
                    {["Code", "Item", "Category", "Qty", "Unit", "Rate", "Source", "Amount"].map((h, i) => (
                      <th key={h} className={i >= 3 ? "text-right" : undefined}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item, i) => {
                    const idx = items.indexOf(item);
                    return (
                      <tr key={i}>
                        <td className="font-mono text-xs">{item.item_code}</td>
                        <td>{item.item_name}</td>
                        <td className="text-xs text-muted-foreground">{item.category}</td>
                        <td className="text-right">
                          <input
                            type="number"
                            aria-label="Quantity"
                            value={item.quantity}
                            onChange={(e) => updateItem(idx, "quantity", parseFloat(e.target.value) || 0)}
                            className="cell-input ml-auto"
                          />
                        </td>
                        <td className="text-right text-xs">{item.unit}</td>
                        <td className="text-right">
                          <input
                            type="number"
                            aria-label="Rate"
                            value={item.rate}
                            onChange={(e) => updateItem(idx, "rate", parseFloat(e.target.value) || 0)}
                            className="cell-input ml-auto"
                          />
                        </td>
                        <td className="text-[10px] text-muted-foreground">
                          {(item as LineItem & { rate_source?: string }).rate_source ?? "Rate library"}
                        </td>
                        <td className="text-right font-medium font-data">
                          {(item.quantity * item.rate).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot className="bg-background/95 border-t border-border">
                  {categorySubtotals.map(([cat, amt]) => (
                    <tr key={cat} className="text-xs text-muted-foreground">
                      <td colSpan={6} className="text-right py-1.5">
                        {cat} subtotal
                      </td>
                      <td />
                      <td className="text-right font-medium text-foreground-secondary py-1.5">
                        {amt.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                  <tr className="font-semibold text-foreground">
                    <td colSpan={6} className="text-right py-2.5">
                      Phase total
                    </td>
                    <td />
                    <td className="text-right py-2.5 font-data text-primary">
                      {footerTotal.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
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
