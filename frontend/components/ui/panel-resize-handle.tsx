"use client";

import { cn } from "@/lib/utils";

export function PanelResizeHandle({
  orientation,
  onPointerDown,
  className,
}: {
  orientation: "horizontal" | "vertical";
  onPointerDown: (e: React.PointerEvent) => void;
  className?: string;
}) {
  const horizontal = orientation === "horizontal";

  return (
    <div
      role="separator"
      aria-orientation={horizontal ? "horizontal" : "vertical"}
      aria-label={horizontal ? "Resize panels vertically" : "Resize panel width"}
      title={horizontal ? "Drag to resize layers / chat" : "Drag to resize sidebar"}
      onPointerDown={onPointerDown}
      className={cn(
        "shrink-0 touch-none select-none bg-border/70 hover:bg-primary/45 active:bg-primary/60 transition-colors",
        horizontal
          ? "h-1.5 w-full cursor-ns-resize"
          : "w-1.5 cursor-ew-resize self-stretch",
        className,
      )}
    />
  );
}
