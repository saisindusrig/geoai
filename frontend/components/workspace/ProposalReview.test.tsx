import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import ProposalReview from "./ProposalReview";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() } }));
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.get).mockResolvedValue({ id: "pv", version: 2, status: "READY_FOR_REVIEW", contentHash: "h", dependencyHash: "d", validationHash: "v", alternatives: [],
    validation: { issues: [{ severity: "WARNING", message: "Concept only" }] }, content: { request: { title: "Raise piers", rationale: "Review clearance", assets: [{ name: "Bridge", assetType: "BRIDGE" }], assumptions: ["Height to confirm"] },
      context: { modelRevisionId: "7" }, contract: { assumptionVersionIds: ["a1"] }, preview: { objectIds: ["P03", "P04", "P05"], deltaM: [0, 0, 0.5] } } });
  vi.mocked(api.post).mockResolvedValue({});
});

it("requires explicit review and acknowledgment for exact approval without building", async () => {
  render(<ProposalReview projectId={1} versionId="pv" />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  expect(screen.getByLabelText("Temporary proposal preview")).toHaveTextContent("Local XYZ 0, 0, 0.5 m");
  expect(screen.getByRole("button", { name: "Approve proposal" })).toBeDisabled();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Approve proposal" }));
  await waitFor(() => expect(api.post).toHaveBeenCalledWith("/api/projects/1/proposals/approve", expect.objectContaining({ proposalVersionId: "pv", proposalHash: "h", dependencyHash: "d", validationHash: "v", acknowledgedAssumptionVersionIds: ["a1"], expectedModelRevisionId: "7" })));
  expect(api.post).toHaveBeenCalledTimes(1);
});

it("shows approval failures without claiming success", async () => {
  vi.mocked(api.post).mockRejectedValueOnce(new Error("STALE_PROPOSAL"));
  render(<ProposalReview projectId={1} versionId="pv" />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Approve proposal" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("STALE_PROPOSAL");
});
