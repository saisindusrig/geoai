"use client";

import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { useWorkspaceMap } from "@/components/layout/WorkspaceMapContext";

/** Render engine-owned controls in the shared toolbar without moving engine state. */
export default function WorkspaceMapControl({ children, side, fallbackClassName }: {
  children: ReactNode;
  side: "left" | "right";
  fallbackClassName: string;
}) {
  const { leftControlsContainer, rightControlsContainer } = useWorkspaceMap();
  const controlsContainer = side === "left" ? leftControlsContainer : rightControlsContainer;
  return controlsContainer
    ? createPortal(<div className="workspace-map-control relative shrink-0 text-xs">{children}</div>, controlsContainer)
    : <div className={fallbackClassName}>{children}</div>;
}
