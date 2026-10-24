# Retained dependency advisory review

37 affected package entries, not 37 independently reachable vulnerabilities. Retained severity: 5 critical, 22 high, 9 moderate, 1 low. No audit/upgrade/install was run. Installed versions and each retained leaf advisory are preserved in dependency-review.json; per-advisory exposure remains unverified unless specifically stated.

| Package | Installed versions | Retained severity | Exposure classification |
|---|---|---|---|
| @deck.gl/geo-layers | 9.3.4 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @deck.gl/mesh-layers | 9.3.4 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @loaders.gl/3d-tiles | 4.4.3 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @loaders.gl/compression | 4.4.3 | moderate | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @loaders.gl/gltf | 4.4.3 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @loaders.gl/textures | 4.4.3 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @loaders.gl/zip | 4.4.3 | moderate | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @luma.gl/gltf | 9.3.4 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| @next/eslint-plugin-next | 16.4.2 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| @vitest/mocker | 3.2.6 | moderate | Test/development tooling â€” POTENTIAL_RISK |
| @watergis/maplibre-gl-terradraw | 1.13.2 | critical | Browser mapping â€” CONFIRMED_AFFECTED_COMPONENT_CONDITIONAL_EXPOSURE |
| argparse | 1.0.10 | moderate | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| baseline-browser-mapping | 2.10.36 | moderate | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| brace-expansion | 5.0.6, 1.1.15 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| braces | 3.0.3 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| browserslist | 4.28.2 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| dompurify | 3.4.9 | moderate | Transitive browser sanitization â€” POTENTIAL_RISK |
| esbuild | 0.27.7 | low | Test/development tooling â€” POTENTIAL_RISK |
| eslint-config-next | 16.4.2 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| fast-glob | 3.3.1 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| fflate | 0.7.4 | moderate | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| image-size | 0.7.5 | high | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| js-yaml | 4.2.0 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| maplibre-gl | 5.24.0 | critical | Browser mapping â€” CONFIRMED_AFFECTED_COMPONENT_CONDITIONAL_EXPOSURE |
| micromatch | 4.0.8 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| nanoid | 3.3.20 | high | ID generation â€” POTENTIAL_RISK |
| next | 16.4.2 | critical | Active Windows HTTP framework â€” CURRENT_VERSION_COMPARED_WITH_RETAINED_RANGES |
| postcss | , 8.5.23 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| protobufjs | 8.6.3 | moderate | Browser map/3D asset pipeline â€” POTENTIAL_RISK |
| sharp | 0.35.5 | high | Next image optimization dependency â€” POTENTIAL_RISK |
| source-map-js | 1.2.1 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| sprintf-js | 1.0.3 | moderate | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| texture-compressor | 1.0.2 | high | Build/lint or offline asset tooling â€” POTENTIAL_RISK |
| tinypool | 1.1.1 | critical | Test/development tooling â€” POTENTIAL_RISK |
| undici | 7.28.0 | high | Transitive HTTP client â€” POTENTIAL_RISK |
| vite | 7.3.5 | high | Test/development tooling â€” POTENTIAL_RISK |
| vitest | 3.2.6 | critical | Test/development tooling â€” POTENTIAL_RISK |

Historical Next finding: current Next 16.4.2 and sharp 0.35.5 are outside the previously reviewed affected floors documented in Milestone 5. Current installed versions are compared per retained advisory in the JSON; this is not a new comprehensive advisory feed. [MapLibre publisher advisory](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579) requires an untrusted attribution source; reviewed attributions are constants. [Vitest advisory](https://github.com/advisories/GHSA-82fw-gwwq-j7x9) distinguishes an exposed standalone plugin from token-protected local browser testing. [Tinypool advisory](https://github.com/advisories/GHSA-85c8-ppgw-ccpr) requires prototype pollution and a worker-options sink. No such application endpoint was demonstrated.
