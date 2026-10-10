import { expect, test, type Locator } from "@playwright/test";

// Isolated API fixtures exercise the real dashboard and CSS without depending
// on the developer's saved projects or changing any backend data.
const projects = Array.from({ length: 12 }, (_, index) => ({
  id: index + 1,
  name: index === 0 ? "Latest bridge" : `Saved road ${index + 1}`,
  project_type: index === 0 ? "bridge" : "road",
  location_name: "River crossing",
  folder_id: null,
  status: "draft",
  units: "metric",
  center_lat: 12,
  center_lng: 77,
  boundary_geojson: null,
  alignment_geojson: null,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: `2026-09-${String(30 - index).padStart(2, "0")}T00:00:00Z`,
  disclaimer: "",
}));

async function expectInsideViewport(locator: Locator) {
  await expect(locator).toBeVisible();
  const bounds = await locator.boundingBox();
  expect(bounds).not.toBeNull();
  const viewport = locator.page().viewportSize()!;
  // Fractional CSS positions are rounded differently by headless Chromium.
  // A 1px tolerance still catches meaningful overflow or clipped controls.
  const tolerance = 1;
  expect(bounds!.x).toBeGreaterThanOrEqual(-tolerance);
  expect(bounds!.y).toBeGreaterThanOrEqual(-tolerance);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(viewport.width + tolerance);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(viewport.height + tolerance);
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
  for (const populated of [false, true]) {
    test(`dashboard ${populated ? "with saved concepts" : "empty"} fits ${viewport.width}x${viewport.height} without page scrolling`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.route("**/api/projects", route => route.fulfill({ json: populated ? projects : [] }));
      await page.route("**/api/project-folders", route => route.fulfill({ json: [] }));
      await page.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Your projects", exact: true })).toBeVisible();
      await expect(page.getByLabel("Loading saved concepts")).toHaveCount(0);
      for (const name of ["Your projects", "Recent projects"]) {
        await expectInsideViewport(page.getByRole("heading", { name, exact: true }));
      }
      await expectInsideViewport(page.locator(".hub-toolbar").getByRole("button", { name: "New Project", exact: true }));
      await expectInsideViewport(page.getByRole("link", { name: "Open sandbox", exact: true }));
      if (populated) {
        await expect(page.locator(".hub-featured")).toHaveCount(0);
        // Overview intentionally shows six recent projects; the library retains all work.
        await expect(page.locator(".hub-concept-card")).toHaveCount(6);
        await expect(page.getByRole("heading", { name: "Latest bridge" })).toHaveCount(1);
        await expectInsideViewport(page.getByRole("heading", { name: "Latest bridge" }));
        await expectInsideViewport(page.locator(".hub-concept-card").first().getByRole("link", { name: "Open workspace" }));
        const navigation = page.getByRole("navigation", {name:"Dashboard navigation"});
        await navigation.getByRole("button", {name:"Projects", exact:true}).click();
        await expect(page.locator(".hub-concept-card")).toHaveCount(projects.length);
        const search = page.getByRole("searchbox", {name:"Search projects"});
        await search.fill("bridge");
        await expect(page.locator(".hub-concept-card")).toHaveCount(1);
        await search.clear();
        await expect(page.locator(".hub-concept-card")).toHaveCount(projects.length);
        await navigation.getByRole("button", {name:"Overview", exact:true}).click();
        await expect(page.locator(".hub-concept-card")).toHaveCount(6);
      } else {
        await expectInsideViewport(page.getByRole("heading", { name: "No projects yet" }));
      }
      const dimensions = await page.evaluate(() => ({
        height: window.innerHeight,
        width: window.innerWidth,
        bodyHeight: document.body.scrollHeight,
        documentHeight: document.documentElement.scrollHeight,
        bodyWidth: document.body.scrollWidth,
        documentWidth: document.documentElement.scrollWidth,
        // Overview itself must fit; scrollable libraries and folders are allowed.
        mainHeight: document.querySelector(".hub-main")!.clientHeight,
        mainScrollHeight: document.querySelector(".hub-main")!.scrollHeight,
      }));
      expect(dimensions.bodyHeight).toBeLessThanOrEqual(dimensions.height);
      expect(dimensions.documentHeight).toBeLessThanOrEqual(dimensions.height);
      expect(dimensions.bodyWidth).toBeLessThanOrEqual(dimensions.width);
      expect(dimensions.documentWidth).toBeLessThanOrEqual(dimensions.width);
      expect(dimensions.mainScrollHeight).toBeLessThanOrEqual(dimensions.mainHeight);
      await page.screenshot({ path: `test-results/dashboard-${viewport.width}-${populated ? "saved" : "empty"}.png` });
    });
  }
}
