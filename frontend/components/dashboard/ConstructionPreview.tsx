"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { defaultSpec, type ConstructionType } from "@/lib/construction";

const ConstructionScene = dynamic(
  () => import("@/components/civicspan/ConstructionScene"),
  { ssr: false },
);

/**
 * A procedural scene is mounted only after its gallery card is close to view.
 * This keeps six template previews and large project libraries inexpensive.
 */
export default function ConstructionPreview({
  type,
  className = "",
}: {
  type: ConstructionType;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (typeof IntersectionObserver === "undefined") {
      const frame = window.requestAnimationFrame(() => setVisible(true));
      return () => window.cancelAnimationFrame(frame);
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "160px 0px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`relative overflow-hidden bg-[radial-gradient(ellipse_at_50%_0%,rgba(178,187,171,0.2),transparent_52%),#0e100f] ${className}`}
      aria-label={`${type} procedural 3D preview`}
    >
      {visible && (
        <ConstructionScene spec={defaultSpec(type)} stage="finish" preview />
      )}
      {!visible && (
        <div className="h-full w-full bg-[linear-gradient(125deg,rgba(178,187,171,0.12),transparent_55%)]" />
      )}
    </div>
  );
}
