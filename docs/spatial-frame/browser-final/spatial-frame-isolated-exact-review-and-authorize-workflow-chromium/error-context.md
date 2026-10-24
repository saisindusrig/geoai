# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: spatial-frame.spec.ts >> isolated exact review and authorize workflow
- Location: e2e\spatial-frame.spec.ts:26:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: 'Spatial structural engineering' }).getByLabel('Spatial load case')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: 'Spatial structural engineering' }).getByLabel('Spatial load case') with timeout 5000ms
  - waiting for getByRole('region', { name: 'Spatial structural engineering' }).getByLabel('Spatial load case')

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
    - /url: /projects/825/report
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
  - text: 12.97160° N · 77.59460° E
  - button "Select" [pressed]
  - button "Orbit"
  - button "Pan"
  - button "Mouse controls"
  - button "Model view" [pressed]
  - text: /
  - button "Site view"
  - text: Illustrative finishes · not material evidence
  - group: Standard views
  - button "Focus Structure"
  - button "Fit All"
  - button "Fit selection" [disabled]
  - button "Dimensions off"
  - group: Display legend
  - button "Full screen"
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
      - button "Edit site boundary"
      - text: Drag existing boundary vertices
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
  - group "Camera orientation gizmo":
    - button "Positive Y axis view": "Y"
    - button "Negative Z axis view" [disabled]
    - button "Positive X axis view": X
    - button "Negative X axis view"
    - button "Positive Z axis view": Z
    - button "Negative Y axis view"
  - complementary:
    - text: Analysis
    - button "Close inspector"
    - tabpanel "Analysis":
      - region "Spatial structural engineering":
        - heading "Connected 3D frame · explore" [level=3]
        - paragraph: Synthetic verification · no safety or code approval
        - button "Structural load paths" [disabled] [pressed]
        - button "Applied loads and reactions" [disabled]
        - button "Deformed versus original" [disabled]
        - button "Beam and column forces" [disabled]
        - button "Slab-to-beam distribution" [disabled]
        - button "Foundation and soil response" [disabled]
        - button "Warnings and connections" [disabled]
        - paragraph: Loading, running or unsaved preview · saved overlays disabled.
        - paragraph: No current verified spatial result. No response field or load path is fabricated.
        - group:
          - text: Review and authorize local solver inputs
          - paragraph: Review saved parametric geometry, fixed bases, shared-node rigid joints, E/G/A/I/J and declared loads. J is a synthetic input; no actual RC torsion capacity. No self-weight added. Review does not execute the solver.
          - text: "{ \"nodes\": [ { \"id\": 1, \"position\": [ 0, 0, 0 ], \"fixed\": true }, { \"id\": 2, \"position\": [ 4, 0, 0 ], \"fixed\": true }, { \"id\": 3, \"position\": [ 8, 0, 0 ], \"fixed\": true }, { \"id\": 4, \"position\": [ 0, 4, 0 ], \"fixed\": true }, { \"id\": 5, \"position\": [ 4, 4, 0 ], \"fixed\": true }, { \"id\": 6, \"position\": [ 8, 4, 0 ], \"fixed\": true }, { \"id\": 7, \"position\": [ 0, 0, 3 ], \"fixed\": false }, { \"id\": 8, \"position\": [ 4, 0, 3 ], \"fixed\": false }, { \"id\": 9, \"position\": [ 8, 0, 3 ], \"fixed\": false }, { \"id\": 10, \"position\": [ 0, 4, 3 ], \"fixed\": false }, { \"id\": 11, \"position\": [ 4, 4, 3 ], \"fixed\": false }, { \"id\": 12, \"position\": [ 8, 4, 3 ], \"fixed\": false } ], \"members\": [ { \"id\": \"column-F1-N1-7\", \"nodes\": [ 1, 7 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"column-F1-N2-8\", \"nodes\": [ 2, 8 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"column-F1-N3-9\", \"nodes\": [ 3, 9 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"column-F1-N4-10\", \"nodes\": [ 4, 10 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"column-F1-N5-11\", \"nodes\": [ 5, 11 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"column-F1-N6-12\", \"nodes\": [ 6, 12 ], \"floor\": 1, \"kind\": \"column\", \"vecxz\": [ 0, 1, 0 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N7-8\", \"nodes\": [ 7, 8 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N8-9\", \"nodes\": [ 8, 9 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N10-11\", \"nodes\": [ 10, 11 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N11-12\", \"nodes\": [ 11, 12 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N7-10\", \"nodes\": [ 7, 10 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N8-11\", \"nodes\": [ 8, 11 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 }, { \"id\": \"beam-F1-N9-12\", \"nodes\": [ 9, 12 ], \"floor\": 1, \"kind\": \"beam\", \"vecxz\": [ 0, 0, 1 ], \"E\": 30000000000, \"G\": 12500000000, \"A\": 0.09, \"Iy\": 0.0006749999999999998, \"Iz\": 0.0006749999999999998, \"J\": 0.001 } ], \"slabs\": [ { \"id\": \"slab-F1-B1\", \"floor\": 1, \"beams\": [ \"beam-F1-N7-8\", \"beam-F1-N10-11\" ], \"width_m\": 4, \"pressure_pa\": 5000 }, { \"id\": \"slab-F1-B2\", \"floor\": 1, \"beams\": [ \"beam-F1-N8-9\", \"beam-F1-N11-12\" ], \"width_m\": 4, \"pressure_pa\": 5000 } ], \"cases\": [ { \"name\": \"Gravity · 5 kPa one-way slabs\", \"nodal\": {}, \"slab_factor\": 1 }, { \"name\": \"Lateral · E + N nodal actions\", \"nodal\": { \"7\": [ 1000, 600, 0, 0, 0, 0 ], \"8\": [ 1000, 600, 0, 0, 0, 0 ], \"9\": [ 1000, 600, 0, 0, 0, 0 ], \"10\": [ 1500, 600, 0, 0, 0, 0 ], \"11\": [ 1500, 600, 0, 0, 0, 0 ], \"12\": [ 1500, 600, 0, 0, 0, 0 ] }, \"slab_factor\": 0 }, { \"name\": \"Linear gravity + lateral\", \"nodal\": { \"7\": [ 1000, 600, 0, 0, 0, 0 ], \"8\": [ 1000, 600, 0, 0, 0, 0 ], \"9\": [ 1000, 600, 0, 0, 0, 0 ], \"10\": [ 1500, 600, 0, 0, 0, 0 ], \"11\": [ 1500, 600, 0, 0, 0, 0 ], \"12\": [ 1500, 600, 0, 0, 0, 0 ] }, \"slab_factor\": 1 } ], \"connection_review\": \"rigid_coincident_joints_reviewed\", \"section_source\": \"Synthetic uncracked E=30 GPa, G=12.5 GPa; 300 mm square A/I bound to CAD; prescribed J=0.001 m4 (not physical RC torsion design). Slab 5 kPa includes declared total gravity; member self-weight excluded.\", \"purpose\": \"SYNTHETIC_VERIFICATION_ONLY\" }"
          - button "Prepare exact saved review" [disabled]
          - paragraph: Review 685 · SHA 85e224de02d0dbb8e0a96c83fc1d41bb050dd4a0e1ceb4a57aeba95451f609d9
          - button "Authorize exact local OpenSees run" [disabled]
      - group: Analysis overview and input guidance
      - group: Advanced analysis · inputs, tools and evidence
    - tablist "Inspector views":
      - tab "Layers"
      - tab "Inspect"
      - tab "History"
      - tab "Analysis" [selected]
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
  29 |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{const req=r.request();if(!['GET','HEAD','OPTIONS'].includes(req.method())){expect(req.url()).toMatch(/^http:\/\/127\.0\.0\.1:18001\/api\/projects\/\d+\/engineering\/spatial-frame\/(review|authorize-run)$/);writes.push(req.url());}if(req.url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
> 30 |  await page.goto(`http://localhost:13001/projects/${fixture.project_id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await panel.getByText('Review and authorize local solver inputs',{exact:true}).click();await panel.getByRole('button',{name:'Prepare exact saved review',exact:true}).click();await expect(panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true})).toBeEnabled();await panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true}).click();await expect(panel.getByLabel('Spatial load case')).toBeVisible();expect(writes).toHaveLength(2);expect(errors).toEqual([]);writeFileSync('../docs/spatial-frame/authorization-browser.json',JSON.stringify({project:fixture.project_id,reviewed:true,authorized_exact_hash:true,writes,errors},null,2));
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               ^ Error: expect(locator).toBeVisible() failed
  31 | });
  32 | for(const id of [793,794,804])test(`normal original ${id} read-only regression`,async({page})=>{
  33 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false');expect(writes).toEqual([]);expect(errors).toEqual([]);
  34 | });
  35 | 
```