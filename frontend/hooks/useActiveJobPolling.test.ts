import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useActiveJobPolling } from "@/hooks/useActiveJobPolling";

const setActiveJob = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
  formatApiErrorMessage: vi.fn((e: unknown) => String(e)),
}));

vi.mock("@/lib/toast", () => ({
  toast: vi.fn(),
}));

vi.mock("@/stores/projectStore", () => ({
  useProjectStore: vi.fn(() => ({
    activeJob: { job_id: "job-42", status: "running" },
    setActiveJob,
  })),
}));

import { api } from "@/lib/api";

describe("useActiveJobPolling", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("cancelJob posts to cancel endpoint", async () => {
    vi.mocked(api.post).mockResolvedValue({});
    vi.mocked(api.get).mockResolvedValue({ job_id: "job-42", status: "cancelled" });

    const { result } = renderHook(() => useActiveJobPolling());

    await act(async () => {
      await result.current.cancelJob();
    });

    expect(api.post).toHaveBeenCalledWith("/api/jobs/job-42/cancel");
  });
});
