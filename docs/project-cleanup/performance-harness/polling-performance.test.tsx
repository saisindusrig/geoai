import { act, cleanup, renderHook } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { useActiveJobPolling as before } from "./polling-before-cleanup";
import { useActiveJobPolling as after } from "./useActiveJobPolling";
const mocks = vi.hoisted(() => ({ get: vi.fn(), set: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { get: mocks.get }, formatApiErrorMessage: () => "Offline" }));
vi.mock("@/lib/toast", () => ({ toast: vi.fn() }));
vi.mock("@/stores/projectStore", () => ({ useProjectStore: () => ({ activeJob: {job_id: "perf", status: "running"}, setActiveJob: mocks.set }) }));
it("measures archived baseline and current polling under identical latency and outage", async () => {
  vi.useFakeTimers();
  const result: Record<string, number> = {};
  for (const [label, hook] of [["before", before], ["after", after]] as const) {
    mocks.get.mockReset().mockImplementation(() => new Promise(() => {}));
    renderHook(() => hook());
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    result[`${label}_pending_requests_at_10_seconds`] = mocks.get.mock.calls.length;
    cleanup();
    mocks.get.mockReset().mockRejectedValue(new Error("offline"));
    renderHook(() => hook());
    await act(() => vi.advanceTimersByTimeAsync(120_000));
    result[`${label}_failed_requests_at_120_seconds`] = mocks.get.mock.calls.length;
    cleanup();
  }
  vi.useRealTimers();
  console.log("POLLING_MEASUREMENT", JSON.stringify(result));
  expect(result).toEqual({ before_pending_requests_at_10_seconds: 10, before_failed_requests_at_120_seconds: 120, after_pending_requests_at_10_seconds: 1, after_failed_requests_at_120_seconds: 5 });
});
