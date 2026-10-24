# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: floor-system.spec.ts >> integrated floors, topology and static-case animation 1280
- Location: e2e\floor-system.spec.ts:5:36

# Error details

```
Error: expect(received).toBeLessThanOrEqual(expected)

Expected: <= 7
Received:    8
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
                    - generic "3D workspace viewport" [ref=e87]
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
            - complementary [ref=e253]:
              - generic [ref=e255]:
                - generic [ref=e256]:
                  - generic [ref=e258]:
                    - generic [ref=e259]: Analysis
                    - button "Close inspector" [ref=e260]
                  - tabpanel "Analysis" [ref=e264]:
                    - generic [ref=e265]:
                      - region "Spatial structural engineering" [ref=e266]:
                        - heading "Connected 3D frame · explore" [level=3] [ref=e267]
                        - paragraph [ref=e268]: Synthetic verification · no safety or code approval
                        - generic [ref=e269]:
                          - generic [ref=e270]:
                            - checkbox "Show LOAD-ONLY floor surfaces" [checked] [ref=e271]
                            - text: LOAD-ONLY floor surfaces
                          - generic [ref=e272]:
                            - text: Labels
                            - combobox "Engineering label density" [ref=e273]:
                              - option "Selection + floor names" [selected]
                              - option "Compact overview"
                              - option "All available values"
                        - generic [ref=e274]:
                          - button "Structural load paths" [ref=e275]
                          - button "Applied loads and reactions" [active] [pressed] [ref=e276]
                          - button "Deformed versus original" [ref=e277]
                          - button "Beam and column forces" [ref=e278]
                          - button "Slab-to-beam distribution" [ref=e279]
                          - button "Foundation and soil response" [ref=e280]
                          - button "Warnings and connections" [ref=e281]
                        - generic [ref=e282]:
                          - text: Saved spatial load case
                          - combobox "Spatial load case" [ref=e283]:
                            - option "Gravity · 5 kPa one-way slabs"
                            - option "Lateral · E + N nodal actions"
                            - option "Linear gravity + lateral" [selected]
                        - generic [ref=e284]:
                          - text: Inspect floor · display only
                          - combobox "Spatial floor" [ref=e285]:
                            - option "All storeys" [selected]
                            - option "Floor 1"
                            - option "Floor 2"
                        - paragraph [ref=e286]: "Cyan: explicit shared-node analytical connectivity. Yellow: applied force; green: reaction. Arrow lengths normalized; signed values in kN. No force path is inferred from CAD proximity."
                        - paragraph [ref=e287]: 26 analyzed members · 18 six-DOF nodes · 4 load-only slabs
                        - generic [ref=e288]:
                          - text: Inspect a load or support
                          - combobox "Inspect analytical load or support" [ref=e289]:
                            - option "Select a yellow load arrow, base or joint" [selected]
                            - option "Base N1"
                            - option "Base N2"
                            - option "Base N3"
                            - option "Base N4"
                            - option "Base N5"
                            - option "Base N6"
                            - option "Joint N7"
                            - option "N7 applied load"
                            - option "Joint N8"
                            - option "N8 applied load"
                            - option "Joint N9"
                            - option "N9 applied load"
                            - option "Joint N10"
                            - option "N10 applied load"
                            - option "Joint N11"
                            - option "N11 applied load"
                            - option "Joint N12"
                            - option "N12 applied load"
                            - option "Joint N13"
                            - option "N13 applied load"
                            - option "Joint N14"
                            - option "N14 applied load"
                            - option "Joint N15"
                            - option "N15 applied load"
                            - option "Joint N16"
                            - option "N16 applied load"
                            - option "Joint N17"
                            - option "N17 applied load"
                            - option "Joint N18"
                            - option "N18 applied load"
                            - option "q · beam-F1-N7-8"
                            - option "q · beam-F1-N8-9"
                            - option "q · beam-F1-N10-11"
                            - option "q · beam-F1-N11-12"
                            - option "q · beam-F2-N13-14"
                            - option "q · beam-F2-N14-15"
                            - option "q · beam-F2-N16-17"
                            - option "q · beam-F2-N17-18"
                            - option "Pressure · slab-F1-B1"
                            - option "Pressure · slab-F1-B2"
                            - option "Pressure · slab-F2-B1"
                            - option "Pressure · slab-F2-B2"
                        - article "Connected analytical path" [ref=e290]:
                          - text: beam-F2-N14-15
                          - paragraph [ref=e291]: Whole saved-case end actions and section samples; no selected-load attribution.
                          - paragraph [ref=e292]: Topology route only. All member actions and reactions belong to the whole saved case; no individual-load force shares. No joint, base-plate, foundation or soil capacity verification.
                          - generic [ref=e293]:
                            - checkbox "Highlight verified connected route" [checked] [ref=e294]
                            - text: Highlight connected route
                          - generic [ref=e295]:
                            - text: Reachable prescribed base
                            - combobox "Connected route destination" [ref=e296]:
                              - option "Base N2 · 5 topology steps" [selected]
                              - option "Base N3 · 5 topology steps"
                              - option "Base N1 · 7 topology steps"
                              - option "Base N5 · 7 topology steps"
                              - option "Base N6 · 7 topology steps"
                              - option "Base N4 · 9 topology steps"
                          - group [ref=e297]:
                            - generic "Route · 5 verified topology steps" [ref=e298] [cursor=pointer]
                            - list "Verified topology route" [ref=e299]:
                              - listitem [ref=e300]: 1. beam-F2-N14-15
                              - listitem [ref=e301]: 2. Joint N14
                              - listitem [ref=e302]: 3. column-F2-N8-14
                              - listitem [ref=e303]: 4. Joint N8
                              - listitem [ref=e304]: 5. column-F1-N2-8
                              - listitem [ref=e305]: 6. Base N2
                          - group [ref=e306]:
                            - generic "Follow an adjacent analytical connection" [ref=e307] [cursor=pointer]
                          - button "Isolate this floor" [ref=e308]
                          - group [ref=e309]:
                            - generic "Selected transfer / node equilibrium evidence" [ref=e310] [cursor=pointer]
                        - generic [ref=e311]:
                          - text: Inspect spatial component
                          - combobox "Inspect spatial component" [ref=e312]:
                            - option "Select in 3D or choose here"
                            - option "column-F1-N1-7"
                            - option "column-F1-N2-8"
                            - option "column-F1-N3-9"
                            - option "column-F1-N4-10"
                            - option "column-F1-N5-11"
                            - option "column-F1-N6-12"
                            - option "beam-F1-N7-8"
                            - option "beam-F1-N8-9"
                            - option "beam-F1-N10-11"
                            - option "beam-F1-N11-12"
                            - option "beam-F1-N7-10"
                            - option "beam-F1-N8-11"
                            - option "beam-F1-N9-12"
                            - option "slab-F1-B1"
                            - option "slab-F1-B2"
                            - option "column-F2-N7-13"
                            - option "column-F2-N8-14"
                            - option "column-F2-N9-15"
                            - option "column-F2-N10-16"
                            - option "column-F2-N11-17"
                            - option "column-F2-N12-18"
                            - option "beam-F2-N13-14"
                            - option "beam-F2-N14-15" [selected]
                            - option "beam-F2-N16-17"
                            - option "beam-F2-N17-18"
                            - option "beam-F2-N13-16"
                            - option "beam-F2-N14-17"
                            - option "beam-F2-N15-18"
                            - option "slab-F2-B1"
                            - option "slab-F2-B2"
                        - article "Selected spatial evidence" [ref=e313]:
                          - text: beam-F2-N14-15
                          - paragraph [ref=e314]: Computed |u|max 1.051 mm · |Mz|max 0.227 kN·m · floor 2
                          - group [ref=e315]:
                            - generic "Member / slab numerical evidence" [ref=e316] [cursor=pointer]
                        - generic [ref=e317]:
                          - checkbox "Isolate selected floor/system" [checked] [ref=e318]
                          - text: Isolate selected floor/system
                        - generic [ref=e319]:
                          - button "Frame 3D model" [ref=e320]
                          - button "Restore full geometry" [ref=e321]
                        - group [ref=e322]:
                          - generic "Independent calculations, assumptions and immutable evidence" [ref=e323] [cursor=pointer]
                        - group [ref=e324]:
                          - generic "Review and authorize local solver inputs" [ref=e325] [cursor=pointer]
                      - group [ref=e326]:
                        - generic "Analysis overview and input guidance" [ref=e327] [cursor=pointer]
                      - group [ref=e328]:
                        - generic "Advanced analysis · inputs, tools and evidence" [ref=e329] [cursor=pointer]
                - tablist "Inspector views" [ref=e330]:
                  - tab "Layers" [ref=e331]
                  - tab "Inspect" [ref=e337]
                  - tab "History" [ref=e341]
                  - tab "Analysis" [selected] [ref=e347]
                  - tab "Review" [ref=e352]
        - region "Engineering dock" [ref=e357]:
          - generic [ref=e359]:
            - button "Engineering dock" [ref=e360]
            - button "Cost —" [ref=e365]:
              - 'generic "Cost: —" [ref=e366]':
                - generic [ref=e369]: Cost
                - generic [ref=e370]: —
            - button "Cement —" [ref=e372]:
              - 'generic "Cement: —" [ref=e373]':
                - generic [ref=e377]: Cement
                - generic [ref=e378]: —
            - button "Steel —" [ref=e380]:
              - 'generic "Steel: —" [ref=e381]':
                - generic [ref=e386]: Steel
                - generic [ref=e387]: —
            - button "Excavation —" [ref=e389]:
              - 'generic "Excavation: —" [ref=e390]':
                - generic [ref=e395]: Excavation
                - generic [ref=e396]: —
            - button "Duration —" [ref=e398]:
              - 'generic "Duration: —" [ref=e399]':
                - generic [ref=e403]: Duration
                - generic [ref=e404]: —
            - button "Area —" [ref=e406]:
              - 'generic "Area: —" [ref=e407]':
                - generic [ref=e411]: Area
                - generic [ref=e412]: —
            - button "Risk —" [ref=e414]:
              - 'generic "Risk: —" [ref=e415]':
                - generic [ref=e419]: Risk
                - generic [ref=e420]: —
  - button "Open Next.js Dev Tools" [ref=e426] [cursor=pointer]
  - alert [ref=e430]
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
  12 |  await panel.getByText(/Route · \d+ verified topology steps/).click();await expect(panel.getByLabel('Verified topology route')).toContainText('Base N');await expect(panel.getByLabel('Verified topology route')).toContainText('column-F1');await page.screenshot({path:`../docs/floor-system/floor-transfer-${width}.png`});
  13 |  await panel.getByRole('button',{name:'Isolate this floor',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('2');await expect(canvas).toHaveAttribute('data-structural-transition','ready');await page.screenshot({path:`../docs/floor-system/floor-isolation-${width}.png`});await panel.getByRole('button',{name:'Show complete route across floors',exact:true}).click();await expect(panel.getByLabel('Spatial floor')).toHaveValue('0');
  14 |  await panel.getByLabel('Show LOAD-ONLY floor surfaces').uncheck();await expect.poll(async()=>JSON.parse(await canvas.getAttribute('data-floor-surface-points')||'[]').length).toBe(0);await panel.getByLabel('Show LOAD-ONLY floor surfaces').check();
  15 |  await panel.getByLabel('Inspect spatial component').selectOption(d.fixture.inputs.members[20].id);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Computed |u|max');
  16 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(canvas).toHaveAttribute('data-structural-transition','ready');
  17 |   if(key==='deformation'){await panel.getByLabel('Spatial displacement magnification').fill('100');await panel.getByRole('button',{name:'Animate computed deformation',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','playing');const before=await canvas.getAttribute('data-deformation-phase');await expect.poll(()=>canvas.getAttribute('data-deformation-phase')).not.toBe(before);await page.screenshot({path:`../docs/floor-system/deformation-${width}.png`});await panel.getByRole('button',{name:'Stop animation · show full static case',exact:true}).click();await expect(canvas).toHaveAttribute('data-deformation-animation','paused');await expect(panel).toContainText('NOT dynamic analysis');}
> 18 |   const boxes=JSON.parse(await canvas.getAttribute('data-engineering-label-boxes')||'[]') as {x:number;y:number;width:number;height:number}[];expect(boxes.length).toBeLessThanOrEqual(7);for(const [i,a] of boxes.entries())for(const b of boxes.slice(i+1))expect(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y).toBe(false);
     |                                                                                                                                                                    ^ Error: expect(received).toBeLessThanOrEqual(expected)
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