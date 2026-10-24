# Accessibility review

Focused axe-core WCAG2A/AA,2.1AA and2.2AA sweep:16 route/width states (login,dashboard,persisted workspace,report at390/1280/1440/1920),0 detected violations. Incomplete rules are retained in accessibility-results.json; this is not certification.

CameraGizmo's six orientation actions now use a stable3-column grid of at least28px targets with4px gaps below the unchanged projected axis visualization. Depth sorting no longer places clickable targets on top of each other. Names distinguish Positive/Negative X/Y/Z; the existing underground restriction on−Z remains. The orientation handler's camera mathematics and reduced-motion duration are unchanged.

Browser checks verify six nonoverlapping rectangles at1280/1440/1920, pointer click,+Y keyboard Enter and visible focus; the unit regression asserts exact+Z(heading0,pitch−90) and+Y(heading180,pitch−5) orientation events and no movement on mount. Forced-colors/reduced-motion workspace focus returns a visible outline. This verifies dispatch/usable controls, not a metrology certification of every camera pose.

Actual browser zoom uses chrome.tabs.setZoom/getZoom at2.0 in a disposable Chromium profile. Four routes pass at720 CSSpx from1440px viewport; unsupported workspace shows Desktop Required. Current mobile workspace has0 canvases. Engineering editing was not rebuilt for mobile. Existing focus traps/Escape, loading/status/error roles and reduced-motion regressions pass in the full suite.

Protected downloads have accessible button names,busy/disabled state,error announcements and retry; PDF iframe title is retained and its URL is a Blob, not a credential-bearing link.

Remaining:real NVDA/JAWS/VoiceOver reading/speech testing; every engineering inspector and dialog; physical tablet/hardware reliability; full keyboard drawing/measurement; dynamic reduced-motion changes during an existing preview loop. No screen-reader certification or blanket WCAG2.2 conformity claim.

Evidence:accessibility-results.json,logs/accessibility-final.log,screenshots/a11y-workspace-1280.png,screenshots/forced-colors-gizmo.png,screenshots/zoom-_projects_2_workspace.png,CameraGizmo.test.tsx.
