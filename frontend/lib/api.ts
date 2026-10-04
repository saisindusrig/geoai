import type { CopilotAction, CopilotStreamResult } from "@/lib/types";
import {
  formatApiErrorMessage as formatApiErrorMessageFromLib,
  isUsageLimitError as isUsageLimitErrorFromLib,
  parseApiErrorPayload,
  type ParsedApiError,
} from "@/lib/api-errors";
import { reportClientError } from "@/lib/observability";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_KEY = "geoai_access_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_KEY);
}

export function setAuthToken(token: string) {
  localStorage.setItem(AUTH_KEY, token);
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_KEY);
}

export function authRequired(): boolean {
  return process.env.NEXT_PUBLIC_AUTH_REQUIRE_JWT === "true";
}

function handleUnauthorized() {
  if (typeof window === "undefined" || !authRequired()) return;
  clearAuthToken();
  if (!window.location.pathname.startsWith("/login")) {
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: Record<string, unknown>,
    public requestId?: string,
    public code?: string,
  ) {
    super(message);
  }

  toParsed(): ParsedApiError {
    return {
      status: this.status,
      message: this.message,
      detail: this.detail,
      requestId: this.requestId,
      code: this.code,
    };
  }
}

export function formatApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return formatApiErrorMessageFromLib(error as ParsedApiError);
}

export function isUsageLimitError(error: unknown): boolean {
  if (error instanceof ApiError) {
    return isUsageLimitErrorFromLib({
      status: error.status,
      code: error.code,
      detail: error.detail,
    });
  }
  return false;
}

async function parseErrorResponse(res: Response): Promise<ApiError> {
  const headerRequestId = res.headers.get("X-Request-ID");
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  const parsed = parseApiErrorPayload(res.status, body, headerRequestId);
  const apiError = new ApiError(parsed.status, parsed.message, parsed.detail, parsed.requestId, parsed.code);
  reportClientError(apiError, { path: res.url, status: res.status, requestId: parsed.requestId });
  return apiError;
}

export async function streamChat(
  projectId: number,
  message: string,
  onChunk: (chunk: string) => void,
): Promise<CopilotStreamResult> {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/api/projects/${projectId}/ai/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  });
  if (!res.ok || !res.body) {
    if (res.status === 401) handleUnauthorized();
    throw await parseErrorResponse(res);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: CopilotStreamResult = { actions: [], warnings: [] };
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = JSON.parse(line.slice(6)) as {
        chunk?: string;
        done?: boolean;
        message?: string;
        actions?: CopilotAction[];
        warnings?: string[];
        provider?: string;
        action?: CopilotAction | null;
        disclaimer?: string;
      };
      if (data.chunk) onChunk(data.chunk);
      if (data.done) {
        result = {
          message: data.message,
          actions: data.actions ?? [],
          warnings: data.warnings ?? [],
          provider: data.provider,
          action: data.action ?? null,
          disclaimer: data.disclaimer,
        };
      }
    }
  }
  return result;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    if (res.status === 401) handleUnauthorized();
    throw await parseErrorResponse(res);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  const data = JSON.parse(text) as T | null;
  return data as T;
}

/** GET optional resource — returns null when missing (404 or JSON null). */
async function getOptional<T>(path: string): Promise<T | null> {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    if (res.status === 401) handleUnauthorized();
    throw await parseErrorResponse(res);
  }
  const text = await res.text();
  if (!text || text === "null") return null;
  return JSON.parse(text) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  getOptional: <T>(path: string) => getOptional<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export async function uploadSurveyFile<T>(
  projectId: number,
  file: File,
  fields: Record<string, string>,
): Promise<T> {
  const token = getAuthToken();
  const form = new FormData();
  form.append("file", file);
  for (const [k, v] of Object.entries(fields)) form.append(k, v);
  const res = await fetch(`${API_URL}/api/projects/${projectId}/survey/import`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    if (res.status === 401) handleUnauthorized();
    throw await parseErrorResponse(res);
  }
  return res.json();
}

export const apiUrl = (path: string) => `${API_URL}${path}`;

export type { ParsedApiError };
