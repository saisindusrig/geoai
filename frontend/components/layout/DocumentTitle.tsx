"use client";

import { BRAND_NAME, SITE_TITLE } from "@/lib/brand";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

const TITLES: Record<string, string> = {
  "/": SITE_TITLE,
  "/dashboard": `Dashboard | ${BRAND_NAME}`,
  "/projects/new": `New Concept | ${BRAND_NAME}`,
  "/login": `Sign in | ${BRAND_NAME}`,
  "/settings": `Settings | ${BRAND_NAME}`,
  "/privacy": `Privacy | ${BRAND_NAME}`,
};

export default function DocumentTitle() {
  const pathname = usePathname();
  useEffect(() => {
    const title = TITLES[pathname] ?? (pathname?.match(/^\/projects\/\d+\/(workspace|map|analysis|estimate|cost|report|timeline|scenarios|model)$/)?.[1]
      ? `${pathname.split("/").at(-1)!.replace(/^./, (char) => char.toUpperCase())} | ${BRAND_NAME}`
      : SITE_TITLE);
    document.title = title;
  }, [pathname]);
  return null;
}
