import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PersistentAssistant from "./PersistentAssistant";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn(), post: vi.fn() } }));
const props = { projectId: 1, selectedIds: ["pier-a"], revisionId: 7, dirty: false };
let messages: object[];
let items: object[];
let failSend: boolean;
let postBodies: unknown[];
afterEach(cleanup);

beforeEach(() => {
  vi.resetAllMocks(); messages = []; items = []; failSend = false; postBodies = [];
  vi.mocked(api.get).mockImplementation(async path => {
    if (path.endsWith("/conversations")) return { conversations: [{ id: "c1", title: "Project discussion" }] };
    if (path.includes("/messages")) return { messages, nextBefore: null };
    if (path.endsWith("/memory")) return { items };
    if (path.endsWith("/site-profiles")) return { profiles: [{ id: "p1" }] };
    if (path.endsWith("/readiness")) return { siteDataState: "UNCONFIGURED", databaseMode: "DEMO", current: true, operations: [] };
    return { id: "p1", current: true, refreshState: "IDLE", version: { id: "pv1", version: 2, selectionVersion: { id: "sv1" }, relief: { minElevation: { sourceKind: "UNKNOWN", value: null } } } };
  });
  vi.mocked(api.post).mockImplementation(async (path, body) => {
    if (path.endsWith("/messages")) {
      postBodies.push(body);
      if (failSend) throw new Error("Network unavailable");
      const sent = body as { parts: object[]; context: { selectedObjectIds: string[]; modelRevisionId: string } };
      messages = [{ id: "m1", role: "USER", parts: sent.parts, context: { ...sent.context, selection: sent.context.selectedObjectIds.map(objectId => ({ objectId })) }, run: { status: "WAITING_FOR_INPUT", errorCode: "ORCHESTRATION_NOT_ENABLED" } }];
      return { messageId: "m1", runId: "r1" };
    }
    if (path.endsWith("/accept") || path.endsWith("/reject")) {
      items = items.map(item => ({ ...item, status: path.endsWith("/accept") ? "ACCEPTED" : "REJECTED" }));
    }
    return {};
  });
});

async function ready() {
  await screen.findByText("Site profile v2 · Current");
  await waitFor(() => expect(screen.getByRole("button", { name: "Refresh site" })).toBeEnabled());
}

describe("persistent project Assistant", () => {
  it("loads an assistant reply and clarification after reload", async () => {
    messages = [{ id: "reply", role: "ASSISTANT", context: { selection: [] }, parts: [{ kind: "TEXT", text: "I can help plan a retaining wall concept." }, { kind: "QUESTION", questionId: "q", text: "Which side is retained?", options: ["East side"] }], run: null }];
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.click(screen.getByRole("button", { name: "East side" }));
    expect(screen.getByRole("textbox", { name: "Project message" })).toHaveValue("East side");
    view.unmount(); render(<PersistentAssistant {...props} />);
    expect(await screen.findByText("I can help plan a retaining wall concept.")).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("retries the persisted run and displays capability limitations", async () => {
    messages = [{ id: "m", role: "USER", context: { selection: [{ objectId: "old-pier" }], modelRevisionId: "6" }, parts: [{ kind: "TEXT", text: "Raise this pier" }],
      run: { id: "r", status: "FAILED", errorCode: "TIMEOUT", capabilities: [{ assetType: "BRIDGE", discussionSupport: "FULL", planningSupport: "CONCEPT_ONLY", generationSupport: "UNSUPPORTED", engineeringAnalysisSupport: "UNSUPPORTED" }] } }];
    render(<PersistentAssistant {...props} />); await ready();
    expect(screen.getByText(/generation unsupported/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry assistant" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/api/projects/1/assistant/runs/r/retry", { clientRequestId: expect.any(String) }));
    expect(screen.getByText("Captured: old-pier · revision 6")).toBeInTheDocument();
  });
  it("persists a message and reloads it from the server", async () => {
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Could the road move west?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Could the road move west?");
    expect(screen.getByText("Saved before AI processing was enabled")).toBeInTheDocument();
    view.unmount(); render(<PersistentAssistant {...props} />);
    await screen.findByText("Could the road move west?");
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).not.toHaveBeenCalledWith(expect.stringContaining("/ai/chat"), expect.anything());
  });

  it("shows current selection and unknown site readiness without claiming zero elevation", async () => {
    render(<PersistentAssistant {...props} dirty />); await ready();
    expect(screen.getByLabelText("Selected object context")).toHaveTextContent("Selected: pier-a · revision 7 · unsaved edits");
    expect(screen.getByLabelText("Site readiness")).toHaveTextContent("UNCONFIGURED · Demo storage");
    expect(screen.getByText("Elevation: Unknown")).toBeInTheDocument();
  });

  it("retries exactly the original message context after selection changes", async () => {
    failSend = true;
    const view = render(<PersistentAssistant {...props} />); await ready();
    fireEvent.change(screen.getByRole("textbox", { name: "Project message" }), { target: { value: "Discuss this pier" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Network unavailable");
    view.rerender(<PersistentAssistant {...props} selectedIds={["pier-b"]} revisionId={8} />);
    failSend = false; fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("Discuss this pier");
    expect(postBodies[1]).toEqual(postBodies[0]);
    expect(screen.getByText("Captured: pier-a · revision 7")).toBeInTheDocument();
  });

  it.each(["Accept", "Reject"])("requires the explicit %s action for proposed memory", async action => {
    items = [{ id: "requirement", versionId: "v1", version: 1, status: "PROPOSED", assetId: null,
      content: { kind: "REQUIREMENT", key: "width", constraint: { operator: "EQ", value: 7, unit: "m" } } }];
    render(<PersistentAssistant {...props} />); await ready();
    const card = screen.getByRole("article", { name: "proposed memory" });
    expect(api.post).not.toHaveBeenCalled();
    fireEvent.click(within(card).getByRole("button", { name: action }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(`/api/projects/1/memory/requirement/versions/1/${action.toLowerCase()}`, { expectedStatus: "PROPOSED" }));
  });

  it("offers a retry when loading conversation history fails", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error("History unavailable"));
    render(<PersistentAssistant {...props} />);
    await screen.findByText("History unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await ready();
    expect(screen.queryByText("History unavailable")).not.toBeInTheDocument();
  });
});
