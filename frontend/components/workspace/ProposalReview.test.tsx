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

it("reviews per-asset families and blockers without offering generation", async () => {
  const fixture = await api.get<object>("fixture");
  vi.mocked(api.get).mockResolvedValue({ ...fixture, content: {
    ...(fixture as { content: object }).content,
    assetProposals: [
      { assetRequestId: "A01", displayName: "Building A", assetFamily: "BUILDING", proposalState: "CONCEPT_REVIEW", generationEligible: false, blockers: ["Building specialist unavailable"] },
      { assetRequestId: "A02", displayName: "Bridge A", assetFamily: "BRIDGE", proposalState: "CONCEPT_REVIEW", generationEligible: false, blockers: ["Bridge specialist unavailable"] },
    ],
  } });
  render(<ProposalReview projectId={1} versionId="pv" />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  expect(screen.getByText(/Building A · BUILDING/)).toBeInTheDocument();
  expect(screen.getByText(/Bridge A · BRIDGE/)).toBeInTheDocument();
  expect(screen.getAllByText("Generation: Unavailable")).toHaveLength(2);
  expect(screen.queryByRole("button", { name: /build|generate/i })).not.toBeInTheDocument();
});

it("generates only an approved eligible building and reports its saved revision", async () => {
  const fixture = await api.get<object>("fixture");
  vi.mocked(api.get).mockResolvedValue({ ...fixture, status: "APPROVED", content: {
    ...(fixture as { content: object }).content,
    assetProposals: [{ assetRequestId: "A01", displayName: "Office", assetFamily: "BUILDING", proposalState: "CONCEPT_REVIEW", generationEligible: true, blockers: [] }],
  } });
  vi.mocked(api.post).mockResolvedValue({ modelRevisionId: "9" });
  render(<ProposalReview projectId={1} versionId="pv" />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  fireEvent.click(screen.getByRole("button", { name: "Generate building concept" }));
  await waitFor(() => expect(api.post).toHaveBeenCalledWith("/api/projects/1/proposals/versions/pv/build", {}));
  expect(await screen.findByRole("status")).toHaveTextContent("revision 9");
});

it("summarizes a typed opening patch and blocks application with unsaved edits", async () => {
  const fixture = await api.get<object>("fixture");
  vi.mocked(api.get).mockResolvedValue({ ...fixture, status: "APPROVED", content: {
    ...(fixture as { content: object }).content,
    request: { title: "Widen window", rationale: "Requested width", assets: [{ name: "Office", assetType: "OFFICE_BUILDING", buildingPatch: {
      sourceModelRevisionId: "7", operations: [{ targetComponentId: "office:window", parameters: { operationType: "RESIZE_OPENING", width: 1.5 } }],
    } }] },
    patchPreview: { hostWallId: "east-wall", previousOpening: { width: 1, offset: 2 }, proposedOpening: { width: 1.5, offset: 2 }, affectedComponentIds: ["office:window"] },
    assetProposals: [{ assetRequestId: "A01", displayName: "Office", assetFamily: "BUILDING", generationEligible: true, blockers: [] }],
  } });
  const { rerender } = render(<ProposalReview projectId={1} versionId="pv" dirty />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  expect(screen.getByText(/Width: 1 m → 1.5 m/)).toBeInTheDocument();
  expect(screen.getByText("Host wall: east-wall")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Apply approved building patch" })).toBeDisabled();
  expect(api.post).not.toHaveBeenCalled();
  rerender(<ProposalReview projectId={1} versionId="pv" dirty={false} />);
  vi.mocked(api.post).mockResolvedValue({ modelRevisionId: "10" });
  fireEvent.click(screen.getByRole("button", { name: "Apply approved building patch" }));
  expect(await screen.findByRole("status")).toHaveTextContent("Building patch saved as revision 10");
});

it("reviews a generic composition and requires saved state before generation", async () => {
  const fixture = await api.get<object>("fixture");
  vi.mocked(api.get).mockResolvedValue({ ...fixture, status: "APPROVED", content: {
    ...(fixture as { content: object }).content,
    request: { title: "Pedestrian bridge", rationale: "Primitive composition", assets: [{ name: "Bridge", assetType: "AI3D_DESIGN", ai3dDesign: {
      systems: [{ id: "bridge", role: "PEDESTRIAN_BRIDGE" }], objects: [{ objectId: "deck", systemId: "bridge", role: "DECK", parameters: { primitiveType: "SWEEP" } }],
      assumptions: [{ field: "deck width", value: "4 m", reason: "Preview only" }], unknowns: ["soil", "designLoads"],
    } }] }, assetProposals: [{ assetRequestId: "A01", displayName: "Bridge", assetFamily: "CUSTOM", generationEligible: true, blockers: [] }],
  } });
  const { rerender } = render(<ProposalReview projectId={1} versionId="pv" dirty />);
  fireEvent.click(await screen.findByRole("button", { name: "Review proposal" }));
  expect(screen.getByLabelText("Generic 3D design summary")).toHaveTextContent("PEDESTRIAN BRIDGE");
  expect(screen.getByLabelText("Generic 3D design summary")).toHaveTextContent("deck width = 4 m");
  expect(screen.getByLabelText("Generic 3D design summary")).toHaveTextContent("soil, designLoads");
  expect(screen.getByRole("button", { name: "Approve & Generate 3D" })).toBeDisabled();
  rerender(<ProposalReview projectId={1} versionId="pv" dirty={false} />);
  vi.mocked(api.post).mockResolvedValue({ modelRevisionId: "11" });
  fireEvent.click(screen.getByRole("button", { name: "Approve & Generate 3D" }));
  expect(await screen.findByRole("status")).toHaveTextContent("Generic 3D concept saved as revision 11");
});
