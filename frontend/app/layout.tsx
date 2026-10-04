import type { Metadata } from "next";
import "./globals.css";
import ThemeProvider from "@/components/ThemeProvider";
import DashboardShell from "@/components/layout/DashboardShell";
import Toaster from "@/components/ui/toaster";
import SiteUtilities from "@/components/layout/SiteUtilities";
import DocumentTitle from "@/components/layout/DocumentTitle";
import { inter, jetbrainsMono } from "@/lib/fonts";

export const metadata: Metadata = {
  title: { default: "GeoAI | Infrastructure Planning", template: "%s | GeoAI" },
  description:
    "GeoAI helps civil engineering teams explore site-aware infrastructure concepts using real-world terrain, maps, and preliminary engineering parameters.",
  icons: { icon: "/icon.svg" },
  openGraph: { title: "GeoAI | Infrastructure Planning", description: "Site-aware, conceptual infrastructure planning for engineering teams.", type: "website" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`h-full antialiased ${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body className="flex h-full flex-col overflow-hidden bg-ambient font-sans">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Skip to main content
        </a>
        <ThemeProvider>
          <DocumentTitle />
          <DashboardShell>{children}</DashboardShell>
          <Toaster />
          <SiteUtilities />
          <div className="desktop-only-notice" role="alert">
            <div>
              <p className="text-lg font-semibold">
                GeoAI is built for desktop
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Use a screen at least 1280px wide to plan, inspect, and save
                construction concepts.
              </p>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
