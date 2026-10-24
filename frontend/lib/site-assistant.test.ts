import { afterEach, expect, it, vi } from "vitest";
import { AssistantRequestError, sendAssistant } from "./site-assistant";
vi.mock("./api", () => ({ authenticatedFetch: (url: string, options: RequestInit) => fetch(url, { ...options, headers: { ...options.headers, Authorization: "Bearer test-token" } }) }));
afterEach(() => vi.unstubAllGlobals());

it("parses genuine SSE chunks without simulating a completed response", async () => {
  const emit = vi.fn();
  const fetchMock = vi.fn().mockResolvedValue(new Response('data: {"type":"delta","text":"hello"}\n\ndata: {"type":"task","task":{"status":"SUCCEEDED"}}\n\n'));
  vi.stubGlobal("fetch", fetchMock);
  await sendAssistant({ message: "hi" }, emit, new AbortController().signal);
  expect(emit.mock.calls[0][0]).toEqual({ type: "delta", text: "hello" }); expect(emit).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer test-token"); expect(fetchMock.mock.calls[0][1].redirect).toBe("error");
});

it("does not fabricate success or automatically retry a truncated stream", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response('data: {"type":"delta","text":"partial"}\n\n'));
  vi.stubGlobal("fetch", fetchMock);
  await expect(sendAssistant({}, vi.fn(), new AbortController().signal)).rejects.toThrow("interrupted"); expect(fetchMock).toHaveBeenCalledOnce();
});

it("surfaces provider quota errors without a fallback", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"Budget reached"}', { status: 429 })); vi.stubGlobal("fetch", fetchMock);
  await expect(sendAssistant({}, vi.fn(), new AbortController().signal)).rejects.toThrow("Budget reached"); expect(fetchMock).toHaveBeenCalledOnce();
});

it("reads the real application's structured error envelope", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response('{"detail":{"message":"Explicit spending approval required","code":"unavailable"}}', { status: 503 })));
  await expect(sendAssistant({}, vi.fn(), new AbortController().signal)).rejects.toThrow("Explicit spending approval required");
});

it("handles UTF-8 and CRLF frames split across network chunks", async () => {
  const bytes = new TextEncoder().encode('data: {"type":"delta","text":"地理"}\r\n\r\ndata: {"type":"task","task":{"status":"SUCCEEDED"}}\r\n\r\n');
  const stream = new ReadableStream({ start(controller) { for (let i = 0; i < bytes.length; i++) controller.enqueue(bytes.slice(i, i + 1)); controller.close(); } });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(stream)));
  const emit = vi.fn(); await sendAssistant({}, emit, new AbortController().signal);
  expect(emit.mock.calls[0][0]).toMatchObject({ text: "地理" }); expect(emit).toHaveBeenCalledTimes(2);
});

it("preserves the backend quota code and availability state", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response('{"detail":{"code":"TOKEN_LIMIT","availability":"RATE_LIMITED","message":"Allowance reached"}}', { status: 429 })));
  const error = await sendAssistant({}, vi.fn(), new AbortController().signal).catch(e => e);
  expect(error).toBeInstanceOf(AssistantRequestError); expect(error.code).toBe("TOKEN_LIMIT"); expect(error.availability).toBe("RATE_LIMITED");
});
