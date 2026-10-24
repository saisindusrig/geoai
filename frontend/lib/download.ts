import { fetchBinary } from "./api";
import { toast } from "./toast";

export function downloadFilename(disposition: string | null, fallback: string): string {
  const extended = disposition?.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)?.[1];
  let name = disposition?.match(/filename\s*=\s*(?:"((?:\\.|[^"\\])*)"|([^;]+))/i)?.slice(1).find(Boolean) || fallback;
  if (extended) { try { name = decodeURIComponent(extended.trim()); } catch { /* Use the ordinary filename. */ } }
  name = name.replace(/\\"/g, '"').split(/[\\/]/).pop()!.replace(/[\u0000-\u001f\u007f<>:"|?*]/g, "_").trim().replace(/[. ]+$/, "");
  if (!name || /^\.+$/.test(name) || /^(con|prn|aux|nul|com\d|lpt\d)(\.|$)/i.test(name)) return fallback;
  return name.slice(-180);
}

const pending = new Map<string, Promise<void>>();
/** Explicit retries only. Concurrent callers share the same export request. */
export function downloadFile(path: string, fallback = "download.bin"): Promise<void> {
  const existing = pending.get(path);
  if (existing) return existing;
  const task = (async () => {
    toast("Preparing download…");
    try {
      const response = await fetchBinary(path);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      try {
        anchor.href = url;
        anchor.download = downloadFilename(response.headers.get("Content-Disposition"), fallback);
        document.body.append(anchor);
        anchor.click();
      } finally {
        anchor.remove();
        // Allow the browser to acquire the Blob before releasing our reference.
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      toast("Download prepared", { variant: "success" });
    } catch (reason) {
      toast(reason instanceof Error ? reason.message : "Download failed. Retry the download.", { variant: "error" });
      throw reason;
    }
  })();
  pending.set(path, task);
  void task.finally(() => pending.delete(path)).catch(() => {});
  return task;
}
