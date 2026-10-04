import { expect, test } from "@playwright/test";

const unique = Date.now();

async function dismissNavDrawer(page: import("@playwright/test").Page) {
  const overlay = page.locator(".modal-overlay");
  if (!(await overlay.isVisible().catch(() => false))) return;

  // Sidebar (248px) sits above the header toggle — click the overlay to the right.
  await overlay.click({ position: { x: 320, y: 240 } });
  await overlay.waitFor({ state: "hidden", timeout: 10_000 });
}

test.describe("Critical path", () => {
  test("register → login → create project → workspace → estimate", async ({ page }) => {
    const projectName = `E2E Project ${unique}`;

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });
    await dismissNavDrawer(page);

    await page.goto("/projects/new");
    await dismissNavDrawer(page);
    await page.getByLabel(/Project name/i).fill(projectName);
    await expect(page.getByRole("button", { name: /Create Project/i })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: /Create Project/i }).click();

    await expect(page).toHaveURL(/\/projects\/\d+\/workspace/, { timeout: 30_000 });
    await expect(page.getByText(/AI Studio|Studio|Workspace/i).first()).toBeVisible({
      timeout: 30_000,
    });

    const workspaceUrl = page.url();
    const projectBase = workspaceUrl.replace(/\/workspace.*/, "");
    await page.goto(`${projectBase}/estimate`);
    await expect(page).toHaveURL(/\/projects\/\d+\/estimate/, { timeout: 30_000 });
    await expect(
      page.getByText(/BOQ|Estimate|Bill of quantities|No estimate/i).first(),
    ).toBeVisible({ timeout: 30_000 });
  });
});
