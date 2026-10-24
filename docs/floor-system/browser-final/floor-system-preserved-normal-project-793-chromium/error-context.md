# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: floor-system.spec.ts >> preserved normal project 793
- Location: e2e\floor-system.spec.ts:25:35

# Error details

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator:  getByRole('region', { name: 'Structural visual engineering' })
Expected: "false"
Received: "true"
Timeout:  5000ms

Call log:
  - Expect "toHaveAttribute" getByRole('region', { name: 'Structural visual engineering' }) with timeout 5000ms
  - waiting for getByRole('region', { name: 'Structural visual engineering' })
    13 × locator resolved to <section data-mode="path" data-blocked="true" aria-label="Structural visual engineering" class="mb-4 space-y-3 rounded border border-border p-3 text-xs [&_button]:rounded [&_button]:border [&_button]:border-border [&_button]:px-2 [&_button]:py-2 [&_button:disabled]:opacity-40 [&_select]:w-full [&_select]:bg-background">…</section>
       - unexpected value "true"

```

```yaml
- region "Structural visual engineering":
  - heading "Structure · explore in 3D" [level=3]
  - paragraph: Saved analytical evidence · no safety or code approval
  - button "Structural load paths" [disabled] [pressed]
  - button "Applied loads and reactions" [disabled]
  - button "Deformed versus original" [disabled]
  - button "Beam and column forces" [disabled]
  - button "Slab-to-beam distribution" [disabled]
  - button "Foundation and soil response" [disabled]
  - button "Warnings and connections" [disabled]
  - status: Loading saved evidence…
  - text: "Cyan: saved member topology · pink: declared rigid arms. Topology arrows are not force magnitudes or directions. Connections have no verified capacity."
  - paragraph: Labels avoid overlap. Select a component or yellow marker for full saved values.
  - checkbox "Isolate analyzed structural system" [checked] [disabled]
  - text: Isolate analyzed system
  - button "Frame view" [disabled]
  - button "Restore full structure"
  - text: Inspect saved component
  - combobox "Inspect structural component"
  - group: Coverage, warnings and immutable numerical evidence
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync,readFileSync} from 'node:fs';
  3  | import demo from '../../docs/spatial-frame/demo.json';
  4  | const d=demo[1],modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  5  | for(const width of [1280,1600])test(`integrated floors, topology and static-case animation ${width}`,async({page,request})=>{
  6  |  test.setTimeout(240000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
  7  |  const attestation=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(attestation.original_writes).toBe(false);
  8  |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  9  |  await page.goto('http://localhost:13001/projects/823/workspace');const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await expect(panel.getByLabel('Spatial load case')).toBeVisible();await panel.getByLabel('Spatial load case').selectOption(d.analysis.result.cases[2].case.name);
  10 |  await expect(canvas).toHaveAttribute('data-structural-transition','ready');await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(4);
  11 |  const surfaces=JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]') as {key:string;x:number;y:number}[];const face=surfaces.find(p=>p.key==='slab-F2-B1')!;expect(face).toBeTruthy();const box=await canvas.boundingBox();await page.mouse.click(box!.x+face.x,box!.y+face.y);await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('LOAD-ONLY');await expect(panel.getByLabel('Connected route destination')).toBeVisible();
  12 |  await panel.getByText(/Route · \d+ verified topology steps/).click();await expect(panel.getByLabel('Verified topology route')).toContainText('Base N');await expect(panel.getByLabel('Verified topology route')).toContainText('column-F1');await page.screenshot({path:`../docs/floor-system/floor-transfer-${width}.png`});
  13 |  await panel.getByRole('button',{name:'Isolate this floor',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('2');await expect(canvas).toHaveAttribute('data-structural-transition','ready');await page.screenshot({path:`../docs/floor-system/floor-isolation-${width}.png`});await panel.getByRole('button',{name:'Show complete route across floors',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('0');
  14 |  await panel.getByLabel('Show LOAD-ONLY floor surfaces').uncheck();await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(0);await panel.getByLabel('Show LOAD-ONLY floor surfaces').check();
  15 |  await panel.getByLabel('Inspect spatial component').selectOption(d.fixture.inputs.members[20].id);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Computed |u|max');
  16 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(canvas).toHaveAttribute('data-structural-transition','ready');
  17 |   if(key==='deformation'){await panel.getByLabel('Spatial displacement magnification').fill('100');await panel.getByRole('button',{name:'Animate computed deformation',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','playing');const before=await canvas.getAttribute('data-deformation-phase');await expect.poll(()=>canvas.getAttribute('data-deformation-phase')).not.toBe(before);await page.screenshot({path:`../docs/floor-system/deformation-${width}.png`});await panel.getByRole('button',{name:'Stop animation · show full static case',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','paused');await expect(panel).toContainText('NOT dynamic analysis');}
  18 |   const boxes=JSON.parse(await canvas.getAttribute('data-engineering-label-boxes')||'[]') as {x:number;y:number;width:number;height:number}[];expect(boxes.length).toBeLessThanOrEqual(7);for(const [i,a] of boxes.entries())for(const b of boxes.slice(i+1))expect(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y).toBe(false);
  19 |  }
  20 |  await panel.getByRole('button',{name:'Applied loads and reactions',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready');const loads=JSON.parse(await canvas.getAttribute('data-engineering-load-points')||'[]') as {key:string;x:number;y:number}[];const load=loads.find(p=>p.key.startsWith('load:node:')&&p.x>100&&p.x<box!.width-30&&p.y>120&&p.y<800);expect(load).toBeTruthy();await page.mouse.click(box!.x+load!.x,box!.y+load!.y);await expect(panel.getByLabel('Inspect analytical load or support')).toHaveValue(load!.key);await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('whole saved case');
  21 |  await panel.getByLabel('Inspect analytical load or support').selectOption('node:1');await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('foundation/soil capacity NOT VERIFIED');await page.screenshot({path:`../docs/floor-system/base-reactions-${width}.png`});
  22 |  await panel.getByText('Floor mechanics status and transfer download',{exact:true}).click();const [download]=await Promise.all([page.waitForEvent('download'),panel.getByRole('button',{name:'Download floor-transfer evidence',exact:true}).click()]);const savedPath=`../docs/floor-system/downloaded-floor-evidence-${width}.json`;await download.saveAs(savedPath);const downloaded=JSON.parse(readFileSync(savedPath,'utf8'));expect(downloaded.analysis_id).toBe(684);expect(downloaded.cases.every((c:{status:string;capabilities:{diaphragm:boolean;slab_structural_analysis:boolean}})=>c.status==='VERIFIED'&&!c.capabilities.diaphragm&&!c.capabilities.slab_structural_analysis)).toBe(true);
  23 |  await panel.getByRole('button',{name:'Restore full geometry',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/floor-system/acceptance-${width}.json`,JSON.stringify({width,surface_picked:face.key,load_picked:load!.key,modes:7,animation:true,isolated_floor:true,route_to_base:true,writes,errors},null,2));
  24 | });
  25 | for(const id of [793,794,804])test(`preserved normal project ${id}`,async({page})=>{
> 26 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false');expect(writes).toEqual([]);expect(errors).toEqual([]);
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^ Error: expect(locator).toHaveAttribute(expected) failed
  27 | });
  28 | 
  29 | 
  30 | 
```