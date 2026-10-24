# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-system.spec.ts >> isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits
- Location: e2e\foundation-system.spec.ts:5:5

# Error details

```
Error: apiRequestContext.get: connect EACCES 127.0.0.1:18001
Call log:
  - → GET http://127.0.0.1:18001/__foundation_validation
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.8010.12 Safari/537.36
    - accept: */*
    - accept-encoding: gzip,deflate,br

```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000}),API='http://127.0.0.1:18001';
  4  | test.use({trace:'off'});
  5  | test('isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits',async({page,request})=>{
  6  |  test.setTimeout(300000);page.setDefaultTimeout(30000);
> 7  |  const attestation=await (await request.get(API+'/__foundation_validation')).json();expect(attestation.mode).toBe('foundation-isolated-20261015');expect(attestation.database.replaceAll('\\','/').endsWith('/docs/foundation-system/isolated/foundation.db')).toBe(true);
     |                                         ^ Error: apiRequestContext.get: connect EACCES 127.0.0.1:18001
  8  |  expect(process.env.PLAYWRIGHT_BASE_URL).toContain(':13001');
  9  |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  10 |  await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())&&!r.request().url().startsWith(API+'/')){throw new Error('Write outside attested backend forbidden: '+r.request().url().split('?')[0]);}const u=r.request().url();if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(u))throw new Error('Original backend forbidden in isolated browser');await r.fallback();});
  11 |  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  12 |  await page.setViewportSize({width:1600,height:1000});
  13 |  await page.goto('/projects/804/workspace');
  14 |  const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  15 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  16 |  let panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  17 |  await expect(panel).toBeVisible();
  18 |  const create=panel.getByRole('button',{name:'Create separate foundation study from 804'});await expect(create).toBeEnabled({timeout:60000});
  19 |  const copyResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/copy')&&r.request().method()==='POST',{timeout:60000});
  20 |  await create.click();
  21 |  const response=await copyResponse;expect(response.ok(),await response.text()).toBeTruthy();const copy=await response.json();
  22 |  await page.waitForURL(`**/projects/${copy.project_id}/workspace`);
  23 |  await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  24 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  25 |  await expect(panel.getByLabel('Foundation code and edition')).toHaveValue('IS456-2000-A1A2');
  26 |  await expect(panel.getByRole('button',{name:'Preview integrated foundation calculation'})).toBeDisabled();
  27 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  28 |  const previewResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Preview integrated foundation calculation'}).click();
  29 |  const preview=await previewResponse;expect(preview.ok(),await preview.text()).toBeTruthy();const proposal=await preview.json();
  30 |  await expect(panel).toHaveAttribute('data-busy','false');
  31 |  await expect(panel.getByRole('button',{name:'Save reviewed foundation result'})).toBeDisabled();
  32 |  await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  33 |  const authResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Save reviewed foundation result'}).click();const auth=await authResponse;expect(auth.ok(),await auth.text()).toBeTruthy();const result=await auth.json();
  34 |  const output=panel.getByRole('article',{name:'Foundation visual analysis'});await expect(output).toContainText('Exceeds implemented check');expect(result.result.computed.rc.layers.map((l:{effective_depth_mm:number})=>l.effective_depth_mm)).toEqual([365,345]);
  35 |  await output.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(1000);
  36 |  await page.screenshot({path:'../docs/foundation-visual/system-regression-3d-foundation-1600.png'});
  37 |  await panel.getByText('Reports, methods and immutable evidence',{exact:true}).click();const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Download calculation report'}).click();const file=await download;await file.saveAs('../docs/foundation-visual/system-regression-browser-calculation-report.html');
  38 |  await output.getByRole('button',{name:'Foundation alternatives',exact:true}).click();await output.getByRole('button',{name:'Calculate validated comparisons'}).click();await expect(output.getByRole('button',{name:'Review selected alternative'})).toBeVisible();
  39 |  const assistant=page.getByRole('region',{name:'Project assistant',exact:true});if(!await assistant.isVisible())await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const input=assistant.getByRole('textbox',{name:'Project message'});await expect(input).toBeEnabled({timeout:30000});await input.fill('Explain saved foundation reinforcement, punching and supported alternatives');await page.getByRole('button',{name:'Send message',exact:true}).click();await expect(assistant.getByRole('article',{name:'Assistant message'}).last()).toContainText('Saved foundation evidence #',{timeout:60000});await expect(assistant.getByText(/chat cannot apply or authorize/).first()).toBeVisible();
  40 |  await page.screenshot({path:'../docs/foundation-visual/system-regression-offline-copilot-1600.png'});
  41 |  if(await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).isVisible())await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).click();await page.getByRole('tab',{name:'Analysis',exact:true}).click();await panel.getByText('Inputs, proposals and authorization',{exact:true}).click();await panel.getByText('Actions, materials, soil and detailing inputs',{exact:true}).click();await panel.getByLabel('Independent factored column action kN',{exact:true}).fill('432');await expect(output).toHaveAttribute('data-stale','true');await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');await expect(panel.locator('button').filter({hasText:'Download calculation report'})).toBeDisabled();
  42 |  await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(output).toHaveAttribute('data-stale','false');
  43 |  await page.setViewportSize({width:1280,height:900});await output.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(800);await page.screenshot({path:'../docs/foundation-visual/system-regression-3d-foundation-1280.png'});
  44 |  await panel.getByRole('button',{name:'Restore full model from foundation view'}).click();await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');
  45 |  expect(errors).toEqual([]);
  46 |  writeFileSync('../docs/foundation-visual/system-regression-browser-results.json',JSON.stringify({attestation,copy,proposal_id:proposal.id,result_id:result.id,two_mats:true,download:true,alternatives:true,offline_copilot:true,stale_edit_clears_overlay:true,reload:true,page_errors:errors},null,2));
  47 | });
  48 | 
```