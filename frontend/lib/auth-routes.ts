import { authRequired, getAuthToken } from "@/lib/api";

/** Login URL with optional post-auth redirect target. */
export function loginPath(next = "/dashboard"): string {
  return `/login?next=${encodeURIComponent(next)}`;
}

/** Account creation URL with a return route for gated AI actions. */
export function registrationPath(next = "/dashboard"): string {
  return `/login?mode=register&next=${encodeURIComponent(next)}`;
}

/**
 * Demo visitors can explore and edit locally. Cloud AI usage requires an
 * account, then returns them to the exact demo state they were viewing.
 */
export function redirectDemoGuestToRegistration(next: string): boolean {
  if (typeof window === "undefined" || getAuthToken()) return false;
  window.location.assign(registrationPath(next));
  return true;
}

/** Entry path for protected app areas — login when JWT is required. */
export function appEntryPath(next = "/dashboard"): string {
  return authRequired() ? loginPath(next) : next;
}

export const PUBLIC_APP_PATHS = new Set(["/", "/login"]);
