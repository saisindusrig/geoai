# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: spatial-frame.spec.ts >> isolated exact review and authorize workflow
- Location: e2e\spatial-frame.spec.ts:25:5

# Error details

```
Error: expect(received).toMatch(expected)

Expected pattern: /^http:\/\/127\.0\.0\.1:18001\/api\/projects\/\d+\/engineering\/spatial-frame\/(review|authorize-run)$/
Received string:  "http://127.0.0.1:18001/api/projects/824/site-suggestions"
```

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator: locator('.cesium-widget canvas')
Expected: "true"
Error: element(s) not found

Call log:
  - Expect "toHaveAttribute" locator('.cesium-widget canvas') with timeout 120000ms
  - waiting for locator('.cesium-widget canvas')
  - Test ended.

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- banner:
  - link "GeoAI home":
    - /url: /
    - text: GeoAI
  - heading "Spatial review · 2×1 bays · 1 storey · synthetic" [level=1]
  - link "3D Sandbox editor":
    - /url: /projects/999999/workspace?local=1
  - link "Projects":
    - /url: /dashboard
  - button "Save site geometry"
  - link "Export":
    - /url: /projects/824/report
    - button "Export"
  - link "New concept":
    - /url: /projects/new
    - button "New concept"
  - link "Open settings":
    - /url: /settings
- main:
  - button "1 Site"
  - group: Workflow help
  - group: 2 Create / Import
  - button "3 Review 3D"
  - button "4 Edit"
  - button "5 Analyze / Results"
  - button "6 Review"
  - status: Saved · v1
  - button "Save model" [disabled]
  - complementary "Workspace tools":
    - group "Object editing":
      - text: Edit
      - button "Select object" [pressed]
      - text: Click to select and inspect · Ctrl to add · V
      - button "Move selection" [disabled]
      - text: Move selection · Select an editable object first
      - button "Rotate selection" [disabled]
      - text: Rotate selection · Select an editable object first
      - button "Scale selection" [disabled]
      - text: Scale selection · Select an editable object first
    - group "Site geometry":
      - text: Site
      - button "Draw rectangular boundary"
      - text: Draw a rectangular site boundary
      - button "Draw site boundary"
      - text: Draw a closed site boundary
      - button "Edit site boundary" [disabled]
      - text: Edit site boundary · Draw a site boundary first
      - button "Draw alignment"
      - text: Draw a road or infrastructure centerline
      - button "Edit alignment" [disabled]
      - text: Edit alignment · Draw an alignment first
    - text: View
    - button "Measure"
    - text: Measure distance, elevation, slope, area or clearance · M
    - button "Fit project"
    - text: Fit the project in view · F Actions
    - button "Duplicate selection" [disabled]
    - text: Duplicate selection · Select an editable object first
    - button "Delete selection" [disabled]
    - text: Delete selection · Select an editable object first
    - button "Undo" [disabled]
    - text: Undo · No object edits to undo
    - button "Redo" [disabled]
    - text: Redo · No object edits to redo
  - button "Scene / Sun study"
  - button "Search workspace"
  - group: Import
  - button "Show AI Copilot panel": Assistant
  - complementary:
    - tablist "Inspector views":
      - tab "Layers"
      - tab "Inspect"
      - tab "History"
      - tab "Analysis"
      - tab "Review"
  - region "Engineering dock":
    - button "Engineering dock"
    - button "Cost —"
    - button "Cement —"
    - button "Steel —"
    - button "Excavation —"
    - button "Duration —"
    - button "Area —"
    - button "Risk —"
