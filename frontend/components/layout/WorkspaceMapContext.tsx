"use client";

import { createContext, useContext } from "react";

interface WorkspaceMapContextValue {
  leftControlsContainer?: HTMLDivElement | null;
  rightControlsContainer?: HTMLDivElement | null;
  creditsContainer?: HTMLDivElement | null;
  focusMode: boolean;
  toolsOpen: boolean;
  copilotOpen: boolean;
  copilotPanelVisible: boolean;
  onOpenTools: () => void;
  onOpenCopilot: () => void;
  onToggleCopilotPanel: () => void;
}

const WorkspaceMapContext = createContext<WorkspaceMapContextValue>({
  focusMode: false,
  toolsOpen: false,
  copilotOpen: false,
  copilotPanelVisible: true,
  onOpenTools: () => {},
  onOpenCopilot: () => {},
  onToggleCopilotPanel: () => {},
});

export function WorkspaceMapProvider({
  value,
  children,
}: {
  value: WorkspaceMapContextValue;
  children: React.ReactNode;
}) {
  return <WorkspaceMapContext.Provider value={value}>{children}</WorkspaceMapContext.Provider>;
}

export function useWorkspaceMap() {
  return useContext(WorkspaceMapContext);
}
