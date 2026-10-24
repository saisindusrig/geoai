"use client";
import { useRef, useState } from "react";
import { downloadFile } from "@/lib/download";
import { Button, type ButtonProps } from "./button";

export function DownloadButton({ path, filename, children, disabled, ...props }: ButtonProps & { path: string; filename: string }) {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  return <Button {...props} disabled={disabled || busy} aria-busy={busy} onClick={async () => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setFailed(false);
    try { await downloadFile(path, filename); } catch { setFailed(true); }
    finally { lock.current = false; setBusy(false); }
  }}>{busy ? "Preparing download…" : failed ? <>Retry: {children}</> : children}</Button>;
}
