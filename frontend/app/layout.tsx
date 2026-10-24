import type { Metadata } from "next";
import { BRAND_NAME, SITE_TITLE, SITE_DESCRIPTION, publicSiteUrl } from "@/lib/brand";
import "./globals.css";
import ThemeProvider from "@/components/ThemeProvider";
import DashboardShell from "@/components/layout/DashboardShell";
import Toaster from "@/components/ui/toaster";
import SiteUtilities from "@/components/layout/SiteUtilities";
import SiteAssistant from "@/components/ai/SiteAssistant";
import { inter, jetbrainsMono } from "@/lib/fonts";
import SessionBoundary from "@/components/auth/SessionBoundary";

export const metadata: Metadata = {
  metadataBase: publicSiteUrl(),
  title: { default: SITE_TITLE, template: `%s | ${BRAND_NAME}` },
  description: SITE_DESCRIPTION,
  applicationName: BRAND_NAME,
  icons: { icon: "/icon.svg", apple: "/brand/app-icon-180.png" },
  manifest: "/manifest.webmanifest",
  openGraph: { title: SITE_TITLE, description: SITE_DESCRIPTION, siteName: BRAND_NAME, type: "website", images: [{ url: "/brand-social.png", width: 1200, height: 630, alt: SITE_TITLE }] },
  twitter: { card: "summary_large_image", title: SITE_TITLE, description: SITE_DESCRIPTION, images: ["/brand-social.png"] },
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
          <SessionBoundary>
          <DashboardShell>{children}</DashboardShell>
          <Toaster />
          <SiteUtilities />
          <SiteAssistant />
          </SessionBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
