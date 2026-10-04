"use client";

import { useEffect, useState } from "react";

export function useLandingScrollSpy(sectionIds: readonly string[]) {
  const [activeId, setActiveId] = useState("");

  useEffect(() => {
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section));

    const resolveActive = () => {
      const marker = window.innerHeight * 0.38;
      let current = "";

      for (const section of sections) {
        const rect = section.getBoundingClientRect();
        if (rect.top <= marker && rect.bottom > marker) {
          current = section.id;
          break;
        }
      }

      setActiveId(current);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visible?.target instanceof HTMLElement) {
          setActiveId(visible.target.id);
          return;
        }

        resolveActive();
      },
      {
        root: null,
        rootMargin: "-28% 0px -58% 0px",
        threshold: [0.05, 0.2, 0.4, 0.6],
      },
    );

    sections.forEach((section) => observer.observe(section));
    resolveActive();
    window.addEventListener("scroll", resolveActive, { passive: true });
    window.addEventListener("resize", resolveActive);
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", resolveActive);
      window.removeEventListener("resize", resolveActive);
    };
  }, [sectionIds]);

  return activeId;
}
