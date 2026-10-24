# Retained dependency advisory review

37 affected package entries, not 37 independently reachable vulnerabilities. Retained severity: 5 critical, 22 high, 9 moderate, 1 low. No audit/upgrade/install was run. Installed versions and each retained leaf advisory are preserved in dependency-review.json; per-advisory exposure remains unverified unless specifically stated.

| Package | Installed versions | Retained severity | Exposure classification |
|---|---|---|---|
| @deck.gl/geo-layers | 9.4.0 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @deck.gl/mesh-layers | 9.4.0 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @loaders.gl/3d-tiles | 4.5.2 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @loaders.gl/compression | 4.5.2 | moderate | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @loaders.gl/gltf | 4.5.2 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @loaders.gl/textures | 4.5.2 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @loaders.gl/zip | 4.5.2 | moderate | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @luma.gl/gltf | 9.4.2 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| @next/eslint-plugin-next | 16.2.9 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| @vitest/mocker | 3.2.7 | moderate | Test/development tooling — POTENTIAL_RISK |
| @watergis/maplibre-gl-terradraw | 1.16.0 | critical | Browser mapping — CONFIRMED_AFFECTED_COMPONENT_CONDITIONAL_EXPOSURE |
| argparse | 1.0.10 | moderate | Build/lint or offline asset tooling — POTENTIAL_RISK |
| baseline-browser-mapping | 2.11.25 | moderate | Build/lint or offline asset tooling — POTENTIAL_RISK |
| brace-expansion | 5.0.12, 1.1.21 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| braces | 3.0.3 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| browserslist | 4.29.0 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| dompurify | 3.4.15 | moderate | Transitive browser sanitization — POTENTIAL_RISK |
| esbuild | 0.28.2 | low | Test/development tooling — POTENTIAL_RISK |
| eslint-config-next | 16.2.9 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| fast-glob | 3.3.1 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| fflate | 0.7.4 | moderate | Browser map/3D asset pipeline — POTENTIAL_RISK |
| image-size | 0.7.5 | high | Browser map/3D asset pipeline — POTENTIAL_RISK |
| js-yaml | 4.3.2 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| maplibre-gl | 5.24.0 | critical | Browser mapping — CONFIRMED_AFFECTED_COMPONENT_CONDITIONAL_EXPOSURE |
| micromatch | 4.0.8 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| nanoid | 3.3.19 | high | ID generation — POTENTIAL_RISK |
| next | 16.2.9 | critical | Active Windows HTTP framework — CONFIRMED_AFFECTED_COMPONENT |
| postcss | 8.4.31, 8.5.28 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| protobufjs | 8.8.0 | moderate | Browser map/3D asset pipeline — POTENTIAL_RISK |
| sharp | 0.34.5 | high | Next image optimization dependency — POTENTIAL_RISK |
| source-map-js | 1.2.1 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| sprintf-js | 1.0.3 | moderate | Build/lint or offline asset tooling — POTENTIAL_RISK |
| texture-compressor | 1.0.2 | high | Build/lint or offline asset tooling — POTENTIAL_RISK |
| tinypool | 1.1.1 | critical | Test/development tooling — POTENTIAL_RISK |
| undici | 7.29.1 | high | Transitive HTTP client — POTENTIAL_RISK |
| vite | 7.3.6 | high | Test/development tooling — POTENTIAL_RISK |
| vitest | 3.2.7 | critical | Test/development tooling — POTENTIAL_RISK |

Critical runtime finding: [Next publisher advisory](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36) covers the installed Windows version and has no known vendor workaround; loopback is exposure reduction only. [MapLibre publisher advisory](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579) requires an untrusted attribution source; reviewed attributions are constants. [Vitest advisory](https://github.com/advisories/GHSA-82fw-gwwq-j7x9) distinguishes an exposed standalone plugin from token-protected local browser testing. [Tinypool advisory](https://github.com/advisories/GHSA-85c8-ppgw-ccpr) requires prototype pollution and a worker-options sink. No such application endpoint was demonstrated.
