"use client";

import type { AccuracyTier } from "@/lib/types";

export default function SurveyVisualWarning({
  surveyMode,
  accuracyTier,
}: {
  surveyMode: boolean;
  accuracyTier: AccuracyTier;
}) {
  const needsWarning =
    !surveyMode || accuracyTier === "visual" || accuracyTier === "gis_grade";

  if (!needsWarning) return null;

  return (
    <div className="pointer-events-none absolute bottom-3 left-1/2 z-30 max-w-lg -translate-x-1/2 rounded-lg border border-[rgba(245,158,11,0.35)] bg-[rgba(15,23,42,0.92)] backdrop-blur-[14px] px-3 py-2 text-center text-[11px] text-[#FBBF24] shadow-md">
      <strong className="font-semibold text-foreground">Visual reference — not for quantity takeoff.</strong>{" "}
      Public satellite/3D map data is for visualization and planning. Final construction quantities
      require licensed survey/LiDAR/RTK data.
    </div>
  );
}
