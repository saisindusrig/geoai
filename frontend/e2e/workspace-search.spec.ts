import { expect, test } from "@playwright/test";

test("scene filtering and workspace place search remain independently usable", async ({ page }) => {
  await page.setViewportSize({ width: 1714, height: 982 });
  await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  await page.route("**/api/geocode?q=*", route => route.fulfill({ json: { results: [{ name: "Bengaluru test location", lat: 12.97, lng: 77.59, provider: "test" }] } }));
  await page.goto("/projects/5/workspace");
  const sceneQuery = page.getByLabel("Search scene components");
  await expect(sceneQuery).toBeVisible({ timeout: 60000 });
  await sceneQuery.fill("barrier");
  await expect(page.getByRole("button", { name: "barrier_left", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "barrier_right", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "deck-slab", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "barrier_left", exact: true }).click();
  await expect(page.getByText("1 selected · Shift for range", { exact: true })).toBeVisible();
  await sceneQuery.fill("no-such-object-xyz");
  await expect(page.getByText("No matching components.")).toBeVisible();
  await sceneQuery.clear();

  await page.getByRole("button", { name: "Search workspace", exact: true }).click();
  const search = page.getByRole("region", { name: "Workspace search" });
  const query = search.getByRole("textbox", { name: "Search workspace query" });
  await query.fill("100, 20");
  await query.press("Enter");
  await expect(search.getByRole("alert")).toContainText("Latitude must");
  await query.fill("Bengaluru");
  await query.press("Enter");
  await expect(search.getByLabel("Search results").getByRole("button")).toContainText("Bengaluru test location");
  await page.screenshot({ path: "test-results/workspace-search-places.png" });
  await query.press("ArrowDown");
  await query.press("Enter");
  await expect(search).toHaveCount(0);
  await expect.poll(async () => {
    const raw = await page.locator(".cesium-widget canvas").getAttribute("data-scene-camera");
    if (!raw) return false;
    const camera = JSON.parse(raw) as { lng: number; lat: number };
    return Math.abs(camera.lng - 77.59) < .01 && Math.abs(camera.lat - 12.97) < .01;
  }).toBe(true);
  await expect(page.getByText("1 selected · Shift for range", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Search workspace", exact: true }).click();
  await expect(query).toHaveValue("");
  await query.press("Escape");
  await expect(search).toHaveCount(0);
});
