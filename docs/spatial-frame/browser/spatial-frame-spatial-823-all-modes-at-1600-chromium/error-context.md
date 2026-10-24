# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: spatial-frame.spec.ts >> spatial 823 all modes at 1600
- Location: e2e\spatial-frame.spec.ts:6:56

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 4

- Array []
+ Array [
+   "http://127.0.0.1:18001/api/projects/823/site-suggestions",
+   "http://127.0.0.1:18001/api/projects/823/site-suggestions",
+ ]
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
                    - generic "Edit site boundary · Draw a site boundary first" [ref=e136]:
                      - button "Edit site boundary" [disabled] [ref=e137]
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
                          - button "Structural load paths" [ref=e270]
                          - button "Applied loads and reactions" [ref=e271]
                          - button "Deformed versus original" [ref=e272]
                          - button "Beam and column forces" [ref=e273]
                          - button "Slab-to-beam distribution" [ref=e274]
                          - button "Foundation and soil response" [ref=e275]
                          - button "Warnings and connections" [ref=e276]
                        - generic [ref=e277]:
                          - text: Saved spatial load case
                          - combobox "Spatial load case" [ref=e278]:
                            - option "Gravity · 5 kPa one-way slabs"
                            - option "Lateral · E + N nodal actions"
                            - option "Linear gravity + lateral" [selected]
                        - generic [ref=e279]:
                          - text: Analyze / inspect floor
                          - combobox "Spatial floor" [ref=e280]:
                            - option "All storeys" [selected]
                            - option "Floor 1"
                            - option "Floor 2"
                        - paragraph [ref=e281]: "Cyan: reviewed one-way 5 kPa allocation, shared by two equal-span beams. No plate stresses or diaphragm."
                        - paragraph [ref=e282]: 26 analyzed members · 18 six-DOF nodes · 4 load-only slabs
                        - generic [ref=e283]:
                          - text: Inspect spatial component
                          - combobox "Inspect spatial component" [ref=e284]:
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
                            - option "slab-F1-B1" [selected]
                            - option "slab-F1-B2"
                            - option "column-F2-N7-13"
                            - option "column-F2-N8-14"
                            - option "column-F2-N9-15"
                            - option "column-F2-N10-16"
                            - option "column-F2-N11-17"
                            - option "column-F2-N12-18"
                            - option "beam-F2-N13-14"
                            - option "beam-F2-N14-15"
                            - option "beam-F2-N16-17"
                            - option "beam-F2-N17-18"
                            - option "beam-F2-N13-16"
                            - option "beam-F2-N14-17"
                            - option "beam-F2-N15-18"
                            - option "slab-F2-B1"
                            - option "slab-F2-B2"
                        - article "Selected spatial evidence" [ref=e285]:
                          - text: slab-F1-B1
                          - paragraph [ref=e286]: Load-only slab · 5.00 kPa · beam-F1-N7-8 + beam-F1-N10-11 · no plate analysis
                          - group [ref=e287]:
                            - generic "Member / slab numerical evidence" [ref=e288] [cursor=pointer]
                        - generic [ref=e289]:
                          - checkbox "Isolate selected floor/system" [ref=e290]
                          - text: Isolate selected floor/system
                        - generic [ref=e291]:
                          - button "Frame 3D model" [ref=e292]
                          - button "Restore full geometry" [active] [ref=e293]
                        - group [ref=e294]:
                          - generic "Independent calculations, assumptions and immutable evidence" [ref=e295] [cursor=pointer]
                        - group [ref=e296]:
                          - generic "Review and authorize local solver inputs" [ref=e297] [cursor=pointer]
                      - group [ref=e298]:
                        - generic "Analysis overview and input guidance" [ref=e299] [cursor=pointer]
                      - group [ref=e300]:
                        - generic "Advanced analysis · inputs, tools and evidence" [ref=e301] [cursor=pointer]
                - tablist "Inspector views" [ref=e302]:
                  - tab "Layers" [ref=e303]
                  - tab "Inspect" [ref=e309]
                  - tab "History" [ref=e313]
                  - tab "Analysis" [selected] [ref=e319]
                  - tab "Review" [ref=e324]
        - region "Engineering dock" [ref=e329]:
          - generic [ref=e331]:
            - button "Engineering dock" [ref=e332]
            - button "Cost —" [ref=e337]:
              - 'generic "Cost: —" [ref=e338]':
                - generic [ref=e341]: Cost
                - generic [ref=e342]: —
            - button "Cement —" [ref=e344]:
              - 'generic "Cement: —" [ref=e345]':
                - generic [ref=e349]: Cement
                - generic [ref=e350]: —
            - button "Steel —" [ref=e352]:
              - 'generic "Steel: —" [ref=e353]':
                - generic [ref=e358]: Steel
                - generic [ref=e359]: —
            - button "Excavation —" [ref=e361]:
              - 'generic "Excavation: —" [ref=e362]':
                - generic [ref=e367]: Excavation
                - generic [ref=e368]: —
            - button "Duration —" [ref=e370]:
              - 'generic "Duration: —" [ref=e371]':
                - generic [ref=e375]: Duration
                - generic [ref=e376]: —
            - button "Area —" [ref=e378]:
              - 'generic "Area: —" [ref=e379]':
                - generic [ref=e383]: Area
                - generic [ref=e384]: —
            - button "Risk —" [ref=e386]:
              - 'generic "Risk: —" [ref=e387]':
                - generic [ref=e391]: Risk
                - generic [ref=e392]: —
  - button "Open Next.js Dev Tools" [ref=e398] [cursor=pointer]
  - alert [ref=e402]
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
> 22 |  await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready');const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(l=>l.key.startsWith('slab-')&&l.x>50&&l.x<900&&l.y>100&&l.y<850);if(pick){const box=await canvas.boundingBox();await page.mouse.click(box!.x+pick.x,box!.y+pick.y);await expect(panel.getByRole('article',{name:'Selected spatial evidence'})).toContainText('Load-only slab');}
     |                                                                                                                                                                        ^ Error: expect(received).toEqual(expected) // deep equality
  23 |  await panel.getByRole('button',{name:'Restore full geometry',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);expect(writes).toEqual([]);expect(errors).toEqual([]);
  24 |  writeFileSync(`../docs/spatial-frame/acceptance-${d.fixture.project_id}-${width}.json`,JSON.stringify({project:d.fixture.project_id,width,modes:7,force_components:6,load_cases:3,floor_filter:true,member_and_slab_inspection:true,writes,errors},null,2));
  25 | });
  26 | test('isolated exact review and authorize workflow',async({page,request})=>{
  27 |  test.setTimeout(180000);const a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);expect(a.database).toMatch(/foundation-system[\\/]isolated[\\/]foundation.db$/);
  28 |  const response=await request.post('http://127.0.0.1:18001/api/projects/793/engineering/spatial-frame/review-fixture',{data:{storeys:1,review_parametric_geometry:true}});expect(response.ok()).toBe(true);const fixture=await response.json();
  29 |  const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{const req=r.request();if(!['GET','HEAD','OPTIONS'].includes(req.method())){expect(req.url()).toMatch(/^http:\/\/127\.0\.0\.1:18001\/api\/projects\/\d+\/engineering\/spatial-frame\/(review|authorize-run)$/);writes.push(req.url());}if(req.url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  30 |  await page.goto(`http://localhost:13001/projects/${fixture.project_id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Spatial structural engineering'});await expect(panel).toHaveAttribute('data-blocked','false');await panel.getByText('Review and authorize local solver inputs',{exact:true}).click();await panel.getByRole('button',{name:'Prepare exact saved review',exact:true}).click();await expect(panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true})).toBeEnabled();await panel.getByRole('button',{name:'Authorize exact local OpenSees run',exact:true}).click();await expect(panel.getByLabel('Spatial load case')).toBeVisible();expect(writes).toHaveLength(2);expect(errors).toEqual([]);writeFileSync('../docs/spatial-frame/authorization-browser.json',JSON.stringify({project:fixture.project_id,reviewed:true,authorized_exact_hash:true,writes,errors},null,2));
  31 | });
  32 | for(const id of [793,794,804])test(`normal original ${id} read-only regression`,async({page})=>{
  33 |  test.setTimeout(180000);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});await page.goto(`http://localhost:3001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(page.getByRole('region',{name:'Structural visual engineering'})).toHaveAttribute('data-blocked','false');expect(writes).toEqual([]);expect(errors).toEqual([]);
  34 | });
  35 | 
```