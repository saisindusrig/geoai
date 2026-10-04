// Backend catalogue is canonical. Keep the browser bundle inside Next's project root.
const fs = require("node:fs");
const path = require("node:path");
const source = path.resolve(__dirname, "../../backend/app/core/asset-types.json");
const destination = path.resolve(__dirname, "../lib/asset-types.generated.json");
const catalogue = fs.readFileSync(source, "utf8");
const parsed = JSON.parse(catalogue);
if (new Set(parsed.assets.map((asset) => asset.id)).size !== parsed.assets.length) {
  throw new Error("Duplicate asset catalogue IDs");
}
if (!fs.existsSync(destination) || fs.readFileSync(destination, "utf8") !== catalogue) {
  fs.writeFileSync(destination, catalogue);
}
console.log(`Asset catalogue: ${parsed.assets.length} types`);
