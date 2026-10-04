"use client";

import { ArrowUp, Copy, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { toast } from "@/lib/toast";

export default function SiteUtilities() {
  const pathname = usePathname();
  const [progress, setProgress] = useState(0);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    const update = () => {
      const root = document.documentElement;
      const max = Math.max(1, root.scrollHeight - root.clientHeight);
      setProgress(Math.round((window.scrollY / max) * 100));
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => { window.removeEventListener("scroll", update); window.removeEventListener("resize", update); };
  }, []);
  const copyPageLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      toast("Page link copied", { variant: "success" });
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      toast("Could not copy the page link", { variant: "error" });
    }
  };
  if (pathname === "/projects/new" || pathname?.includes("/workspace")) return null;
  return <><div className="site-scroll-progress" style={{ transform: `scaleX(${progress / 100})` }} aria-hidden="true" />
    <div className="site-utilities" aria-label="Page utilities">
      <button type="button" onClick={copyPageLink} title="Copy page link" aria-label="Copy page link">{copied ? <Check size={15} /> : <Copy size={15} />}</button>
      {progress > 8 && <button type="button" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} title="Back to top" aria-label="Back to top"><ArrowUp size={16} /></button>}
    </div>
  </>;
}
