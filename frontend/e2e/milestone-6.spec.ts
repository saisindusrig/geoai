import { test, expect } from "@playwright/test";
import { writeFileSync } from "node:fs";
const evidence = "../docs/milestone-6/";

for (const width of [1280, 1600]) {
  test(`site assistant honest failure and manual retry ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [], unexpected: string[] = []; let sends = 0;
    page.on("pageerror", e => errors.push(e.message));
    await page.route("**/*", async route => {
      const req = route.request(), url = new URL(req.url());
      if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
      if (url.pathname.endsWith("/api/assistant/turn")) { sends++; return route.continue(); }
      if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { unexpected.push(req.method()+" "+url.pathname); return route.abort(); }
      return route.continue();
    });
    await page.goto("/dashboard");
    await page.getByRole("button", { name: "StruvoCivil Assistant", exact: true }).click();
    const assistant = page.getByRole("complementary", { name: "StruvoCivil Assistant" });
    await expect(assistant).toContainText("No offline AI fallback");
    await expect(assistant.getByLabel("Assistant model")).toHaveValue("zai-org/GLM-5.3-Flash");
    await assistant.getByLabel("Message StruvoCivil Assistant").fill("Explain what project tools are available.");
    await assistant.getByRole("button", { name: "Send", exact: true }).click();
    await expect(assistant.getByRole("alert")).toContainText("explicit spending approval required");
    await expect(assistant.locator("article")).toHaveCount(0);
    await page.waitForTimeout(1000); expect(sends).toBe(1);
    await assistant.getByRole("button", { name: "Retry", exact: true }).click();
    await expect.poll(() => sends).toBe(2);
    await expect(assistant.getByLabel("Message StruvoCivil Assistant")).toHaveValue("Explain what project tools are available.");
    await expect(assistant.getByRole("button", { name: "Send", exact: true })).toBeEnabled();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
    await page.screenshot({ path: evidence+`unavailable-${width}.png` });
    await assistant.getByRole("button", { name: "Close site assistant" }).focus(); await page.keyboard.press("Enter");
    await expect(page.getByRole("button", { name: "StruvoCivil Assistant", exact: true })).toBeVisible();
    expect(errors).toEqual([]); expect(unexpected).toEqual([]);
    writeFileSync(evidence+`failure-${width}.json`, JSON.stringify({ width, height: 900, real_disabled_backend: true, sends, no_fabricated_messages: true, manual_retry: true, errors, unexpected, inference_requests: 0 }, null, 2));
  });

  test(`site assistant selected evidence preview navigation ${width}`, async ({ page }) => {
    test.setTimeout(150000); await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [], forbidden: string[] = []; let turns = 0; let mockedTasks: unknown[] = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.route("**/*", async route => {
      const req = route.request(), url = new URL(req.url());
      if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
      if (url.pathname.endsWith("/api/geocode/map-runtime-config")) return route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } });
      if (url.pathname.endsWith("/api/assistant/history")) return route.fulfill({ json: { tasks: mockedTasks } });
      if (url.pathname.endsWith("/api/assistant/turn")) {
        turns++; const p = req.postDataJSON();
        expect(p.project_id).toBe(793); expect(p.revision_id).toBe(103); expect(p.selected_ids).toHaveLength(1);
        const context = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, selected_ids: p.selected_ids, dirty: false, page: "/projects/793/workspace" } });
        const saved = (await context.json()).project;
        const before = saved.selected[0].transform.position, after = [before[0]+0.1, before[1], before[2]];
        const events = [
          { type: "progress", text: "Automated test fixture: reading actual saved evidence" },
          { type: "delta", text: "Automated mocked provider: prepare a visual position preview and inspect existing results. No model has been saved." },
          { type: "tool_result", name: "prepare_position_preview", ok: true, result: { kind: "position_preview", projectId: 793, revisionId: 103, componentId: p.selected_ids[0], before, after, documentHash: saved.documentHash, requiresApproval: true, saved: false } },
          { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "results", href: "/projects/793/workspace", projectId: 793, revisionId: 103, componentIds: p.selected_ids, executed: false } },
          { type: "tool_result", name: "navigate", ok: true, result: { kind: "navigation", destination: "diagnostics", href: "/diagnostics", executed: false } },
        ];
        const task = { id: p.request_id, request: p, status: "SUCCEEDED", model: p.model, reply: events[1].text, events }; mockedTasks = [task];
        return route.fulfill({ contentType: "text/event-stream", body: [...events, { type: "task", task }].map(e => "data: "+JSON.stringify(e)+"\n\n").join("") });
      }
      if (!["GET", "HEAD", "OPTIONS"].includes(req.method()) && !url.pathname.endsWith("/api/assistant/context")) { forbidden.push(req.method()+" "+url.pathname); return route.abort(); }
      return route.continue();
    });
    await page.goto("/projects/793/workspace");
    await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 90000 });
    const source = await page.request.post("/local-api/api/assistant/context", { data: { project_id: 793, revision_id: 103, page: "/projects/793/workspace", selected_ids: [], dirty: false } });
    expect(source.ok()).toBe(true); const saved = (await source.json()).project;
    const id: string = saved.drawingReferences[0].componentId;
    await page.evaluate(id => window.dispatchEvent(new CustomEvent("geoai:inspect-component", { detail: { projectId: 793, revisionId: 103, componentIds: [id] } })), id);
    await expect(page.getByLabel("Component edit form")).toBeVisible();
    await page.getByRole("button", { name: "StruvoCivil Assistant", exact: true }).click();
    const assistant = page.getByRole("complementary", { name: "StruvoCivil Assistant" });
    await expect(assistant).toContainText("1 selected");
    await assistant.getByRole("textbox").fill("Preview a small East move for my selected component, then show saved results.");
    await assistant.getByRole("button", { name: "Send", exact: true }).click();
    await expect(assistant.getByRole("button", { name: "Review visual preview in editor" })).toBeEnabled();
    await assistant.getByRole("button", { name: "Review visual preview in editor" }).click();
    await expect(assistant.getByRole("status")).toContainText("Visual preview shown", { timeout: 10000 });
    await page.screenshot({ path: evidence+`preview-${width}.png` });
    await assistant.getByRole("button", { name: "Close site assistant" }).click();
    await expect(page.getByLabel("Component edit form")).toContainText("Edit preview · not applied");
    await page.screenshot({ path: evidence+`editor-preview-${width}.png` });
    await page.getByLabel("Component edit form").getByRole("button", { name: "Cancel", exact: true }).click();
    await page.getByRole("button", { name: "StruvoCivil Assistant", exact: true }).click();
    await assistant.getByRole("button", { name: "Open results", exact: true }).click();
    await assistant.getByRole("button", { name: "Close site assistant" }).click();
    await expect(page.getByRole("region", { name: "Guided Analysis", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "StruvoCivil Assistant", exact: true }).click();
    await assistant.getByRole("button", { name: "Open diagnostics", exact: true }).click();
    await expect(page).toHaveURL(/\/diagnostics$/); await expect(assistant).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
    await page.screenshot({ path: evidence+`navigation-${width}.png` });
    expect(turns).toBe(1); expect(errors).toEqual([]); expect(forbidden).toEqual([]);
    writeFileSync(evidence+`preview-navigation-${width}.json`, JSON.stringify({ width, height: 900, automated_mock_provider_only: true, actual_saved_project: 793, revision: 103, component: id, preview_shown: true, applied: false, saved: false, analysis_executed: false, navigation: ["results", "diagnostics"], forbidden, errors, turns, inference_requests: 0 }, null, 2));
  });
}
