import { afterEach, expect, it, vi } from "vitest";
import { api } from "./api";
afterEach(() => vi.unstubAllGlobals());
it("does not automatically retry a failed read transport", async () => {
  const transport = vi.fn().mockRejectedValueOnce(new TypeError("Failed to fetch")).mockResolvedValue(new Response('{"ok":true}'));
  vi.stubGlobal("fetch", transport);
  await expect(api.get("/api/read-only")).rejects.toThrow("no request was automatically repeated");
  expect(transport).toHaveBeenCalledTimes(1);
});
it("does not repeat a write after a transport failure", async () => {
  const transport = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
  vi.stubGlobal("fetch", transport);
  await expect(api.post("/api/edit", { value: 1 })).rejects.toThrow("no request was automatically repeated");
  expect(transport).toHaveBeenCalledTimes(1);
});
it("surfaces an interrupted response body without cloning or replaying it", async () => {
  const partial = {ok:true,status:200,text: () => Promise.reject(new TypeError("body interrupted"))};
  const transport = vi.fn().mockResolvedValueOnce(partial).mockResolvedValue(new Response('{"ok":true}'));
  vi.stubGlobal("fetch", transport);
  await expect(api.get("/api/read-only")).rejects.toThrow("body interrupted");
  expect(transport).toHaveBeenCalledTimes(1);
});
it("does not retry an HTTP rejection or convert missing optional resources", async () => {
  const transport = vi.fn().mockResolvedValue(new Response("", { status: 404 }));
  vi.stubGlobal("fetch", transport);
  expect(await api.getOptional("/api/missing")).toBeNull();
  expect(transport).toHaveBeenCalledTimes(1);
});
