import { authenticatedFetch } from "./api";
import { assertSession, sessionRevision } from "./firebase-auth";
import { parseApiErrorPayload } from "./api-errors";

export type AssistantContext = { project_id: number | null; revision_id: number | null; selected_ids: string[]; dirty: boolean };
export type ToolResult = Partial<Omit<import("./workspace-assistant").WorkspaceCommand,"kind">> & { kind?: string; href?: string; destination?: string; projectId?: number; revisionId?: number; projectName?: string; componentIds?: string[]; componentId?: string; before?: number[]; after?: number[]; documentHash?: string; componentHash?: string; candidate?: import("./types").EditableModelComponent; notice?: string };
export type AssistantAvailability = { enabled: boolean; message: string; state?: "AVAILABLE" | "DISABLED" | "RATE_LIMITED" | "AWAITING_SPENDING_APPROVAL"; code?: string; requestAllowance?: number; canSend?: boolean; models?: string[]; usage?: { daily_requests?: number; accounted_daily_tokens: number; accounted_usd: number }; dailyTokenAllowance?: number };
export type AssistantEvent = { type: string; text?: string; steps?: string[]; name?: string; ok?: boolean; message?: string; error?: string; code?: string; availability?: AssistantAvailability["state"]; result?: ToolResult; task?: AssistantTask };
export type AssistantTask = { id: string; request: AssistantContext & { message: string; model: string; page: string }; context?: unknown; status: string; reply: string; error?: string; events: AssistantEvent[]; model: string };

export class AssistantRequestError extends Error {
  constructor(message: string, public code?: string, public availability?: AssistantAvailability["state"]) { super(message); }
}

export async function sendAssistant(body: object, onEvent: (event: AssistantEvent) => void, signal: AbortSignal) {
  const expectedSession = sessionRevision();
  const response = await authenticatedFetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/api/assistant/turn`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body), signal, redirect: "error",
  });
  if (!response.ok || !response.body) {
    let message = `Assistant unavailable (${response.status}). Retry manually.`;
    let code: string | undefined, availability: AssistantAvailability["state"];
    try { const parsed = parseApiErrorPayload(response.status, await response.json(), response.headers.get("X-Request-ID")); if (parsed.message !== "Request failed") message = parsed.message; code = parsed.code; availability = parsed.detail?.availability as AssistantAvailability["state"]; } catch { /* Retain status without exposing response bodies. */ }
    throw new AssistantRequestError(message, code, availability || (response.status === 429 ? "RATE_LIMITED" : "DISABLED"));
  }
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "", completed = false, finished = false, received = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      assertSession(expectedSession);
      received += value?.byteLength || 0;
      if (received > 4000000) throw new Error("Assistant response limit exceeded.");
      buffer += decoder.decode(value, { stream: !done });
      buffer = buffer.replaceAll("\r\n", "\n");
      let end: number;
      while ((end = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, end); buffer = buffer.slice(end + 2);
        if (frame.startsWith("data: ")) { const event = JSON.parse(frame.slice(6)) as AssistantEvent; onEvent(event); if (event.type === "task") completed = true; }
      }
      if (buffer.length > 2000000) throw new Error("Assistant response limit exceeded.");
      if (done) { finished = true; break; }
    }
  } finally { if (!finished) await reader.cancel().catch(() => {}); reader.releaseLock(); }
  if (!completed) throw new Error("Assistant stream interrupted. Review saved history, then Retry manually.");
}

export function publishAssistantContext(context: AssistantContext) {
  window.dispatchEvent(new CustomEvent("geoai:assistant-context", { detail: context }));
}
