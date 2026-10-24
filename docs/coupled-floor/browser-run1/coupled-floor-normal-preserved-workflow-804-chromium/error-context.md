# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: coupled-floor.spec.ts >> normal preserved workflow 804
- Location: e2e\coupled-floor.spec.ts:14:35

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/projects/804/workspace
Call log:
  - navigating to "http://localhost:3001/projects/804/workspace", waiting until "load"

```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | import demo from '../../docs/coupled-floor/demo.json';
  4  | const pid=demo.fixture.project_id,modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Computed slab displacement'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  5  | for(const width of [1280,1600])test(`native coupled shell/frame seven modes ${width}`,async({page,request})=>{
  6  |  test.setTimeout(240000);await page.setViewportSize({width,height:1000});const a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);
  7  |  const errors:string[]=[],writes:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  8  |  await page.goto(`http://localhost:13001/projects/${pid}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Coupled floor engineering'});await expect(panel.getByLabel('Coupled numerical summary')).toContainText('-0.9380',{timeout:60000});await expect(canvas).toHaveAttribute('data-structural-transition','ready');
  9  |  const surfaces=JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]') as {key:string;x:number;y:number}[];expect(surfaces).toHaveLength(256);const box=await canvas.boundingBox(),face=surfaces.find(p=>p.key==='shell:1119')!;expect(face).toBeTruthy();await page.mouse.click(box!.x+face.x,box!.y+face.y);await expect(panel.getByRole('article',{name:'Selected coupled evidence'})).toContainText('Shell');await page.screenshot({path:`../docs/coupled-floor/shell-inspection-${width}.png`});
  10 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(canvas).toHaveAttribute('data-structural-transition','ready');await expect(panel.getByLabel('Coupled legend')).toBeVisible();if(key==='deformation'){await panel.getByRole('button',{name:'Animate computed shell and frame',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','playing');const phase=await canvas.getAttribute('data-deformation-phase');await expect.poll(()=>canvas.getAttribute('data-deformation-phase')).not.toBe(phase);await panel.getByRole('button',{name:'Stop animation · full static case',exact:true}).click();}await page.screenshot({path:`../docs/coupled-floor/${key}-${width}.png`});}
  11 |  await panel.getByLabel('Inspect coupled component').selectOption('column-0');await expect(panel.getByRole('article',{name:'Selected coupled evidence'})).toContainText('column-0');await panel.getByRole('button',{name:'Computed slab displacement',exact:true}).click();await panel.getByLabel('Show computed shell surface').uncheck();await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(0);await panel.getByLabel('Show computed shell surface').check();
  12 |  await panel.getByText('Independent checks, assumptions and download',{exact:true}).click();const [download]=await Promise.all([page.waitForEvent('download'),panel.getByRole('button',{name:'Download coupled calculations',exact:true}).click()]);await download.saveAs(`../docs/coupled-floor/download-${width}.json`);expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/coupled-floor/browser-${width}.json`,JSON.stringify({project:pid,width,modes:7,picked_shell:face.key,native_shells:256,animation:true,download:true,writes,errors},null,2));
  13 | });
  14 | for(const id of [793,794,804])test(`normal preserved workflow ${id}`,async({page})=>{
> 15 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false',{timeout:60000});expect(writes).toEqual([]);expect(errors).toEqual([]);
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                  ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/projects/804/workspace
  16 | });
  17 | test('existing two-storey floors remain LOAD-ONLY',async({page})=>{
  18 |  test.setTimeout(180000);await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method()))return r.abort();if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto('http://localhost:13001/projects/823/workspace');await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Spatial structural engineering'}).getByLabel('Show LOAD-ONLY floor surfaces')).toBeChecked({timeout:60000});
  19 | });
  20 | 
```