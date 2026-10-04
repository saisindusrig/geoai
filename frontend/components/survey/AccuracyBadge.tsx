"use client";

import type { AccuracyTier } from "@/lib/types";
import { cn } from "@/lib/utils";

const TIER_LABELS: Record<AccuracyTier, string> = {
  visual: "Visual only",
  gis_grade: "GIS-grade",
  survey_grade: "Survey-grade",
  engineering_ready: "Engineering-ready",
};

const TIER_CLASS: Record<AccuracyTier, string> = {
  visual: "badge-warning",
  gis_grade: "badge-info",
  survey_grade: "badge-info",
  engineering_ready: "badge-success",
};

export default function AccuracyBadge({
  tier,
  compact = false,
  className,
}: {
  tier: AccuracyTier;
  compact?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-1.5 py-0.5 font-medium border",
        compact ? "text-[10px]" : "text-[11px]",
        TIER_CLASS[tier],
        className,
      )}
      title={`Accuracy tier: ${TIER_LABELS[tier]}`}
    >
      {TIER_LABELS[tier]}
    </span>
  );
}
