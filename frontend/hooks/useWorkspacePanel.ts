"use client";

import { useCallback, useEffect, useState } from "react";

/** Keep map popovers mutually exclusive without coupling their renderers. */
export function useWorkspacePanel(name: string) {
  const [open, setOpen] = useState(false);
  const show = useCallback(() => {
    window.dispatchEvent(new CustomEvent("geoai:workspace-panel", { detail: name }));
    setOpen(true);
  }, [name]);
  useEffect(() => {
    const onPanel = (event: Event) => {
      if ((event as CustomEvent<string>).detail !== name) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onOpen = () => show();
    window.addEventListener(`geoai:open-${name}`, onOpen);
    window.addEventListener("geoai:workspace-panel", onPanel);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("geoai:workspace-panel", onPanel);
      window.removeEventListener("keydown", onKey);
      window.removeEventListener(`geoai:open-${name}`, onOpen);
    };
  }, [name, show]);
  return { open, show, close: () => setOpen(false), toggle: () => open ? setOpen(false) : show() };
}
