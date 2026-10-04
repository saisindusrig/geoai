import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import UserMenu from "@/components/layout/UserMenu";

vi.mock("@/lib/useAuthUser", () => ({
  useAuthUser: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  authRequired: vi.fn(() => true),
  getAuthToken: vi.fn(() => null),
  clearAuthToken: vi.fn(),
}));

import { useAuthUser } from "@/lib/useAuthUser";
import { authRequired, getAuthToken } from "@/lib/api";

describe("UserMenu", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.mocked(authRequired).mockReturnValue(true);
    vi.mocked(getAuthToken).mockReturnValue(null);
  });

  it("shows Sign in when unauthenticated", () => {
    vi.mocked(useAuthUser).mockReturnValue({
      user: null,
      loading: false,
      isAdmin: false,
      reload: vi.fn(),
    });
    render(<UserMenu pathname="/dashboard" />);
    expect(screen.getByRole("link", { name: /Sign in/i })).toHaveAttribute(
      "href",
      "/login?next=%2Fdashboard",
    );
  });

  it("shows user name when authenticated", () => {
    vi.mocked(useAuthUser).mockReturnValue({
      user: { id: 1, name: "Alex Planner", email: "alex@example.com", role: "user" },
      loading: false,
      isAdmin: false,
      reload: vi.fn(),
    });
    vi.mocked(getAuthToken).mockReturnValue("token");
    render(<UserMenu pathname="/dashboard" />);
    expect(screen.getByText("Alex Planner")).toBeInTheDocument();
  });

  it("shows loading skeleton while auth resolves", () => {
    vi.mocked(useAuthUser).mockReturnValue({
      user: null,
      loading: true,
      isAdmin: false,
      reload: vi.fn(),
    });
    const { container } = render(<UserMenu pathname="/dashboard" />);
    expect(container.querySelector("[aria-hidden]")).toBeTruthy();
  });
});
