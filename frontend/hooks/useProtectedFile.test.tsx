import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("@/lib/api", () => ({ fetchBinary: vi.fn(), isApiFileUrl: (url: string) => url.startsWith('/files/') }));
vi.mock("@/lib/toast", () => ({ toast: vi.fn() }));
import { fetchBinary } from "@/lib/api";
import { useProtectedFile } from "./useProtectedFile";
afterEach(() => { cleanup(); vi.clearAllMocks(); });
it("creates a protected model URL and releases it when the source is replaced", async () => {
  URL.createObjectURL = vi.fn(() => 'blob:model'); URL.revokeObjectURL = vi.fn();
  vi.mocked(fetchBinary).mockResolvedValue(new Response('glTF'));
  const hook = renderHook(({ source }) => useProtectedFile(source), { initialProps: { source: '/files/projects/1/model.glb' } });
  await waitFor(() => expect(hook.result.current).toBe('blob:model'));
  hook.rerender({ source: '/models/public.glb' });
  expect(hook.result.current).toBe('/models/public.glb');
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:model');
  expect(fetchBinary).toHaveBeenCalledOnce();
});
it("does not expose the unauthenticated URL after a protected fetch fails", async () => {
  vi.mocked(fetchBinary).mockRejectedValue(new Error('Forbidden'));
  const hook = renderHook(() => useProtectedFile('/files/projects/1/model.glb'));
  await act(async () => {});
  expect(hook.result.current).toBeNull();
  expect(fetchBinary).toHaveBeenCalledOnce();
});
it("does not allocate a late Blob URL after unmount", async () => {
  let resolve!: (response: Response) => void;
  vi.mocked(fetchBinary).mockImplementation(() => new Promise(yes => { resolve = yes; }));
  URL.createObjectURL = vi.fn();
  const hook = renderHook(() => useProtectedFile('/files/projects/1/model.glb'));
  hook.unmount();
  await act(async () => { resolve(new Response('glTF')); });
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
