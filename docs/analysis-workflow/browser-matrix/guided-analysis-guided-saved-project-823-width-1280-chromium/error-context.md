# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: guided-analysis.spec.ts >> guided saved project 823 width 1280
- Location: e2e\guided-analysis.spec.ts:5:57

# Error details

```
Test timeout of 180000ms exceeded.
```

```
Error: locator.click: Test timeout of 180000ms exceeded.
Call log:
  - waiting for getByRole('region', { name: 'Guided Analysis', exact: true }).getByRole('button', { name: 'Open saved results — no rerun', exact: true })

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
                - button "Positive Y axis view" [ref=e237]: "Y"
                - button "Negative Z axis view" [disabled] [ref=e238]
                - button "Positive X axis view" [ref=e239]: X
                - button "Negative X axis view" [ref=e240]
                - button "Positive Z axis view" [ref=e241]: Z
                - button "Negative Y axis view" [ref=e242]
            - complementary [ref=e244]:
              - generic [ref=e246]:
                - generic [ref=e247]:
                  - generic [ref=e249]:
                    - generic [ref=e250]: Analysis
                    - button "Close inspector" [ref=e251]
                  - tabpanel "Analysis" [ref=e255]:
                    - region "Guided Analysis" [ref=e256]:
                      - generic [ref=e257]:
                        - generic [ref=e258]:
                          - heading "Guided workflow" [level=2] [ref=e259]
                          - button "Advanced mode" [ref=e260]
                        - generic "Current analysis context" [ref=e261]:
                          - paragraph [ref=e262]: Structural analysis · Linear spatial frame · Step 1 of 4
                          - paragraph [ref=e263]: "Selected: No components selected · 30 CAD components"
                          - paragraph [ref=e264]: "Active result: None current · revision 150"
                          - paragraph [ref=e265]: "Next: Choose an analysis type"
                          - button "Restore model" [ref=e266]
                        - navigation "Analysis steps" [ref=e267]:
                          - button "1 SELECT" [ref=e268]
                          - button "2 INPUTS" [ref=e269]
                          - button "3 ANALYZE" [ref=e270]
                          - button "4 RESULTS" [ref=e271]
                      - heading "Choose what to analyze" [active] [level=3] [ref=e272]
                      - generic [ref=e273]:
                        - button "Structural analysis Available for review · Reviewed linear 3D frame; physical connection capacity unverified." [pressed] [ref=e274]:
                          - text: Structural analysis
                          - generic [ref=e275]: Available for review · Reviewed linear 3D frame; physical connection capacity unverified.
                        - button "Slabs and floor systems Available for review · Reviewed one-way LOAD-ONLY floors; no slab stiffness or diaphragm." [ref=e276]:
                          - text: Slabs and floor systems
                          - generic [ref=e277]: Available for review · Reviewed one-way LOAD-ONLY floors; no slab stiffness or diaphragm.
                        - button "Foundations and soil Not available · No integrated foundation study is bound to this model. Existing reference calculations remain in Advanced mode." [ref=e278]:
                          - text: Foundations and soil
                          - generic [ref=e279]: Not available · No integrated foundation study is bound to this model. Existing reference calculations remain in Advanced mode.
                      - button "Continue to inputs" [ref=e280]
                      - generic [ref=e281]:
                        - button "Reload saved inputs and results" [ref=e282]
                        - paragraph [ref=e283]: Reopening restores browser view preferences and saved evidence only. It never authorizes or reruns a solver.
                - tablist "Inspector views" [ref=e284]:
                  - tab "Layers" [ref=e285]
                  - tab "Inspect" [ref=e291]
                  - tab "History" [ref=e295]
                  - tab "Analysis" [selected] [ref=e301]
                  - tab "Review" [ref=e306]
        - region "Engineering dock" [ref=e311]:
          - generic [ref=e313]:
            - button "Engineering dock" [ref=e314]
            - button "Cost —" [ref=e319]:
              - 'generic "Cost: —" [ref=e320]':
                - generic [ref=e323]: Cost
                - generic [ref=e324]: —
            - button "Cement —" [ref=e326]:
              - 'generic "Cement: —" [ref=e327]':
                - generic [ref=e331]: Cement
                - generic [ref=e332]: —
            - button "Steel —" [ref=e334]:
              - 'generic "Steel: —" [ref=e335]':
                - generic [ref=e340]: Steel
                - generic [ref=e341]: —
            - button "Excavation —" [ref=e343]:
              - 'generic "Excavation: —" [ref=e344]':
                - generic [ref=e349]: Excavation
                - generic [ref=e350]: —
            - button "Duration —" [ref=e352]:
              - 'generic "Duration: —" [ref=e353]':
                - generic [ref=e357]: Duration
                - generic [ref=e358]: —
            - button "Area —" [ref=e360]:
              - 'generic "Area: —" [ref=e361]':
                - generic [ref=e365]: Area
                - generic [ref=e366]: —
            - button "Risk —" [ref=e368]:
              - 'generic "Risk: —" [ref=e369]':
                - generic [ref=e373]: Risk
                - generic [ref=e374]: —
  - button "Open Next.js Dev Tools" [ref=e380] [cursor=pointer]
  - alert [ref=e384]: GeoAI | Infrastructure Planning
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
> 9  |  if(c.result){await panel.getByRole('button',{name:'Open saved results — no rerun',exact:true}).click();await expect(panel.getByLabel('Guided visual results')).toBeVisible();for(const name of ['Loads and reactions','Deformation','Bending / shear / axial','Warnings and unsupported checks']){const button=panel.getByRole('button',{name,exact:true});if(await button.count()&&await button.isEnabled())await button.click();}await panel.getByRole('button',{name:'Loads and reactions',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-transition','ready',{timeout:15000});await page.screenshot({path:`../docs/analysis-workflow/after-${c.id}-${width}.png`});await panel.getByLabel('Current analysis context').getByRole('button',{name:'Restore model',exact:true}).click();await expect(panel.getByText('View: complete CAD geometry.',{exact:true})).toBeVisible();await panel.getByRole('button',{name:'Deformation',exact:true}).isEnabled().then(async enabled=>{if(enabled)await panel.getByRole('button',{name:'Deformation',exact:true}).click();});
     |                                                                                                 ^ Error: locator.click: Test timeout of 180000ms exceeded.
  10 |   await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(panel.getByLabel('Guided visual results')).toBeVisible({timeout:60000});
  11 |  }else{await expect(panel.getByRole('button',{name:'Continue to inputs',exact:true})).toBeDisabled();await page.screenshot({path:`../docs/analysis-workflow/after-${c.id}-${width}.png`});}
  12 |  await expect(panel.getByLabel('Advanced engineering tools')).toHaveCount(0);await panel.getByRole('button',{name:'Advanced mode',exact:true}).click();await expect(panel.getByLabel('Advanced engineering tools')).toBeVisible();await panel.getByRole('button',{name:'Return to guided workflow',exact:true}).click();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);expect(errors).toEqual([]);expect(writes).toEqual([]);writeFileSync(`../docs/analysis-workflow/browser-${c.id}-${width}.json`,JSON.stringify({project:c.id,width,keyboard:true,read_only:true,reopened_results:c.result,advanced_access:true,writes,errors},null,2));
  13 | });
  14 | test('first-time structural review and explicit authorization without accordions',async({page,request})=>{
  15 |  test.setTimeout(240000);await page.setViewportSize({width:1600,height:1000});const id=review.projects[1].project_id,base=`/api/projects/${id}/engineering/assembly`,a=await(await request.get('http://127.0.0.1:18001/__spatial_validation')).json();expect(a.original_writes).toBe(false);const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{const url=r.request().url();if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(url);if(!url.startsWith('http://127.0.0.1:18001'+base+'/')||!['preview','inputs','proposals','authorize-run'].some(s=>url.endsWith('/'+s)))return r.abort();}if(url.includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
  16 |  await page.goto(`http://localhost:13001/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();const p=page.getByRole('region',{name:'Guided Analysis',exact:true});await p.getByRole('button',{name:'Continue to inputs',exact:true}).click();
  17 |  await p.getByLabel('Analysis Column 1').selectOption('guided-left');await p.getByLabel('Analysis Beam',{exact:true}).selectOption('guided-beam');await p.getByLabel('Analysis Column 2').selectOption('guided-right');await p.getByRole('button',{name:'Select these members',exact:true}).click();
  18 |  await p.getByRole('button',{name:'Inspect selected geometry',exact:true}).click();await expect(p.getByLabel('Structural inputs')).toBeVisible();for(const name of ['guided-left','guided-beam','guided-right'])await p.getByLabel(`${name} elastic modulus GPa`).fill('200');for(const input of await p.getByLabel('Material identification',{exact:true}).all())await input.fill('Synthetic elastic steel');for(const input of await p.getByLabel('Material source or declared assumption',{exact:true}).all())await input.fill('Explicit synthetic E=200 GPa verification input');await p.getByLabel('Declare observed solid rectangular sections').check();await p.getByLabel('Guided base restraints').selectOption('both_column_bases_fixed');await p.getByLabel('Guided support source').fill('Synthetic fixed bases, not foundation capacity');await p.getByLabel('Declare analytical joints').check();await p.getByLabel('Guided joint source').fill('Explicit synthetic coincident rigid joints, no capacity');await p.getByLabel('Guided total horizontal kN').fill('20');await p.getByLabel('Guided load source').fill('Explicit synthetic 20 kN total horizontal verification load');await p.getByRole('button',{name:'Continue to review',exact:true}).click();await p.getByLabel('Review analytical assumptions').check();await p.getByRole('button',{name:'Review exact analysis proposal',exact:true}).click();await expect(p.getByLabel('Authorize exact reviewed analysis')).toBeVisible();expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(0);await expect(p.getByRole('button',{name:'Authorize and analyze',exact:true})).toBeDisabled();await p.getByLabel('Review analytical assumptions').check();await p.getByLabel('Authorize exact reviewed analysis').check();await p.getByRole('button',{name:'Authorize and analyze',exact:true}).click();await expect(p.getByLabel('Guided visual results')).toBeVisible({timeout:90000});await page.screenshot({path:'../docs/analysis-workflow/completed-structural-analysis.png'});expect(writes.filter(u=>u.endsWith('/authorize-run'))).toHaveLength(1);expect(errors).toEqual([]);writeFileSync('../docs/analysis-workflow/modifying-acceptance.json',JSON.stringify({isolated_database:a.database,project:id,explicit_authorization:true,technical_accordions_used:0,writes,errors},null,2));
  19 | });
  20 | 
```