// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { ApiError, fetchBinary, setAuthToken, clearAuthToken } from "./api";
import { downloadFile, downloadFilename } from "./download";
vi.mock("./toast", () => ({ toast: vi.fn() }));
afterEach(() => { clearAuthToken(); vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.useRealTimers(); });

it("preserves UTF-8 server names and removes dangerous path/control characters", () => {
  expect(downloadFilename("attachment; filename=old.pdf; filename*=UTF-8''%E2%82%AC-report.pdf", "report.pdf")).toBe("€-report.pdf");
  expect(downloadFilename('attachment; filename="../../report.pdf"', "safe.pdf")).toBe("report.pdf");
  expect(downloadFilename('attachment; filename="CON"', "safe.pdf")).toBe("safe.pdf");
  expect(downloadFilename("attachment; filename*=UTF-8''%ZZ", "safe.pdf")).toBe("safe.pdf");
});
it("sends the bearer only to the configured API and preserves binary bytes and MIME", async () => {
  setAuthToken("fixture-token");
  const bytes = new Uint8Array([0, 1, 255, 128]);
  const fetcher = vi.fn().mockResolvedValue(new Response(bytes, { headers: { "Content-Type": "model/gltf-binary" } }));
  vi.stubGlobal("fetch", fetcher);
  const result = await fetchBinary("/api/projects/1/exports/model.glb");
  expect(new Uint8Array(await result.arrayBuffer())).toEqual(bytes);
  expect(result.headers.get("Content-Type")).toBe("model/gltf-binary");
  expect(fetcher).toHaveBeenCalledWith(expect.not.stringContaining("fixture-token"), expect.objectContaining({ redirect: "error" }));
  expect(new Headers(fetcher.mock.calls[0][1].headers).get("Authorization")).toBe("Bearer fixture-token");
  await expect(fetchBinary("https://foreign.invalid/export")).rejects.toThrow("outside");
  expect(fetcher).toHaveBeenCalledOnce();
});
it.each([401, 403, 404, 500])("preserves HTTP %i without unauthenticated replay", async status => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: `Fixture ${status}` }), { status }));
  vi.stubGlobal("fetch", fetcher);
  await expect(fetchBinary("/api/projects/1/exports/pdf")).rejects.toMatchObject({ status });
  expect(fetcher).toHaveBeenCalledOnce();
});
it("deduplicates a large binary download, revokes its URL and permits explicit retry", async () => {
  vi.useFakeTimers();
  let resolve!: (value: Response) => void;
  const fetcher = vi.fn().mockImplementationOnce(() => new Promise(yes => { resolve = yes; }));
  vi.stubGlobal("fetch", fetcher);
  const create = vi.fn(() => "blob:fixture"); const revoke = vi.fn();
  vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: create, revokeObjectURL: revoke }));
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  const first = downloadFile("/api/projects/1/exports/pdf", "report.pdf");
  expect(downloadFile("/api/projects/1/exports/pdf", "report.pdf")).toBe(first);
  resolve(new Response(new Uint8Array(5 * 1024 * 1024), { headers: { "Content-Disposition": 'attachment; filename="trusted.pdf"' } }));
  await first;
  expect(fetcher).toHaveBeenCalledOnce(); expect(click).toHaveBeenCalledOnce();
  expect(create.mock.calls).toHaveLength(1);
  expect(document.querySelector('a[download]')).toBeNull();
  await vi.advanceTimersByTimeAsync(1000); expect(revoke).toHaveBeenCalledWith("blob:fixture");
  fetcher.mockRejectedValueOnce(new TypeError("Offline"));
  await expect(downloadFile("/api/projects/1/exports/pdf")).rejects.toThrow("no request was automatically repeated");
  fetcher.mockResolvedValueOnce(new Response("%PDF-fixture"));
  await downloadFile("/api/projects/1/exports/pdf", "report.pdf");
  expect(fetcher).toHaveBeenCalledTimes(3);
  expect(ApiError).toBeDefined();
});
