"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Menu, Minimize2, X } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useState, type ReactNode } from "react";
import { WorkspaceMapProvider } from "@/components/layout/WorkspaceMapContext";
import { PanelResizeHandle } from "@/components/ui/panel-resize-handle";
import { Button } from "@/components/ui/button";
import { useHorizontalPanelResize } from "@/hooks/usePointerResize";
import type { DesignOutput } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/stores/projectStore";

const LEFT_WIDTH = 304;
const RIGHT_WIDTH_DEFAULT = 440;
const RIGHT_WIDTH_MIN = 340;
const RIGHT_WIDTH_MAX = 560;

function focusKey(projectId: number) {
  return `project-${projectId}-focus-mode`;
}

function readStoredFocus(projectId: number, defaultFocus: boolean) {
  if (typeof window === "undefined") return defaultFocus;
  const stored = localStorage.getItem(focusKey(projectId));
  return stored !== null ? stored === "true" : defaultFocus;
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
  mapBottomControls?: ReactNode;
  mapCreditsContainer?: HTMLDivElement | null;
  rightPanel?: ReactNode;
  compactInspector?: boolean;
  inspectorOpen?: boolean;
  defaultFocus?: boolean;
}

export default function WorkspaceLayout({
  projectId,
  leftPanel,
  map,
  toolbar,
  toolRail,
  mapToolbar,
  mapBottomControls,
  mapCreditsContainer,
  rightPanel,
  compactInspector = false,
  inspectorOpen = false,
  defaultFocus = false,
}: WorkspaceLayoutProps) {
  const [focusMode, setFocusMode] = useState(() => readStoredFocus(projectId, defaultFocus));
  const [focusProjectId, setFocusProjectId] = useState(projectId);
  const [analysisMode,setAnalysisMode] = useState(false);
  useEffect(()=>{const handler=(event:Event)=>setAnalysisMode(!!(event as CustomEvent<{active:boolean}>).detail?.active);window.addEventListener("geoai:analysis-workspace",handler);return()=>window.removeEventListener("geoai:analysis-workspace",handler);},[]);
  const [leftOpen, setLeftOpen] = useState(false);
  const [leftControlsContainer, setLeftControlsContainer] = useState<HTMLDivElement | null>(null);
  const [rightControlsContainer, setRightControlsContainer] = useState<HTMLDivElement | null>(null);
  const setWorkspaceFullscreen = useProjectStore((s) => s.setWorkspaceFullscreen);
  const { size: rightWidth, onResizePointerDown: onRightWidthPointerDown } = useHorizontalPanelResize({
    storageKey: "geoai-workspace-right-width",
    defaultSize: RIGHT_WIDTH_DEFAULT,
    minSize: RIGHT_WIDTH_MIN,
    maxSize: RIGHT_WIDTH_MAX,
  });

  const {size: inspectorWidth,onResizePointerDown: onInspectorResize}=useHorizontalPanelResize({storageKey:"geoai-inspector-width",defaultSize:344,minSize:320,maxSize:520});

  if (projectId !== focusProjectId) {
    setFocusProjectId(projectId);
    setFocusMode(readStoredFocus(projectId, defaultFocus));
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
      }
      return next;
    });
  }, [projectId]);

  useEffect(() => {
    if (!focusMode) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (leftOpen) {
          setLeftOpen(false);
        } else {
          toggleFocus();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusMode, leftOpen, toggleFocus]);

  useEffect(() => {
    if (!focusMode || !leftOpen) return;
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
  }, [focusMode, leftOpen]);

  const hasLeftPanel = Boolean(leftPanel);
  const showInlineLeft = !focusMode && Boolean(leftPanel);
  const showInlineRight = !focusMode && Boolean(rightPanel);

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
          <aside aria-label="Engineering tools sidebar" className={cn("hidden lg:flex shrink-0 min-h-0 flex-col border-r border-border bg-sidebar overflow-hidden", "w-[304px]")}>
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
            copilotOpen: false,
            copilotPanelVisible: false,
            onOpenTools: () => {
              if (hasLeftPanel) setLeftOpen(true);
            },
            onOpenCopilot: () => window.dispatchEvent(new Event("geoai:open-site-assistant")),
            onToggleCopilotPanel: () => window.dispatchEvent(new Event("geoai:open-site-assistant")),
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
              <div className="workspace-map-commandrow absolute left-16 right-3 top-3 z-40 min-w-0 pointer-events-none">
                <div ref={setLeftControlsContainer} className="absolute left-0 top-0 flex items-center gap-2 pointer-events-auto" />
                <div className="workspace-main-tools pointer-events-none absolute top-0 w-max">{!focusMode && mapToolbar}</div>
                <div ref={setRightControlsContainer} className="absolute right-0 top-0 flex items-center gap-2 pointer-events-auto" />
              </div>
            )}
            {!focusMode && mapBottomControls && <div className="workspace-bottom-controls absolute bottom-10 right-3 z-40">{mapBottomControls}</div>}
          </div>
        </WorkspaceMapProvider>

        {showInlineRight && (
          <div
            className={cn("hidden md:flex relative shrink-0 min-h-0", compactInspector && "workspace-inspector-slot")}
            style={{ width: compactInspector ? (inspectorOpen ? (analysisMode ? "min(484px, calc(42vw + 44px))" : `min(${inspectorWidth}px, 45vw)`) : 44) : rightWidth }}
          >
            {(!compactInspector || inspectorOpen && !analysisMode) && <PanelResizeHandle
              orientation="vertical"
              onPointerDown={compactInspector ? onInspectorResize : onRightWidthPointerDown}
              className="absolute left-0 top-0 bottom-0 z-50 -translate-x-1/2"
            />}
            <aside className={cn("flex w-full min-h-0 flex-col border-l border-border bg-background-secondary", compactInspector ? "overflow-visible" : "overflow-hidden")}>
              <div className="min-h-0 flex-1">{rightPanel}</div>
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

    </div>
  );
}
