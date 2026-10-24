# Final performance evidence

Local production build, headless Chromium, unthrottled desktop host, synthetic intercepted API data. One observation per route/width; no field Core Web Vitals or percentile certification. Browser axe injection and concurrent test processes can influence timings. Resource measurements precede/overlap audit work; use raw JSON for observation window.

| Route, 1440px | Observed LCP ms | CLS | Script encoded bytes | Largest observed task ms |
|---|---:|---:|---:|---:|
| / | 840 | 0 | 485170 | 302 |
| /dashboard | 160 | 0 | 516810 | 189 |
| /projects/999998/report | 208 | 0.012971494231047454 | 380234 | 74 |
| /projects/999998/workspace | 48 | 0.24133992727020642 | 2765313 | 209 |

LCP is the most recent buffered candidate over the short observation window, not final user-session LCP. A canvas drawing can have a very early text LCP while its renderer continues loading. Bytes are Resource Timing encodedBodySize for scripts, not total assets or a route bundle manifest. Cross-origin aborted resources and caching affect the total. Every context is fresh per width; later routes may reuse caches.

**Measured optimization:** scrolling a synthetic 150-project library increased canvases 12 → 76 before correction; the same interaction after correction measured 12 → 12. Decorative ConstructionPreview observers previously disconnected permanently on first intersection. They now remain subscribed and unmount offscreen renderers. Desktop engineering renderers and model state are untouched. A regression test verifies mount/unmount.

Coarse heap samples before/after scroll were 27600000/27600000 bytes in the earlier run and 53500000/53500000 in the final run. These samples are not a leak test, GPU memory measurement or an improvement claim. GC, process reuse and Chromium's coarse precision prevent a causal heap comparison.

Observed interaction Event Timing durations in the final library interaction: [{"duration":64,"name":"pointerdown"},{"duration":64,"name":"pointerup"},{"duration":64,"name":"click"}]. This is a limited interaction sample, **not field INP**; page lifecycle and enough representative interactions were not measured. No INP pass is asserted.

Fresh unsupported advanced routes have zero canvases across 390/768/1024 checks. Homepage and dashboard decorative canvases are allowed and distinct from the engineering workspace. Framework script bytes may still be prefetched. Desktop workspace initialization and retained resize lifecycle have unit/browser evidence, but terrain fidelity, actual map latency, long-session GPU behavior, React rerender counts and production backend latency remain unverified.

An earlier 1440px workspace sample had CLS 0.2413. Preserve this as a performance concern pending a representative loaded project and repeated controlled profiling; no layout-threshold certification. No geometry fidelity reduction was made. Build compilation time is deliberately excluded from runtime claims.

Evidence: final-browser-loaded.json, final-browser-loaded-before.json, final-workflow-before-performance.json, final-workflow-browser.json, logs/final-build-release.log.
