# Struvo Civil — Milestone 9.1

Completed locally, 23 October 2026. Firebase Authentication remains a separate milestone.

The website uses **Struvo Civil**, **Struvo Civil — Structural Engineering Software**, and **Model. Analyze. Design.** The site-wide assistant is **Struvo Assistant**, retaining Nebius Token Factory and its existing `zai-org/GLM-5.3-Flash` default. No inference allowance, provider credentials, DNS, deployment or authentication callback was activated.

## Delivered changes

- Shared structural-frame SVG wordmark, matching SVG/ICO favicon, responsive navigation and local SVG/PNG social card. The existing dark engineering palette and prominent 3D workspace are retained.
- Landing presentation, dashboard, shared page/results headers, settings, diagnostics, administration, login, privacy copy, CAD/planner surfaces, assistant panels and accessible names use the new identity.
- New assistant identity instructions affect future generated messages only. Historical response bodies and model/provider provenance are retained. Existing events, actions, review gates, beam/column previews and saved-model handling remain compatible.
- Future PDF headers and document titles use Struvo Civil. Existing reports, hashes, numerical outputs and solver evidence were not regenerated or renamed.
- Root metadata and server route titles, Open Graph/Twitter metadata, favicon and manifest are updated. The homepage canonical uses the configured public origin. Private project routes do not inherit a homepage canonical.
- Existing Firebase future architecture documentation and current README reflect the new identity. A fictitious contact mail link was removed; no replacement contact or legal claim was invented.

## Domain preparation

Set `NEXT_PUBLIC_SITE_URL` in the frontend environment for public metadata; its default is `https://struvocivil.com`. `http://localhost:3001` is supported for local metadata checks. Only HTTP(S) origins without credentials are accepted; paths/query fragments are normalized to the origin.

This variable is separate from `NEXT_PUBLIC_API_URL`, the existing `/local-api` proxy, backend destinations and authentication configuration. Those destinations were not redirected to production. The existing localhost frontend and isolated API were exercised successfully.

External work still required: domain ownership/registration verification, DNS, hosting selection and deployment, TLS, production API origin and CORS validation, and separately reviewed Firebase project/billing/authorized-domain/callback configuration. None is claimed live or configured here.

## Branding audit and intentional exceptions

The source audit covers `frontend/app`, `frontend/components`, `frontend/lib`, and `backend/app`, plus current public README/environment examples and the existing Firebase plan. See `remaining-legacy-references.json` for inspectable source matches.

Intentional legacy references:

- `geoai:*` browser events and storage keys, authentication token keys, CSS classes, imported component/function names, package/module names, database identities, environment variables and logger prefixes.
- `sitegeoai.structural-analysis-result/v1` and `sitegeoai.structural-analysis-package/v1` remain stable import/export format contracts.
- The geocoding HTTP user-agent remains a technical integration identifier.
- Existing solver script header strings remain unchanged to preserve deterministic artifact bytes and provenance.
- The documented synthetic half-space benchmark source citation retains its original GeoAI name; it identifies an existing numerical reference, rather than the current product. No source evidence was relabeled.
- The assistant claim-detection guard recognizes the historical GeoAI name as well as the new names.
- Historical conversations, audit records, saved engineering artifacts, prior milestone reports/screenshots, retained manifests and repository URLs retain their original text.

Current checked screen text contains no unintended old brand. The audit does not replace legacy text at render time in historical records.

## Verification

- TypeScript, scoped ESLint and final production build passed. Logs: `typescript.log`, `lint.log`, `build.log`.
- 23 frontend tests passed: assistant presentation/tool parsing/primitive handling plus branding, configurable origin, manifest, auth redirects and revision comparison. Logs: `frontend-tests.log`, `metadata-auth-tests.log`.
- 56 backend tests passed, one skipped: site-wide assistant, quota, ownership and export-contract checks. Provider traffic was mocked. Log: `backend-tests.log`.
- 58 additional backend tests passed: supervised beams/columns and workspace tool/approval behavior. Log: `workflow-tests.log`.
- Fresh read-only browser checks at 1280×900 and 1600×900 covered homepage, dashboard, settings, diagnostics, saved 3D workspace and assistant. Mobile homepage/dashboard checked at 390×900. Exact homepage title/tagline, canonical normalization and manifest were asserted. Zero page JavaScript errors, unexpected mutations or horizontal overflow in the final run. See `browser.json`, `browser-final-render.log`, `browser.cjs`.
- Fresh screenshots were visually inspected. A mobile wordmark wrap was corrected. Final saved geometry and assistant screenshots use Chrome's SwiftShader renderer; an initial blank headless viewport was a rendering configuration issue. Favicon RGBA compatibility was corrected before the passing production build.
- Browser project reads use the retained Milestone 9 synthetic API on port 8003 with inference disabled, map credentials omitted and writes blocked. No original project was edited. Full CAD imports, new numerical analyses and live inference were not rerun; their underlying methods were unchanged. Coverage combines existing mocked tool/backend tests with read-only browser navigation, rather than claiming new solver certification or complete browser execution of every engineering screen.

Before: `before-1280.png`, `before-1600.png`. After: `after-home-*`, `after-dashboard-*`, `after-settings-*`, `after-diagnostics-*`, `after-workspace-*`, `after-assistant-*`. All are in this directory.

## Preservation and test side effect

All **10,269 original development rows and original schemas are unchanged**. Original assistant history/accounting is exactly unchanged (three rows in its separate history database). See final `preservation.json` and reproducible read-only `verify_final_preservation.py` (run from the repository root).

**The existing ownership regression suite uses the development database. Its run appended 13 synthetic records: one user, one project, five audit entries and six usage entries.** Final state is therefore not byte-for-byte or row-count identical. `final-row-differences.json` records the difference. No original row was changed or removed. These additions were retained; no destructive cleanup or database restoration was performed. No paid inference was submitted. This is an explicit verification side effect, not a rebranding migration.

The reused retained-archive checks verified **55,296 original storage files**, **2,090 original engineering proof files**, **66 live database schemas**, and **198 archived-only database fingerprints**. The older baseline comparison was exact before the ownership tests appended the records above; final original-row comparisons explicitly report the additions. Twenty-one coupled solver evidence files were verified without running a solver. See `preservation.log`, `preservation-audit.json`, `preservation-manifests.json`, `coupled-evidence-preservation.json`.

No Git operations, parallel agents, dependency installation, paid inference, destructive cleanup, deployment or Firebase activation were used. Development stops after Milestone 9.1.
