# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: milestone-6.spec.ts >> site assistant honest failure and manual retry 1600
- Location: e2e\milestone-6.spec.ts:6:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('complementary', { name: 'GeoAI Assistant' }).getByRole('alert')
Expected substring: "explicit spending approval required"
Received string:    "Assistant unavailable (503). Retry manually.Retry"
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for getByRole('complementary', { name: 'GeoAI Assistant' }).getByRole('alert')
    13 × locator resolved to <div role="alert" class="border-t border-border p-3 text-xs">…</div>
       - unexpected value "Assistant unavailable (503). Retry manually.Retry"

```

```yaml
- alert:
  - paragraph: Assistant unavailable (503). Retry manually.
  - button "Retry"
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | import { writeFileSync } from "node:fs";
  3   | const evidence = "../docs/milestone-6/";
  4   | 
  5   | for (const width of [1280, 1600]) {
  6   |   test(`site assistant honest failure and manual retry ${width}`, async ({ page }) => {
  7   |     await page.setViewportSize({ width, height: 900 });
  8   |     const errors: string[] = [], unexpected: string[] = []; let sends = 0;
  9   |     page.on("pageerror", e => errors.push(e.message));
  10  |     await page.route("**/*", async route => {
  11  |       const req = route.request(), url = new URL(req.url());
  12  |       if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
  13  |       if (url.pathname.endsWith("/api/assistant/turn")) { sends++; return route.continue(); }
  14  |       if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { unexpected.push(req.method()+" "+url.pathname); return route.abort(); }
  15  |       return route.continue();
  16  |     });
  17  |     await page.goto("/dashboard");
  18  |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  19  |     const assistant = page.getByRole("complementary", { name: "GeoAI Assistant" });
  20  |     await expect(assistant).toContainText("No offline AI fallback");
  21  |     await expect(assistant.getByLabel("Assistant model")).toHaveValue("zai-org/GLM-5.3-Flash");
  22  |     await assistant.getByLabel("Message GeoAI Assistant").fill("Explain what project tools are available.");
  23  |     await assistant.getByRole("button", { name: "Send", exact: true }).click();
> 24  |     await expect(assistant.getByRole("alert")).toContainText("explicit spending approval required");
      |                                                ^ Error: expect(locator).toContainText(expected) failed
  25  |     await expect(assistant.locator("article")).toHaveCount(0);
  26  |     await page.waitForTimeout(1000); expect(sends).toBe(1);
  27  |     await assistant.getByRole("button", { name: "Retry", exact: true }).click();
  28  |     await expect.poll(() => sends).toBe(2);
  29  |     await expect(assistant.getByLabel("Message GeoAI Assistant")).toHaveValue("Explain what project tools are available.");
  30  |     await expect(assistant.getByRole("button", { name: "Send", exact: true })).toBeEnabled();
  31  |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  32  |     await page.screenshot({ path: evidence+`unavailable-${width}.png` });
  33  |     await assistant.getByRole("button", { name: "Close site assistant" }).focus(); await page.keyboard.press("Enter");
  34  |     await expect(page.getByRole("button", { name: "GeoAI Assistant", exact: true })).toBeVisible();
  35  |     expect(errors).toEqual([]); expect(unexpected).toEqual([]);
  36  |     writeFileSync(evidence+`failure-${width}.json`, JSON.stringify({ width, height: 900, real_disabled_backend: true, sends, no_fabricated_messages: true, manual_retry: true, errors, unexpected, inference_requests: 0 }, null, 2));
  37  |   });
  38  | 
  39  |   test(`site assistant selected evidence preview navigation ${width}`, async ({ page }) => {
  40  |     test.setTimeout(150000); await page.setViewportSize({ width, height: 900 });
  41  |     const errors: string[] = [], forbidden: string[] = []; let turns = 0; let mockedTasks: unknown[] = [];
  42  |     page.on("pageerror", e => errors.push(e.message));
  43  |     await page.route("**/*", async route => {
  44  |       const req = route.request(), url = new URL(req.url());
  45  |       if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
  46  |       if (url.pathname.endsWith("/api/geocode/map-runtime-config")) return route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } });
  47  |       if (url.pathname.endsWith("/api/assistant/history") && url.searchParams.get("project_id") === "793") return route.fulfill({ json: { tasks: mockedTasks } });
  48  |       if (url.pathname.endsWith("/api/assistant/turn")) {
  49  |         turns++; const p = req.postDataJSON();
  50  |         expect(p.project_id).toBe(793); expect(p.revision_id).toBe(103); expect(p.selected_ids).toHaveLength(1);
  51  |         const context = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, selected_ids: p.selected_ids, dirty: false, page: "/projects/793/workspace" } });
  52  |         const saved = (await context.json()).project;
  53  |         const before = saved.selected[0].transform.position, after = [before[0]+0.1, before[1], before[2]];
  54  |         const events = [
  55  |           { type: "progress", text: "Automated test fixture: reading actual saved evidence" },
  56  |           { type: "delta", text: "Automated mocked provider: prepare a visual position preview and inspect existing results. No model has been saved." },
  57  |           { type: "tool_result", name: "prepare_position_preview", ok: true, result: { kind: "position_preview", projectId: 793, revisionId: 103, componentId: p.selected_ids[0], before, after, documentHash: saved.documentHash, requiresApproval: true, saved: false } },
  58  |           { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "results", href: "/projects/793/workspace", projectId: 793, revisionId: 103, componentIds: p.selected_ids, executed: false } },
  59  |           { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "diagnostics", href: "/diagnostics", executed: false } },
  60  |         ];
  61  |         const task = { id: p.request_id, request: p, status: "SUCCEEDED", model: p.model, reply: events[1].text, events }; mockedTasks = [task];
  62  |         return route.fulfill({ contentType: "text/event-stream", body: [...events, { type: "task", task }].map(e => "data: "+JSON.stringify(e)+"\n\n").join("") });
  63  |       }
  64  |       if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { forbidden.push(req.method()+" "+url.pathname); return route.abort(); }
  65  |       return route.continue();
  66  |     });
  67  |     await page.goto("/projects/793/workspace");
  68  |     await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 90000 });
  69  |     const source = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, page: "/projects/793/workspace", selected_ids: [], dirty: false } });
  70  |     expect(source.ok()).toBe(true); const saved = (await source.json()).project;
  71  |     const id: string = saved.drawingReferences[0].componentId;
  72  |     await page.evaluate(id => window.dispatchEvent(new CustomEvent("geoai:inspect-component", { detail: { projectId: 793, revisionId: 103, componentIds: [id] } })), id);
  73  |     await expect(page.getByLabel("Component edit form")).toBeVisible();
  74  |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  75  |     const assistant = page.getByRole("complementary", { name: "GeoAI Assistant" });
  76  |     await expect(assistant).toContainText("1 selected");
  77  |     await assistant.getByRole("textbox").fill("Preview a small East move for my selected component, then show saved results.");
  78  |     await assistant.getByRole("button", { name: "Send", exact: true }).click();
  79  |     await expect(assistant.getByRole("button", { name: "Review visual preview in editor" })).toBeEnabled();
  80  |     await assistant.getByRole("button", { name: "Review visual preview in editor" }).click();
  81  |     await expect(assistant.getByRole("status")).toContainText("Visual preview shown", { timeout: 10000 });
  82  |     await page.screenshot({ path: evidence+`preview-${width}.png` });
  83  |     await assistant.getByRole("button", { name: "Close site assistant" }).click();
  84  |     await expect(page.getByLabel("Component edit form")).toContainText("Edit preview · not applied");
  85  |     await page.screenshot({ path: evidence+`editor-preview-${width}.png` });
  86  |     await page.getByLabel("Component edit form").getByRole("button", { name: "Cancel", exact: true }).click();
  87  |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  88  |     await assistant.getByRole("button", { name: "Open results", exact: true }).click();
  89  |     await assistant.getByRole("button", { name: "Close site assistant" }).click();
  90  |     await expect(page.getByRole("region", { name: "Guided Analysis", exact: true })).toBeVisible();
  91  |     await page.getByRole("button", { name: "GeoAI Assistant", exact: true }).click();
  92  |     await assistant.getByRole("button", { name: "Open diagnostics", exact: true }).click();
  93  |     await expect(page).toHaveURL(/\/diagnostics$/); await expect(assistant).toBeVisible();
  94  |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  95  |     await page.screenshot({ path: evidence+`navigation-${width}.png` });
  96  |     expect(turns).toBe(1); expect(errors).toEqual([]); expect(forbidden).toEqual([]);
  97  |     writeFileSync(evidence+`preview-navigation-${width}.json`, JSON.stringify({ width, height: 900, automated_mock_provider_only: true, actual_saved_project: 793, revision: 103, component: id, preview_shown: true, applied: false, saved: false, analysis_executed: false, navigation: ["results", "diagnostics"], forbidden, errors, turns, inference_requests: 0 }, null, 2));
  98  |   });
  99  | }
  100 | 
```