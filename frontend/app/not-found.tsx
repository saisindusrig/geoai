import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Page not found | GeoAI",
};

export default function NotFound() {
  return <main id="main-content" className="flex min-h-screen flex-col items-center justify-center bg-background px-6 text-center">
    <p className="font-data text-xs uppercase tracking-[0.2em] text-primary">Error 404</p>
    <h1 className="mt-3 text-4xl font-semibold tracking-tight">This page is not on the project map.</h1>
    <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">The link may be outdated, or the page may have moved. Return to the dashboard to continue planning.</p>
    <div className="mt-7 flex gap-3"><Link href="/" className="btn-glass px-4 py-2 text-sm">Home</Link><Link href="/dashboard" className="btn-primary-gradient px-4 py-2 text-sm">Dashboard</Link></div>
  </main>;
}
