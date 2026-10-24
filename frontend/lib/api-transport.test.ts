// @vitest-environment jsdom
import {afterEach,expect,it,vi} from "vitest";
import {api} from "./api";
afterEach(()=>vi.unstubAllGlobals());
it("surfaces a failed read once and allows explicit recovery",async()=>{
  const fetch=vi.fn().mockRejectedValueOnce(new TypeError("Failed to fetch")).mockResolvedValueOnce(new Response('{"saved":true}'));
  vi.stubGlobal("fetch",fetch);
  await expect(api.get("/api/projects/793")).rejects.toThrow("no request was automatically repeated");
  expect(fetch).toHaveBeenCalledTimes(1);
  await expect(api.get("/api/projects/793")).resolves.toEqual({saved:true});
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(new Headers(fetch.mock.calls[1][1].headers).has("Content-Type")).toBe(false);
});
it("never automatically repeats a mutation after transport failure",async()=>{
  const fetch=vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));vi.stubGlobal("fetch",fetch);
  await expect(api.post("/api/projects/793/authorize",{hash:"exact"})).rejects.toThrow("draft has been kept");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(new Headers(fetch.mock.calls[0][1].headers).get("Content-Type")).toBe("application/json");
});
