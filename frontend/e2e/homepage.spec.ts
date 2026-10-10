import { expect, test } from "@playwright/test";

test.use({ launchOptions: { args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

test("homepage workflow, system switching and FAQ support keyboard review", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Real terrain.");
  await expect(page.getByRole("link", { name: "Launch GeoAI" }).first()).toHaveAttribute("href", /projects|login/);
  await expect(page.locator("canvas")).toBeVisible();
  const workflow = page.getByRole("tablist", { name: "Site to concept workflow" });
  await workflow.getByRole("tab", { name: "01 Site" }).click();
  await page.keyboard.press("ArrowRight");
  await expect(workflow.getByRole("tab", { name: "02 Data" })).toBeFocused();
  await expect(page.locator("#workflow-panel")).toContainText("Read the terrain.");
  await page.keyboard.press("End");
  await expect(workflow.getByRole("tab", { name: "06 Export" })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#workflow-panel")).toContainText("Carry the evidence forward.");
  const systems = page.getByRole("tablist", { name: "Infrastructure system" });
  await systems.getByRole("tab", { name: /Road/ }).click();
  await page.keyboard.press("End");
  await expect(systems.getByRole("tab", { name: /Dam/ })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#system-panel")).toContainText("Work with the watershed.");
  await expect(page.locator("canvas")).toHaveCount(1);
  await page.getByRole("button", { name: /Can I use my own survey data/ }).click();
  await expect(page.locator("#faq-answer-1")).toBeVisible();
  await page.getByRole("button", { name: /Are GeoAI measurements engineering-grade/ }).click();
  await expect(page.locator("#faq-answer-1")).toBeHidden();
  await expect(page.locator("#faq-answer-2")).toBeVisible();
  await page.getByRole("link", { name: "GeoAI home", exact: true }).click();
  await page.screenshot({ path: "test-results/homepage-desktop.png" });
});

for (const width of [390, 768]) {
  test(`homepage fits ${width}px viewport`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    for (const id of ["earth", "how-it-works", "projects", "design-basis", "faq"]) {
      const section = page.locator(`#${id}`);
      await section.scrollIntoViewIfNeeded();
      const bounds = await section.boundingBox();
      expect(bounds!.x).toBeGreaterThanOrEqual(0);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width + 1);
      const overflow = await section.evaluate(el => el.scrollWidth > el.clientWidth + 1);
      expect(overflow, `${id} should not overflow`).toBe(false);
    }
    await page.getByRole("link", { name: "GeoAI home", exact: true }).click();
    await page.screenshot({ path: `test-results/homepage-${width}.png` });
  });
}
