"use client";

import { Suspense } from "react";
import { ProjectLoading } from "@/components/layout/ProjectHeader";
import dynamic from "next/dynamic";
const MapSelectionPageInner = dynamic(() => import("./MapSelectionPageInner"), { ssr: false, loading: () => <ProjectLoading message="Loading map…" /> });

export default function MapSelectionPage() {
  return (
    <Suspense fallback={<ProjectLoading message="Loading map…" />}>
      <MapSelectionPageInner />
    </Suspense>
  );
}
