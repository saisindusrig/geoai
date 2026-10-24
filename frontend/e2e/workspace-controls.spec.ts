import { test, expect } from "@playwright/test";
for (const width of [1280, 1600]) test(`workflow and camera controls ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  const writes: string[] = [];
  await page.route("**/*", async route => {
    const req = route.request(), url = new URL(req.url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
    if (!["GET", "HEAD", "OPTIONS"].includes(req.method())) { writes.push(req.method()+" "+url.pathname); return route.abort(); }
    return route.continue();
  });
  await page.goto("/projects/805/workspace");
  await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 90000 });
  const workflow = page.getByLabel("Design workflow");
  const step = (name: string) => workflow.getByRole("button", { name, exact: true });
  await expect(step("3 Review 3D")).toHaveAttribute("aria-current", "step");
  for (const name of ["1 Site", "3 Review 3D", "4 Edit", "5 Analyze / Results", "6 Review"]) {
    await step(name).click();
    await expect(step(name)).toHaveAttribute("aria-current", "step");
    await expect(workflow.locator('[aria-current="step"]')).toHaveCount(1);
  }
  // Changes made through the side tabs must also update the workflow.
  await page.getByRole("tab", { name: "Inspect", exact: true }).click();
  await expect(step("4 Edit")).toHaveAttribute("aria-current", "step");
  await page.getByRole("button", { name: "Close inspector", exact: true }).click();
  await expect(step("3 Review 3D")).toHaveAttribute("aria-current", "step");
  await workflow.getByText("2 Create / Import", { exact: true }).click();
  await expect(workflow.getByRole("button", { name: "Import site geometry", exact: true })).toBeVisible();
  await expect(workflow.locator('[aria-current="step"]')).toHaveCount(1);
  await expect(workflow.getByText("2 Create / Import", { exact: true })).toHaveAttribute("aria-current", "step");
  await workflow.getByText("2 Create / Import", { exact: true }).click();
  const gizmo = page.getByRole("group", { name: "Camera orientation gizmo" });
  await expect(gizmo.getByText("Orientation", { exact: true })).toHaveCount(0);
  await expect(gizmo.getByText("Click an axis to align")).toHaveCount(0);
  const placement = await page.getByLabel("Viewport presentation").boundingBox();
  const viewport = await page.locator(".workspace-map-viewport").boundingBox();
  expect(placement!.x - viewport!.x).toBeLessThanOrEqual(16);
  expect(viewport!.y + viewport!.height - placement!.y - placement!.height).toBeLessThanOrEqual(16);
  const assistantButton = page.getByRole("button", { name: "StruvoCivil Assistant", exact: true });
  await expect(assistantButton).toHaveCount(1);
  expect(await assistantButton.evaluate(button => parseFloat(getComputedStyle(button).borderRadius))).toBeGreaterThan(20);
  const assistantBox = await assistantButton.boundingBox();
  expect(assistantBox!.y + assistantBox!.height).toBeLessThanOrEqual(900 - 60);
  await assistantButton.click();
  await expect(page.getByRole("complementary", { name: "StruvoCivil Assistant" })).toBeVisible();
  await page.getByRole("button", { name: "Close site assistant" }).click();
  await expect(gizmo.getByRole("button")).toHaveCount(6);
  await expect(gizmo.getByRole("button", { name: "Negative Z axis view" })).toBeDisabled();
  await gizmo.getByRole("button", { name: "Positive Z axis view" }).click();
  await page.waitForTimeout(1000);
  await gizmo.getByRole("button", { name: "Positive X axis view" }).click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `../docs/workspace-placement/workspace-${width}.png` });
  await gizmo.screenshot({ path: `../docs/workspace-placement/gizmo-${width}.png` });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  expect(writes).toEqual([]);
});
