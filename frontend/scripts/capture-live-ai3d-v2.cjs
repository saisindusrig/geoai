// Read-only workspace evidence capture; never sends an Assistant message.
const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1626, height: 982 } });
    await page.goto('http://localhost:3000/projects/578/workspace');
    await page.getByLabel('Search scene components').waitFor({ timeout: 60000 });
    await page.getByRole('tab', { name: 'Layers', exact: true }).click();
    await page.getByLabel('Search scene components').fill('deck-001');
    await page.getByRole('button', { name: 'deck-001', exact: true }).click();
    await page.getByRole('tab', { name: 'Inspect', exact: true }).click();
    await page.getByRole('button', { name: 'Engineering dock', exact: true }).click();
    await page.getByRole('tab', { name: 'SECTION', exact: true }).click();
    await page.getByRole('checkbox', { name: 'Underground view', exact: true }).check();
    await page.getByRole('button', { name: 'Engineering dock', exact: true }).click();
    await page.getByRole('button', { name: 'Frame selection', exact: true }).click();
    await page.waitForTimeout(1800);
    await page.screenshot({ path: '../backend/live-results/universal-v2/workspace-accepted.png' });
  } finally { await browser.close(); }
})();
