/** Readable text from API risk/warning objects (fixes "[object Object]"). */
export function formatRiskText(item: unknown): string {
  if (item == null) return "";
  if (typeof item === "string") return item;
  if (typeof item === "number" || typeof item === "boolean") return String(item);
  if (typeof item === "object") {
    const o = item as Record<string, unknown>;
    for (const key of ["message", "label", "title", "description", "text", "risk", "name"]) {
      const v = o[key];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
    if (Array.isArray(o.details)) {
      return o.details.map(formatRiskText).filter(Boolean).join(" · ");
    }
  }
  return "";
}

export type RiskSeverity = "critical" | "review" | "info";

export function riskSeverity(item: unknown): RiskSeverity {
  if (typeof item === "object" && item !== null) {
    const s = String((item as Record<string, unknown>).severity ?? (item as Record<string, unknown>).level ?? "")
      .toLowerCase();
    if (s.includes("crit") || s.includes("high")) return "critical";
    if (s.includes("info") || s.includes("low")) return "info";
  }
  return "review";
}

export function formatCrINR(n: number, currency = "INR"): string {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })} ${currency === "INR" ? "" : currency}`.trim();
}

export function formatNumber(n: number, decimals = 0): string {
  return n.toLocaleString("en-IN", { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
}

export function formatUnit(value: number, unit: string): string {
  return `${formatNumber(value, unit === "m³" || unit === "kg" ? 1 : 0)} ${unit}`;
}

export function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function pctDiff(from: number, to: number): string | null {
  if (!from || !to) return null;
  const p = ((to - from) / from) * 100;
  const sign = p >= 0 ? "+" : "";
  return `${sign}${p.toFixed(0)}%`;
}
