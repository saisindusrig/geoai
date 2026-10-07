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
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(viewport.width);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(viewport.height);
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
  for (const populated of [false, true]) {
    test(`dashboard ${populated ? "with saved concepts" : "empty"} fits ${viewport.width}x${viewport.height} without page scrolling`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.route("**/api/projects", route => route.fulfill({ json: populated ? projects : [] }));
      await page.route("**/api/project-folders", route => route.fulfill({ json: [] }));
      await page.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Your concepts", exact: true })).toBeVisible();
      await expect(page.getByLabel("Loading saved concepts")).toHaveCount(0);
      for (const name of ["Your concepts", "Start a new concept"]) {
        await expectInsideViewport(page.getByRole("heading", { name, exact: true }));
      }
      await expectInsideViewport(page.locator(".hub-toolbar").getByRole("link", { name: "New concept", exact: true }));
      await expectInsideViewport(page.getByRole("link", { name: "Open sandbox", exact: true }));
      if (populated) {
        await expect(page.locator(".hub-featured")).toHaveCount(0);
        await expect(page.locator(".hub-concept-card")).toHaveCount(projects.length);
        await expect(page.getByRole("heading", { name: "Latest bridge" })).toHaveCount(1);
        await expectInsideViewport(page.getByRole("heading", { name: "Latest bridge" }));
        await expectInsideViewport(page.locator(".hub-concept-card").first().getByRole("link", { name: "Open workspace" }));
        await page.getByLabel("Filter by concept type").selectOption("bridge");
        await expect(page.locator(".hub-concept-card")).toHaveCount(1);
        await page.getByLabel("Filter by concept type").selectOption("all");
        await expect(page.locator(".hub-concept-card")).toHaveCount(projects.length);
      } else {
        await expectInsideViewport(page.getByRole("heading", { name: "No saved concepts yet" }));
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
