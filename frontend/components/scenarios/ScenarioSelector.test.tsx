import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ScenarioSelector from "@/components/scenarios/ScenarioSelector";
import type { DesignOutput, DesignScenario } from "@/lib/types";

const scenarios: DesignScenario[] = [
  {
    id: 1,
    name: "Baseline",
    status: "completed",
    created_at: "2026-01-01",
    input_parameters_json: null,
    design_output_json: {} as DesignOutput,
    assumptions_json: null,
  },
  {
    id: 2,
    name: "Option B",
    status: "draft",
    created_at: "2026-01-02",
    input_parameters_json: null,
    design_output_json: null,
    assumptions_json: null,
  },
];

describe("ScenarioSelector", () => {
  it("shows empty message when no scenarios", () => {
    render(
      <ScenarioSelector projectId={1} scenarios={[]} selectedId={null} onSelect={vi.fn()} />,
    );
    expect(screen.getByText(/No design scenarios yet/i)).toBeInTheDocument();
  });

  it("calls onSelect when selection changes", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <ScenarioSelector
        projectId={5}
        scenarios={scenarios}
        selectedId={1}
        onSelect={onSelect}
      />,
    );

    await user.selectOptions(screen.getByTitle("Select a design scenario"), "2");
    expect(onSelect).toHaveBeenCalledWith(scenarios[1]);
  });
});
