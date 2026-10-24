import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, expect, it, vi } from "vitest";
const state = vi.hoisted(() => ({ device: "unsupported" }));
vi.mock("@/hooks/useWorkspaceDevice", () => ({ useWorkspaceDevice: () => state.device }));
vi.mock("next/link", () => ({ default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => <a href={href} {...props}>{children}</a> }));
import DesktopWorkspaceGate from "./DesktopWorkspaceGate";

afterEach(() => { cleanup(); state.device = "unsupported"; });
it("does not mount workspace content on an unsupported fresh visit and retains project URL", () => {
  const mounted = vi.fn();
  function HeavyWorkspace() { useEffect(mounted, []); return <div>Renderer</div>; }
  render(<DesktopWorkspaceGate required projectId={805} projectName="Saved bridge" returnPath="/projects/805/workspace?demo=1"><HeavyWorkspace /></DesktopWorkspaceGate>);
  expect(screen.getByRole("heading", { name: "Desktop Required" })).toBeVisible();
  expect(screen.getByText("Saved bridge")).toBeVisible();
  expect(screen.getByRole("link", { name: "Back to Dashboard" })).toHaveAttribute("href", "/dashboard?returnTo=%2Fprojects%2F805%2Fworkspace%3Fdemo%3D1");
  expect(mounted).not.toHaveBeenCalled();
  expect(screen.queryByText("Renderer")).not.toBeInTheDocument();
});
it("preserves an admitted desktop session through an unsupported resize", async () => {
  const mounted = vi.fn(), unmounted = vi.fn();
  function Workspace() { useEffect(() => { mounted(); return unmounted; }, []); return <div>Desktop draft</div>; }
  const content = <Workspace />;
  const view = () => <DesktopWorkspaceGate required projectId={805} returnPath="/projects/805/workspace">{content}</DesktopWorkspaceGate>;
  state.device = "desktop";
  const { rerender } = render(view());
  expect(await screen.findByText("Desktop draft")).toBeVisible();
  state.device = "unsupported";
  rerender(view());
  expect(screen.getByRole("heading", { name: "Desktop Required" })).toBeVisible();
  expect(screen.getByText("Desktop draft")).not.toBeVisible();
  expect(unmounted).not.toHaveBeenCalled();
  state.device = "desktop";
  rerender(view());
  await waitFor(() => expect(screen.getByText("Desktop draft")).toBeVisible());
  expect(mounted).toHaveBeenCalledTimes(1);
});
it("does not restrict ordinary responsive pages", () => {
  render(<DesktopWorkspaceGate required={false} projectId={null} returnPath="/settings"><h1>Settings</h1></DesktopWorkspaceGate>);
  expect(screen.getByRole("heading", { name: "Settings" })).toBeVisible();
});
