# StruvoCivil official logo integration

Implemented locally on 23 October 2026. The Dark Lemon interface, engineering workflows and existing layout were retained. Current branding now uses **StruvoCivil** and **Structural Design Clarity**. The existing large “Model. Analyze. Design.” homepage headline remains presentation copy; it was not redesigned.

## Logo assets

`frontend/public/brand/` contains five consistent variants, each in dark and light treatments:

- `main-*`: stacked symbol, outlined StruvoCivil wordmark and tagline.
- `secondary-*`: horizontal symbol and wordmark for desktop navigation.
- `simplified-*`: compact horizontal lockup for mobile.
- `submark-*`: standalone structural S.
- `animated-*`: grid, connection nodes, beam reveal, then completed wordmark. It plays once and honors `prefers-reduced-motion`. Its PNG is the completed static poster.

All SVG lettering consists of actual vector paths, not embedded raster images or font-dependent text. Every variant derives from the same six-node structural S source. Transparent PNG versions are supplied for both treatments. Square app icons are provided at 16, 32, 64, 180, 192 and 512 pixels; the ICO contains 16/32/64 sizes. `app/icon.svg` and `app/favicon.ico` use the new submark. A local SVG/PNG social card also uses the main logo.

Dark artwork uses the approved #080C08, #C8FF32, #B7C3AA and #F2F3ED palette. Light artwork is a #080C08 monochrome treatment on transparency so the symbol remains readable on paper without introducing unrelated colors. PNG antialiasing naturally creates intermediate edge pixels.

The reproducible vector source is `frontend/scripts/generate-official-logo.py` (run from the repository root with Python/fontTools and the existing Windows Segoe fonts). `render-assets.cjs` renders raster derivatives using the project's existing Playwright installation. No dependencies were installed. `assets.json` lists each generated asset and byte size.

## Integration and files

- `components/brand/BrandLogo.tsx`: reusable main, secondary, simplified, submark and animated components, dark/light options, accessible names and decorative mode.
- `components/landing/BrandWordmark.tsx`: shared responsive desktop/mobile lockups. Existing callers automatically update navigation, dashboard, project/workspace headers and authentication screens.
- `DashboardSidebar.tsx`: standalone submark replaces the collapsed-sidebar placeholder.
- `app/loading.tsx`: accessible loading state with the animated lockup and static reduced-motion behavior.
- `HomePage.tsx`: main logo in the homepage footer; current tagline in the existing branding copy. Hero, terrain and workflow layout retained.
- `lib/brand.ts`, browser metadata, manifest and current UI copy: exact StruvoCivil spelling and new official tagline. Legacy technical names and stored historical text are retained.
- `backend/app/services/exports/pdf_report.py` and its packaged light PNG: main logo on future report covers and updated report title. Existing numerical content, warnings and calculation code remain unchanged. Existing report files were not rewritten.

Full created/modified file inventory: `files.json`. Current theme tokens were not recolored; only the public brand-name string in global CSS changed. The existing assistant name remains Struvo Assistant.

## Verification

- TypeScript: passed (`typescript.log`).
- Scoped ESLint: passed with zero warnings (`lint.log`).
- Production build: passed (`build.log`).
- Existing focused tests: 13 passed across branding/origin/manifest, auth-return paths, assistant presentation and revision comparison (`tests.log`). These tests do not open project databases.
- Browser checks: homepage, dashboard, login and settings at 1280×900, 1600×900 and 390×900. All visible logo assets loaded successfully; no document horizontal overflow. Direct SVG reduced-motion check confirms all logo animation names become `none`. See `browser.json`, `verify-browser.cjs` and screenshots.
- Additional read-only browser checks: collapsed sidebar submark, local 3D sandbox header and homepage main/footer logo (`extra-browser.json`). No save, generation, inference or project mutation was performed; non-read browser requests were blocked.
- Synthetic PDF generation succeeded using in-memory placeholder project properties, with no database calls or engineering calculations (`report-test.log`, `synthetic-report.pdf`). A PDF raster renderer was unavailable, so the generated PDF cover was not raster-reviewed; the exact packaged light logo PNG was generated from the same inspected vector assets.
- Original development and assistant-history database file hashes are identical before/after final browser verification (`database-preservation.json`). No database writes, authentication changes, API changes, deployments, Git operations or paid inference were performed.

Before screenshots: `before-1280.png`, `before-390.png`. After screenshots: `after-home-*`, `after-dashboard-*`, `after-login-*`, `after-settings-*`, `after-collapsed-sidebar.png`, `after-workspace-1280.png`, `after-footer-main.png`.

## Reconstruction limitations

The supplied reference is a raster brand presentation, not the original vector/font master. The implementation is a careful planar reconstruction, **not an exact trace**: beam intersections, node spacing, rail thickness and inner-beam geometry are approximated. Photographic shading, construction guides and dimensional effects from the presentation are not baked into the static logo. The reference's bold/light wordmark is approximated with Segoe UI Bold/Light converted to paths; exact original glyphs and kerning cannot be recovered reliably from the image. The registration symbol was omitted rather than adding a registration claim.

At 16 pixels the S silhouette remains recognizable, while the paired rails and node holes necessarily lose detail; use the larger assets for full structural detail. The original vector master would be required for exact brand-master fidelity. No claim of exact geometric identity or engineering certification is made.
