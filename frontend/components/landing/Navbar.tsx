"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { loginPath, registrationPath } from "@/lib/auth-routes";
import { useLandingScrollSpy } from "@/lib/useLandingScrollSpy";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { NAV_LINKS } from "./landing-theme";
import BrandWordmark from "./BrandWordmark";

function LandingNavLink({
  label,
  href,
  active,
}: {
  label: string;
  href: string;
  active: boolean;
}) {
  return (
    <a
      href={href}
      className={cn(
        "relative shrink-0 rounded-lg px-3.5 py-2 text-[13px] font-medium transition-colors",
        active
          ? "bg-primary/15 text-foreground"
          : "text-muted-foreground hover:bg-[var(--surface-hover)] hover:text-foreground",
      )}
      aria-current={active ? "page" : undefined}
    >
      {label}
    </a>
  );
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const sectionIds = useMemo(() => NAV_LINKS.map((link) => link.href.slice(1)), []);
  const activeSection = useLandingScrollSpy(sectionIds);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-[var(--border-marketing)] bg-[var(--header-bg)] backdrop-blur-xl shadow-md"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-6 px-8">
        <Link
          href="/"
          className="group min-w-0 shrink-0 rounded-lg py-1 transition-opacity hover:opacity-90"
        >
          <BrandWordmark size="nav" />
        </Link>

        <nav className="flex flex-1 items-center justify-center gap-0.5">
          {NAV_LINKS.map(({ label, href }) => {
            const sectionId = href.slice(1);
            return (
              <LandingNavLink
                key={href}
                label={label}
                href={href}
                active={sectionId !== "home" && activeSection === sectionId}
              />
            );
          })}
        </nav>

        <div className="flex shrink-0 items-center gap-3">
          <Link
            href={loginPath("/dashboard")}
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "text-foreground-secondary hover:text-foreground",
            )}
          >
            Sign In
          </Link>
          <Link
            href={registrationPath("/dashboard")}
            className={cn(buttonVariants({ variant: "marketing", size: "sm" }), "font-semibold")}
          >
            Get started
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
