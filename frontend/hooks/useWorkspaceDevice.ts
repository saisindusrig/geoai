"use client";

import { useSyncExternalStore } from "react";
import { WORKSPACE_DESKTOP_QUERY } from "@/lib/workspace-device";

function subscribe(notify: () => void) {
  if (typeof window.matchMedia !== "function") return () => {};
  const media = window.matchMedia(WORKSPACE_DESKTOP_QUERY);
  media.addEventListener("change", notify);
  return () => media.removeEventListener("change", notify);
}

export function useWorkspaceDevice() {
  return useSyncExternalStore(subscribe, () => typeof window.matchMedia === "function" && window.matchMedia(WORKSPACE_DESKTOP_QUERY).matches ? "desktop" : "unsupported", () => "checking");
}
