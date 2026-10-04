import { expect, test } from "@playwright/test";

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
  test(`new project fits ${viewport.width}×${viewport.height} and only assets scroll`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/projects/new");
    const create = page.getByRole("button", { name: "CREATE PROJECT", exact: true });
    await expect(create).toBeVisible();
    await expect(create).toBeDisabled();
    await page.getByLabel("PROJECT NAME", { exact: true }).fill("NH-48 Junction Flyover");
    await expect(create).toBeEnabled();
    await page.screenshot({ path: `test-results/new-project-${viewport.width}.png` });
    await page.getByLabel("Search asset types", { exact: true }).fill("bridge");
    await expect(page.getByRole("radio", { name: /Highway Bridge/ })).toBeVisible();
    await expect(page.getByRole("radio", { name: /Flyover \/ Overpass/ })).toBeVisible();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("Enter");
    await expect(page.getByRole("radio", { checked: true })).toHaveCount(1);
    await page.keyboard.press("Control+k");
    await expect(page.getByLabel("Search asset types", { exact: true })).toBeFocused();
    await page.keyboard.press("Escape");
    const list = page.getByRole("radiogroup", { name: "Asset types" });
    const box = await list.boundingBox();
    expect(box).not.toBeNull();
    await page.mouse.move(box!.x + box!.width / 2, box!.y + box!.height / 2);
    await page.mouse.wheel(0, 2500);
    await expect.poll(() => list.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
    await expect(create).toBeVisible();
    const dimensions = await page.evaluate(() => ({ width: window.innerWidth, height: window.innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight, y: window.scrollY }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.width);
    expect(dimensions.scrollHeight).toBe(dimensions.height);
    expect(dimensions.y).toBe(0);
    const cta = await create.boundingBox();
    expect(cta!.y + cta!.height).toBeLessThan(viewport.height);
  });
}

test("search crosses categories and reference assets state their limits", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/projects/new");
  await page.getByRole("button", { name: /Energy/ }).click();
  await page.getByLabel("Search asset types", { exact: true }).fill("custom");
  await page.getByRole("radio", { name: /Custom Asset/ }).click();
  await expect(page.getByText("Site reference only. Engineering generation and asset-specific quantities are unavailable.")).toBeVisible();
  await page.getByLabel("Search asset types", { exact: true }).fill("zzzzzzzzzzz");
  await expect(page.getByText(/No assets match/)).toBeVisible();
  await expect(page.getByRole("button", { name: "CREATE PROJECT", exact: true })).toBeVisible();
});

test("creation retains payload and guards duplicate submissions and retry", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  let calls = 0;
  let payload: Record<string, unknown> = {};
  await page.route("**/api/projects", async (route) => {
    if (route.request().method() !== "POST") return route.fulfill({ json: [] });
    calls++;
    payload = route.request().postDataJSON();
    await new Promise((resolve) => setTimeout(resolve, 250));
    await route.fulfill({ status: calls === 1 ? 422 : 201, json: calls === 1 ? { detail: "Please retry creation" } : { id: 987654, ...payload } });
  });
  await page.goto("/projects/new");
  await page.getByLabel("PROJECT NAME", { exact: true }).fill("  Bridge test  ");
  await page.getByLabel("Search asset types", { exact: true }).fill("Bridge / Viaduct");
  await page.getByRole("radio", { name: /Bridge \/ Viaduct/ }).click();
  await page.getByLabel("UNITS", { exact: true }).selectOption("indian");
  const create = page.getByRole("button", { name: "CREATE PROJECT", exact: true });
  await create.dblclick();
  await expect(page.getByRole("alert").filter({ hasText: "Please retry creation" }).first()).toBeVisible();
  expect(calls).toBe(1);
  expect(payload).toEqual({ name: "Bridge test", project_type: "bridge", units: "indian", location_name: "", center_lat: 12.9716, center_lng: 77.5946, boundary_geojson: null, alignment_geojson: null });
  await create.click();
  await expect(page).toHaveURL(/\/projects\/987654\/workspace/);
  expect(calls).toBe(2);
});
