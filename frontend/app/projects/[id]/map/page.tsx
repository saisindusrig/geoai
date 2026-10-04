"use client";

import { Suspense } from "react";
import { ProjectLoading } from "@/components/layout/ProjectHeader";
import MapSelectionPageInner from "./MapSelectionPageInner";

export default function MapSelectionPage() {
  return (
    <Suspense fallback={<ProjectLoading message="Loading map…" />}>
      <MapSelectionPageInner />
    </Suspense>
  );
}
