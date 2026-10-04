import data from "./asset-types.generated.json";

export type AssetMaturity = "SUPPORTED" | "BASIC" | "REFERENCE" | "PLANNED";
export interface AssetCapabilities {
  supportsAlignment: boolean;
  supportsTerrainFollowing: boolean;
  supportsProfile: boolean;
  supportsCrossSection: boolean;
  supportsCutFill: boolean;
  supportsFoundations: boolean;
  supportsClearance: boolean;
  supportsHydraulics: boolean;
  supportsQuantities: boolean;
  supportsSunStudy: boolean;
  supportsLinearEditing: boolean;
}
export interface AssetTypeDefinition {
  id: string;
  name: string;
  category: string;
  subtype: string;
  description: string;
  icon: string;
  geometryType: "line" | "area" | "point";
  maturity: AssetMaturity;
  status: "available" | "planned";
  supportsGeneration: boolean;
  capabilities: AssetCapabilities;
  aliases: string[];
}
export const ASSET_TYPES = data.assets as AssetTypeDefinition[];
export const ASSET_CATEGORIES = data.categories;
export function assetDefinition(id: string) {
  return ASSET_TYPES.find((asset) => asset.id === id);
}
export function assetSupportsGeneration(id: string) {
  return assetDefinition(id)?.supportsGeneration === true;
}
const normalize = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
function distance(a: string, b: string): number {
  const row = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let previous = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const above = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, previous + (a[i - 1] === b[j - 1] ? 0 : 1));
      previous = above;
    }
  }
  return row[b.length];
}
/** Rank exact names before aliases; tolerate typos without changing catalogue order on browse. */
export function searchAssets(query: string, category = "all"): AssetTypeDefinition[] {
  const terms = normalize(query).split(" ").filter(Boolean);
  return ASSET_TYPES.filter((asset) => category === "all" || asset.category === category)
    .map((asset) => {
      const name = normalize(asset.name);
      const words = normalize(`${asset.name} ${asset.description} ${asset.category} ${asset.aliases.join(" ")}`).split(" ");
      const matched = terms.every((term) => words.some((word) => word.includes(term) || (term.length >= 4 && distance(term, word) <= (term.length >= 6 ? 2 : 1))));
      return { asset, score: matched ? (name === normalize(query) ? 3 : name.includes(normalize(query)) ? 2 : 1) : 0 };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => terms.length ? b.score - a.score : 0)
    .map(({ asset }) => asset);
}
