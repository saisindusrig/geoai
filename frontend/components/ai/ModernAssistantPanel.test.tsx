import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ModernAssistantPanel from "./ModernAssistantPanel";
import { streamChat } from "@/lib/api";
import type { DesignOutput } from "@/lib/types";

vi.mock("@/lib/api", () => ({ streamChat: vi.fn(), apiUrl: (s: string) => s }));
vi.mock("@/components/map/BlenderLayerPanel", () => ({ default: () => null }));
vi.mock("@/components/layout/WorkspaceMapContext", () => ({ useWorkspaceMap: () => ({ copilotPanelVisible: true, onToggleCopilotPanel: vi.fn() }) }));
vi.mock("@/hooks/usePointerResize", () => ({ useVerticalSplitResize: () => ({ size: 240, onResizePointerDown: vi.fn() }) }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("rejects streamed model-changing actions while retaining the explicit manual regenerate control", async () => {
  vi.mocked(streamChat).mockResolvedValue({ message: "Suggested change", actions: [{ type: "generate_design", payload: {} }], warnings: [] });
  const apply = vi.fn(), regenerate = vi.fn();
  const design = { calculated: { cost_summary: { total_medium: 10, currency: "INR" }, timeline: { estimated_months_medium: 2 } } } as unknown as DesignOutput;
  render(<ModernAssistantPanel projectId={1} design={design} onApplyParameters={apply} onRegenerate={regenerate} />);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Move the entrance" } });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));
  await screen.findByText("Suggested change");
  expect(screen.getByText(/requires a reviewed proposal/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Apply this action" })).not.toBeInTheDocument();
  expect(apply).not.toHaveBeenCalled();
  expect(regenerate).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
  expect(regenerate).toHaveBeenCalledTimes(1);
});

it("keeps the existing read-only site analysis action available", async () => {
  vi.mocked(streamChat).mockResolvedValue({ message: "I can inspect the site", actions: [{ type: "run_site_analysis", payload: {} }], warnings: [] });
  const runSiteAnalysis = vi.fn().mockResolvedValue(undefined);
  render(<ModernAssistantPanel projectId={1} onApplyParameters={vi.fn()} onRegenerate={vi.fn()} onRunSiteAnalysis={runSiteAnalysis} />);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Inspect this site" } });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));
  await screen.findByText("I can inspect the site");
  fireEvent.click(screen.getByRole("button", { name: "Apply this action" }));
  expect(runSiteAnalysis).toHaveBeenCalledTimes(1);
});
