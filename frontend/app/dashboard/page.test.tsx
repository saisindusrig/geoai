import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("@/components/dashboard/ConstructionPreview", () => ({
  default: ({ type }: { type: string }) => (
    <div data-testid={`preview-${type}`} />
  ),
}));

vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(async (url: string) => {
      if (url === "/api/projects") return [];
      if (url === "/api/projects/summaries") return [];
      return [];
    }),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status = 500) {
      super(message);
      this.status = status;
    }
  },
  authRequired: vi.fn(() => false),
  getAuthToken: vi.fn(() => null),
}));

import DashboardPage from "@/app/dashboard/page";
import { api } from "@/lib/api";
import { LOCAL_SANDBOX_PATH } from "@/lib/local-sandbox";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DashboardPage", () => {
  it("renders the empty command center and global actions", async () => {
    vi.mocked(api.get).mockImplementation(async () => []);
    render(<DashboardPage />);

    expect(
      await screen.findByText(/No saved concepts yet/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Your concepts" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Start a new concept/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "QUICK START" })).toBeInTheDocument();
    for (const link of screen.getAllByRole("link", { name: /^New concept$/i })) {
      expect(link).toHaveAttribute("href", "/projects/new");
    }
    expect(screen.getByRole("link", { name: /Open sandbox/i })).toHaveAttribute("href", LOCAL_SANDBOX_PATH);
    expect(api.get).toHaveBeenCalledWith("/api/projects");
    expect(api.get).toHaveBeenCalledWith("/api/project-folders");
  });

  it("offers compact asset shortcuts and a separate searchable catalogue", async () => {
    vi.mocked(api.get).mockResolvedValue([]);
    render(<DashboardPage />);
    await screen.findByText("No saved concepts yet");
    for (const name of ["Bridge", "Road", "Pipeline", "Dam", "Building"]) {
      expect(screen.getByRole("link", { name: new RegExp(`^${name} `) })).toHaveAttribute("href", `/projects/new?template=${name.toLowerCase()}`);
    }
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /^More assets$/i }));
    const library = within(screen.getByRole("dialog", { name: "All assets" }));
    const search = library.getByRole("textbox", { name: "Search asset library" });
    await user.type(search, "no-such-asset-xyz");
    expect(library.getByText(/No matching assets/)).toBeInTheDocument();
    await user.clear(search);
    expect(library.getAllByRole("link").length).toBeGreaterThan(5);
    await user.click(library.getByRole("button", { name: "Close asset library" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("combines type and folder filters for saved concepts", async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === "/api/projects") {
        return [
          {
            id: 1,
            name: "River dam",
            project_type: "dam",
            folder_id: 7,
            status: "draft",
            units: "metric",
            center_lat: 12,
            center_lng: 77,
            location_name: "Site",
            boundary_geojson: null,
            alignment_geojson: null,
            created_at: "2026-09-22T00:00:00Z",
            updated_at: "2026-09-22T00:00:00Z",
            disclaimer: "",
          },
          {
            id: 2,
            name: "Town road",
            project_type: "road",
            folder_id: null,
            status: "draft",
            units: "metric",
            center_lat: 12,
            center_lng: 77,
            location_name: "Town",
            boundary_geojson: null,
            alignment_geojson: null,
            created_at: "2026-09-22T00:00:00Z",
            updated_at: "2026-09-22T00:00:00Z",
            disclaimer: "",
          },
        ];
      }
      if (url === "/api/project-folders") {
        return [
          {
            id: 7,
            name: "Water studies",
            color: "sage",
            created_at: "",
            updated_at: "",
          },
        ];
      }
      return [];
    });
    render(<DashboardPage />);
    const user = userEvent.setup();
    await screen.findByRole("button", { name: "Show recent project River dam" });
    await user.click(screen.getByRole("button", { name: "View all" }));
    expect(screen.getByRole("heading", { name: "Concepts" })).toBeInTheDocument();
    expect(screen.getByText("River dam")).toBeInTheDocument();
    expect(screen.getByText("Town road")).toBeInTheDocument();
    await user.selectOptions(screen.getByRole("combobox", { name: "Filter by concept type" }), "dam");
    expect(screen.getByText("River dam")).toBeInTheDocument();
    expect(screen.queryByText("Town road")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Water studies" }));
    expect(screen.getByText("River dam")).toBeInTheDocument();
    expect(screen.queryByText("Town road")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Unfiled" }));
    expect(
      await screen.findByText(/No matching concepts/i),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.click(screen.getByRole("button", { name: "Unfiled" }));
    expect(screen.getByText("Town road")).toBeInTheDocument();
    expect(screen.queryByText("River dam")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Water studies" }));
    expect(screen.getByText("River dam")).toBeInTheDocument();
    expect(screen.queryByText("Town road")).not.toBeInTheDocument();
  });

  it("features the most recently updated project with its location and workspace route", async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => url === "/api/projects" ? [
      { id: 1, name: "Older concept", project_type: "road", location_name: "Town", updated_at: "2026-09-01T00:00:00Z" },
      { id: 2, name: "Latest bridge", project_type: "bridge", location_name: "River crossing", updated_at: "2026-10-01T00:00:00Z" },
    ] : []);
    render(<DashboardPage />);
    const heading = await screen.findByRole("heading", { name: "CONTINUE WORKING" });
    const featured = within(heading.closest("article")!);
    expect(await featured.findByRole("heading", { name: "Latest bridge" })).toBeInTheDocument();
    expect(featured.getByText("River crossing")).toBeInTheDocument();
    expect(featured.getByRole("link", { name: "Open workspace" })).toHaveAttribute("href", "/projects/2/workspace");
    expect(featured.queryByText("Older concept")).not.toBeInTheDocument();
  });

  it("reports API failures, allows retry, and keeps new-concept actions available", async () => {
    vi.mocked(api.get).mockRejectedValue(new Error("Offline"));
    render(<DashboardPage />);
    expect(await screen.findByText(/Saved concepts are unavailable/)).toBeInTheDocument();
    expect(screen.queryByText("No saved concepts yet")).not.toBeInTheDocument();
    for (const link of screen.getAllByRole("link", { name: "New concept" })) {
      expect(link).toHaveAttribute("href", "/projects/new");
    }
    vi.mocked(api.get).mockResolvedValue([]);
    await userEvent.setup().click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("No saved concepts yet")).toBeInTheDocument();
    expect(screen.queryByText(/Saved concepts are unavailable/)).not.toBeInTheDocument();
  });

  it("creates a personal folder", async () => {
    vi.mocked(api.get).mockImplementation(async () => []);
    vi.mocked(api.post).mockResolvedValue({
      id: 9,
      name: "October studies",
      color: "sage",
      created_at: "",
      updated_at: "",
    });
    render(<DashboardPage />);
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: /New folder/i }),
    );
    await user.type(screen.getByLabelText("Folder name"), "October studies");
    await user.click(screen.getByRole("button", { name: "Create folder" }));
    expect(api.post).toHaveBeenCalledWith("/api/project-folders", {
      name: "October studies",
    });
    expect(
      await screen.findByRole("button", { name: /^October studies$/ }),
    ).toBeInTheDocument();
  });
});
