/** Public identity only. Never use this origin for API or authentication routing. */
export const BRAND_NAME = "StruvoCivil";
export const ASSISTANT_NAME = "StruvoCivil Assistant";
export const BRAND_TAGLINE = "Model. Analyze. Design.";
export const SITE_TITLE = "StruvoCivil — Structural Engineering Software";
export const SITE_DESCRIPTION = "StruvoCivil — Model. Analyze. Design. A 3D civil and structural engineering workspace for modeling, analysis and design review. Engineering outputs require professional verification.";

export function publicSiteUrl(value = process.env.NEXT_PUBLIC_SITE_URL): URL {
  const url = new URL(value || "https://struvocivil.com");
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
    throw new Error("NEXT_PUBLIC_SITE_URL must be an HTTP(S) public origin");
  }
  return new URL(url.origin);
}