- alert
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | import demo from '../../docs/spatial-frame/demo.json';
  4  | const modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  5  | test.use({trace:'off'});
  6  | for(const width of [1280,1600])for(const d of demo)test(`spatial ${d.fixture.project_id} all modes at ${width}`,async({page,request})=>{
  7  |  test.setTimeout(180000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
  8  |  const a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);expect(a.database).toMatch(/foundation-system[\\/]isolated[\\/]foundation.db$/);
  9  |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  10 |  await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  11 |  await page.goto(`http://localhost:13001/projects/${d.fixture.project_id}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await expect(panel.getByLabel('Spatial load case')).toBeVisible();
  12 |  await panel.getByLabel('Spatial load case').selectOption(d.analysis.result.cases[2].case.name);
  13 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(canvas).toHaveAttribute('data-structural-transition','ready');await expect(panel.getByLabel('Spatial legend')).toBeVisible();
  14 |   if(key==='deformation'){await panel.getByLabel('Spatial displacement magnification').fill('100');await expect(panel).toContainText('magnification ×100');}
  15 |   if(key==='forces'){for(const force of ['My','Mz','Vy','Vz','N','T']){await panel.getByLabel('Spatial force').selectOption(force);await expect(panel.getByLabel('Spatial legend')).toContainText(`${force}:`);}await panel.getByLabel('Spatial force').selectOption('My');}
  16 |   const boxes=JSON.parse(await canvas.getAttribute('data-engineering-label-boxes')||'[]') as {x:number;y:number;width:number;height:number}[];for(const [i,a] of boxes.entries())for(const b of boxes.slice(i+1))expect(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y).toBe(false);
  17 |   if(d.fixture.inputs.nodes.length===18)await page.screenshot({path:`../docs/spatial-frame/${key}-${width}.png`});
  18 |  }
  19 |  for(const c of d.analysis.result.cases){await panel.getByLabel('Spatial load case').selectOption(c.case.name);await expect(panel.getByLabel('Spatial load case')).toHaveValue(c.case.name);}
  20 |  await panel.getByLabel('Spatial floor').selectOption(String(d.fixture.inputs.nodes.length===18?2:1));await panel.getByRole('button',{name:'Beam and column forces',exact:true}).click();const member=d.fixture.inputs.members.find(m=>m.floor===(d.fixture.inputs.nodes.length===18?2:1))!;await panel.getByLabel('Inspect spatial component').selectOption(member.id);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Computed |u|max');
  21 |  await panel.getByLabel('Spatial floor').selectOption('0');const slab=d.fixture.inputs.slabs[0];await panel.getByLabel('Inspect spatial component').selectOption(slab.id);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Load-only slab');
  22 |  await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready');const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(l=>l.key.startsWith('slab-')&&l.x>50&&l.x<900&&l.y>100&&l.y<850);if(pick){const box=await canvas.boundingBox();await page.mouse.click(box!.x+pick.x,box!.y+pick.y);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Load-only slab');}
  23 |  await panel.getByRole('button',{name:'Restore full geometry',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);expect(writes).toEqual([]);expect(errors).toEqual([]);
  24 |  writeFileSync(`../docs/spatial-frame/acceptance-${d.fixture.project_id}-${width}.json`,JSON.stringify({project:d.fixture.project_id,width,modes:7,force_components:6,load_cases:3,floor_filter:true,member_and_slab_inspection:true,writes,errors},null,2));
  25 | });
  26 | test('isolated exact review and authorize workflow',async({page,request})=>{
  27 |  test.setTimeout(180000);const a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);expect(a.database).toMatch(/foundation-system[\\/]isolated[\\/]foundation.db$/);
  28 |  const response=await request.post('http://127.0.0.1:18001/api/projects/793/engineering/spatial-frame/review-fixture',{data:{storeys:1,review_parametric_geometry:true}});expect(response.ok()).toBe(true);const fixture=await response.json();
> 29 |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{const req=r.request();if(!['GET','HEAD','OPTIONS'].includes(req.method())){expect(req.url()).toMatch(/^http:\/\/127\.0\.0\.1:18001\/api\/projects\/\d+\/engineering\/spatial-frame\/(review|authorize-run)$/);writes.push(req.url());}if(req.url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
     |                                                                                                                                         ^ Error: expect(locator).toHaveAttribute(expected) failed
  30 |  await page.goto(`http://localhost:13001/projects/${fixture.project_id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await panel.getByText('Review and authorize local solver inputs',{exact:true}).click();await panel.getByRole('button',{name:'Prepare exact saved review',exact:true}).click();await expect(panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true})).toBeEnabled();await panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true}).click();await expect(panel.getByLabel('Spatial load case')).toBeVisible();expect(writes).toHaveLength(2);expect(errors).toEqual([]);writeFileSync('../docs/spatial-frame/authorization-browser.json',JSON.stringify({project:fixture.project_id,reviewed:true,authorized_exact_hash:true,writes,errors},null,2));
  31 | });
  32 | for(const id of [793,794,804])test(`normal original ${id} read-only regression`,async({page})=>{
  33 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false');expect(writes).toEqual([]);expect(errors).toEqual([]);
  34 | });
  35 | 
```