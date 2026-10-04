import { afterEach, describe, expect, it, vi } from "vitest";
import {
  appEntryPath,
  loginPath,
  PUBLIC_APP_PATHS,
  registrationPath,
} from "@/lib/auth-routes";

vi.mock("@/lib/api", () => ({
  authRequired: vi.fn(() => false),
}));

import { authRequired } from "@/lib/api";

describe("loginPath", () => {
  it("encodes next path in query string", () => {
    expect(loginPath("/dashboard")).toBe("/login?next=%2Fdashboard");
    expect(loginPath("/projects/5/workspace")).toBe(
      "/login?next=%2Fprojects%2F5%2Fworkspace",
    );
  });
});

describe("registrationPath", () => {
  it("starts registration and preserves the return route", () => {
    expect(registrationPath("/projects/5/workspace?demo=1")).toBe(
      "/login?mode=register&next=%2Fprojects%2F5%2Fworkspace%3Fdemo%3D1",
    );
  });
});

describe("appEntryPath", () => {
  afterEach(() => {
    vi.mocked(authRequired).mockReturnValue(false);
  });

  it("returns login when JWT is required", () => {
    vi.mocked(authRequired).mockReturnValue(true);
    expect(appEntryPath("/dashboard")).toBe("/login?next=%2Fdashboard");
  });

  it("returns target path when JWT is off", () => {
    vi.mocked(authRequired).mockReturnValue(false);
    expect(appEntryPath("/dashboard")).toBe("/dashboard");
  });
});

describe("PUBLIC_APP_PATHS", () => {
  it("includes landing and login", () => {
    expect(PUBLIC_APP_PATHS.has("/")).toBe(true);
    expect(PUBLIC_APP_PATHS.has("/login")).toBe(true);
    expect(PUBLIC_APP_PATHS.has("/dashboard")).toBe(false);
  });
});
