"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, Menu, Minimize2, X } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useState, type ReactNode } from "react";
import ModernAssistantPanel from "@/components/ai/ModernAssistantPanel";
import { WorkspaceMapProvider } from "@/components/layout/WorkspaceMapContext";
import { PanelResizeHandle } from "@/components/ui/panel-resize-handle";
import { Button } from "@/components/ui/button";
import { useHorizontalPanelResize } from "@/hooks/usePointerResize";
import type { DesignOutput } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/stores/projectStore";

const LEFT_WIDTH = 304;
const RIGHT_WIDTH_DEFAULT = 380;
const RIGHT_WIDTH_MIN = 340;
const RIGHT_WIDTH_MAX = 560;

function focusKey(projectId: number) {
  return `project-${projectId}-focus-mode`;
}

function copilotPanelKey(projectId: number) {
  return `project-${projectId}-copilot-panel`;
}

function readStoredFocus(projectId: number, defaultFocus: boolean) {
  if (typeof window === "undefined") return defaultFocus;
  const stored = localStorage.getItem(focusKey(projectId));
  return stored !== null ? stored === "true" : defaultFocus;
}

function readStoredCopilotVisible(projectId: number) {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem(copilotPanelKey(projectId));
  return stored !== null ? stored === "true" : true;
}

interface AiProps {
  projectId: number;
  design?: DesignOutput | null;
  onApplyParameters: (params: Record<string, unknown>) => void;
  onRegenerate: (params: Record<string, unknown>) => void;
  onRunSiteAnalysis?: () => Promise<void>;
  currentParameters?: Record<string, unknown> | null;
}

interface WorkspaceLayoutProps {
  projectId: number;
  ai: AiProps;
  leftPanel?: ReactNode;
  map: ReactNode;
  toolbar?: ReactNode;
  /** Compact controls that sit over the map instead of consuming a second app bar. */
  toolRail?: ReactNode;
  mapToolbar?: ReactNode;
  mapCreditsContainer?: HTMLDivElement | null;
  rightPanel?: ReactNode;
  defaultFocus?: boolean;
}

