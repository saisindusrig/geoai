# Foundation visual milestone — final visual review

Open http://localhost:13001/projects/814/workspace and select **Analysis** for the isolated synthetic demonstration. The normal website remains at http://localhost:3001/projects/804/workspace; modifying acceptance tests use the separate attested database and ports 13001/18001.

## Visual demonstration

- [Recorded application demonstration](foundation-visual-demo.webm), approximately 24 seconds, 1600 × 1000.
- [Reinforcement at 1600 px](reinforcement-1600.png), [soil at 1280 px](soil-1280.png), [ghost alternative at 1600 px](alternatives-1600.png).
- All seven modes: loads/reactions, soil/settlement, bending, one-way shear, punching, reinforcement/anchorage and alternatives. Mode changes derive temporary overlays from saved evidence and do not recalculate or modify results.
- Actual bar radii, both mat directions, cover, spacing and effective depths; temporary transparent concrete; interactive labels and focused check evidence.
- Uniform soil pressure and explicitly scaled settlement display reflect the implemented numerical method. No fabricated FEA contour fields.
- Compact summaries use Within implemented check, Exceeds implemented check, Not verified and Not supported. Full calculations and reports remain behind expandable details.
- Validated alternatives have ghost previews. CAD changes require exact preview authorization and a separate Save model action. Compared reinforcement has its own explicit input-draft action; it never changes silently.

## Engineering limits

Straight-bar development remains failing: required 970.982 mm versus available 375 mm, independently checked using full design steel stress. Required reach is shown separately from actual steel. No invented hooks or reduced requirements.

IS 456 Amendment 1 resolves the soil critical section at d (piles d/2). Demand is shown at the correct soil cut. IS one-way shear resistance remains disabled because Table 19 resistance/interpolation/applicability has not been independently validated. See [independent hardening evidence](HARDENING.md). Unsupported checks stay disabled. This synthetic demonstration is not an engineering safety certificate, site design approval or verification of all foundation types.

## Validation evidence

- Full frontend regression: **70 files / 343 tests passed**, [log](frontend-regression-release.log).
- Relevant backend regression, including independent calculation, CAD, soil, RC, authorization and ownership checks: **327 passed**, [log](backend-regression.log).
- TypeScript and changed-file ESLint passed: [log](quality-checks.log).
- **All four browser acceptance workflows passed** in the final combined run. Coverage includes both 1280 and 1600 px, all modes, real label picking, opacity, immutable saved results, alternative authorization and explicit Save, stale results, report download and the prior integrated workflow: [final log](browser-final-verified.log). Earlier failed attempts remain in their separate logs, including sandbox-localhost/browser-path launch failures and a subsequently corrected readiness timeout.
- Normal website canvas and foundation entry point passed a read-only browser smoke test: [evidence](normal-website.json), [screenshot](normal-website-3001.png).

## Original-data preservation

Read-only comparison against the existing recovery manifests confirms **10,239 pre-existing rows, 55,296 original storage files, 2,090 engineering-proof files and all 264 database schemas preserved**. 263 databases retain exact baseline table fingerprints.

The development database has six additional rows: one project (study 805), one scenario, one revision and three drawing/review/proposal records. No baseline row was removed or modified. Their origin cannot be established by fingerprint comparison. They were retained; no restoration or deletion was performed. Therefore the strict whole-table baseline check correctly reports a mismatch, rather than claiming all databases are identical. See [preservation audit](preservation-audit.json), [original-row verification](preservation-rows.json) and [strict manifest report](preservation-manifests.json).

No Git operations, installations, deployment, paid inference, destructive cleanup or new full-project backups were performed. The milestone stops for visual review.
