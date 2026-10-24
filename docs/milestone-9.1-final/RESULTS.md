# StruvoCivil — Final Milestone 9.1 consistency correction

Completed locally on 23 October 2026. Stopped after this correction; Milestone 10 has not begun.

## Exact changes

- Public brand: **StruvoCivil**. Site title: **StruvoCivil — Structural Engineering Software**. Domain remains `struvocivil.com`. Tagline remains **Model. Analyze. Design.** Assistant: **StruvoCivil Assistant**.
- Updated shared branding constants, current page/browser metadata and manifest-derived names, navigation, public copy, accessibility labels, all existing local SVG wordmark variants, social SVG/PNG, current assistant interface/system identity and future PDF report title/logo. The wordmark now joins Struvo and Civil without a space.
- Preserved the structural logo symbol, bridge scene, dark/bright-green palette, typography, layout, navigation, 3D workspace, editor/tool workflows and approval gates. Only lettering/public identity and availability presentation/guarding changed.
- Idle task status is **No task in progress**, rather than Ready. Stopping an active response says **Response stopped**. Disabled spending approval displays **AI unavailable — awaiting activation**, with the backend explanation separately visible. Other unavailable states display their actual reason. Unknown availability says **Checking AI availability…**.
- Send and manual retry fail closed unless the backend reports enabled, AVAILABLE and no explicit canSend block. The request handler enforces the same rule. Completed historical tasks remain Completed independently of current AI availability.
- Existing compatibility identifiers, API/environment names, browser events/storage, database schemas/identities, saved revisions and immutable conversations/artifacts remain unchanged. Historical spellings remain recognized in the internal claim-rejection guard. See `changed-brand-source-files.json` and `branding-audit.json`.
- Updated current README/environment heading and existing future Firebase architecture identity text. Earlier milestone reports, screenshots and logo-history documents retain their original wording.

## Focused verification

**31 tests passed across six files**: branding/manifest/origin, availability presentation, site assistant, legacy assistant labels and empty-project actions. Added coverage for disabled inference without history, completed history plus disabled inference, contradictory backend availability, explicit canSend blocks, unknown availability and both exact public names. Existing provider calls are mocked. Logs: `tests.log`.

TypeScript and scoped ESLint with zero warnings passed (`typescript.log`, `lint.log`). No production build or broad backend/engineering suite was rerun for this bounded correction.

Fresh installed-Chrome checks passed at **1280×900**, **1600×900** and **390×900**. Checked homepage title/tagline, canonical origin, Open Graph site name, wordmark accessible name, manifest name/start path and favicon response; desktop dashboard/settings/main workspace plus mobile dashboard and assistant. The assistant shows the exact unavailable label, no Ready state, and a disabled Send button. Screenshots were visually inspected at both desktop sizes and mobile. Saved synthetic beam/columns remain visible with the assistant open. No horizontal overflow, page JavaScript errors, unexpected application writes or downloads were recorded. See `browser.cjs`, `browser.log`, `browser.json`.

Browser API reads used the retained isolated M9 fixture on localhost:8003. Suggestions were fulfilled with empty local mocks, external requests/application writes/downloads were blocked, and no assistant turn, CAD import, save, calculation or accounting operation was submitted. Temporary review API stopped after checks; the existing localhost frontend was left running.

Screenshots: `after-home-1280.png`, `after-home-1600.png`, `after-home-390.png`, `after-assistant-1280.png`, `after-assistant-1600.png`, `after-assistant-390.png`, plus dashboard/settings/workspace captures.

## Preservation comparison

Exact request-entry comparison: **10,282 application database rows and all schemas unchanged**; **three assistant-history/accounting rows unchanged**. Zero added, removed or changed rows. See `database-baseline.json`, `preservation.json`.

Reused original manifests verify **55,296 original storage files**, **2,090 engineering proof files**, **66 live database schemas**, **198 archive-only database fingerprints**, and **21 coupled solver artifact files**. All checked original hashes are unchanged. The older 10,269-row baseline remains preserved; its 13 extra synthetic rows predate this correction and were retained. See `preservation-manifests.json`, `preservation-audit.json`, `preservation-files.log`, `coupled-evidence-preservation.json`.

Historical reports, saved geometry, CAD sources, solver evidence, numerical values, provenance, authorizations, conversations and accounting were not rewritten. The packaged logo change applies to future report generation only.

## Unchanged limitations and external configuration

The previously documented legacy `/model` Cesium RuntimeError: YA issue remains unresolved and untouched; this correction checked the working main `/workspace` route instead. No viewer rebuild was attempted.

Nebius Token Factory and `zai-org/GLM-5.3-Flash` remain configured with spending disabled. No offline fallback, paid inference, automatic retries/escalation, domain activation, DNS/SSL configuration, Firebase activation, deployment, Git operation, additional agent, dependency installation or destructive cleanup occurred. Domain hosting/DNS and future Firebase Authentication remain separate work.
