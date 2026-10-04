/** Optional client-side error reporting — no-op without NEXT_PUBLIC_SENTRY_DSN. */

export function reportClientError(error: unknown, context?: Record<string, unknown>): void {
  if (typeof window === "undefined") return;
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  if (!dsn) {
    if (process.env.NODE_ENV === "development") {
      console.debug("[geoai] client error", context, error);
    }
    return;
  }
  // Install @sentry/browser or @sentry/nextjs and initialize here when enabling Sentry.
  console.warn("[geoai] NEXT_PUBLIC_SENTRY_DSN is set but Sentry SDK is not bundled yet.", context, error);
}

export function initClientObservability(): void {
  if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;
  reportClientError(new Error("Sentry DSN configured — add @sentry/nextjs to enable forwarding"));
}
