# Final accessibility review

Axe-core installed in the existing local dependency tree, WCAG 2 A/AA, 2.1 AA and 2.2 AA tags. 114 final populated route/viewport states plus 96 error/missing-data states. Automated checks do not establish WCAG conformity. Raw violation and incomplete-rule records: final-browser-loaded.json.

Confirmed and corrected: cost/BOQ data scroll wrappers now use named keyboard-focusable TableScrollRegion; report Preview is separate from its download link and has a 44px minimum height; unavailable export descriptions no longer inherit 55% opacity (reported 3.11:1 contrast); draft failures announced through the existing alert toaster; local return URL checked before router navigation.

Current automated findings (3 route/rule entries):
- /projects/999998/workspace at 1280px: target-size (serious); button[title="+Z view"]; button[title="+Y view"]
- /projects/999998/workspace at 1440px: target-size (serious); button[title="+Z view"]; button[title="+Y view"]
- /projects/999998/workspace at 1920px: target-size (serious); button[title="+Z view"]; button[title="+Y view"]

Desktop camera orientation gizmo +Y/+Z buttons are 20px targets with overlapping projected spacing. This is an open P2 accessibility issue, not a mobile engineering requirement. Altering the camera gizmo layout/interaction requires a focused desktop design/regression pass; no camera algorithm or geometry interaction was modified during acceptance. F25 remains partial.

Manual/interaction evidence: keyboard dialog initial focus, Shift+Tab wrap, Escape close and opener focus return; keyboard ArrowRight actually scrolls populated cost rows; event pagination and visible announcements; unsupported workspace context return; mobile report lacks Edit controls. Browser emulated forced-colors/reduced-motion login retained focus outline (auto) on the first link. This is a focused spot check, not every control in forced colors.

Actual 200% browser zoom tested 14 routes. Ordinary pages render responsive layouts; advanced workspace correctly gates at 720 CSS px. At 200% this intentional admission policy limits engineering editing; no desktop controls were compressed. See final-zoom.json and zoom200 screenshots.

Status/skeleton semantics, indeterminate progress, known-zero/missing metrics and recovery are additionally component-tested. Historical source-color sample improved 3.94 → 8.43:1; no full computed contrast census claimed. Long report/100-row cost fixture assessed in browser.

Not certified: real NVDA/JAWS/VoiceOver speech and reading order, physical tablet reliability, full keyboard drawing/editing, every engineering inspector/dialog, dynamic reduced-motion preference changes during an active preview loop, all screenreader announcement timing, all target-size exceptions or complete WCAG2.2 checklist. Axe incomplete rules need human judgement.

Evidence: screenshots/final/, final-workflow-browser.json, final-zoom.json, logs/final-browser-release.log.
