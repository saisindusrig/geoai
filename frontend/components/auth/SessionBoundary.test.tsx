import { act, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import SessionBoundary from "./SessionBoundary";
import { invalidateSession } from "@/lib/firebase-auth";
import { useProjectStore } from "@/stores/projectStore";
import { useToastStore } from "@/lib/toast";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn().mockResolvedValue({ mode: "local_development", password_login_allowed: true,
  firebase_project_id: null, firebase: { enabled: false, ready: false, code: "DISABLED", message: "Disabled" } }) } }));
afterEach(() => { cleanup(); vi.unstubAllEnvs(); localStorage.clear(); });
it("remounts private assistant/project state and resets existing global caches on an identity boundary", async () => {
  function PrivateView() {
    const [privateText, setPrivateText] = useState("Empty account cache");
    return <button onClick={() => setPrivateText("Account A private assistant history")}>{privateText}</button>;
  }
  render(<SessionBoundary><PrivateView /></SessionBoundary>);
  await screen.findByText("Empty account cache");
  act(() => screen.getByRole("button").click());
  expect(screen.getByText("Account A private assistant history")).toBeInTheDocument();
  useProjectStore.setState({ project: { id: 123, name: "Private A project" } as never });
  useToastStore.setState({ toasts: [{ id: "one", title: "Private A result", variant: "default" }] });
  act(() => invalidateSession());
  await waitFor(() => expect(screen.queryByText("Account A private assistant history")).toBeNull());
  expect(useProjectStore.getState().project).toBeNull(); expect(useToastStore.getState().toasts).toEqual([]);
});
it("clears Firebase account view caches while retaining preferences and original offline drafts", async () => {
  vi.stubEnv("NEXT_PUBLIC_FIREBASE_AUTH_ENABLED", "true");
  localStorage.setItem("geoai-map-bookmarks-123", "private bookmark");
  localStorage.setItem("geoai:analysis-guided:123", "private result selection");
  localStorage.setItem("project-123-scenario-id", "1");
  localStorage.setItem("planning-portal-theme", "dark");
  localStorage.setItem("geoai-local-3d-sandbox-layout", "preserved offline draft");
  render(<SessionBoundary><div>Session prepared</div></SessionBoundary>);
  await screen.findByText("Session prepared");
  expect(localStorage.getItem("geoai-map-bookmarks-123")).toBeNull();
  expect(localStorage.getItem("geoai:analysis-guided:123")).toBeNull();
  expect(localStorage.getItem("project-123-scenario-id")).toBeNull();
  expect(localStorage.getItem("planning-portal-theme")).toBe("dark");
  expect(localStorage.getItem("geoai-local-3d-sandbox-layout")).toBe("preserved offline draft");
});
it("keeps login progress visible through an identity change while still clearing project caches", async () => {
  window.history.replaceState(null, "", "/login");
  function LoginProgress() {
    const [message, setMessage] = useState("Waiting");
    return <button onClick={() => setMessage("Checking backend approval")}>{message}</button>;
  }
  try {
    render(<SessionBoundary><LoginProgress /></SessionBoundary>);
    await screen.findByText("Waiting");
    act(() => screen.getByRole("button").click());
    act(() => invalidateSession());
    expect(screen.getByText("Checking backend approval")).toBeVisible();
    expect(useProjectStore.getState().project).toBeNull();
  } finally { window.history.replaceState(null, "", "/"); }
});
