# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: guided-analysis.spec.ts >> first-time structural review and explicit authorization without accordions
- Location: e2e\guided-analysis.spec.ts:14:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: 'Guided Analysis', exact: true }).getByLabel('Authorize exact reviewed analysis')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: 'Guided Analysis', exact: true }).getByLabel('Authorize exact reviewed analysis') with timeout 5000ms
  - waiting for getByRole('region', { name: 'Guided Analysis', exact: true }).getByLabel('Authorize exact reviewed analysis')

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- banner:
  - link "GeoAI home":
    - /url: /
    - text: GeoAI
  - heading "Guided planar analysis verification" [level=1]
  - link "3D Sandbox editor":
    - /url: /projects/999999/workspace?local=1
  - link "Projects":
    - /url: /dashboard
  - button "Save site geometry"
  - link "Export":
    - /url: /projects/830/report
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
  - button "Fit selection"
  - button "Dimensions off"
  - group: Display legend
  - button "Full screen"
  - complementary "Workspace tools":
    - group "Object editing":
      - text: Edit
      - button "Select object" [pressed]
      - text: Click to select and inspect · Ctrl to add · V
      - button "Move selection"
      - text: Move selected objects · G · changes geometry; undo with Ctrl+Z
      - button "Rotate selection"
      - text: Rotate selected objects · R · review local/global axes
      - button "Scale selection"
      - text: Scale selected objects · S · changes dimensions; engineering results may become stale
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
    - button "Frame selection"
    - text: Focus the selected object · F Actions
    - button "Duplicate selection"
    - text: Duplicate selected objects
    - button "Delete selection"
    - text: Delete selected objects · Del
    - button "Undo" [disabled]
    - text: Undo · No object edits to undo
    - button "Redo" [disabled]
    - text: Redo · No object edits to redo
  - status:
    - paragraph: 3 selected · select
    - button "Inspect selection"
    - paragraph: Step 0.5 m · Esc cancels · Ctrl+Z undoes
    - button "Move west one step": E−
    - button "Move east one step": E+
    - button "Move north one step": N+
    - button "Clear selection"
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
      - region "Guided Analysis":
        - heading "Analysis" [level=2]
        - button "Advanced mode"
        - paragraph: Structural analysis · assembly · Step 3 of 4
        - paragraph: "Selected: guided-left, guided-beam, guided-right · 3 CAD components"
        - paragraph: "Active result: None current · revision 157"
        - paragraph: "Next: Prepare an exact review"
        - button "Restore model"
        - navigation "Analysis steps":
          - button "1 SELECT"
          - button "2 INPUTS"
          - button "3 ANALYZE"
          - button "4 RESULTS"
        - heading "Review and authorize" [level=3]
        - alert:
          - paragraph: Centerline declaration cannot contain an offset approval or nonzero vector
          - button "Retry reading saved analysis"
          - paragraph: Failed/stale proposals require a new review; calculations are never retried automatically.
        - list "Analysis readiness":
          - listitem: ✓ Saved revision selected
          - listitem: ✓ Method available for review
          - listitem: No current saved result
        - paragraph: Numerical verification only. Analytical supports/joints do not establish physical capacity. Unsupported methods remain disabled. No structural safety or code approval.
        - checkbox "Review analytical assumptions" [checked]
        - text: I reviewed the declared inputs, analytical assumptions and exclusions.
        - button "Review exact analysis proposal"
        - button "Edit inputs"
        - button "Reload saved inputs and results"
        - paragraph: Reopening restores browser view preferences and saved evidence only. It never authorizes or reruns a solver.
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
  7  |  await page.goto(`http://localhost:${c.port}/projects/${c.id}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Guided Analysis',exact:true});await expect(panel.getByRole('navigation',{name:'Analysis steps'})).toBeVisible();await panel.getByRole('button',{name:new RegExp('^'+c.family)}).click();await expect(panel.getByText('Reading saved analysis — no calculation is running.',{exact:true})).toHaveCount(0,{timeout:60000});
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
> 18 |  await p.getByRole('button',{name:'Inspect selected geometry',exact:true}).click();await expect(p.getByLabel('Structural inputs')).toBeVisible();for(const name of ['guided-left','guided-beam','guided-right'])await p.getByLabel(`${name} elastic modulus GPa`).fill('200');for(const input of await p.getByLabel('Material identification',{exact:true}).all())await input.fill('Synthetic elastic steel');for(const input of await p.getByLabel('Material source or declared assumption',{exact:true}).all())await input.fill('Explicit synthetic E=200 GPa verification input');await p.getByLabel('Declare observed solid rectangular sections').check();await p.getByLabel('Guided base restraints').selectOption('both_column_bases_fixed');await p.getByLabel('Guided support source').fill('Synthetic fixed bases, not foundation capacity');await p.getByLabel('Declare analytical joints').check();await p.getByLabel('Guided joint source').fill('Explicit synthetic coincident rigid joints, no capacity');await p.getByLabel('Guided total horizontal kN').fill('20');await p.getByLabel('Guided load source').fill('Explicit synthetic 20 kN total horizontal verification load');await p.getByRole('button',{name:'Continue to review',exact:true}).click();await p.getByLabel('Review analytical assumptions').check();await p.getByRole('button',{name:'Review exact analysis proposal',exact:true}).click();await expect(p.getByLabel('Authorize exact reviewed analysis')).toBeVisible();expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(0);await expect(p.getByRole('button',{name:'Authorize and analyze',exact:true})).toBeDisabled();await p.getByLabel('Review analytical assumptions').check();await p.getByLabel('Authorize exact reviewed analysis').check();await p.getByRole('button',{name:'Authorize and analyze',exact:true}).click();await expect(p.getByLabel('Guided visual results')).toBeVisible({timeout:90000});await page.screenshot({path:'../docs/analysis-workflow/completed-structural-analysis.png'});expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(1);expect(errors).toEqual([]);writeFileSync('../docs/analysis-workflow/modifying-acceptance.json',JSON.stringify({isolated_database:a.database,project:id,explicit_authorization:true,technical_accordions_used:0,writes,errors},null,2));
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ^ Error: expect(locator).toBeVisible() failed
  19 | });
  20 | 
```