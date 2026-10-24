# Workspace performance and stability

## Repeated layout protocol

release-cls.cjs uses3 fresh contexts at each1280/1440/1920×900 viewport, deterministic intercepted project data, blocked external assets and4seconds of observation after navigation. LayoutShift entries with hadRecentInput are excluded. Raw source rectangles are retained in cls-before.json/cls-after.json.

- 1280px: before 0.270847–0.270847; after 0.001673–0.001673 (3 visits each).
- 1440px: before 0.240399–0.240399; after 0.001331–0.001331 (3 visits each).
- 1920px: before 0.179768–0.179768; after 0.000765–0.002700 (3 visits each).

The baseline identified the header's hydration transition: main moved from y52.05 to48px and the action region expanded from241.56 to602.80px, shifting existing content horizontally. DashboardShell now reserves a48px workspace header and604px right-aligned action region, with a stable home/title slot before project hydration. The change affects shell layout only, not renderer dimensions after admission, camera, geometry or numerical data.

There are9 observations before and9 after, not a single favorable sample. Baseline frontend JWT mode was off; final isolated build requires JWT and the layout probe uses an intercepted test token. This authentication-mode difference limits a strict single-variable causal comparison. The same width/data/timing protocol and source rectangles support the correction, but these are short-window lab CLS values, not field percentiles.

## Gallery and resource retention

The prior offscreen-preview observer cleanup remains covered by a unit regression and was exercised again with150 intercepted project rows. Canvas count8→12 across8 scroll positions, bounded near visible cards rather than the previous76 retained canvases. Heap samples283744521→310972529 bytes increased; they are not a leak-free result or GC-normalized comparison. Long-session heap/GPU profiling remains open. No model quality or terrain resolution was reduced.

Protected model/PDF resource hooks abort stale reads, avoid late URL allocation and revoke object URLs.5MiB download cleanup and duplicate suppression are unit-tested. Binary downloads intentionally buffer one Blob; very large multi-gigabyte exports need a future streaming/server delivery design, not a claim of unlimited memory safety.

Current field LCP/INP and representative terrain interaction latency are NOT VERIFIED. Earlier local LCP/EventTiming values remain historical, not relabeled as current production metrics. Build time is not runtime performance. Desktop admission remains min1280 CSSpx plus fine pointer; fresh unsupported visits initialize no engineering canvas.

Evidence:logs/cls-before.log,logs/cls-after.log,cls-before.json,cls-after.json,accessibility-results.json,logs/build-final.log.
