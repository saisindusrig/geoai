# Struvo Civil — Milestone 9.1

Implemented locally on 23 October 2026. Development stops here; Firebase Authentication has not begun.

## Result

Current public branding uses **Struvo Civil**, the exact title **Struvo Civil — Structural Engineering Software**, the tagline **Model. Analyze. Design.**, and **Struvo Assistant**. The workspace already contained a substantial rebranding implementation and later logo/palette work on entry. This task retained that design and corrected its conflicting “StruvoCivil” spelling and “Structural Design Clarity” tagline across current surfaces. Earlier milestone and logo reports/screenshots were preserved as historical evidence.

The shared local SVG wordmark retains the structural S symbol and now includes the visible space between Struvo and Civil. Main/secondary/simplified/animated/light/dark variants, accessible names, social SVG/PNG and the packaged future-report logo match the approved identity. The matching submark favicon, ICO and manifest remain in place. Dashboard, navigation, settings, diagnostics, loading/error/empty states, CAD/planner copy, model/editor, results/review, login and current export title/template branding were audited. A synthetic in-memory PDF verified the new report title without database calls or calculations; historical reports were not regenerated.

The existing dark palette, responsive navigation and workspace layout are retained. Shared branding constants supply the identity, metadata, wordmark descriptions and homepage tagline. A scoped lint finding in the branded legacy sidebar was corrected by using the existing Next router for its analysis link, preserving the destination.

## Domain preparation

`frontend/lib/brand.ts` supplies a configurable `NEXT_PUBLIC_SITE_URL`, defaulting to `https://struvocivil.com`, solely for public metadata. It supports HTTP(S) localhost origins, rejects credential-bearing/non-HTTP URLs and normalizes paths to the origin. Homepage canonical, title/template, description, Open Graph/Twitter metadata and local manifest are configured. Private project pages do not inherit a homepage canonical.

Local API proxy, backend addresses, authentication routes/callbacks, stable storage names and environment variable identities were retained. Browser navigation and the same-origin `/local-api` path work locally. Existing future Firebase architecture documentation now states the exact approved brand/tagline and intended domain. No Firebase project, billing, callback or deployment was configured.

Still external and unverified: domain ownership/registration, DNS, hosting/deployment, TLS, production API/CORS, and separately reviewed Firebase project/authorized-domain/authentication configuration. The domain is not claimed live. No email address, legal entity or certification was invented.

## Audit and compatibility exceptions

See `legacy-source-audit.json` for 374 case-insensitive source matches, including technical identifiers; `public-brand-exceptions.txt` lists the much narrower capitalized-brand matches. Remaining exceptions are intentional:

- Stable `geoai:*` events, browser storage/auth keys, CSS classes, function/import names, format schemas, environment variables, logger/user-agent names and repository URLs.
- Deterministic solver-source headers, preserving artifact bytes and numerical provenance.
- The existing GeoAI synthetic half-space benchmark citation, identifying historical evidence rather than the current product.
- The assistant guard still recognizes the historical GeoAI name when rejecting unverified completion claims.
- Original conversations, audit/billing records, historical documents, artifacts and evidence retain their original text.

No unintended old branding appeared in checked current screen text. No current “StruvoCivil” or “Structural Design Clarity” public copy remains. Future assistant system identity is Struvo Assistant; saved conversation bodies and provider/model provenance were preserved. Nebius Token Factory and `zai-org/GLM-5.3-Flash` remain unchanged. No paid inference, offline fallback, model escalation or automatic retry was enabled.

## Verification

- **116 backend tests passed**, using isolated in-memory fixtures and mocked providers: assistant, quota/disabled state, workspace ownership, exact saved-result binding, stale rejection, beam/column proposal protections and approval workflows. One existing Starlette deprecation warning remains.
- **48 frontend tests passed**: 40 assistant/history/tool/preview/branding tests plus eight authentication/return-path tests. No live inference was used.
- TypeScript, scoped ESLint with zero warnings and final optimized production build passed. Logs are retained alongside this report.
- Fresh Chrome screenshots at **1280×900**, **1600×900**, plus **390×900** mobile. Homepage exact title/tagline, canonical, Open Graph site name, manifest and favicon response were checked. Dashboard, settings, diagnostics, login, model, analysis, report and main workspace routes were opened. No checked screen had old branding or horizontal overflow.
- Main workspace and Struvo Assistant were visually inspected together at both desktop sizes: saved synthetic beam/columns remain visible, and new AI messages are clearly disabled. Assistant/tool tests verify existing history and preview gates; browser checks did not submit assistant turns or edit models.
- Browser harness forwards application reads only to the retained isolated M9 API. Site-suggestions POSTs are fulfilled locally with empty mocks. Application writes, downloads and external requests are rejected; recorded unexpected writes/downloads are empty. No new imports, saves, analyses or accounting events occurred.
- **Limitation:** the separate legacy `/projects/991600/model` route emits two Cesium `RuntimeError: YA` errors per desktop run and shows no fixture geometry. A focused probe recorded no blocked external request and one 404 console message; its cause is unresolved. This is not counted as successful model rendering. The main `/workspace` view rendered the actual saved geometry correctly without these errors. See `model-view-diagnostic.json` and `browser.json`.
- CAD import execution, numerical solver execution and production authentication were deliberately not exercised; their navigation/source branding and focused safety tests were checked. No full-suite or new solver-certification claim is made.

Before screenshots: `before-1280.png`, `before-1600.png`. Fresh after screenshots: `after-home-*`, `after-dashboard-*`, `after-settings-*`, `after-diagnostics-*`, `after-login-*`, `after-model-*`, `after-analysis-*`, `after-report-*`, `after-workspace-*`, `after-assistant-*`.

## Preservation

Exact comparison against this request entry confirms **10,282 application database rows and schemas**, plus **three assistant-history/accounting rows**, unchanged. There were no additions during this request. The entry state already included 13 synthetic rows documented by an earlier run; those were retained rather than deleted. The older 10,269-row baseline remains an unchanged subset.

Reused retained-archive manifests verify **55,296 original storage files**, **2,090 original engineering proof files**, **66 live database schemas**, **198 archived-only fingerprints** and **21 coupled solver evidence files**. No original CAD, revision, solver output, report, source hash, authorization record or accounting entry was modified. See `preservation.json`, `entry-database-baseline.json`, `preservation-manifests.json`, `preservation-audit.json` and `coupled-evidence-preservation.json`.

No Git operations, parallel agents, installations, paid inference, destructive cleanup, deployment, DNS changes or Firebase activation were used. The temporary isolated review API was stopped after verification; the existing localhost frontend was left running.
