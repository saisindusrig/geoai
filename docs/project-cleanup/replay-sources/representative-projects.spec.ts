import { test, expect } from "@playwright/test";
import { writeFileSync } from "node:fs";

test.skip(process.env.GEOAI_CLEANUP_ACCEPTANCE !== "true", "Requires the isolated cleanup acceptance database");
for (const projectId of [793, 794, 788, 802, 803, 804]) {
  test(`preserved project ${projectId}: render, select, inspector and analysis`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({json: {cesium_ion_token: null, google_maps_api_key: null}}));
    await page.goto(`/projects/${projectId}/workspace`);
    await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", {timeout: 60000});
    await page.getByRole("tab", {name: "Layers", exact: true}).click();
    await expect(page.getByRole("heading", {name: "Scene layers"})).toBeVisible();
    const row = page.locator('[id^="layer-row-"] button[aria-pressed]').first();
    await row.click();
    await expect(row).toHaveAttribute("aria-pressed", "true");
    await page.getByRole("tab", {name: "Inspect", exact: true}).click();
    await expect(page.getByRole("button", {name: "Fit selection", exact: true}).last()).toBeVisible();
    await page.getByRole("tab", {name: "Analysis", exact: true}).click();
    await page.screenshot({path: `../docs/project-cleanup/browser/project-${projectId}.png`});
    expect(errors).toEqual([]);
    writeFileSync(`../docs/project-cleanup/browser/project-${projectId}.json`, JSON.stringify({projectId, render: true, selection: true, inspector: true, analysis: true, errors}, null, 2));
  });
}

test.beforeEach(async ({request}) => { const response=await request.get('http://127.0.0.1:18001/__cleanup_session'); expect((await response.json()).mode).toBe('isolated-cleanup-20261015'); });
