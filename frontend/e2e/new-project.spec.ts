import { expect, test } from "@playwright/test";

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
  test(`name-only project dialog fits ${viewport.width}×${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/projects/new");
    const dialog = page.getByRole("dialog", { name: "New project" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("textbox", { name: "Project name" })).toBeFocused();
    await expect(dialog.getByRole("textbox")).toHaveCount(1);
    await expect(dialog.getByRole("combobox")).toHaveCount(0);
    await expect(dialog.getByRole("button", { name: "Create Project" })).toBeDisabled();
    await dialog.getByRole("textbox").fill("Junction study");
    await expect(dialog.getByRole("button", { name: "Create Project" })).toBeEnabled();
    const box = await dialog.boundingBox();
    expect(box!.y + box!.height).toBeLessThan(viewport.height);
    await page.screenshot({ path: `.cache/new-project-${viewport.width}.png` });
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole("button", { name: "New Project", exact: true }).first()).toBeFocused();
  });
}

test("name-only creation preserves input, prevents duplicate requests, and enters workspace", async ({ page }) => {
  let calls = 0;
  let payload: Record<string, unknown> = {};
  await page.route("**/api/projects", async route => {
    if (route.request().method() !== "POST") return route.fulfill({ json: [] });
    calls++; payload = route.request().postDataJSON();
    await new Promise(resolve => setTimeout(resolve, 250));
    await route.fulfill({ status: calls === 1 ? 422 : 201, json: calls === 1 ? { detail: "Please retry creation" } : { id: 987654, project_type: "unclassified", ...payload } });
  });
  await page.goto("/dashboard");
  await page.getByRole("button", { name: "New Project", exact: true }).first().click();
  const dialog = page.getByRole("dialog", { name: "New project" });
  await dialog.getByRole("textbox", { name: "Project name" }).fill("  Junction study  ");
  await dialog.evaluate(form => { form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })); form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })); });
  await expect(dialog.getByRole("alert")).toContainText("Please retry creation");
  expect(calls).toBe(1); expect(payload).toEqual({ name: "Junction study" });
  await expect(dialog.getByRole("textbox")).toHaveValue("  Junction study  ");
  await dialog.getByRole("textbox").press("Enter");
  await expect(page).toHaveURL(/\/projects\/987654\/workspace/);
  expect(calls).toBe(2);
});
