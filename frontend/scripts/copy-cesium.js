// Copies Cesium's static assets (workers, widgets, assets) into public/cesium
// so the viewer can load them at runtime. Runs automatically before dev/build.
const fs = require("fs");
const path = require("path");

const src = path.join(__dirname, "..", "node_modules", "cesium", "Build", "Cesium");
const dest = path.join(__dirname, "..", "public", "cesium");

if (!fs.existsSync(src)) {
  console.warn("[copy-cesium] cesium package not found; skipping");
  process.exit(0);
}
if (fs.existsSync(path.join(dest, "Cesium.js"))) {
  process.exit(0); // already copied
}
fs.cpSync(src, dest, { recursive: true });
console.log("[copy-cesium] Copied Cesium assets to public/cesium");
