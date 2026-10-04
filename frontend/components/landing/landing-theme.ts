/** Landing page tokens — reads from globals.css CSS variables where possible. */

export const BRAND_NAME = "GeoAI";
export const BRAND_COPILOT = "GeoAI Copilot";

export const landing = {
  bg: "var(--background)",
  bgElevated: "var(--background-elevated)",
  surface: "var(--background-secondary)",
  surfaceGlass: "var(--glass-bg)",
  card: "var(--card)",
  primary: "var(--marketing-primary)",
  secondary: "var(--marketing-secondary)",
  success: "var(--success)",
  text: "var(--foreground)",
  textMuted: "var(--muted-foreground)",
  border: "var(--border-marketing)",
  borderCyan: "rgba(142, 160, 163, 0.35)",
} as const;

export const NAV_LINKS = [
  { label: "Home", href: "#home" },
  { label: "Features", href: "#features" },
  { label: "Workflow", href: "#workflow" },
  { label: "Accuracy", href: "#accuracy" },
  { label: "Pricing", href: "#pricing" },
] as const;
