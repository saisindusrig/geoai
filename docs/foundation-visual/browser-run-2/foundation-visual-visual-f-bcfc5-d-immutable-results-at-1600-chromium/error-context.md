# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-visual.spec.ts >> visual foundation modes, picking, ghost alternatives and immutable results at 1600
- Location: e2e\foundation-visual.spec.ts:7:36

# Error details

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator: getByRole('article', { name: 'Foundation visual analysis' }).locator('details')
Expected: ""
Timeout: 30000ms
Error: element(s) not found

Call log:
  - Expect "toHaveAttribute" getByRole('article', { name: 'Foundation visual analysis' }).locator('details') with timeout 30000ms
  - waiting for getByRole('article', { name: 'Foundation visual analysis' }).locator('details')
    3 × locator resolved to <details>…</details>
      - unexpected value "null"

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- banner:
  - link "GeoAI home":
    - /url: /
    - text: GeoAI
  - heading "Foundation integrated study · reference 804" [level=1]
  - link "3D Sandbox editor":
    - /url: /projects/999999/workspace?local=1
  - link "Projects":
    - /url: /dashboard
  - button "Save site geometry"
  - link "Export":
    - /url: /projects/814/report
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
  - paragraph: CAD footing SW · click to select
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
      - button "Edit site boundary" [disabled]
      - text: Edit site boundary · Draw a site boundary first
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
    - paragraph: 1 selected · select
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
    - button "Negative Z axis view" [disabled]
    - button "Negative Y axis view"
    - button "Positive X axis view": X
    - button "Negative X axis view"
    - button "Positive Y axis view": "Y"
    - button "Positive Z axis view": Z
  - separator "Resize panel width"
  - complementary:
    - text: Inspect
    - button "Close inspector"
    - tabpanel "Inspect":
      - region "Object summary":
        - heading "CAD footing SW" [level=3]
        - paragraph: foundation · Editable
        - term: Dimensions · metres
        - definition: 1.200 × 1.200 × 0.450 m
        - term: Position · East / North / Up · m
        - definition: 0.150 / 0.150 / -0.225
        - term: Orientation · X / Y / Z · degrees
        - definition: 0.0 / 0.0 / 0.0
        - term: Geometry source
        - definition: Reviewed CAD entity dxf:614f117ae2a74794:9A
        - term: Material verification
        - definition: Unverified · appearance is not engineering evidence · declaration supplied, independent validation not established
        - term: Stable component ID
        - definition: drawing-cad:614f117ae2a74794:9A
        - term: Appearance finish · illustrative
        - definition: Concrete-style appearance
        - term: Declared engineering material
        - definition: Explicit synthetic material identity; no grade/E/fy
        - group: Material declaration source
        - paragraph: Saved v1 · Engineering Unverified
        - button "Fit selection"
        - button "Edit"
        - button "Existing analysis"
        - button "Isolate"
        - button "Hide"
        - button "Restore visibility"
      - group: Assembly tools and parameters
      - heading "Edit component" [level=3]
      - paragraph: "Local axes: East / North / Up · metres. Changes remain pending until Apply, then Save model."
      - text: Component name
      - textbox "Component name": CAD footing SW
      - paragraph: Dimensions · metres
      - text: Dimensions · metres X
      - textbox "Dimensions · metres X": "1.2"
      - text: Dimensions · metres Y
      - textbox "Dimensions · metres Y": "1.2"
      - text: Dimensions · metres Z
      - textbox "Dimensions · metres Z": "0.45"
      - paragraph: Position · metres
      - text: Position · metres East
      - textbox "Position · metres East": "0.15"
      - text: Position · metres North
      - textbox "Position · metres North": "0.15"
      - text: Position · metres Up
      - textbox "Position · metres Up": "-0.225"
      - paragraph: Rotation · degrees
      - text: Rotation · degrees X
      - textbox "Rotation · degrees X": "0"
      - text: Rotation · degrees Y
      - textbox "Rotation · degrees Y": "0"
      - text: Rotation · degrees Z
      - textbox "Rotation · degrees Z": "0"
      - group: Scale and appearance
      - status: No pending changes
      - button "Preview" [disabled]
      - button "Apply" [disabled]
      - button "Cancel"
      - group: Identity and source references
    - tablist "Inspector views":
      - tab "Layers"
      - tab "Inspect" [selected]
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
  15 |  await page.route('**/*',async r=>{if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(r.request().url()))throw new Error('Original backend forbidden');await r.fallback();});
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
> 39 |  await expect(visual.getByText('Selected check · detailed evidence')).toBeVisible();await expect(visual.locator('details')).toHaveAttribute('open','');
     |                                                                                                                             ^ Error: expect(locator).toHaveAttribute(expected) failed
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
  55 | 
```