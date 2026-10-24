# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-visual.spec.ts >> alternative changes require exact authorization and explicit Save; bar inputs and old results remain distinct
- Location: e2e\foundation-visual.spec.ts:55:5

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
  2  | import {readFileSync,writeFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000}),API='http://127.0.0.1:18001';
  4  | const fixture=JSON.parse(readFileSync('../docs/foundation-visual/demo.json','utf8'));
  5  | const modes=[['loads','Loads and reactions'],['soil','Soil pressure and settlement'],['bending','Bending moments'],['one-way','One-way shear'],['punching','Punching shear'],['reinforcement','Reinforcement and anchorage'],['alternatives','Foundation alternatives']] as const;
  6  | test.use({trace:'off'});
  7  | for(const width of [1280,1600])test(`visual foundation modes, picking, ghost alternatives and immutable results at ${width}`,async({page,request})=>{
  8  |  test.setTimeout(240000);page.setDefaultTimeout(30000);
  9  |  expect(process.env.PLAYWRIGHT_BASE_URL).toContain(':13001');
  10 |  const attested=await(await request.get(API+'/__foundation_validation')).json();expect(attested.database).toBe(fixture.attestation.database);
  11 |  await page.setViewportSize({width,height:1000});
  12 |  const errors:string[]=[],writes:string[]=[];
  13 |  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().startsWith(API)&&r.method()==='POST')writes.push(r.url());});
  14 |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  15 |  await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())&&!r.request().url().startsWith(API+'/')){throw new Error('Write outside attested backend forbidden: '+r.request().url().split('?')[0]);}if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(r.request().url()))throw new Error('Original backend forbidden');await r.fallback();});
  16 |  const pid=fixture.study.project_id,rid=fixture.study.model_revision_id,base=`${API}/api/projects/${pid}/engineering/foundation-system`;
  17 |  const before=await(await request.get(`${base}?model_revision_id=${rid}`)).json();
  18 |  await page.goto(`/projects/${pid}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  19 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  20 |  const panel=page.getByRole('region',{name:'Integrated foundation workflow'}),visual=page.getByRole('article',{name:'Foundation visual analysis'});
  21 |  await expect(visual).toBeVisible();await expect(canvas).toHaveAttribute('data-foundation-mode','reinforcement');await expect(canvas).toHaveAttribute('data-foundation-bars','16');
  22 |  await expect(panel.getByLabel('Foundation code and edition')).not.toBeVisible();
  23 |  await expect(panel.getByRole('button',{name:'Download calculation report'})).not.toBeVisible();
  24 |  writes.length=0;
  25 |  for(const [key,name] of modes){
  26 |   await visual.getByRole('button',{name,exact:true}).click();await expect(canvas).toHaveAttribute('data-foundation-mode',key);
  27 |   if(key==='alternatives')break;
  28 |   await expect(visual.getByLabel('Engineering legend')).toBeVisible();await page.waitForTimeout(400);
  29 |   await page.screenshot({path:`../docs/foundation-visual/${key}-${width}.png`});
  30 |  }
  31 |  expect(writes).toEqual([]);
  32 |  await visual.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();
  33 |  await expect(visual.getByLabel('Compact engineering summary')).toContainText('971 mm required / 375 mm available');
  34 |  await expect(visual.getByLabel('Compact engineering summary')).toContainText('Exceeds implemented check');
  35 |  await visual.getByLabel('Transparent foundation concrete').uncheck();await visual.getByLabel('Transparent foundation concrete').check();
  36 |  const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];
  37 |  const pick=labels.find(p=>p.key==='anchorage-EW'&&p.x>10&&p.x<width-460&&p.y>10&&p.y<950);
  38 |  expect(pick).toBeTruthy();const bounds=await canvas.boundingBox();await page.mouse.click(bounds!.x+pick!.x,bounds!.y+pick!.y);
  39 |  await expect(visual.getByText('Selected check · detailed evidence')).toBeVisible();await expect(visual.locator('details')).toHaveAttribute('open','');
  40 |  await expect(visual.locator('pre')).toContainText('970.982');
  41 |  await visual.getByText('Selected check · detailed evidence').click();
  42 |  await visual.getByRole('button',{name:'Foundation alternatives',exact:true}).click();await visual.getByRole('button',{name:'Calculate validated comparisons'}).click();
  43 |  await expect(visual.getByRole('button',{name:'Review selected alternative'})).toBeVisible();
  44 |  await visual.getByRole('button').filter({hasText:'1.50 m square × 0.54 m'}).click();
  45 |  await expect(canvas).toHaveAttribute('data-foundation-mode','alternatives');await page.waitForTimeout(500);await page.screenshot({path:`../docs/foundation-visual/alternatives-${width}.png`});
  46 |  const after=await(await request.get(`${base}?model_revision_id=${rid}`)).json();expect(after.records).toEqual(before.records);
  47 |  await visual.getByRole('button',{name:'Review selected alternative'}).click();const review=panel.getByRole('region',{name:'Review foundation alternative'});await expect(review).toContainText('Geometry preview, exact authorization');
  48 |  await review.getByRole('button',{name:'Preview CAD alternative'}).click();await expect(review).toContainText('PREVIEW_READY_GEOMETRY_ONLY');await expect(review.getByRole('button',{name:'Apply authorized alternative draft'})).toBeDisabled();
  49 |  await review.getByRole('button',{name:'Cancel alternative review'}).click();
  50 |  const model=await(await request.get(`${API}/api/projects/${pid}/scenarios/${fixture.study.scenario_id}/model-revisions/latest`)).json();expect(model.id).toBe(rid);
  51 |  await panel.getByText('Reports, methods and immutable evidence',{exact:true}).click();const pending=page.waitForEvent('download');await panel.getByRole('button',{name:'Download calculation report'}).click();await(await pending).saveAs(`../docs/foundation-visual/report-${width}.html`);
  52 |  await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(canvas).toHaveAttribute('data-foundation-mode','reinforcement');
  53 |  expect(errors).toEqual([]);writeFileSync(`../docs/foundation-visual/acceptance-${width}.json`,JSON.stringify({width,project_id:pid,result_unchanged:true,modes:7,picked_3d_label:true,opacity:true,ghost_preview:true,authorization_required:true,cancel_preserves_revision:true,reload:true,report_download:true,page_errors:errors},null,2));
  54 | });
  55 | test('alternative changes require exact authorization and explicit Save; bar inputs and old results remain distinct',async({page,request})=>{
  56 |  test.setTimeout(180000);page.setDefaultTimeout(30000);
> 57 |  const a=await(await request.get(API+'/__foundation_validation')).json();expect(a.database).toBe(fixture.attestation.database);
     |                              ^ Error: apiRequestContext.get: connect EACCES 127.0.0.1:18001
  58 |  const copyResponse=await request.post(`${API}/api/projects/804/engineering/foundation-system/copy`,{data:{model_revision_id:124,authorize_separate_study:true}});expect(copyResponse.ok()).toBeTruthy();const copy=await copyResponse.json();
  59 |  const base=`${API}/api/projects/${copy.project_id}/engineering/foundation-system`,state=await(await request.get(`${base}?model_revision_id=${copy.model_revision_id}`)).json();
  60 |  const p=await(await request.post(base+'/preview',{data:{model_revision_id:copy.model_revision_id,inputs:state.fixture}})).json();
  61 |  const result=await(await request.post(base+'/authorize',{data:{proposal_id:p.id,proposal_sha256:p.result.proposal_sha256,authorize_calculation:true}})).json();
  62 |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  63 |  await page.setViewportSize({width:1600,height:1000});await page.goto(`/projects/${copy.project_id}/workspace`);
  64 |  const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  65 |  const panel=page.getByRole('region',{name:'Integrated foundation workflow'}),visual=page.getByRole('article',{name:'Foundation visual analysis'});
  66 |  await visual.getByRole('button',{name:'Foundation alternatives',exact:true}).click();await visual.getByRole('button',{name:'Calculate validated comparisons'}).click();
  67 |  await visual.getByRole('button').filter({hasText:'1.20 m square × 0.54 m'}).filter({hasText:'10 × Ø20 / 10 × Ø20'}).click();
  68 |  await visual.getByRole('button',{name:'Review selected alternative'}).click();const review=panel.getByRole('region',{name:'Review foundation alternative'});
  69 |  await review.getByRole('button',{name:'Preview CAD alternative'}).click();await expect(review).toContainText('PREVIEW_READY_GEOMETRY_ONLY');
  70 |  await expect(page.getByRole('button',{name:'Save model',exact:true})).toBeDisabled();await expect(review.getByRole('button',{name:'Apply authorized alternative draft'})).toBeDisabled();
  71 |  await review.getByLabel('Authorize exact alternative geometry').check();
  72 |  const authorized=page.waitForResponse(r=>r.url().endsWith('/drawing-cad/authorize')&&r.request().method()==='POST');await review.getByRole('button',{name:'Apply authorized alternative draft'}).click();expect((await authorized).ok()).toBeTruthy();
  73 |  await expect(page.getByRole('button',{name:'Save model',exact:true})).toBeEnabled();
  74 |  const revisions=`${API}/api/projects/${copy.project_id}/scenarios/${copy.scenario_id}/model-revisions`;
  75 |  expect((await(await request.get(revisions+'/latest')).json()).id).toBe(copy.model_revision_id);
  76 |  const saved=page.waitForResponse(r=>r.url().endsWith('/model-revisions')&&r.request().method()==='POST');await page.getByRole('button',{name:'Save model',exact:true}).click();const response=await saved;expect(response.ok(),await response.text()).toBeTruthy();const next=await response.json();
  77 |  const latest=await(await request.get(revisions+'/latest')).json();expect(latest.id).toBe(next.id);expect(latest.id).not.toBe(copy.model_revision_id);
  78 |  const footing=latest.document.components.find((c:{id:string})=>c.id===state.geometry.footing_id);expect(footing.geometry.size).toEqual([1.2,1.2,.54]);
  79 |  const history=await(await request.get(`${base}?model_revision_id=${latest.id}`)).json();const old=history.records.find((r:{id:number})=>r.id===result.id);expect(old.status).toBe('STALE');expect(old.result.inputs.inputs.east_west.count).toBe(8);
  80 |  await expect(canvas).not.toHaveAttribute('data-foundation-mode','reinforcement');
  81 |  writeFileSync('../docs/foundation-visual/authorization-acceptance.json',JSON.stringify({project_id:copy.project_id,original_revision:copy.model_revision_id,saved_revision:next.id,explicit_authorization:true,explicit_save:true,bar_inputs_not_silently_changed:true,old_results_stale:true},null,2));
  82 | });
  83 | 
```