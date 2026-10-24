import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useActiveJobPolling } from "./useActiveJobPolling";

const mocks = vi.hoisted(() => ({ get: vi.fn(), setActiveJob: vi.fn(), toast: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { get: mocks.get }, formatApiErrorMessage: () => "Offline" }));
vi.mock("@/lib/toast", () => ({ toast: mocks.toast }));
vi.mock("@/stores/projectStore", () => ({ useProjectStore: () => ({
  activeJob: { job_id: "test-job", status: "running" }, setActiveJob: mocks.setActiveJob,
}) }));

describe("job polling lifecycle", () => {
  beforeEach(() => { vi.useFakeTimers(); vi.clearAllMocks(); });
  afterEach(() => { vi.useRealTimers(); });

  it("keeps slow requests single flight and ignores results after unmount", async () => {
    let resolve!: (value: unknown) => void;
    mocks.get.mockImplementation(() => new Promise(r => { resolve = r; }));
    const { unmount } = renderHook(() => useActiveJobPolling());
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(mocks.get).toHaveBeenCalledTimes(1);
    unmount();
    await act(async () => { resolve({ job_id: "test-job", status: "completed" }); });
    expect(mocks.setActiveJob).not.toHaveBeenCalled();
    expect(mocks.toast).not.toHaveBeenCalled();
  });

  it("stops after five consecutive failures with backoff", async () => {
    mocks.get.mockRejectedValue(new Error("offline"));
    const { unmount } = renderHook(() => useActiveJobPolling());
    await act(() => vi.advanceTimersByTimeAsync(120_000));
    expect(mocks.get).toHaveBeenCalledTimes(5);
    expect(mocks.toast).toHaveBeenCalledWith("Job status polling paused", expect.any(Object));
    unmount();
  });

  it("notifies completion once and schedules no further requests", async () => {
    mocks.get.mockResolvedValue({ job_id: "test-job", status: "completed" });
    const onCompleted = vi.fn();
    const { unmount } = renderHook(() => useActiveJobPolling({ onCompleted }));
    await act(() => vi.advanceTimersByTimeAsync(30_000));
    expect(mocks.get).toHaveBeenCalledTimes(1);
    expect(onCompleted).toHaveBeenCalledTimes(1);
    unmount();
  });

  it("resumes the same job after a disconnected pause without creating a job", async () => {
    mocks.get.mockRejectedValue(new Error("offline"));
    const { result, unmount } = renderHook(() => useActiveJobPolling());
    await act(() => vi.advanceTimersByTimeAsync(120_000));
    expect(result.current.pollingError).toBe("Offline");
    mocks.get.mockResolvedValue({ job_id: "test-job", status: "completed" });
    act(() => result.current.retryPolling());
    await act(() => vi.advanceTimersByTimeAsync(5_000));
    expect(result.current.pollingError).toBeNull();
    expect(mocks.get).toHaveBeenLastCalledWith("/api/jobs/test-job");
    expect(mocks.get).toHaveBeenCalledTimes(6);
    expect(mocks.setActiveJob).toHaveBeenCalledWith(expect.objectContaining({ status: "completed" }));
    unmount();
  });
});
