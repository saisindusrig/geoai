import type { ScenarioCompareResult, ScenarioSummary } from "./types";

const recorded = (value: number | null | undefined) => typeof value === "number" && Number.isFinite(value) ? value : null;

/** Presentation only: absent measurements remain gaps, including after comparison. */
export function scenarioChartData(scenarios: ScenarioSummary[], comparison: ScenarioCompareResult | null) {
  const durations = new Map((comparison?.rows ?? []).map(row => [row.scenario_id, recorded(row.duration_months)]));
  return scenarios.map(scenario => {
    const steel = recorded(scenario.materials_summary?.steel_kg);
    return {
      name: scenario.name.length > 14 ? `${scenario.name.slice(0, 12)}…` : scenario.name,
      cost: recorded(scenario.cost_total),
      cement: recorded(scenario.materials_summary?.concrete_m3),
      steel: steel === null ? null : steel / 1000,
      duration: durations.has(scenario.scenario_id) ? durations.get(scenario.scenario_id)! : recorded(scenario.duration_months),
    };
  });
}
