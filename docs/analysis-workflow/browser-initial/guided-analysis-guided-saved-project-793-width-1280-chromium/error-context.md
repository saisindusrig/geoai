# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: guided-analysis.spec.ts >> guided saved project 793 width 1280
- Location: e2e\guided-analysis.spec.ts:5:57

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: 'Guided Analysis', exact: true }).getByRole('navigation', { name: 'Analysis steps' })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: 'Guided Analysis', exact: true }).getByRole('navigation', { name: 'Analysis steps' }) with timeout 5000ms
  - waiting for getByRole('region', { name: 'Guided Analysis', exact: true }).getByRole('navigation', { name: 'Analysis steps' })

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- banner:
  - link "GeoAI home":
    - /url: /
    - text: GeoAI
  - heading "Unequal CAD frame — gravity and distributed load verification" [level=1]
  - link "3D Sandbox editor":
    - /url: /projects/999999/workspace?local=1
  - link "Projects":
    - /url: /dashboard
  - button "Save site geometry"
  - link "Export":
    - /url: /projects/793/report
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
  - status: Saved · v2
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
    - button "Negative Y axis view"
    - button "Positive X axis view": X
    - button "Negative Z axis view" [disabled]
    - button "Positive Z axis view": Z
    - button "Negative X axis view"
    - button "Positive Y axis view": "Y"
  - complementary:
    - text: Analysis
    - button "Close inspector"
    - tabpanel "Analysis":
      - region "Structural visual engineering":
        - heading "Structure · explore in 3D" [level=3]
        - paragraph: Saved analytical evidence · no safety or code approval
        - button "Structural load paths" [pressed]
        - button "Applied loads and reactions"
        - button "Deformed versus original"
        - button "Beam and column forces"
        - button "Slab-to-beam distribution"
        - button "Foundation and soil response"
        - button "Warnings and connections"
        - text: Saved load case
        - combobox "Structural saved load case":
          - option "Linear sum" [selected]
          - option "Horizontal"
          - option "Gravity"
          - option "Self weight"
        - group: Compare available saved load cases
        - text: "Cyan: saved member topology · pink: declared rigid arms. Topology arrows are not force magnitudes or directions. Connections have no verified capacity."
        - paragraph: Labels avoid overlap. Select a component or yellow marker for full saved values.
        - checkbox "Isolate analyzed structural system" [checked]
        - text: Isolate analyzed system
        - button "Frame view"
        - button "Restore full structure"
        - text: Inspect saved component
        - combobox "Inspect structural component":
          - option "Click a component in 3D or choose here" [selected]
          - option "beam-east · beam"
          - option "beam-north · beam"
          - option "beam-south · beam"
          - option "beam-west · beam"
          - option "column-ne · column"
          - option "column-nw · column"
          - option "column-se · column"
          - option "column-sw · column"
          - option "platform-deck · slab"
          - option "foundation c9e0e256-1608-4be2-b1ab-adafa10424c0 · body · foundation"
          - option "base plate 44d566cb-7ca0-4c95-bf4d-1d574f788df0 · body · base_plate"
          - option "connection 149f0f5d-b98f-4260-a428-b2fc50959cf2 · joint · connection"
          - option "foundation b1ad97d4-faca-46e7-87c9-f5eebb37575f · body · foundation"
          - option "base plate d9a7247f-b6fa-4e50-a3de-7a8c243f3dc3 · body · base_plate"
          - option "connection 13ff4b82-88f8-4c41-9613-ad85bf72054b · joint · connection"
          - option "foundation 9c6c5059-9557-4c35-887a-a66e95606df4 · body · foundation"
          - option "base plate 2054528e-2362-4a24-843c-01988b6c8fea · body · base_plate"
          - option "connection a1f8b089-a278-4474-8596-ff0dade18975 · joint · connection"
          - option "foundation 850c983b-9d8c-416d-8785-eb7106e068bb · body · foundation"
          - option "base plate b5d32b14-a981-4478-888f-42d19034592d · body · base_plate"
          - option "connection ed0730b0-c13b-47ba-9753-b63f1e86d4ac · joint · connection"
          - option "CAD column SW · column"
          - option "CAD column SE · column"
          - option "CAD beam South · beam"
          - option "CAD slab · slab"
          - option "CAD footing SW · foundation"
          - option "CAD footing SE · foundation"
        - group: Coverage, warnings and immutable numerical evidence
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
  3  | import review from '../../docs/analysis-workflow/review-projects.json';
  4  | const cases=[{id:793,port:3001,family:'Structural analysis',result:true},{id:794,port:3001,family:'Slabs and floor systems',result:true},{id:804,port:3001,family:'Foundations and soil',result:false},{id:814,port:13001,family:'Foundations and soil',result:true},{id:823,port:13001,family:'Structural analysis',result:true},{id:828,port:13001,family:'Slabs and floor systems',result:true},{id:review.projects[0].project_id,port:13001,family:'Structural analysis',result:false}];
  5  | for(const width of [1280,1600])for(const c of cases)test(`guided saved project ${c.id} width ${width}`,async({page})=>{
  6  |  test.setTimeout(180000);await page.setViewportSize({width,height:1000});const errors:string[]=[],writes:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
> 7  |  await page.goto(`http://localhost:${c.port}/projects/${c.id}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Guided Analysis',exact:true});await expect(panel.getByRole('navigation',{name:'Analysis steps'})).toBeVisible();await panel.getByRole('button',{name:new RegExp('^'+c.family)}).click();await expect(panel.getByText('Reading saved analysis — no calculation is running.',{exact:true})).toHaveCount(0,{timeout:60000});
     |                                                                                                                                                                                                                                                                                                                                                                                                                               ^ Error: expect(locator).toBeVisible() failed
  8  |  await panel.getByRole('button',{name:'1 SELECT',exact:true}).focus();await page.keyboard.press('Tab');await expect(panel.getByRole('button',{name:'2 INPUTS',exact:true})).toBeFocused();await page.keyboard.press('Enter');await expect(panel.getByRole('heading',{name:'Review engineering inputs'})).toBeVisible();await panel.getByRole('button',{name:'1 SELECT',exact:true}).click();
  9  |  if(c.result){await panel.getByRole('button',{name:'Open saved results — no rerun',exact:true}).click();await expect(panel.getByLabel('Guided visual results')).toBeVisible();for(const name of ['Loads and reactions','Deformation','Bending / shear / axial','Warnings and unsupported checks']){const button=panel.getByRole('button',{name,exact:true});if(await button.isEnabled())await button.click();}await panel.getByRole('button',{name:'Loads and reactions',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready',{timeout:15000});await page.screenshot({path:`../docs/analysis-workflow/after-${c.id}-${width}.png`});await panel.getByLabel('Current analysis context').getByRole('button',{name:'Restore model',exact:true}).click();await expect(panel.getByText('View: complete CAD geometry.',{exact:true})).toBeVisible();await panel.getByRole('button',{name:'Deformation',exact:true}).isEnabled().then(async enabled=>{if(enabled)await panel.getByRole('button',{name:'Deformation',exact:true}).click();});
  10 |   await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(panel.getByLabel('Guided visual results')).toBeVisible({timeout:60000});
  11 |  }else{await expect(panel.getByRole('button',{name:'Continue to inputs',exact:true})).toBeDisabled();await page.screenshot({path:`../docs/analysis-workflow/after-${c.id}-${width}.png`});}
  12 |  await expect(panel.getByLabel('Advanced engineering tools')).toHaveCount(0);await panel.getByRole('button',{name:'Advanced mode',exact:true}).click();await expect(panel.getByLabel('Advanced engineering tools')).toBeVisible();await panel.getByRole('button',{name:'Return to guided workflow',exact:true}).click();expect(errors).toEqual([]);expect(writes).toEqual([]);writeFileSync(`../docs/analysis-workflow/browser-${c.id}-${width}.json`,JSON.stringify({project:c.id,width,keyboard:true,read_only:true,reopened_results:c.result,advanced_access:true,writes,errors},null,2));
  13 | });
  14 | test('first-time structural review and explicit authorization without accordions',async({page,request})=>{
  15 |  test.setTimeout(240000);await page.setViewportSize({width:1600,height:1000});const id=review.projects[1].project_id,base=`/api/projects/${id}/engineering/assembly`,a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{const url=r.request().url();if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(url);if(!url.startsWith('http://127.0.0.1:18001'+base+'/')||!['preview','inputs','proposals','authorize-run'].some(s=>url.endsWith('/'+s)))return r.abort();}if(url.includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  16 |  await page.goto(`http://localhost:13001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const p=page.getByRole('region',{name:'Guided Analysis',exact:true});await p.getByRole('button',{name:'Continue to inputs',exact:true}).click();
  17 |  await p.getByLabel('Analysis Column 1').selectOption('guided-left');await p.getByLabel('Analysis Beam',{exact:true}).selectOption('guided-beam');await p.getByLabel('Analysis Column 2').selectOption('guided-right');await p.getByRole('button',{name:'Select these members',exact:true}).click();
  18 |  await p.getByRole('button',{name:'Inspect selected geometry',exact:true}).click();await expect(p.getByLabel('Structural inputs')).toBeVisible();for(const name of ['guided-left','guided-beam','guided-right'])await p.getByLabel(`${name} elastic modulus GPa`).fill('200');for(const input of await p.getByLabel('Material identification',{exact:true}).all())await input.fill('Synthetic elastic steel');for(const input of await p.getByLabel('Material source or declared assumption',{exact:true}).all())await input.fill('Explicit synthetic E=200 GPa verification input');await p.getByLabel('Declare observed solid rectangular sections').check();await p.getByLabel('Guided base restraints').selectOption('both_column_bases_fixed');await p.getByLabel('Guided support source').fill('Synthetic fixed bases, not foundation capacity');await p.getByLabel('Declare analytical joints').check();await p.getByLabel('Guided joint source').fill('Explicit synthetic coincident rigid joints, no capacity');await p.getByLabel('Guided total horizontal kN').fill('20');await p.getByLabel('Guided load source').fill('Explicit synthetic 20 kN total horizontal verification load');await p.getByRole('button',{name:'Continue to review',exact:true}).click();await p.getByLabel('Review analytical assumptions').check();await p.getByRole('button',{name:'Review exact analysis proposal',exact:true}).click();await expect(p.getByLabel('Authorize exact reviewed analysis')).toBeVisible();expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(0);await expect(p.getByRole('button',{name:'Authorize and analyze',exact:true})).toBeDisabled();await p.getByLabel('Review analytical assumptions').check();await p.getByLabel('Authorize exact reviewed analysis').check();await p.getByRole('button',{name:'Authorize and analyze',exact:true}).click();await expect(p.getByLabel('Guided visual results')).toBeVisible({timeout:90000});await page.screenshot({path:'../docs/analysis-workflow/completed-structural-analysis.png'});expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(1);expect(errors).toEqual([]);writeFileSync('../docs/analysis-workflow/modifying-acceptance.json',JSON.stringify({isolated_database:a.database,project:id,explicit_authorization:true,technical_accordions_used:0,writes,errors},null,2));
  19 | });
  20 | 
```