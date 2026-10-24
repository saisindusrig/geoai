# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-system.spec.ts >> isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits
- Location: e2e\foundation-system.spec.ts:5:5

# Error details

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator: locator('.cesium-widget canvas')
Expected: "true"
Timeout: 90000ms
Error: element(s) not found

Call log:
  - Expect "toHaveAttribute" locator('.cesium-widget canvas') with timeout 90000ms
  - waiting for locator('.cesium-widget canvas')

```

```yaml
- navigation:
  - button "previous" [disabled]:
    - img "previous"
  - text: 1/1
  - button "next" [disabled]:
    - img "next"
- img
- link "Next.js 16.2.9 (stale) Turbopack":
  - /url: https://nextjs.org/docs/messages/version-staleness
  - img
  - text: Next.js 16.2.9 (stale) Turbopack
- img
- dialog "Build Error":
  - text: Build Error
  - button "Copy Error Info":
    - img
  - button "No related documentation found" [disabled]:
    - img
  - button "Attach Node.js inspector":
    - img
  - text: Reading source code for parsing failed
  - img
  - text: ./components/model-editor/FoundationSystemPanel.tsx
  - button "Open in editor":
    - img
  - text: "Reading source code for parsing failed An unexpected error happened while trying to read the source code to parse: failed to convert rope into string Caused by: - invalid utf-8 sequence of 1 bytes from index 7687 Import traces: Client Component Browser: ./components/model-editor/FoundationSystemPanel.tsx [Client Component Browser] ./components/model-editor/ProfessionalModelEditor.tsx [Client Component Browser] ./app/projects/[id]/workspace/page.tsx [Client Component Browser] ./app/projects/[id]/workspace/page.tsx [Server Component] Client Component SSR: ./components/model-editor/FoundationSystemPanel.tsx [Client Component SSR] ./components/model-editor/ProfessionalModelEditor.tsx [Client Component SSR] ./app/projects/[id]/workspace/page.tsx [Client Component SSR] ./app/projects/[id]/workspace/page.tsx [Server Component]"
- button "Open Next.js Dev Tools":
  - img
- button "Open issues overlay": 1 Issue
- alert
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000}),API='http://127.0.0.1:18001';
  4  | test.use({trace:'off'});
  5  | test('isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits',async({page,request})=>{
  6  |  test.setTimeout(300000);page.setDefaultTimeout(30000);
  7  |  const attestation=await (await request.get(API+'/__foundation_validation')).json();expect(attestation.mode).toBe('foundation-isolated-20261015');expect(attestation.database.replaceAll('\\','/').endsWith('/docs/foundation-system/isolated/foundation.db')).toBe(true);
  8  |  expect(process.env.PLAYWRIGHT_BASE_URL).toContain(':13001');
  9  |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  10 |  await page.route('**/*',async r=>{const u=r.request().url();if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(u))throw new Error('Original backend forbidden in isolated browser');await r.fallback();});
  11 |  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  12 |  await page.setViewportSize({width:1600,height:1000});
  13 |  await page.goto('/projects/804/workspace');
> 14 |  const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
     |                                                                          ^ Error: expect(locator).toHaveAttribute(expected) failed
  15 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  16 |  let panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  17 |  await expect(panel).toBeVisible();
  18 |  const copyResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/copy')&&r.request().method()==='POST');
  19 |  await panel.getByRole('button',{name:'Create separate foundation study from 804'}).click();
  20 |  const response=await copyResponse;expect(response.ok(),await response.text()).toBeTruthy();const copy=await response.json();
  21 |  await page.waitForURL(`**/projects/${copy.project_id}/workspace`);
  22 |  await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  23 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  24 |  await expect(panel.getByLabel('Foundation code and edition')).toHaveValue('IS456-2000-A1A2');
  25 |  await expect(panel.getByRole('button',{name:'Preview integrated foundation calculation'})).toBeDisabled();
  26 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  27 |  const previewResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Preview integrated foundation calculation'}).click();
  28 |  const preview=await previewResponse;expect(preview.ok(),await preview.text()).toBeTruthy();const proposal=await preview.json();
  29 |  await expect(panel).toHaveAttribute('data-busy','false');
  30 |  await expect(panel.getByRole('button',{name:'Save reviewed foundation result'})).toBeDisabled();
  31 |  await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  32 |  const authResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Save reviewed foundation result'}).click();const auth=await authResponse;expect(auth.ok(),await auth.text()).toBeTruthy();const result=await auth.json();
  33 |  const output=panel.getByRole('article',{name:'Integrated foundation results'});await expect(output).toContainText('EXCEEDS_IMPLEMENTED_CHECK');await expect(output).toContainText('365.000');await expect(output).toContainText('345.000');
  34 |  await output.getByRole('button',{name:'Show foundation engineering 3D'}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(1000);
  35 |  await page.screenshot({path:'../docs/foundation-system/3d-foundation-1600.png'});
  36 |  const download=page.waitForEvent('download');await output.getByRole('button',{name:'Download calculation report'}).click();const file=await download;await file.saveAs('../docs/foundation-system/browser-calculation-report.html');
  37 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();await panel.getByRole('button',{name:'Compare foundation alternatives'}).click();await expect(panel.getByText('Unsaved alternatives · review required',{exact:true})).toBeVisible();
  38 |  const assistant=page.getByRole('region',{name:'Project assistant',exact:true});if(!await assistant.isVisible())await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const input=assistant.getByRole('textbox',{name:'Project message'});await expect(input).toBeEnabled({timeout:30000});await input.fill('Explain saved foundation reinforcement, punching and supported alternatives');await page.getByRole('button',{name:'Send message',exact:true}).click();await expect(assistant.getByRole('article',{name:'Assistant message'}).last()).toContainText('Saved foundation evidence #',{timeout:60000});await expect(assistant.getByText(/chat cannot apply or authorize/).first()).toBeVisible();
  39 |  await page.screenshot({path:'../docs/foundation-system/offline-copilot-1600.png'});
  40 |  if(await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).isVisible())await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).click();await page.getByRole('tab',{name:'Analysis',exact:true}).click();await panel.getByText('Actions, materials, soil and detailing inputs',{exact:true}).click();await panel.getByLabel('Independent factored column action kN',{exact:true}).fill('432');await expect(output).toContainText('STALE');await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');await expect(output.getByRole('button',{name:'Download calculation report'})).toBeDisabled();
  41 |  await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(output).toContainText('REVIEWED_SYNTHETIC_CALCULATION');
  42 |  await page.setViewportSize({width:1280,height:900});await output.getByRole('button',{name:'Show foundation engineering 3D'}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(800);await page.screenshot({path:'../docs/foundation-system/3d-foundation-1280.png'});
  43 |  await panel.getByRole('button',{name:'Restore full model from foundation view'}).click();await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');
  44 |  expect(errors).toEqual([]);
  45 |  writeFileSync('../docs/foundation-system/browser-results.json',JSON.stringify({attestation,copy,proposal_id:proposal.id,result_id:result.id,two_mats:true,download:true,alternatives:true,offline_copilot:true,stale_edit_clears_overlay:true,reload:true,page_errors:errors},null,2));
  46 | });
  47 | 
```