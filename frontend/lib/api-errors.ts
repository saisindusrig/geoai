/** Client-safe API error parsing and display helpers. */

export interface ParsedApiError {
  status: number;
  message: string;
  requestId?: string;
  code?: string;
  detail?: Record<string, unknown>;
}

export function apiErrorTitle(status: number, code?: string): string {
  if (status === 401 || code === "unauthorized") return "Sign in required";
  if (status === 403 || code === "forbidden") return "Access denied";
  if (status === 429 && code === "usage_limit_exceeded") return "Usage limit reached";
  if (status === 429) return "Too many requests";
  if (status >= 500) return "Server error";
  if (status === 404) return "Not found";
  return "Request failed";
}

export function parseApiErrorPayload(
  status: number,
  body: unknown,
  requestId?: string | null,
): ParsedApiError {
  let message = "Request failed";
  let code: string | undefined;
  let detail: Record<string, unknown> | undefined;
  let rid = requestId ?? undefined;

  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    if (typeof record.request_id === "string") rid = record.request_id;
    const rawDetail = record.detail;
    if (typeof rawDetail === "string") {
      message = rawDetail;
    } else if (rawDetail && typeof rawDetail === "object") {
      detail = rawDetail as Record<string, unknown>;
      if (typeof detail.message === "string") message = detail.message;
      if (typeof detail.code === "string") code = detail.code;
      if (typeof detail.request_id === "string") rid = detail.request_id;
    }
  }

  return { status, message, requestId: rid, code, detail };
}

export function formatApiErrorMessage(error: ParsedApiError | { message: string }): string {
  return "message" in error ? error.message : "Request failed";
}

export function isUsageLimitError(error: { status?: number; code?: string; detail?: Record<string, unknown> }): boolean {
  return (
    error.status === 429 &&
    (error.code === "usage_limit_exceeded" || error.detail?.code === "usage_limit_exceeded")
  );
}

export function shouldRedirectOn401(status: number): boolean {
  return status === 401;
}
