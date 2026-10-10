import { expect, test } from "@playwright/test";

const unique = Date.now();

async function dismissNavDrawer(page: import("@playwright/test").Page) {
  const overlay = page.locator(".modal-overlay");
  if (!(await overlay.isVisible().catch(() => false))) return;

  // Sidebar (248px) sits above the header toggle — click the overlay to the right.
  await overlay.click({ position: { x: 320, y: 240 } });
  await overlay.waitFor({ state: "hidden", timeout: 10_000 });
}

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
test.describe(`Critical path ${viewport.width}px`, () => {
  test.use({ viewport });
  test("create project → first-run actions → 3D site tools → estimate", async ({ page }) => {
    const projectName = `E2E Project ${unique}-${viewport.width}`;
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });
    await dismissNavDrawer(page);

    await page.getByRole("button", { name: "New Project", exact: true }).first().click();
    await page.getByLabel(/Project name/i).fill(projectName);
    await expect(page.getByRole("button", { name: /Create Project/i })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: /Create Project/i }).click();

    await expect(page).toHaveURL(/\/projects\/\d+\/workspace/, { timeout: 30_000 });
    const starter = page.getByRole("region", { name: "Empty project starter" });
    await expect(starter).toHaveCount(1, { timeout: 30_000 });
    await expect(starter).toBeVisible();
    await expect(page.getByText("Start anywhere.")).toBeVisible();
    const canvas = page.locator(".cesium-widget canvas");
    await expect(canvas).toBeVisible({ timeout: 30_000 });
    await expect(canvas).toHaveAttribute("data-scene-camera", /.+/, { timeout: 30_000 });
    await page.screenshot({ path: `.cache/empty-project-workspace-${viewport.width}.png` });
    await page.getByRole("button", {name:"Measure", exact:true}).click();
    await expect(starter).toHaveCount(0);
    await expect(page.getByLabel("Measurement tools")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByLabel("Measurement tools")).toHaveCount(0);
    await expect(starter).toBeVisible();
    await starter.getByRole("button", {name:"Ask GeoAI", exact:true}).click();
    await expect(page.getByRole("tab", {name:"Assistant", exact:true})).toHaveAttribute("aria-selected", "true");
    await expect(starter).toHaveCount(0);
    // Reload to exercise the other first-run action, without sending an AI message.
    await page.reload();
    await expect(starter).toBeVisible({ timeout: 30_000 });
    await expect(canvas).toHaveAttribute("data-scene-camera", /.+/, { timeout: 30_000 });
    await starter.getByRole("button", {name:"Draw / select site", exact:true}).click();
    await expect(starter).toHaveCount(0);
    await expect(page.getByRole("button", {name:"Draw site boundary", exact:true})).toHaveAttribute("aria-pressed", "true");
    const drawing = page.getByLabel("Drawing tool options");
    await expect(drawing).toBeVisible();
    const bounds = (await canvas.boundingBox())!;
    // Pick an unobstructed point in the 3D canvas; the existing drawing tool records it.
    await page.mouse.click(bounds.x + bounds.width * .8, bounds.y + bounds.height * .7);
    await expect(drawing.getByText("1 vertices", {exact:true})).toBeVisible();
    await page.screenshot({path:`.cache/site-tools-${viewport.width}.png`});
    await page.keyboard.press("Escape");
    await expect(drawing).toHaveCount(0);
    await expect(canvas).toBeVisible();

    const workspaceUrl = page.url();
    const projectBase = workspaceUrl.replace(/\/workspace.*/, "");
    await page.goto(`${projectBase}/estimate`);
    await expect(page).toHaveURL(/\/projects\/\d+\/estimate/, { timeout: 30_000 });
    await expect(
      page.getByText(/BOQ|Estimate|Bill of quantities|No estimate/i).first(),
    ).toBeVisible({ timeout: 30_000 });
    expect(errors).toEqual([]);
  });
});
}

test("populated and public-demo workspaces keep map/editor tools without a starter", async ({page}) => {
  await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  for (const url of ["/projects/5/workspace", "/projects/5/workspace?demo=1"]) {
    await page.goto(url);
    await expect(page.locator(".cesium-widget canvas")).toBeVisible({timeout:30000});
    await expect(page.getByRole("button", {name:"Select object", exact:true})).toBeVisible();
    await expect(page.getByRole("tab", {name:"Layers", exact:true})).toBeVisible();
    if (!url.includes("demo=1")) await expect(page.getByLabel("Search scene components")).toBeVisible({timeout:30000});
    else await expect(page.getByText("Reference model", {exact:true})).toBeVisible();
    await expect(page.getByRole("region", {name:"Empty project starter"})).toHaveCount(0);
  }
});
