import { test, expect } from "@playwright/test";
for (const width of [1280, 1600]) test(`one workspace assistant ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  const writes: string[] = [];
  await page.route("**/*", async route => {
    const req = route.request(), url = new URL(req.url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname)) return route.abort();
    if (!["GET", "HEAD", "OPTIONS"].includes(req.method())) { writes.push(req.method()+" "+url.pathname); return route.abort(); }
    return route.continue();
  });
  await page.addInitScript(() => localStorage.setItem("project-805-copilot-panel", "true"));
  await page.goto("/projects/805/workspace");
  const launcher = page.getByRole("button", { name: "StruvoCivil Assistant", exact: true });
  await expect(page.getByRole("button", { name: "5 Analyze / Results", exact: true })).toBeVisible({ timeout: 90000 });
  await expect(launcher).toHaveCount(1);
  await expect(page.getByRole("button", { name: /Show AI Copilot|Open AI Copilot|Open StruvoCivil Assistant/ })).toHaveCount(0);
  await expect(page.getByLabel("AI assistant sidebar")).toHaveCount(0);
  await launcher.click();
  const assistant = page.getByRole("complementary", { name: "StruvoCivil Assistant", exact: true });
  await expect(assistant).toHaveCount(1);
  await expect(assistant.getByRole("textbox")).toBeVisible();
  await expect(assistant).toContainText("Project 805");
  await expect(page.getByRole("tab", { name: "Inspect", exact: true })).toBeVisible();
  await page.screenshot({ path: `../docs/assistant-single-ui/workspace-${width}.png` });
  await assistant.getByRole("button", { name: "Close site assistant" }).click();
  await expect(launcher).toHaveCount(1);
  await page.evaluate(() => window.dispatchEvent(new Event("geoai:open-copilot")));
  await expect(assistant).toHaveCount(1);
  await expect(page.getByLabel("AI assistant sidebar")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  expect(writes).toEqual([]);
});
