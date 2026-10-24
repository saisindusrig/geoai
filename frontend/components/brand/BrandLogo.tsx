import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand";

export type LogoVariant = "main" | "secondary" | "simplified" | "submark" | "animated";

/** Every lockup uses the same structural S geometry. */
export default function BrandLogo({ variant = "secondary", tone = "dark", className = "", decorative = false }: {
  variant?: LogoVariant; tone?: "dark" | "light"; className?: string; decorative?: boolean;
}) {
  const dimensions = variant === "main" ? [380, 260] : (variant === "secondary" || variant === "animated") ? [470, 140] : variant === "simplified" ? [360, 110] : [120, 140];
  // Local SVGs contain outlined vector lettering and explicit dimensions.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={`/brand/${variant}-${tone}.svg`} width={dimensions[0]} height={dimensions[1]}
    alt={decorative ? "" : variant === "main" ? `${BRAND_NAME} — ${BRAND_TAGLINE}` : BRAND_NAME}
    className={`struvo-logo struvo-logo-${variant} ${className}`} draggable={false} />;
}
