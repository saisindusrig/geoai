"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

const TITLES: Record<string, string> = {
  "/": "GeoAI | Infrastructure Planning",
  "/dashboard": "Dashboard | GeoAI",
  "/projects/new": "New Concept | GeoAI",
  "/login": "Sign in | GeoAI",
  "/settings": "Settings | GeoAI",
  "/privacy": "Privacy | GeoAI",
};

export default function DocumentTitle() {
  const pathname = usePathname();
  useEffect(() => {
    const title = TITLES[pathname] ?? (pathname?.match(/^\/projects\/\d+\/(workspace|map|analysis|estimate|cost|report|timeline|scenarios|model)$/)?.[1]
      ? `${pathname.split("/").at(-1)!.replace(/^./, (char) => char.toUpperCase())} | GeoAI`
      : "GeoAI | Infrastructure Planning");
    document.title = title;
  }, [pathname]);
  return null;
}
