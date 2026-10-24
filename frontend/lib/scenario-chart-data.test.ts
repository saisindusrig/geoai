import { expect, it } from "vitest";
import { scenarioChartData } from "./scenario-chart-data";
import type { ScenarioCompareResult, ScenarioSummary } from "./types";

it("keeps missing measurements separate from recorded zero and positive quantities", () => {
  const scenarios = [
    { scenario_id: 1, name: "Unknown", status: "completed", created_at: null },
    { scenario_id: 2, name: "Measured", status: "completed", created_at: null, cost_total: 0, materials_summary: { concrete_m3: 0, steel_kg: 2500 }, duration_months: 8 },
  ] satisfies ScenarioSummary[];
  expect(scenarioChartData(scenarios, null)).toEqual([
    { name: "Unknown", cost: null, cement: null, steel: null, duration: null },
    { name: "Measured", cost: 0, cement: 0, steel: 2.5, duration: 8 },
  ]);
});
it("preserves explicitly absent comparison evidence instead of substituting an old duration", () => {
  const scenarios = [{ scenario_id: 1, name: "Option", status: "completed", created_at: null, duration_months: 8 }];
  const comparison = { rows: [{ scenario_id: 1, duration_months: null }] } as ScenarioCompareResult;
  expect(scenarioChartData(scenarios, comparison)[0].duration).toBeNull();
});
