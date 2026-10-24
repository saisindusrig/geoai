import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { useProjectData } from "./useProjectData";
import { useProjectStore } from "@/stores/projectStore";
import { invalidateSession } from "@/lib/firebase-auth";
const fixture = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { get: fixture.get, getOptional: vi.fn().mockResolvedValue(null) }, ApiError: class extends Error {} }));
afterEach(() => { cleanup(); useProjectStore.setState(useProjectStore.getInitialState(), true); });
it("cannot repopulate the global project cache from an old account's delayed aggregate load", async () => {
  let finish!: (value: unknown) => void;
  fixture.get.mockImplementation((path: string) => path === "/api/projects/123" ? new Promise(resolve => { finish = resolve; }) : Promise.resolve([]));
  const { result } = renderHook(() => useProjectData(123));
  await waitFor(() => expect(finish).toBeTypeOf("function"));
  act(() => {
    invalidateSession();
    useProjectStore.setState({ project: { id: 456, name: "Account B project" } as never });
    finish({ id: 123, name: "Account A private project", project_type: "building" });
  });
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(useProjectStore.getState().project?.id).toBe(456);
});
