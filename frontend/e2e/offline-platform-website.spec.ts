import { expect, test } from "@playwright/test";
import { reviewPlatform } from "./helpers/platform-review-workflow";
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

test("fresh website boundary → message → review → approved platform → edit/save/reload", async ({ page }) => {
  test.slow();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route("**/api/geocode/map-runtime-config", r => r.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  const created = await page.request.post(`${api}/api/projects`, { data: { name: `Offline website platform ${Date.now()}`, project_type: "building", center_lng: 77, center_lat: 12 } });
  expect(created.ok()).toBeTruthy();
  const project = await created.json();
  await page.goto(`/projects/${project.id}/workspace`);
  const canvas = page.locator(".cesium-widget canvas");
  await expect(canvas).toHaveAttribute("data-scene-camera", /.+/, { timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.getByRole("button", { name: "Draw site boundary", exact: true }).click();
  const b = (await canvas.boundingBox())!;
  for (const [x, y] of [[.4, .4], [.65, .4], [.65, .65], [.4, .65]]) await page.mouse.click(b.x + b.width * x, b.y + b.height * y);
  await page.keyboard.press("Enter");
  const saved = page.waitForResponse(r => r.url().endsWith(`/api/projects/${project.id}`) && r.request().method() === "PUT" && r.ok());
  await page.getByRole("button", { name: "Save boundary", exact: true }).click();
  await saved;
  await page.getByRole("tab", { name: "Assistant", exact: true }).click();
  await expect(page.getByText("Offline demo · supported platform template", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Refresh site", exact: true }).click();
  await expect(page.getByLabel("Site readiness")).toContainText("Current", { timeout: 60000 });
  // A normal message must retain the exact current pair and never POST a selection.
  let selectionWrites = 0;
  page.on("request", r => { if (r.method() === "POST" && /\/site-selections$/.test(r.url())) selectionWrites++; });
  await page.getByRole("button", { name: "Use platform example", exact: true }).click();
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByRole("button", { name: "Review proposal", exact: true })).toBeVisible({ timeout: 60000 });
  expect(selectionWrites).toBe(0);
  await page.screenshot({ path: "test-results/platform-website-message-1440.png" });
  await reviewPlatform(page, project.id);
});

for (const mode of ["missing-profile", "unsupported-dimensions", "too-small", "rejected"] as const) test(`offline platform fails closed: ${mode}`, async ({ page }) => {
  const delta = mode === "too-small" ? .00001 : .002;
  const boundary = { type: "Polygon", coordinates: [[[77,12],[77+delta,12],[77+delta,12+delta],[77,12+delta],[77,12]]] };
  await page.route("**/api/geocode/map-runtime-config", r => r.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  const created = await page.request.post(`${api}/api/projects`, { data: { name: `Blocked platform ${mode} ${Date.now()}`, project_type: "building", center_lng: 77, center_lat: 12, boundary_geojson: boundary } });
  expect(created.ok()).toBeTruthy();
  const project = await created.json();
  await page.goto(`/projects/${project.id}/workspace`);
  await page.getByRole("tab", { name: "Assistant", exact: true }).click();
  await expect(page.getByRole("button", { name: "Use platform example" })).toBeVisible();
  if (mode !== "missing-profile") {
    await page.getByRole("button", { name: "Refresh site", exact: true }).click();
    await expect(page.getByLabel("Site readiness")).toContainText("Current", { timeout: 60000 });
  }
  await page.getByRole("button", { name: "Use platform example" }).click();
  if (mode === "unsupported-dimensions") {
    const input = page.getByRole("textbox", { name: "Project message" });
    await input.fill((await input.inputValue()).replace("5 m", "6 m"));
  }
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  if (mode === "missing-profile") {
    await expect(page.getByText("Save the current site boundary and Refresh site, then send a new request. No model was generated.")).toBeVisible({ timeout: 60000 });
  } else if (mode === "unsupported-dimensions") {
    await expect(page.getByText(/This demo supports only the 5 m/)).toBeVisible({ timeout: 60000 });
  } else if (mode === "too-small") {
    await expect(page.getByText(/The fixed 5 m × 3 m platform does not fit/)).toBeVisible({ timeout: 60000 });
  } else {
    await page.getByRole("button", { name: "Review proposal", exact: true }).click({ timeout: 60000 });
    await page.getByRole("button", { name: "Reject proposal", exact: true }).click();
    await expect(page.getByLabel("Proposal review")).toContainText("REJECTED");
  }
  await expect(page.getByRole("button", { name: "Approve & Generate 3D", exact: true })).toHaveCount(0);
  const scenarios = await (await page.request.get(`${api}/api/projects/${project.id}/scenarios`)).json();
  for (const scenario of scenarios.scenarios) {
    const response = await page.request.get(`${api}/api/projects/${project.id}/scenarios/${scenario.scenario_id}/model-revisions`);
    expect(response.ok()).toBeTruthy();
    const revisions = await response.json();
    expect(revisions.revisions).toEqual([]);
  }
  await page.screenshot({ path: `test-results/platform-blocked-${mode}.png` });
});
