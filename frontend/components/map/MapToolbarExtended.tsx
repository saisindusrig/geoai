"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/toast";
import { useProjectStore } from "@/stores/projectStore";
import { cn } from "@/lib/utils";

interface MapToolbarExtendedProps {
  view: "2d" | "3d";
  className?: string;
}

export default function MapToolbarExtended({ view, className }: MapToolbarExtendedProps) {
  const mapRef = useProjectStore((s) => s.mapRef);
  const mapReady = useProjectStore((s) => s.mapReady);
  const controlsReady = view === "2d" && mapReady;

  const exportMap = () => {
    if (!mapRef?.exportPng) {
      toast("Export available in 2D map view", { variant: "error" });
      return;
    }
    const ok = mapRef.exportPng();
    if (ok) {
      toast("Map exported", { description: "PNG saved to downloads", variant: "success" });
    } else {
      toast("Export failed", {
        description: "Map tiles blocked export — try again after tiles finish loading",
        variant: "error",
      });
    }
  };

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn("h-7 w-7 shrink-0", className)}
      title="Export PNG"
      disabled={!controlsReady}
      onClick={exportMap}
    >
      <Download className="h-3.5 w-3.5" />
    </Button>
  );
}