export default function WorkspaceLayout({
  projectId,
  ai,
  leftPanel,
  map,
  toolbar,
  toolRail,
  mapToolbar,
  mapCreditsContainer,
  rightPanel,
  defaultFocus = false,
}: WorkspaceLayoutProps) {
  const [focusMode, setFocusMode] = useState(() => readStoredFocus(projectId, defaultFocus));
  const [focusProjectId, setFocusProjectId] = useState(projectId);
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);
  const [leftControlsContainer, setLeftControlsContainer] = useState<HTMLDivElement | null>(null);
  const [rightControlsContainer, setRightControlsContainer] = useState<HTMLDivElement | null>(null);
  const [copilotPanelVisible, setCopilotPanelVisible] = useState(() =>
    readStoredCopilotVisible(projectId),
  );
  const setWorkspaceFullscreen = useProjectStore((s) => s.setWorkspaceFullscreen);
  const { size: rightWidth, onResizePointerDown: onRightWidthPointerDown } = useHorizontalPanelResize({
    storageKey: "geoai-workspace-right-width",
    defaultSize: RIGHT_WIDTH_DEFAULT,
    minSize: RIGHT_WIDTH_MIN,
    maxSize: RIGHT_WIDTH_MAX,
  });

  if (projectId !== focusProjectId) {
    setFocusProjectId(projectId);
    setFocusMode(readStoredFocus(projectId, defaultFocus));
    setCopilotPanelVisible(readStoredCopilotVisible(projectId));
  }

  useLayoutEffect(() => {
    setWorkspaceFullscreen(focusMode);
  }, [focusMode, setWorkspaceFullscreen]);

  useEffect(() => () => setWorkspaceFullscreen(false), [setWorkspaceFullscreen]);

  const toggleFocus = useCallback(() => {
    setFocusMode((prev) => {
      const next = !prev;
      localStorage.setItem(focusKey(projectId), String(next));
      if (next) {
        setLeftOpen(false);
        setRightOpen(false);
      }
      return next;
    });
  }, [projectId]);

  const toggleCopilotPanel = useCallback(() => {
    setCopilotPanelVisible((prev) => {
      const next = !prev;
      localStorage.setItem(copilotPanelKey(projectId), String(next));
      if (!next) setRightOpen(false);
      return next;
    });
  }, [projectId]);

  useEffect(() => {
    const onOpenCopilot = () => {
      setCopilotPanelVisible(true);
      localStorage.setItem(copilotPanelKey(projectId), "true");
      setRightOpen(true);
    };
    const onToggleCopilot = () => toggleCopilotPanel();
    window.addEventListener("geoai:open-copilot", onOpenCopilot);
    window.addEventListener("geoai:toggle-copilot", onToggleCopilot);
    return () => {
      window.removeEventListener("geoai:open-copilot", onOpenCopilot);
      window.removeEventListener("geoai:toggle-copilot", onToggleCopilot);
    };
  }, [projectId, toggleCopilotPanel]);

  useEffect(() => {
    if (!focusMode) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (leftOpen || rightOpen) {
          setLeftOpen(false);
          setRightOpen(false);
        } else {
          toggleFocus();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusMode, leftOpen, rightOpen, toggleFocus]);

  useEffect(() => {
    if (!focusMode || (!leftOpen && !rightOpen)) return;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    const prevOverflow = document.body.style.overflow;
    const prevPadding = document.body.style.paddingRight;
    document.body.style.overflow = "hidden";
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }
    return () => {
      document.body.style.overflow = prevOverflow;
      document.body.style.paddingRight = prevPadding;
    };
  }, [focusMode, leftOpen, rightOpen]);

  const hasLeftPanel = Boolean(leftPanel);
  const showInlineLeft = !focusMode && hasLeftPanel;
  const showInlineRight = !focusMode && copilotPanelVisible;

  return (
    <div
      className={cn(
        "flex flex-1 flex-col min-h-0 bg-background",
        focusMode && "fixed inset-0 z-[35] bg-background",
      )}
    >
      {toolbar && !focusMode && (
        <div className="shrink-0 border-b border-border bg-background/90 px-3 py-1.5 backdrop-blur-xl">
          <div className="flex min-w-0 items-center gap-2">
            <div className="flex-1 min-w-0 overflow-hidden">
              {toolbar}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {showInlineLeft && (
          <aside className="hidden lg:flex w-[304px] shrink-0 min-h-0 flex-col border-r border-border bg-sidebar overflow-hidden">
            {leftPanel}
          </aside>
        )}

        <WorkspaceMapProvider
          value={{
            leftControlsContainer,
            rightControlsContainer,
            creditsContainer: mapCreditsContainer,
            focusMode,
            toolsOpen: hasLeftPanel && leftOpen,
            copilotOpen: rightOpen,
            copilotPanelVisible,
            onOpenTools: () => {
              if (hasLeftPanel) setLeftOpen(true);
            },
            onOpenCopilot: () => {
              setCopilotPanelVisible(true);
              localStorage.setItem(copilotPanelKey(projectId), "true");
              setRightOpen(true);
            },
            onToggleCopilotPanel: toggleCopilotPanel,
          }}
        >
          <div className="workspace-map-viewport flex-1 min-w-0 min-h-0 relative overflow-hidden">
            {focusMode && (
              <div className="absolute top-3 left-3 z-30 flex items-center gap-1.5 pointer-events-auto">
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 gap-1.5 panel-glass shadow-md text-xs"
                  onClick={() => window.dispatchEvent(new CustomEvent("geoai:open-nav"))}
                >
                  <Menu className="h-3.5 w-3.5" />
                  Menu
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 gap-1.5 panel-glass shadow-md text-xs"
                  onClick={toggleFocus}
                  title="Exit full screen (Esc)"
                >
                  <Minimize2 className="h-3.5 w-3.5" />
                  Exit
                </Button>
              </div>
            )}
            <div className="absolute inset-0">{map}</div>

            {!focusMode && toolRail && (
              <div className="absolute left-3 top-3 z-30 pointer-events-auto">
                {toolRail}
              </div>
            )}
            {mapToolbar && (
              <div className="workspace-map-commandrow absolute left-1/2 top-3 z-40 w-max -translate-x-1/2 pointer-events-none">
                <div ref={setLeftControlsContainer} className="absolute right-full top-0 mr-2 flex items-center gap-2 pointer-events-auto" />
                <div className="pointer-events-auto">{!focusMode && mapToolbar}</div>
                <div ref={setRightControlsContainer} className="absolute left-full top-0 ml-2 flex items-center gap-2 pointer-events-auto" />
              </div>
            )}

            {!focusMode && !copilotPanelVisible && (
              <div className="absolute bottom-20 right-3 z-30 pointer-events-auto hidden md:block">
                <Button
                  size="sm"
                  className="h-auto min-w-[2.75rem] flex-col gap-0.5 py-2 px-1.5 panel-glass border-primary/30 shadow-md"
                  title="Show AI Copilot"
                  onClick={() => {
                    setCopilotPanelVisible(true);
                    localStorage.setItem(copilotPanelKey(projectId), "true");
                  }}
                  aria-label="Show AI Copilot panel"
                >
                  <Bot className="h-4 w-4 text-primary" />
                  <span className="text-[8px] font-semibold leading-none">Copilot</span>
                </Button>
              </div>
            )}
          </div>
        </WorkspaceMapProvider>

        {showInlineRight && (
          <div
            className="hidden md:flex relative shrink-0 min-h-0"
            style={{ width: rightWidth }}
          >
            <PanelResizeHandle
              orientation="vertical"
              onPointerDown={onRightWidthPointerDown}
              className="absolute left-0 top-0 bottom-0 z-10 -translate-x-1/2"
            />
            <aside className="flex w-full min-h-0 flex-col border-l border-border bg-background-secondary overflow-hidden">
              <div className="min-h-0 flex-1">{rightPanel ?? <ModernAssistantPanel {...ai} />}</div>
            </aside>
          </div>
        )}
      </div>

      <AnimatePresence>
        {focusMode && hasLeftPanel && leftOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 modal-overlay"
              onClick={() => setLeftOpen(false)}
            />
            <motion.aside
              initial={{ x: -LEFT_WIDTH - 20 }}
              animate={{ x: 0 }}
              exit={{ x: -LEFT_WIDTH - 20 }}
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
              className="fixed inset-y-0 left-0 z-50 flex w-[304px] max-w-[88vw] flex-col border-r border-border bg-sidebar shadow-xl"
            >
              <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
                <span className="text-xs font-semibold">Engineering Tools</span>
                <button
                  title="Close"
                  type="button"
                  onClick={() => setLeftOpen(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="flex-1 min-h-0 overflow-hidden">{leftPanel}</div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {focusMode && rightOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 modal-overlay"
              onClick={() => setRightOpen(false)}
            />
            <motion.aside
              initial={{ x: rightWidth + 20 }}
              animate={{ x: 0 }}
              exit={{ x: rightWidth + 20 }}
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
              style={{ width: rightWidth }}
              className="fixed inset-y-0 right-0 z-50 flex max-w-[94vw] flex-col border-l border-border bg-background-secondary shadow-xl"
            >
              <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
                <span className="text-xs font-semibold">AI Copilot</span>
                <button
                  title="Close"
                  type="button"
                  onClick={() => setRightOpen(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="flex-1 min-h-0 overflow-hidden">
                {rightPanel ?? <ModernAssistantPanel {...ai} />}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
