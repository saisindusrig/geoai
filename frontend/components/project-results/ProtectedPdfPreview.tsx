"use client";
import { useEffect, useState } from "react";
import { fetchBinary } from "@/lib/api";

export default function ProtectedPdfPreview({ path }: { path: string }) {
  const [version, setVersion] = useState(0);
  const [resource, setResource] = useState<{ path: string; url: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void (async () => {
      try {
        const response = await fetchBinary(path, controller.signal);
        if (!response.headers.get("Content-Type")?.toLowerCase().includes("application/pdf")) throw new Error("The server did not return a PDF preview.");
        const blob = await response.blob();
        if (new TextDecoder().decode(await blob.slice(0, 5).arrayBuffer()) !== "%PDF-") throw new Error("The PDF preview has an invalid file signature.");
        if (controller.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob); setResource({ path, url: objectUrl }); setError("");
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "PDF preview unavailable.");
      }
    })();
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [path, version]);
  if (error) return <div role="alert" className="p-4 text-sm">{error}<button className="ml-3 min-h-11 underline" onClick={() => { setError(""); setResource(null); setVersion(v => v + 1); }}>Retry PDF preview</button></div>;
  if (!resource || resource.path !== path) return <p role="status" className="h-[480px] p-4">Preparing PDF preview…</p>;
  return <iframe title="PDF preview" src={resource.url} className="w-full h-[480px] bg-background border-0" />;
}
