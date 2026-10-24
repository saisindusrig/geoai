import type { MetadataRoute } from "next";
import { BRAND_NAME, SITE_DESCRIPTION } from "@/lib/brand";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: BRAND_NAME, short_name: BRAND_NAME, description: SITE_DESCRIPTION,
    start_url: "/", display: "standalone", background_color: "#080C08",
    theme_color: "#080C08",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }, { src: "/brand/app-icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" }, { src: "/brand/app-icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" }],
  };
}
