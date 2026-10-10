import { test } from "@playwright/test";
import { reviewPlatform } from "./helpers/platform-review-workflow";
const projectId = process.env.PLATFORM_ACCEPTANCE_PROJECT_ID;
test.skip(!projectId, "Requires the offline create_platform_workspace_fixture.py project");
test("review and approve one platform, then edit, save, reload and compare", async ({ page }) => {
  test.slow();
  await reviewPlatform(page, projectId!);
});
