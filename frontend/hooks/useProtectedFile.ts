"use client";
import { useEffect, useState } from "react";
import { fetchBinary, isApiFileUrl } from "@/lib/api";
import { toast } from "@/lib/toast";

/** Resolve owned API assets without placing a bearer token in renderer URLs. */
export function useProtectedFile(source: string | null | undefined) {
  const protectedFile = !!source && isApiFileUrl(source);
  const [loaded, setLoaded] = useState<{ source: string; url: string } | null>(null);
  useEffect(() => {
    if (!source || !protectedFile) return;
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void fetchBinary(source, controller.signal).then(response => response.blob()).then(blob => {
      if (controller.signal.aborted) return;
      objectUrl = URL.createObjectURL(blob);
      setLoaded({ source, url: objectUrl });
    }).catch(reason => {
      if (!controller.signal.aborted) toast(reason instanceof Error ? reason.message : "Model file unavailable. Reload to retry.", { variant: "error" });
    });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [source, protectedFile]);
  return protectedFile ? (loaded?.source === source ? loaded.url : null) : source;
}
