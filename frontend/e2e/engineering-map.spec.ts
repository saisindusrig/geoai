import { expect, test } from "@playwright/test";

test("project workspace exposes context, data and scene controls without clutter", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  await page.goto("/projects/5/workspace");
  await expect(page.locator(".cesium-widget canvas")).toBeVisible({ timeout: 60000 });
  await page.getByLabel("Search scene components").fill("pier_1");
  await expect(page.getByRole("button", { name: "pier_1", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "deck-slab", exact: true })).toHaveCount(0);
  await page.getByLabel("Search scene components").fill("no-matching-component");
  await expect(page.getByText("No matching components.")).toBeVisible();
  await page.getByLabel("Search scene components").clear();
  await expect(page.getByText("Scale visual", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Visual reference — not for quantity takeoff.", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Site data/ })).toHaveCount(0);
  await page.evaluate(() => window.dispatchEvent(new Event("geoai:open-site-data")));
  await expect(page.getByRole("heading", { name: "Data & placement" })).toBeVisible();
  await page.screenshot({ path: "test-results/project-site-data.png" });
  await page.getByRole("button", { name: "Scene / Sun study", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Data & placement" })).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("region", { name: "Sun study", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Scene / Sun study", exact: true }).click();
  await expect(page.getByLabel("Terrain elevation")).toBeChecked();
  const sceneBounds = await page.getByRole("region", { name: "Sun study", exact: true }).boundingBox();
  const toolbarBounds = await page.getByRole("button", { name: "Scene / Sun study", exact: true }).boundingBox();
  expect(sceneBounds!.y).toBeGreaterThan(toolbarBounds!.y + toolbarBounds!.height);
  await page.getByLabel("Global 3D buildings").check();
  await expect(page.getByLabel("Global 3D buildings")).toBeChecked();
  await expect(page.getByRole("region", {name:"Sun study",exact:true}).getByText("Unavailable or loading", {exact:true}).first()).toBeVisible();
  await page.screenshot({ path: "test-results/project-scene-controls.png" });
  await page.getByRole("button", { name: "Search workspace", exact: true }).click();
  await expect(page.getByRole("region", { name: "Sun study", exact: true })).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "Search workspace query" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Scene / Sun study", exact: true }).click();
  await page.getByRole("button", { name: "Close sun study" }).click();
  await page.getByRole("button", { name: "Draw site boundary", exact: true }).click();
  await expect(page.getByLabel("Drawing tool options")).toBeVisible();
  await expect(page.getByRole("button", { name: "Draw site boundary", exact: true })).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Escape");
  await expect(page.getByLabel("Drawing tool options")).toHaveCount(0);
  await page.screenshot({ path: "test-results/project-workspace-ui.png" });
  expect(errors).toEqual([]);
});

test("terrain provenance is explicit and sun controls use editable timezone", async ({ page }) => {
  const errors: string[] = [];
  const projectRequests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => { if (/\/api\/projects\/999999/.test(request.url())) projectRequests.push(request.url()); });
  await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  await page.goto("/projects/999999/workspace?local=1");
  await page.getByRole("button", { name: /^building \d/i }).click();
  const grid = page.locator('main[aria-label="Layout scene"] canvas').first();
  await expect(grid).toHaveAttribute("data-sandbox-ready", "true");
  const bounds = (await grid.boundingBox())!;
  await page.mouse.click(bounds.x + bounds.width * .5, bounds.y + bounds.height * .6);
  await expect(page.getByLabel("Component name")).toHaveValue("building 1");
  await page.getByRole("button", { name: "Map", exact: true }).click();
  await expect(page.locator(".cesium-widget canvas")).toBeVisible({ timeout: 60000 });
  await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 60000 });
  await expect(page.getByText(/^Origin 12\.9724/)).toBeVisible();
  await page.getByRole("button", { name: "Scene / Sun study", exact: true }).click();
  await page.getByRole("tab", { name: "Sun", exact: true }).click();
  await page.getByLabel("Sun timezone").fill("Asia/Kolkata");
  await page.getByLabel("Sun timezone").press("Tab");
  await page.getByLabel("Sun local date and time").fill("2026-06-21T12:00");
  await expect(page.getByLabel("Sun UTC time")).toHaveValue("2026-06-21T06:30:00.000Z");
  await page.getByRole("button", { name: "Enable sun lighting & shadows", exact: true }).click();
  await expect(page.getByRole("button", { name: "Enable sun lighting & shadows", exact: true })).toHaveCount(0);
  await page.getByRole("tab", { name: "Scene", exact: true }).click();
  // Presets are the current scene controls; detailed quality selectors were removed.
  await page.getByRole("button", {name:"Realistic", exact:true}).click();
  await expect(page.getByRole("button", {name:"Realistic", exact:true})).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", {name:"Engineering", exact:true}).click();
  await expect(page.getByRole("button", {name:"Engineering", exact:true})).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("Terrain elevation").check();
  await expect(page.getByRole("region", {name:"Sun study", exact:true}).getByText("Unavailable or loading", {exact:true}).first()).toBeVisible();
  await page.getByRole("tab", { name: "Sun", exact: true }).click();
  await expect(page.getByLabel("Sun UTC time")).toHaveValue("2026-06-21T06:30:00.000Z");
  await page.getByRole("button", {name:"Enable sun lighting & shadows", exact:true}).click();
  await expect(page.getByText("Azimuth · from north", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Play day", exact: true }).click();
  await expect(page.getByRole("button", { name: "Pause", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await page.screenshot({ path: "test-results/engineering-sun-study.png" });
  await page.getByRole("button", { name: "Scene / Sun study", exact: true }).click();
  await page.screenshot({ path: "test-results/engineering-shadow-scene.png" });
  await expect.poll(async () => {
    const raw = await page.locator(".cesium-widget canvas").getAttribute("data-scene-camera");
    if (!raw) return false;
    const camera = JSON.parse(raw) as { lng: number; lat: number; height: number; globe: boolean };
    return camera.globe && Math.abs(camera.lng - 77.598343) < .01 && Math.abs(camera.lat - 12.97244) < .01 && camera.height > 0 && camera.height < 10000;
  }).toBe(true);
  expect(projectRequests).toEqual([]);
  expect(errors).toEqual([]);
});





