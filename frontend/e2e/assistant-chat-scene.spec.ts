import { expect, test } from "@playwright/test";
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
// Configured world data credentials must never appear in a trace archive.
test.use({ trace: "off" });

test("honest free-form chat persists, scrolls and keeps the keyboard composer visible", async ({ page }) => {
  await page.route("**/api/geocode/map-runtime-config", r => r.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  const result = await page.request.post(`${api}/api/projects`, { data: { name: `Chat acceptance ${Date.now()}`, project_type: "building", center_lng: 77.5946, center_lat: 12.9716 } });
  expect(result.ok()).toBeTruthy(); const project = await result.json();
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto(`/projects/${project.id}/workspace`);
  await page.getByRole("tab", { name: "Assistant", exact: true }).click();
  await expect(page.getByRole("region", { name: "Empty project starter" })).toHaveCount(0);
  await expect(page.getByText("Draw an alignment or generate a concept", { exact: true })).toHaveCount(0);
  const input = page.getByRole("textbox", { name: "Project message" });
  await expect(input).toBeEnabled();
  await input.fill("What loads are safe?"); await input.press("Shift+Enter");
  await expect(input).toHaveValue("What loads are safe?\n");
  await input.press("Enter");
  await expect(page.getByRole("article", { name: "Your message" })).toContainText("What loads are safe?");
  await expect(page.getByRole("article", { name: "Your message" }).getByRole("alert")).toContainText("No inference was sent");
  await expect(page.getByRole("button", { name: "Retry assistant" })).toHaveCount(0);
  await page.reload(); await page.getByRole("tab", { name: "Assistant", exact: true }).click();
  await expect(page.getByRole("article", { name: "Your message" })).toContainText("What loads are safe?");
  // Long saved text uses the transcript's scroll area, leaving the composer fixed.
  await input.fill("Explain site limitations. ".repeat(100)); await input.press("Enter");
  await expect(page.getByRole("article", { name: "Your message" })).toHaveCount(2);
  const log = page.getByRole("log", { name: "Conversation messages" });
  await expect.poll(() => log.evaluate(n => n.scrollHeight > n.clientHeight)).toBe(true);
  await expect(input).toBeInViewport();
  await page.screenshot({ path: "test-results/platform-chat-after-1920.png" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(input).toBeInViewport();
  await page.screenshot({ path: "test-results/platform-chat-after-1440.png" });
});

for (const mode of ["token-free", "configured-world"] as const) test(`low-angle surface orbit and Fit project recover: ${mode}`, async ({ page }) => {
  test.skip(mode === "configured-world" && !process.env.GEOAI_TEST_CONFIGURED_TERRAIN_URL, "Existing world-data connection not supplied; no credentials invented.");
  let runtime = { cesium_ion_token: null as string | null, google_maps_api_key: null as string | null };
  if (mode === "configured-world") {
    const response = await page.request.get(`${process.env.GEOAI_TEST_CONFIGURED_TERRAIN_URL}/api/geocode/map-runtime-config`);
    expect(response.ok()).toBeTruthy(); runtime = await response.json();
    expect(!!runtime.cesium_ion_token).toBeTruthy();
  }
  await page.route("**/api/geocode/map-runtime-config", r => r.fulfill({ json: runtime }));
  const result = await page.request.post(`${api}/api/projects`, { data: { name: `Scene acceptance ${mode} ${Date.now()}`, project_type: "building", center_lng: 77.5946, center_lat: 12.9716 } });
  expect(result.ok()).toBeTruthy(); const project = await result.json();
  await page.goto(`/projects/${project.id}/workspace`);
  const canvas = page.locator(".cesium-widget canvas");
  await expect(canvas).toHaveAttribute("data-camera-surface-mode", "surface", { timeout: 60000 });
  if (mode === "configured-world") {
    await expect(canvas).toHaveAttribute("data-terrain-source", "loaded-terrain", { timeout: 60000 });
    await expect.poll(async () => Number(await canvas.getAttribute("data-camera-surface-floor")), { timeout: 60000 }).toBeGreaterThan(20);
  } else await expect(canvas).toHaveAttribute("data-terrain-source", "ellipsoid-reference");
  await expect(page.getByRole("button", { name: "Negative Z axis view" })).toBeDisabled();
  await page.getByRole("button", { name: "Positive X axis view" }).click();
  await expect.poll(async () => Math.abs(JSON.parse(await canvas.getAttribute("data-scene-camera") || "{}").pitch + Math.PI / 36), { timeout: 15000 }).toBeLessThan(.06);
  const bounds = (await canvas.boundingBox())!;
  await page.mouse.move(bounds.x + bounds.width * .5, bounds.y + bounds.height * .5);
  await page.mouse.down({ button: "middle" });
  await page.mouse.move(bounds.x + bounds.width * .6, bounds.y + bounds.height * .8, { steps: 12 });
  await page.mouse.up({ button: "middle" });
  await expect.poll(async () => Number(await canvas.getAttribute("data-camera-height")) >= Number(await canvas.getAttribute("data-camera-surface-floor")) - .05).toBe(true);
  await page.screenshot({ path: `test-results/platform-scene-low-angle-${mode}.png` });
  await page.getByRole("button", { name: "Fit project", exact: true }).click();
  await expect.poll(async () => {
    const pose = JSON.parse(await canvas.getAttribute("data-scene-camera") || "{}");
    return pose.height > 100 && pose.pitch < -.7;
  }).toBe(true);
  await expect(page.locator(".cesium-widget-errorPanel")).toHaveCount(0);
  await page.screenshot({ path: `test-results/platform-scene-recovered-${mode}.png` });
});
