import { describe, expect, it } from "vitest";
import {
  apiErrorTitle,
  isUsageLimitError,
  parseApiErrorPayload,
  shouldRedirectOn401,
} from "@/lib/api-errors";

describe("parseApiErrorPayload", () => {
  it("extracts message and request id from structured detail", () => {
    const parsed = parseApiErrorPayload(
      429,
      {
        detail: {
          code: "usage_limit_exceeded",
          message: "You have reached your daily generation limit on the free plan.",
          request_id: "abc123",
        },
      },
      "header-id",
    );
    expect(parsed.message).toContain("daily generation limit");
    expect(parsed.code).toBe("usage_limit_exceeded");
    expect(parsed.requestId).toBe("abc123");
  });

  it("falls back to header request id", () => {
    const parsed = parseApiErrorPayload(500, { detail: { message: "Server error" } }, "rid-9");
    expect(parsed.requestId).toBe("rid-9");
  });
});

describe("apiErrorTitle", () => {
  it("maps common statuses", () => {
    expect(apiErrorTitle(401)).toBe("Sign in required");
    expect(apiErrorTitle(403)).toBe("Access denied");
    expect(apiErrorTitle(429, "usage_limit_exceeded")).toBe("Usage limit reached");
    expect(apiErrorTitle(500)).toBe("Server error");
  });
});

describe("isUsageLimitError", () => {
  it("detects usage limit code", () => {
    expect(isUsageLimitError({ status: 429, code: "usage_limit_exceeded" })).toBe(true);
    expect(isUsageLimitError({ status: 429, detail: { code: "usage_limit_exceeded" } })).toBe(true);
    expect(isUsageLimitError({ status: 429, code: "rate_limit_exceeded" })).toBe(false);
  });
});

describe("shouldRedirectOn401", () => {
  it("only redirects for 401", () => {
    expect(shouldRedirectOn401(401)).toBe(true);
    expect(shouldRedirectOn401(403)).toBe(false);
  });
});
