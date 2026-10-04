"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import type { ScenarioCompareResult, ScenarioSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function ScenarioComparePanel({
  result,
  summaries,
  onClose,
}: {
  result: ScenarioCompareResult;
  summaries: ScenarioSummary[];
  onClose: () => void;
}) {
  const nameById = Object.fromEntries(summaries.map((s) => [s.scenario_id, s.name]));

  return (
    <div className="pointer-events-none fixed inset-0 z-[95] flex items-end justify-center p-4 sm:items-center">
      <button type="button" aria-label="Close compare" className="pointer-events-auto absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="pointer-events-auto relative max-h-[85vh] w-full max-w-3xl overflow-hidden rounded-2xl border border-border bg-[rgba(11,17,28,0.98)] shadow-2xl">
        <div className="flex items-center justify-between border-b border-[rgba(148,163,184,0.14)] px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-foreground">Scenario comparison</p>
            <p className="text-[10px] text-muted-foreground">Planning-level comparison only</p>
          </div>
          <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="overflow-x-auto p-4">
          <table className="w-full min-w-[640px] text-[11px]">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="pb-2 pr-3 font-medium">Metric</th>
                {result.rows.map((row) => (
                  <th key={row.scenario_id} className="pb-2 px-2 font-medium min-w-[120px]">
                    <span className="block truncate">{row.name || nameById[row.scenario_id]}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="text-foreground-secondary">
              {[
                {
                  label: "Cost",
                  get: (r: (typeof result.rows)[0]) =>
                    r.cost_total != null ? formatCurrency(r.cost_total) : "—",
                  best: result.best_option_by.lowest_cost,
                },
                {
                  label: "Validation score",
                  get: (r: (typeof result.rows)[0]) =>
                    r.validation_score != null ? String(r.validation_score) : "—",
                  best: result.best_option_by.highest_validation_score,
                },
                {
                  label: "Status",
                  get: (r: (typeof result.rows)[0]) => r.validation_status ?? "—",
                },
                {
                  label: "Length (m)",
                  get: (r: (typeof result.rows)[0]) => (r.length_m != null ? String(r.length_m) : "—"),
                },
                {
                  label: "Lanes / width",
                  get: (r: (typeof result.rows)[0]) =>
                    [r.lanes != null ? `${r.lanes} ln` : null, r.width_m != null ? `${r.width_m}m` : null]
                      .filter(Boolean)
                      .join(" · ") || "—",
                },
                {
                  label: "Max grade %",
                  get: (r: (typeof result.rows)[0]) =>
                    r.max_grade_percent != null ? r.max_grade_percent.toFixed(1) : "—",
                },
                {
                  label: "Geometry / elevation",
                  get: (r: (typeof result.rows)[0]) =>
                    `${r.geometry_mode ?? "—"} / ${r.elevation_mode ?? "—"}`,
                },
                {
                  label: "Warnings / errors",
                  get: (r: (typeof result.rows)[0]) => `${r.warning_count ?? 0} / ${r.error_count ?? 0}`,
                  best: result.best_option_by.fewest_warnings,
                },
              ].map((metric) => (
                <tr key={metric.label} className="border-t border-[rgba(148,163,184,0.08)]">
                  <td className="py-2 pr-3 text-muted-foreground">{metric.label}</td>
                  {result.rows.map((row) => (
                    <td
                      key={row.scenario_id}
                      className={cn(
                        "py-2 px-2 font-data",
                        metric.best === row.scenario_id && "text-[#A7F3D0] font-semibold",
                      )}
                    >
                      {metric.get(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border-t border-border px-4 py-3 space-y-2 text-[10px] text-muted-foreground">
          {result.best_option_by.lowest_cost != null && (
            <p>
              Best by lowest cost:{" "}
              <span className="text-[#A7F3D0]">{nameById[result.best_option_by.lowest_cost]}</span>
            </p>
          )}
          {result.best_option_by.highest_validation_score != null && (
            <p>
              Best by validation score:{" "}
              <span className="text-[#A7F3D0]">{nameById[result.best_option_by.highest_validation_score]}</span>
            </p>
          )}
          {result.rows.some((r) => r.recommendations?.length) && (
            <p className="line-clamp-3">
              Recommendations: {result.rows.flatMap((r) => r.recommendations ?? []).slice(0, 3).join(" · ")}
            </p>
          )}
          {result.notes.map((note) => (
            <p key={note} className="text-muted-foreground">
              {note}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
