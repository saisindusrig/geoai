# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: milestone-6.spec.ts >> site assistant honest failure and manual retry 1280
- Location: e2e\milestone-6.spec.ts:6:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.click: Test timeout of 120000ms exceeded.
Call log:
  - waiting for getByRole('complementary', { name: 'GeoAI Assistant' }).getByRole('button', { name: 'Send', exact: true })
    - locator resolved to <button type="submit" class="rounded bg-primary px-3 py-2 text-primary-foreground disabled:opacity-50">Send</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <button type="button" title="Copy page link" aria-label="Copy page link">…</button> from <div class="site-utilities" aria-label="Page utilities">…</div> subtree intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <button type="button" title="Copy page link" aria-label="Copy page link">…</button> from <div class="site-utilities" aria-label="Page utilities">…</div> subtree intercepts pointer events
    - retrying click action
      - waiting 100ms
    231 × waiting for element to be visible, enabled and stable
        - element is visible, enabled and stable
        - scrolling into view if needed
        - done scrolling
        - <button type="button" title="Copy page link" aria-label="Copy page link">…</button> from <div class="site-utilities" aria-label="Page utilities">…</div> subtree intercepts pointer events
      - retrying click action
        - waiting 500ms

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - main [ref=e5]:
    - generic [ref=e7]:
      - complementary [ref=e8]:
        - generic [ref=e9]:
          - link "GeoAI" [ref=e10] [cursor=pointer]:
            - /url: /
            - generic "GeoAI" [ref=e11]:
              - img [ref=e12]
              - generic [ref=e14]: GeoAI
          - button "Collapse sidebar" [ref=e16] [cursor=pointer]:
            - img [ref=e17]
        - generic [ref=e20]: WORKSPACE
        - navigation "Dashboard navigation" [ref=e21]:
          - button "Overview" [ref=e22] [cursor=pointer]:
            - img [ref=e23]
            - generic [ref=e28]: Overview
          - button "Projects" [ref=e29] [cursor=pointer]:
            - img [ref=e30]
            - generic [ref=e34]: Projects
          - link "3D Sandbox" [ref=e35] [cursor=pointer]:
            - /url: /projects/999999/workspace?local=1
            - img [ref=e36]
            - generic [ref=e39]: 3D Sandbox
        - generic [ref=e40]:
          - generic [ref=e41]:
            - generic [ref=e42]: FOLDERS
            - button "New folder" [ref=e43] [cursor=pointer]:
              - img [ref=e44]
          - paragraph [ref=e46]:
            - text: No folders yet.
            - text: Organize your saved projects here.
        - navigation "Workspace resources" [ref=e47]:
          - link "Diagnostics" [ref=e48] [cursor=pointer]:
            - /url: /diagnostics
            - img [ref=e49]
            - generic [ref=e52]: Diagnostics
          - link "Settings" [ref=e53] [cursor=pointer]:
            - /url: /settings
            - img [ref=e54]
            - generic [ref=e57]: Settings
          - link "Help" [ref=e58] [cursor=pointer]:
            - /url: /#faq
            - img [ref=e59]
            - generic [ref=e62]: Help
        - generic [ref=e63]:
          - text: CONCEPT PLANNING
          - generic [ref=e65]: Professional verification required
      - generic [ref=e66]:
        - generic [ref=e67]:
          - generic [ref=e68]:
            - img [ref=e69]
            - searchbox "Search projects" [ref=e72]
            - generic [ref=e73]: Ctrl K
          - generic [ref=e74]:
            - link "Open sandbox" [ref=e75] [cursor=pointer]:
              - /url: /projects/999999/workspace?local=1
              - img [ref=e76]
              - text: Open sandbox
            - button "New Project" [ref=e79] [cursor=pointer]:
              - img [ref=e80]
              - text: New Project
            - link "Open settings" [ref=e81] [cursor=pointer]:
              - /url: /settings
              - img [ref=e82]
        - generic [ref=e85]:
          - generic [ref=e86]:
            - generic [ref=e87]: WORKSPACE / OVERVIEW
            - heading "Your projects" [level=1] [ref=e88]
            - paragraph [ref=e89]: Your saved infrastructure work, together in one place.
          - region "Continue working" [ref=e90]:
            - heading "Continue working" [level=2] [ref=e91]
            - generic [ref=e92]:
              - strong [ref=e93]: "2"
              - generic [ref=e94]: Location not saved
              - link "Open workspace" [ref=e95] [cursor=pointer]:
                - /url: /projects/807/workspace
                - text: Open workspace
                - img [ref=e96]
          - region "Saved projects" [ref=e98]:
            - heading "Recent projects" [level=2] [ref=e99]
            - generic [ref=e100]:
              - generic [ref=e101]: 166 projects
              - generic [ref=e102]:
                - button "All" [pressed] [ref=e103] [cursor=pointer]
                - button "Recent" [ref=e104] [cursor=pointer]
                - button "Unfiled" [ref=e105] [cursor=pointer]
              - generic [ref=e106]:
                - text: Sort
                - combobox "Sort concepts" [ref=e107] [cursor=pointer]:
                  - option "Recently updated" [selected]
                  - option "Name A–Z"
            - generic [ref=e108]:
              - article [ref=e109]:
                - link "unclassified 2 draft Location not saved Updated today • Unfiled" [ref=e110] [cursor=pointer]:
                  - /url: /projects/807/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e111]:
                    - generic [ref=e112]:
                      - heading "2" [level=3] [ref=e113]
                      - generic [ref=e114]: draft
                      - img [ref=e115]
                    - paragraph [ref=e117]:
                      - img [ref=e118]
                      - text: Location not saved
                    - paragraph [ref=e122]:
                      - img [ref=e123]
                      - text: Updated today
                      - generic [ref=e126]: •
                      - text: Unfiled
                - generic [ref=e127]:
                  - link "Open workspace" [ref=e128] [cursor=pointer]:
                    - /url: /projects/807/workspace
                  - button "Project options for 2" [ref=e129] [cursor=pointer]:
                    - img [ref=e130]
              - article [ref=e134]:
                - link "unclassified Foundation integrated study · reference 804 draft Location not saved Updated yesterday • Unfiled" [ref=e135] [cursor=pointer]:
                  - /url: /projects/805/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e136]:
                    - generic [ref=e137]:
                      - heading "Foundation integrated study · reference 804" [level=3] [ref=e138]
                      - generic [ref=e139]: draft
                      - img [ref=e140]
                    - paragraph [ref=e142]:
                      - img [ref=e143]
                      - text: Location not saved
                    - paragraph [ref=e147]:
                      - img [ref=e148]
                      - text: Updated yesterday
                      - generic [ref=e151]: •
                      - text: Unfiled
                - generic [ref=e152]:
                  - link "Open workspace" [ref=e153] [cursor=pointer]:
                    - /url: /projects/805/workspace
                  - button "Project options for Foundation integrated study · reference 804" [ref=e154] [cursor=pointer]:
                    - img [ref=e155]
              - article [ref=e159]:
                - link "unclassified 2 draft Location not saved Updated yesterday • Unfiled" [ref=e160] [cursor=pointer]:
                  - /url: /projects/806/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e161]:
                    - generic [ref=e162]:
                      - heading "2" [level=3] [ref=e163]
                      - generic [ref=e164]: draft
                      - img [ref=e165]
                    - paragraph [ref=e167]:
                      - img [ref=e168]
                      - text: Location not saved
                    - paragraph [ref=e172]:
                      - img [ref=e173]
                      - text: Updated yesterday
                      - generic [ref=e176]: •
                      - text: Unfiled
                - generic [ref=e177]:
                  - link "Open workspace" [ref=e178] [cursor=pointer]:
                    - /url: /projects/806/workspace
                  - button "Project options for 2" [ref=e179] [cursor=pointer]:
                    - img [ref=e180]
              - article [ref=e184]:
                - link "unclassified RC footing nominal flexure — synthetic review draft Location not saved Updated 8 days ago • Unfiled" [ref=e185] [cursor=pointer]:
                  - /url: /projects/804/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e186]:
                    - generic [ref=e187]:
                      - heading "RC footing nominal flexure — synthetic review" [level=3] [ref=e188]
                      - generic [ref=e189]: draft
                      - img [ref=e190]
                    - paragraph [ref=e192]:
                      - img [ref=e193]
                      - text: Location not saved
                    - paragraph [ref=e197]:
                      - img [ref=e198]
                      - text: Updated 8 days ago
                      - generic [ref=e201]: •
                      - text: Unfiled
                - generic [ref=e202]:
                  - link "Open workspace" [ref=e203] [cursor=pointer]:
                    - /url: /projects/804/workspace
                  - button "Project options for RC footing nominal flexure — synthetic review" [ref=e204] [cursor=pointer]:
                    - img [ref=e205]
              - article [ref=e209]:
                - link "unclassified Footing bending demand — synthetic CAD envelope review draft Location not saved Updated 8 days ago • Unfiled" [ref=e210] [cursor=pointer]:
                  - /url: /projects/803/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e211]:
                    - generic [ref=e212]:
                      - heading "Footing bending demand — synthetic CAD envelope review" [level=3] [ref=e213]
                      - generic [ref=e214]: draft
                      - img [ref=e215]
                    - paragraph [ref=e217]:
                      - img [ref=e218]
                      - text: Location not saved
                    - paragraph [ref=e222]:
                      - img [ref=e223]
                      - text: Updated 8 days ago
                      - generic [ref=e226]: •
                      - text: Unfiled
                - generic [ref=e227]:
                  - link "Open workspace" [ref=e228] [cursor=pointer]:
                    - /url: /projects/803/workspace
                  - button "Project options for Footing bending demand — synthetic CAD envelope review" [ref=e229] [cursor=pointer]:
                    - img [ref=e230]
              - article [ref=e234]:
                - link "unclassified Rectangular bearing — synthetic square review draft Location not saved Updated 8 days ago • Unfiled" [ref=e235] [cursor=pointer]:
                  - /url: /projects/802/workspace
                  - generic:
                    - generic:
                      - img
                    - generic: unclassified
                  - generic [ref=e236]:
                    - generic [ref=e237]:
                      - heading "Rectangular bearing — synthetic square review" [level=3] [ref=e238]
                      - generic [ref=e239]: draft
                      - img [ref=e240]
                    - paragraph [ref=e242]:
                      - img [ref=e243]
                      - text: Location not saved
                    - paragraph [ref=e247]:
                      - img [ref=e248]
                      - text: Updated 8 days ago
                      - generic [ref=e251]: •
                      - text: Unfiled
                - generic [ref=e252]:
                  - link "Open workspace" [ref=e253] [cursor=pointer]:
                    - /url: /projects/802/workspace
                  - button "Project options for Rectangular bearing — synthetic square review" [ref=e254] [cursor=pointer]:
                    - img [ref=e255]
  - generic "Page utilities" [ref=e259]:
    - button "Copy page link" [ref=e260]:
      - img [ref=e261]
  - alert [ref=e264]
  - complementary "GeoAI Assistant" [ref=e265]:
    - generic [ref=e266]:
      - generic [ref=e267]:
        - heading "GeoAI Assistant" [level=2] [ref=e268]
        - paragraph [ref=e269]: Nebius · engineering unverified
      - button "Close site assistant" [ref=e270]: ✕
    - generic [ref=e271]:
      - generic [ref=e272]:
        - text: Model
        - combobox "Assistant model" [ref=e273]:
          - option "GLM-5.3-Flash" [selected]
          - option "GLM-5.3 · advanced, higher cost"
      - paragraph [ref=e274]: "Nebius inference unavailable: credentials and an explicitly approved backend budget are required. No offline AI fallback."
      - group [ref=e275]:
        - generic "Context · Site-wide · 0 selected" [ref=e276]
    - generic "Assistant task history" [ref=e277]:
      - paragraph [ref=e278]: Ask about saved evidence, find a tool, or prepare a selected object’s position preview. Saving, imports, exports and analyses need your review in their existing tools.
    - generic [ref=e279]:
      - generic [ref=e280]: Message GeoAI Assistant
      - textbox "Message GeoAI Assistant" [active] [ref=e281]:
        - /placeholder: What would you like to do?
        - text: Explain what project tools are available.
      - generic [ref=e282]:
        - generic [ref=e283]: Plan → tools → review → verify
        - button "Send" [ref=e284]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | import { writeFileSync } from "node:fs";
  3  | const evidence = "../docs/milestone-6/";
  4  | 
  5  | for (const width of [1280, 1600]) {
  6  |   test(`site assistant honest failure and manual retry ${width}`, async ({ page }) => {
  7  |     await page.setViewportSize({ width, height: 900 });
  8  |     const errors: string[] = [], unexpected: string[] = []; let sends = 0;
  9  |     page.on("pageerror", e => errors.push(e.message));
  10 |     await page.route("**/*", async route => {
  11 |       const req = route.request(), url = new URL(req.url());
  12 |       if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
  13 |       if (url.pathname.endsWith("/api/assistant/turn")) { sends++; return route.continue(); }
  14 |       if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { unexpected.push(req.method()+" "+url.pathname); return route.abort(); }
  15 |       return route.continue();
  16 |     });
  17 |     await page.goto("/dashboard");
  18 |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  19 |     const assistant = page.getByRole("complementary", { name: "GeoAI Assistant" });
  20 |     await expect(assistant).toContainText("No offline AI fallback");
  21 |     await expect(assistant.getByLabel("Assistant model")).toHaveValue("zai-org/GLM-5.3-Flash");
  22 |     await assistant.getByLabel("Message GeoAI Assistant").fill("Explain what project tools are available.");
> 23 |     await assistant.getByRole("button", { name: "Send", exact: true }).click();
     |                                                                        ^ Error: locator.click: Test timeout of 120000ms exceeded.
  24 |     await expect(assistant.getByRole("alert")).toContainText("explicit spending approval required");
  25 |     await expect(assistant.locator("article")).toHaveCount(0);
  26 |     await page.waitForTimeout(1000); expect(sends).toBe(1);
  27 |     await assistant.getByRole("button", { name: "Retry", exact: true }).click();
  28 |     await expect.poll(() => sends).toBe(2);
  29 |     await expect(assistant.getByLabel("Message GeoAI Assistant")).toHaveValue("Explain what project tools are available.");
  30 |     await expect(assistant.getByRole("button", { name: "Send", exact: true })).toBeEnabled();
  31 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  32 |     await page.screenshot({ path: evidence+`unavailable-${width}.png` });
  33 |     await assistant.getByRole("button", { name: "Close site assistant" }).focus(); await page.keyboard.press("Enter");
  34 |     await expect(page.getByRole("button", { name: "GeoAI Assistant", exact: true })).toBeVisible();
  35 |     expect(errors).toEqual([]); expect(unexpected).toEqual([]);
  36 |     writeFileSync(evidence+`failure-${width}.json`, JSON.stringify({ width, height: 900, real_disabled_backend: true, sends, no_fabricated_messages: true, manual_retry: true, errors, unexpected, inference_requests: 0 }, null, 2));
  37 |   });
  38 | 
  39 |   test(`site assistant selected evidence preview navigation ${width}`, async ({ page }) => {
  40 |     test.setTimeout(150000); await page.setViewportSize({ width, height: 900 });
  41 |     const errors: string[] = [], forbidden: string[] = []; let turns = 0;
  42 |     page.on("pageerror", e => errors.push(e.message));
  43 |     await page.route("**/*", async route => {
  44 |       const req = route.request(), url = new URL(req.url());
  45 |       if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
  46 |       if (url.pathname.endsWith("/api/geocode/map-runtime-config")) return route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } });
  47 |       if (url.pathname.endsWith("/api/assistant/turn")) {
  48 |         turns++; const p = req.postDataJSON();
  49 |         expect(p.project_id).toBe(793); expect(p.revision_id).toBe(103); expect(p.selected_ids).toHaveLength(1);
  50 |         const context = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, selected_ids: p.selected_ids, dirty: false, page: "/projects/793/workspace" } });
  51 |         const saved = (await context.json()).project;
  52 |         const before = saved.selected[0].transform.position, after = [before[0]+0.1, before[1], before[2]];
  53 |         const events = [
  54 |           { type: "progress", text: "Automated test fixture: reading actual saved evidence" },
  55 |           { type: "delta", text: "Automated mocked provider: prepare a visual position preview and inspect existing results. No model has been saved." },
  56 |           { type: "tool_result", name: "prepare_position_preview", ok: true, result: { kind: "position_preview", projectId: 793, revisionId: 103, componentId: p.selected_ids[0], before, after, documentHash: saved.documentHash, requiresApproval: true, saved: false } },
  57 |           { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "results", href: "/projects/793/workspace", projectId: 793, revisionId: 103, componentIds: p.selected_ids, executed: false } },
  58 |           { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "diagnostics", href: "/diagnostics", executed: false } },
  59 |         ];
  60 |         return route.fulfill({ contentType: "text/event-stream", body: [...events, { type: "task", task: { id: p.request_id, request: p, status: "SUCCEEDED", model: p.model, reply: events[1].text, events } }].map(e => "data: "+JSON.stringify(e)+"\n\n").join("") });
  61 |       }
  62 |       if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { forbidden.push(req.method()+" "+url.pathname); return route.abort(); }
  63 |       return route.continue();
  64 |     });
  65 |     await page.goto("/projects/793/workspace");
  66 |     await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 90000 });
  67 |     const source = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, page: "/projects/793/workspace", selected_ids: [], dirty: false } });
  68 |     expect(source.ok()).toBe(true); const saved = (await source.json()).project;
  69 |     const id: string = saved.drawingReferences[0].componentId;
  70 |     await page.evaluate(id => window.dispatchEvent(new CustomEvent("geoai:inspect-component", { detail: { projectId: 793, revisionId: 103, componentIds: [id] } })), id);
  71 |     await expect(page.getByLabel("Component edit form")).toBeVisible();
  72 |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  73 |     const assistant = page.getByRole("complementary", { name: "GeoAI Assistant" });
  74 |     await expect(assistant).toContainText("1 selected");
  75 |     await assistant.getByRole("textbox").fill("Preview a small East move for my selected component, then show saved results.");
  76 |     await assistant.getByRole("button", { name: "Send", exact: true }).click();
  77 |     await expect(assistant.getByRole("button", { name: "Review visual preview in editor" })).toBeEnabled();
  78 |     await assistant.getByRole("button", { name: "Review visual preview in editor" }).click();
  79 |     await expect(assistant.getByRole("status")).toContainText("Visual preview shown", { timeout: 10000 });
  80 |     await page.screenshot({ path: evidence+`preview-${width}.png` });
  81 |     await assistant.getByRole("button", { name: "Close site assistant" }).click();
  82 |     await expect(page.getByLabel("Component edit form")).toContainText("Edit preview · not applied");
  83 |     await page.screenshot({ path: evidence+`editor-preview-${width}.png` });
  84 |     await page.getByLabel("Component edit form").getByRole("button", { name: "Cancel", exact: true }).click();
  85 |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  86 |     await assistant.getByRole("button", { name: "Open results", exact: true }).click();
  87 |     await assistant.getByRole("button", { name: "Close site assistant" }).click();
  88 |     await expect(page.getByRole("region", { name: "Guided Analysis", exact: true })).toBeVisible();
  89 |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  90 |     await assistant.getByRole("button", { name: "Open diagnostics", exact: true }).click();
  91 |     await expect(page).toHaveURL(/\/diagnostics$/); await expect(assistant).toBeVisible();
  92 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  93 |     await page.screenshot({ path: evidence+`navigation-${width}.png` });
  94 |     expect(turns).toBe(1); expect(errors).toEqual([]); expect(forbidden).toEqual([]);
  95 |     writeFileSync(evidence+`preview-navigation-${width}.json`, JSON.stringify({ width, height: 900, automated_mock_provider_only: true, actual_saved_project: 793, revision: 103, component: id, preview_shown: true, applied: false, saved: false, analysis_executed: false, navigation: ["results", "diagnostics"], forbidden, errors, turns, inference_requests: 0 }, null, 2));
  96 |   });
  97 | }
  98 | 
```