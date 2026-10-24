# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: structural-visual.spec.ts >> saved structural visual workflow project 804 at 1600
- Location: e2e\structural-visual.spec.ts:6:71

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 3

- Array []
+ Array [
+   "POST http://localhost:3001/__nextjs_original-stack-frames",
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
      - heading "RC footing nominal flexure — synthetic review" [level=1] [ref=e13]
      - generic [ref=e14]:
        - link "3D Sandbox editor" [ref=e15] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
        - link "Projects" [ref=e19] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=e20]:
          - button "Save site geometry" [ref=e21]
          - link [ref=e26] [cursor=pointer]:
            - /url: /projects/804/report
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
                      - button "Fit selection" [disabled] [ref=e79]
                      - button "Dimensions off" [ref=e80]
                      - group [ref=e81]:
                        - generic "Display legend" [ref=e82] [cursor=pointer]
                  - generic [ref=e84]:
                    - generic "3D workspace viewport" [ref=e87]
                    - button "Full screen" [ref=e89] [cursor=pointer]
              - complementary "Workspace tools" [ref=e93]:
                - group "Object editing" [ref=e94]:
                  - generic [ref=e95]: Edit
                  - generic "Click to select and inspect · Ctrl to add · V" [ref=e96]:
                    - button "Select object" [pressed] [ref=e97]
                  - generic "Move selection · Select an editable object first" [ref=e101]:
                    - button "Move selection" [disabled] [ref=e102]
                  - generic "Rotate selection · Select an editable object first" [ref=e109]:
                    - button "Rotate selection" [disabled] [ref=e110]
                  - generic "Scale selection · Select an editable object first" [ref=e115]:
                    - button "Scale selection" [disabled] [ref=e116]
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
                - generic "Fit the project in view · F" [ref=e170]:
                  - button "Fit project" [ref=e171]
                - generic [ref=e180]: Actions
                - generic "Duplicate selection · Select an editable object first" [ref=e181]:
                  - button "Duplicate selection" [disabled] [ref=e182]
                - generic "Delete selection · Select an editable object first" [ref=e187]:
                  - button "Delete selection" [disabled] [ref=e188]
                - generic "Undo · No object edits to undo" [ref=e194]:
                  - button "Undo" [disabled] [ref=e195]
                - generic "Redo · No object edits to redo" [ref=e200]:
                  - button "Redo" [disabled] [ref=e201]
              - generic [ref=e206]:
                - generic "Scene / Sun study" [ref=e207]:
                  - button "Scene / Sun study" [ref=e208]
                - button "Search workspace" [ref=e216]
                - group [ref=e220]:
                  - generic "Import site geometry" [ref=e221] [cursor=pointer]: Import
              - button "Show AI Copilot panel" [ref=e226]:
                - generic [ref=e230]: Assistant
              - group "Camera orientation gizmo" [ref=e231]:
                - button "Positive Y axis view" [ref=e238]: "Y"
                - button "Negative Z axis view" [disabled] [ref=e239]
                - button "Positive X axis view" [ref=e240]: X
                - button "Negative X axis view" [ref=e241]
                - button "Positive Z axis view" [ref=e242]: Z
                - button "Negative Y axis view" [ref=e243]
            - complementary [ref=e245]:
              - generic [ref=e247]:
                - generic [ref=e248]:
                  - generic [ref=e250]:
                    - generic [ref=e251]: Analysis
                    - button "Close inspector" [ref=e252]
                  - tabpanel "Analysis" [ref=e256]:
                    - generic [ref=e257]:
                      - region "Structural visual engineering" [ref=e258]:
                        - heading "Structure · explore in 3D" [level=3] [ref=e259]
                        - paragraph [ref=e260]: Saved analytical evidence · no safety or code approval
                        - generic [ref=e261]:
                          - button "Structural load paths" [ref=e262]
                          - button "Applied loads and reactions" [ref=e263]
                          - button "Deformed versus original" [ref=e264]
                          - button "Beam and column forces" [ref=e265]
                          - button "Slab-to-beam distribution" [ref=e266]
                          - button "Foundation and soil response" [ref=e267]
                          - button "Warnings and connections" [ref=e268]
                        - generic "Structural visual legend" [ref=e269]: Labels identify components without a current verified solver transfer; CAD proximity is not an analytical connection.
                        - paragraph [ref=e270]: No current verified structural solver result for this revision. No response or load path is inferred.
                        - generic [ref=e271]:
                          - generic [ref=e272]:
                            - checkbox "Isolate analyzed structural system" [disabled] [ref=e273]
                            - text: Isolate analyzed system
                          - button "Frame view" [ref=e274]
                          - button "Restore full structure" [active] [ref=e275]
                        - generic [ref=e276]:
                          - text: Inspect saved component
                          - combobox "Inspect structural component" [ref=e277]:
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
                            - option "CAD beam North · beam"
                            - option "CAD column NW · column"
                            - option "CAD column NE · column"
                            - option "CAD footing NW · foundation"
                            - option "CAD footing NE · foundation"
                        - group [ref=e278]:
                          - generic "Coverage, warnings and immutable numerical evidence" [ref=e279] [cursor=pointer]
                      - group [ref=e280]:
                        - generic "Analysis overview and input guidance" [ref=e281] [cursor=pointer]
                      - region "Integrated foundation workflow" [ref=e282]:
                        - heading "Foundation engineering" [level=3] [ref=e283]
                        - paragraph [ref=e284]: Synthetic review · saved CAD identities · no engineering approval
                        - button "Create separate foundation study from 804" [ref=e285]
                      - group [ref=e286]:
                        - generic "Advanced analysis · inputs, tools and evidence" [ref=e287] [cursor=pointer]
                - tablist "Inspector views" [ref=e288]:
                  - tab "Layers" [ref=e289]
                  - tab "Inspect" [ref=e295]
                  - tab "History" [ref=e299]
                  - tab "Analysis" [selected] [ref=e305]
                  - tab "Review" [ref=e310]
        - region "Engineering dock" [ref=e315]:
          - generic [ref=e317]:
            - button "Engineering dock" [ref=e318]
            - button "Cost —" [ref=e323]:
              - 'generic "Cost: —" [ref=e324]':
                - generic [ref=e327]: Cost
                - generic [ref=e328]: —
            - button "Cement —" [ref=e330]:
              - 'generic "Cement: —" [ref=e331]':
                - generic [ref=e335]: Cement
                - generic [ref=e336]: —
            - button "Steel —" [ref=e338]:
              - 'generic "Steel: —" [ref=e339]':
                - generic [ref=e344]: Steel
                - generic [ref=e345]: —
            - button "Excavation —" [ref=e347]:
              - 'generic "Excavation: —" [ref=e348]':
                - generic [ref=e353]: Excavation
                - generic [ref=e354]: —
            - button "Duration —" [ref=e356]:
              - 'generic "Duration: —" [ref=e357]':
                - generic [ref=e361]: Duration
                - generic [ref=e362]: —
            - button "Area —" [ref=e364]:
              - 'generic "Area: —" [ref=e365]':
                - generic [ref=e369]: Area
                - generic [ref=e370]: —
            - button "Risk —" [ref=e372]:
              - 'generic "Risk: —" [ref=e373]':
                - generic [ref=e377]: Risk
                - generic [ref=e378]: —
  - button "Open Next.js Dev Tools" [ref=e384] [cursor=pointer]
  - alert [ref=e388]: GeoAI | Infrastructure Planning
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | import slabFixture from '../../docs/structural-visual/project-794.json';
  4  | const expect=pwExpect.configure({timeout:30000});
  5  | const modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  6  | test.use({trace:'off'});
  7  | for(const width of [1280,1600])for(const project of [793,794,804])test(`saved structural visual workflow project ${project} at ${width}`,async({page})=>{
  8  |  test.setTimeout(240000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
  9  |  const writes:string[]=[],errors:string[]=[];
  10 |  page.on('pageerror',e=>errors.push(e.message));
  11 |  await page.route('**/*',async route=>{const r=route.request();if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+r.url().split('?')[0]);return route.abort('blockedbyclient');}if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
  12 |  await page.goto(`/projects/${project}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
  13 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Structural visual engineering'});
  14 |  await expect(panel).toHaveAttribute('data-blocked','false',{timeout:60000});
  15 |  if(project!==804)await expect(panel.getByLabel('Structural saved load case')).toBeVisible();else await expect(panel).toContainText('No current verified structural solver result');
  16 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(panel.getByLabel('Structural visual legend')).toBeVisible();
  17 |   if(key==='deformation'&&project!==804){await panel.getByLabel('Displacement magnification').fill('200');await expect(panel).toContainText('magnification ×200');await panel.getByLabel('Show original structure').uncheck();await panel.getByLabel('Show original structure').check();}
  18 |   if(key==='forces'&&project!==804){for(const f of ['shear','axial','moment'])await panel.getByLabel('Structural force diagram').selectOption(f);}
  19 |   if((project===793&&['loads','deformation','forces'].includes(key))||(project===794&&['path','slab'].includes(key))||(project===804&&key==='foundation')){await page.waitForTimeout(400);await page.screenshot({path:`../docs/structural-visual/${project}-${key}-${width}.png`});}
  20 |  }
  21 |  if(project===793){await panel.getByRole('button',{name:'Deformed versus original',exact:true}).click();for(const c of ['Horizontal','Gravity','Self weight','Linear sum'])await panel.getByLabel('Structural saved load case').selectOption(c);
  22 |   await panel.getByRole('button',{name:'Frame view',exact:true}).click();await page.waitForTimeout(300);
  23 |   const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(p=>p.x>70&&p.x<width-460&&p.y>150&&p.y<900);expect(pick).toBeTruthy();const bounds=await canvas.boundingBox();await page.mouse.click(bounds!.x+pick!.x,bounds!.y+pick!.y);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toBeVisible();await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('Available saved planar samples');
  24 |  }
  25 |  if(project===794){await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await expect(panel).toContainText('kN applied');const select=panel.getByLabel('Inspect structural component');await select.selectOption(slabFixture.rows[0].result.transfer!.slab_id);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('one-way tributary allocation');}
> 26 |  await panel.getByRole('button',{name:'Restore full structure',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);await expect(panel.getByLabel('Isolate analyzed structural system')).not.toBeChecked();
     |                 ^ Error: expect(received).toEqual(expected) // deep equality
  27 |  expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/structural-visual/acceptance-${project}-${width}.json`,JSON.stringify({project,width,modes:7,write_requests:writes,page_errors:errors,restored_visibility:true},null,2));
  28 | });
  29 | 
```