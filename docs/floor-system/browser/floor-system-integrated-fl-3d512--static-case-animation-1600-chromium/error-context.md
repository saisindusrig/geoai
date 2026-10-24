# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: floor-system.spec.ts >> integrated floors, topology and static-case animation 1600
- Location: e2e\floor-system.spec.ts:5:36

# Error details

```
TimeoutError: locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for getByRole('region', { name: 'Spatial structural engineering' }).getByText(/Route · \d+ verified topology steps/)
    - locator resolved to <summary>Route · 6 verified topology steps</summary>
  - attempting click action
    - waiting for element to be visible, enabled and stable
  - element was detached from the DOM, retrying

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e4]:
    - banner [ref=e5]:
      - link "GeoAI home" [ref=e6] [cursor=pointer]:
        - /url: /
        - generic "GeoAI" [ref=e7]
      - heading "Spatial review · 2×1 bays · 2 storey · synthetic" [level=1] [ref=e13]
      - generic [ref=e14]:
        - link "3D Sandbox editor" [ref=e15] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
        - link "Projects" [ref=e19] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=e20]:
          - button "Save site geometry" [ref=e21]
          - link [ref=e26] [cursor=pointer]:
            - /url: /projects/823/report
            - button "Export" [ref=e27]
        - link [ref=e31] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=e32]
        - link "Open settings" [ref=e34] [cursor=pointer]:
          - /url: /settings
    - main [ref=e38]:
      - generic [ref=e41]:
        - generic [ref=e42]:
          - generic "Design workflow" [ref=e46]:
            - button "1 Site" [ref=e47]
            - group [ref=e48]:
              - generic "Workflow help" [ref=e49] [cursor=pointer]
            - group [ref=e50]:
              - generic "2 Create / Import" [ref=e51] [cursor=pointer]
            - button "3 Review 3D" [ref=e52]
            - button "4 Edit" [ref=e53]
            - button "5 Analyze / Results" [ref=e54]
            - button "6 Review" [ref=e55]
            - status [ref=e56]: Saved · v1
            - button "Save model" [disabled]
          - generic [ref=e57]:
            - generic [ref=e58]:
              - generic [ref=e61]:
                - generic: 12.97160° N · 77.59460° E
                - generic [ref=e62]:
                  - generic "Mouse navigation" [ref=e63]:
                    - button "Select" [pressed] [ref=e64]
                    - button "Orbit" [ref=e65]
                    - button "Pan" [ref=e66]
                    - button "Mouse controls" [ref=e67]
                  - paragraph: Slab F2 B1 · click to select
                  - generic "Viewport presentation" [ref=e68]:
                    - generic [ref=e69]:
                      - button "Model view" [pressed] [ref=e70]
                      - generic [ref=e71]: /
                      - button "Site view" [ref=e72]
                      - generic [ref=e73]: Illustrative finishes · not material evidence
                    - generic [ref=e74]:
                      - group [ref=e75]:
                        - generic "Standard views" [ref=e76] [cursor=pointer]
                      - button "Focus Structure" [ref=e77]
                      - button "Fit All" [ref=e78]
                      - button "Fit selection" [ref=e79]
                      - button "Dimensions off" [ref=e80]
                      - group [ref=e81]:
                        - generic "Display legend" [ref=e82] [cursor=pointer]
                  - generic [ref=e84]:
                    - generic "3D workspace viewport" [active] [ref=e87]
                    - button "Full screen" [ref=e89] [cursor=pointer]
              - generic [ref=e92]:
                - complementary "Workspace tools" [ref=e93]:
                  - group "Object editing" [ref=e94]:
                    - generic [ref=e95]: Edit
                    - generic "Click to select and inspect · Ctrl to add · V" [ref=e96]:
                      - button "Select object" [pressed] [ref=e97]
                    - generic "Move selected objects · G · changes geometry; undo with Ctrl+Z" [ref=e101]:
                      - button "Move selection" [ref=e102]
                    - generic "Rotate selected objects · R · review local/global axes" [ref=e109]:
                      - button "Rotate selection" [ref=e110]
                    - generic "Scale selected objects · S · changes dimensions; engineering results may become stale" [ref=e115]:
                      - button "Scale selection" [ref=e116]
                  - group "Site geometry" [ref=e124]:
                    - generic [ref=e125]: Site
                    - generic "Draw a rectangular site boundary" [ref=e126]:
                      - button "Draw rectangular boundary" [ref=e127]
                    - generic "Draw a closed site boundary" [ref=e131]:
                      - button "Draw site boundary" [ref=e132]
                    - generic "Drag existing boundary vertices" [ref=e136]:
                      - button "Edit site boundary" [ref=e137]
                    - generic "Draw a road or infrastructure centerline" [ref=e142]:
                      - button "Draw alignment" [ref=e143]
                    - generic "Edit alignment · Draw an alignment first" [ref=e149]:
                      - button "Edit alignment" [disabled] [ref=e150]
                  - generic [ref=e160]: View
                  - generic "Measure distance, elevation, slope, area or clearance · M" [ref=e161]:
                    - button "Measure" [ref=e162]
                  - generic "Focus the selected object · F" [ref=e170]:
                    - button "Frame selection" [ref=e171]
                  - generic [ref=e180]: Actions
                  - generic "Duplicate selected objects" [ref=e181]:
                    - button "Duplicate selection" [ref=e182]
                  - generic "Delete selected objects · Del" [ref=e187]:
                    - button "Delete selection" [ref=e188]
                  - generic "Undo · No object edits to undo" [ref=e194]:
                    - button "Undo" [disabled] [ref=e195]
                  - generic "Redo · No object edits to redo" [ref=e200]:
                    - button "Redo" [disabled] [ref=e201]
                - status [ref=e206]:
                  - paragraph [ref=e207]: 1 selected · select
                  - button "Inspect selection" [ref=e208]
                  - paragraph [ref=e209]: Step 0.5 m · Esc cancels · Ctrl+Z undoes
                  - generic [ref=e210]:
                    - button "Move west one step" [ref=e211]: E−
                    - button "Move east one step" [ref=e212]: E+
                    - button "Move north one step" [ref=e213]: N+
                  - button "Clear selection" [ref=e214]
              - generic [ref=e215]:
                - generic "Scene / Sun study" [ref=e216]:
                  - button "Scene / Sun study" [ref=e217]
                - button "Search workspace" [ref=e225]
                - group [ref=e229]:
                  - generic "Import site geometry" [ref=e230] [cursor=pointer]: Import
              - button "Show AI Copilot panel" [ref=e235]:
                - generic [ref=e239]: Assistant
              - group "Camera orientation gizmo" [ref=e240]:
                - button "Positive Y axis view" [ref=e246]: "Y"
                - button "Positive X axis view" [ref=e247]: X
                - button "Negative Z axis view" [disabled] [ref=e248]
                - button "Positive Z axis view" [ref=e249]: Z
                - button "Negative X axis view" [ref=e250]
                - button "Negative Y axis view" [ref=e251]
            - generic [ref=e252]:
              - separator "Resize panel width" [ref=e253]
              - complementary [ref=e254]:
                - generic [ref=e256]:
                  - generic [ref=e257]:
                    - generic [ref=e259]:
                      - generic [ref=e260]: Inspect
                      - button "Close inspector" [ref=e261]
                    - tabpanel "Inspect" [ref=e265]:
                      - region "Object summary" [ref=e266]:
                        - generic [ref=e267]:
                          - heading "Slab F2 B1" [level=3] [ref=e268]
                          - paragraph [ref=e269]: slab · Editable
                        - generic [ref=e270]:
                          - generic [ref=e271]:
                            - term [ref=e272]: Dimensions · metres
                            - definition [ref=e273]: 4.000 × 4.000 × 0.160 m
                          - generic [ref=e274]:
                            - term [ref=e275]: Position · East / North / Up · m
                            - definition [ref=e276]: 2.000 / 2.000 / 6.000
                          - generic [ref=e277]:
                            - term [ref=e278]: Orientation · X / Y / Z · degrees
                            - definition [ref=e279]: 0.0 / 0.0 / 0.0
                          - generic [ref=e280]:
                            - term [ref=e281]: Geometry source
                            - definition [ref=e282]: Saved geometry · source evidence not recorded
                          - generic [ref=e283]:
                            - term [ref=e284]: Material verification
                            - definition [ref=e285]: Unverified · appearance is not engineering evidence · engineering properties missing here
                          - generic [ref=e286]:
                            - term [ref=e287]: Stable component ID
                            - definition [ref=e288]: slab-F2-B1
                          - generic [ref=e289]:
                            - term [ref=e290]: Appearance finish · illustrative
                            - definition [ref=e291]: Concrete-style appearance
                          - generic [ref=e292]:
                            - term [ref=e293]: Declared engineering material
                            - definition [ref=e294]: Not declared in this visual component. Review Analysis inputs.
                        - paragraph [ref=e295]: Saved v1 · Engineering Unverified
                        - generic [ref=e296]:
                          - button "Fit selection" [ref=e297]
                          - button "Edit" [ref=e298]
                          - button "Existing analysis" [ref=e299]
                          - button "Isolate" [ref=e300]
                          - button "Hide" [ref=e301]
                          - button "Restore visibility" [ref=e302]
                      - group [ref=e303]:
                        - generic "Assembly tools and parameters" [ref=e304] [cursor=pointer]
                      - generic "Component edit form" [ref=e305]:
                        - heading "Edit component" [level=3] [ref=e306]
                        - paragraph [ref=e307]: "Local axes: East / North / Up · metres. Changes remain pending until Apply, then Save model."
                        - generic [ref=e308]:
                          - text: Component name
                          - textbox "Component name" [ref=e309]: slab-F2-B1
                        - generic [ref=e310]:
                          - paragraph [ref=e311]: Dimensions · metres
                          - generic [ref=e312]:
                            - generic [ref=e313]:
                              - text: Dimensions · metres X
                              - textbox "Dimensions · metres X" [ref=e314]: "4"
                            - generic [ref=e315]:
                              - text: Dimensions · metres Y
                              - textbox "Dimensions · metres Y" [ref=e316]: "4"
                            - generic [ref=e317]:
                              - text: Dimensions · metres Z
                              - textbox "Dimensions · metres Z" [ref=e318]: "0.16"
                        - generic [ref=e319]:
                          - paragraph [ref=e320]: Position · metres
                          - generic [ref=e321]:
                            - generic [ref=e322]:
                              - text: Position · metres East
                              - textbox "Position · metres East" [ref=e323]: "2"
                            - generic [ref=e324]:
                              - text: Position · metres North
                              - textbox "Position · metres North" [ref=e325]: "2"
                            - generic [ref=e326]:
                              - text: Position · metres Up
                              - textbox "Position · metres Up" [ref=e327]: "6"
                        - generic [ref=e328]:
                          - paragraph [ref=e329]: Rotation · degrees
                          - generic [ref=e330]:
                            - generic [ref=e331]:
                              - text: Rotation · degrees X
                              - textbox "Rotation · degrees X" [ref=e332]: "0"
                            - generic [ref=e333]:
                              - text: Rotation · degrees Y
                              - textbox "Rotation · degrees Y" [ref=e334]: "0"
                            - generic [ref=e335]:
                              - text: Rotation · degrees Z
                              - textbox "Rotation · degrees Z" [ref=e336]: "0"
                        - group [ref=e337]:
                          - generic "Scale and appearance" [ref=e338] [cursor=pointer]
                        - status [ref=e339]: No pending changes
                        - generic [ref=e340]:
                          - button "Preview" [disabled]
                          - button "Apply" [disabled]
                          - button "Cancel" [ref=e341]
                        - group [ref=e342]:
                          - generic "Identity and source references" [ref=e343] [cursor=pointer]
                  - tablist "Inspector views" [ref=e344]:
                    - tab "Layers" [ref=e345]
                    - tab "Inspect" [selected] [ref=e351]
                    - tab "History" [ref=e355]
                    - tab "Analysis" [ref=e361]
                    - tab "Review" [ref=e366]
        - region "Engineering dock" [ref=e371]:
          - generic [ref=e373]:
            - button "Engineering dock" [ref=e374]
            - button "Cost —" [ref=e379]:
              - 'generic "Cost: —" [ref=e380]':
                - generic [ref=e383]: Cost
                - generic [ref=e384]: —
            - button "Cement —" [ref=e386]:
              - 'generic "Cement: —" [ref=e387]':
                - generic [ref=e391]: Cement
                - generic [ref=e392]: —
            - button "Steel —" [ref=e394]:
              - 'generic "Steel: —" [ref=e395]':
                - generic [ref=e400]: Steel
                - generic [ref=e401]: —
            - button "Excavation —" [ref=e403]:
              - 'generic "Excavation: —" [ref=e404]':
                - generic [ref=e409]: Excavation
                - generic [ref=e410]: —
            - button "Duration —" [ref=e412]:
              - 'generic "Duration: —" [ref=e413]':
                - generic [ref=e417]: Duration
                - generic [ref=e418]: —
            - button "Area —" [ref=e420]:
              - 'generic "Area: —" [ref=e421]':
                - generic [ref=e425]: Area
                - generic [ref=e426]: —
            - button "Risk —" [ref=e428]:
              - 'generic "Risk: —" [ref=e429]':
                - generic [ref=e433]: Risk
                - generic [ref=e434]: —
  - button "Open Next.js Dev Tools" [ref=e440] [cursor=pointer]
  - alert [ref=e444]
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | import demo from '../../docs/spatial-frame/demo.json';
  4  | const d=demo[1],modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  5  | for(const width of [1280,1600])test(`integrated floors, topology and static-case animation ${width}`,async({page,request})=>{
  6  |  test.setTimeout(240000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
  7  |  const attestation=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(attestation.original_writes).toBe(false);
  8  |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  9  |  await page.goto('http://localhost:13001/projects/823/workspace');const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await expect(panel.getByLabel('Spatial load case')).toBeVisible();await panel.getByLabel('Spatial load case').selectOption(d.analysis.result.cases[2].case.name);
  10 |  await expect(canvas).toHaveAttribute('data-structural-transition','ready');await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(4);
  11 |  const surfaces=JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]') as {key:string;x:number;y:number}[];const face=surfaces.find(p=>p.key==='slab-F2-B1')!;expect(face).toBeTruthy();const box=await canvas.boundingBox();await page.mouse.click(box!.x+face.x,box!.y+face.y);await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('LOAD-ONLY');await expect(panel.getByLabel('Connected route destination')).toBeVisible();
> 12 |  await panel.getByText(/Route · \d+ verified topology steps/).click();await expect(panel.getByLabel('Verified topology route')).toContainText('Base N');await expect(panel.getByLabel('Verified topology route')).toContainText('column-F1');await page.screenshot({path:`../docs/floor-system/floor-transfer-${width}.png`});
     |                                                               ^ TimeoutError: locator.click: Timeout 30000ms exceeded.
  13 |  await panel.getByRole('button',{name:'Isolate this floor',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('2');await expect(canvas).toHaveAttribute('data-structural-transition','ready');await page.screenshot({path:`../docs/floor-system/floor-isolation-${width}.png`});await panel.getByRole('button',{name:'Show complete route across floors',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('0');
  14 |  await panel.getByLabel('Show LOAD-ONLY floor surfaces').uncheck();await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(0);await panel.getByLabel('Show LOAD-ONLY floor surfaces').check();
  15 |  await panel.getByLabel('Inspect spatial component').selectOption(d.fixture.inputs.members[20].id);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Computed |u|max');
  16 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(canvas).toHaveAttribute('data-structural-transition','ready');
  17 |   if(key==='deformation'){await panel.getByLabel('Spatial displacement magnification').fill('100');await panel.getByRole('button',{name:'Animate computed deformation',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','playing');const before=await canvas.getAttribute('data-deformation-phase');await expect.poll(()=>canvas.getAttribute('data-deformation-phase')).not.toBe(before);await page.screenshot({path:`../docs/floor-system/deformation-${width}.png`});await panel.getByRole('button',{name:'Stop animation · show full static case',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','paused');await expect(panel).toContainText('NOT dynamic analysis');}
  18 |   const boxes=JSON.parse(await canvas.getAttribute('data-engineering-label-boxes')||'[]') as {x:number;y:number;width:number;height:number}[];expect(boxes.length).toBeLessThanOrEqual(7);for(const [i,a] of boxes.entries())for(const b of boxes.slice(i+1))expect(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y).toBe(false);
  19 |  }
  20 |  await panel.getByRole('button',{name:'Applied loads and reactions',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready');const loads=JSON.parse(await canvas.getAttribute('data-engineering-load-points')||'[]') as {key:string;x:number;y:number}[];const load=loads.find(p=>p.key.startsWith('load:node:')&&p.x>100&&p.x<box!.width-30&&p.y>120&&p.y<800);expect(load).toBeTruthy();await page.mouse.click(box!.x+load!.x,box!.y+load!.y);await expect(panel.getByLabel('Inspect analytical load or support')).toHaveValue(load!.key);await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('whole saved case');
  21 |  await panel.getByLabel('Inspect analytical load or support').selectOption('node:1');await expect(panel.getByRole('article',{name:'Connected analytical path'})).toContainText('foundation/soil capacity NOT VERIFIED');await page.screenshot({path:`../docs/floor-system/base-reactions-${width}.png`});
  22 |  await panel.getByRole('button',{name:'Restore full geometry',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/floor-system/acceptance-${width}.json`,JSON.stringify({width,surface_picked:face.key,load_picked:load!.key,modes:7,animation:true,isolated_floor:true,route_to_base:true,writes,errors},null,2));
  23 | });
  24 | for(const id of [793,794,804])test(`preserved normal project ${id}`,async({page})=>{
  25 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false');expect(writes).toEqual([]);expect(errors).toEqual([]);
  26 | });
  27 | 
  28 | 
```