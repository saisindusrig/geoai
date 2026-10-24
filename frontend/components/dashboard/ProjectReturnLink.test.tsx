import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("next/link", () => ({ default: ({ href, children }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => <a href={href}>{children}</a> }));
import ProjectReturnLink from "./ProjectReturnLink";
import type { Project } from "@/lib/types";
afterEach(() => { cleanup(); window.history.replaceState({}, "", "/dashboard"); });
it("retains the exact local project link and resolves its saved name", () => {
  window.history.replaceState({}, "", "/dashboard?returnTo=%2Fprojects%2F805%2Fworkspace%3Flocal%3D1");
  render(<ProjectReturnLink projects={[{ id: 805, name: "Saved bridge" } as Project]} />);
  expect(screen.getByRole("link", { name: "Return to Saved bridge" })).toHaveAttribute("href", "/projects/805/workspace?local=1");
});
