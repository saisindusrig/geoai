import { expect, it } from "vitest";
import { projectReturnPath, requiresDesktopWorkspace } from "./workspace-device";

it("restricts advanced project tools while leaving public, management and read-only results available", () => {
  for (const route of ["workspace", "map", "model", "analysis", "estimate", "scenarios"]) expect(requiresDesktopWorkspace(`/projects/805/${route}`)).toBe(true);
  for (const path of ["/", "/login", "/dashboard", "/projects/new", "/settings", "/admin/usage", "/projects/805/report", "/projects/805/cost", "/projects/805/timeline"]) expect(requiresDesktopWorkspace(path)).toBe(false);
});
it("retains only local project return paths, including their query context", () => {
  expect(projectReturnPath("?returnTo=%2Fprojects%2F805%2Fworkspace%3Flocal%3D1")).toBe("/projects/805/workspace?local=1");
  for (const path of ["https://other.test/", "//other.test", "javascript:alert(1)", "/settings"]) expect(projectReturnPath(`?returnTo=${encodeURIComponent(path)}`)).toBeNull();
});
