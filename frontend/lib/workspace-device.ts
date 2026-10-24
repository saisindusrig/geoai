/** Advanced spatial editing needs the existing desktop layout and precise input. */
export const WORKSPACE_DESKTOP_QUERY = "(min-width: 1280px) and (any-pointer: fine)";

export function requiresDesktopWorkspace(pathname: string | null) {
  return /^\/projects\/\d+\/(workspace|map|model|analysis|estimate|scenarios)\/?$/.test(pathname ?? "");
}

export function projectReturnPath(search: string): string | null {
  const path = new URLSearchParams(search).get("returnTo");
  return path && /^\/projects\/\d+\/(workspace|map|model|analysis|estimate|scenarios)(?:\?[^#]*)?(?:#.*)?$/.test(path) ? path : null;
}
