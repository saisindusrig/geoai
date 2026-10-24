# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: milestone-7.spec.ts >> confirmed workspace inspection 1600
- Location: e2e\milestone-7.spec.ts:5:36

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator: getByRole('complementary', { name: 'GeoAI Assistant' }).getByLabel('Task status')
Expected: "Completed"
Error: strict mode violation: getByRole('complementary', { name: 'GeoAI Assistant' }).getByLabel('Task status') resolved to 2 elements:
    1) <div role="status" aria-live="polite" class="assistant-status" aria-label="Latest task status" data-state="Opening the saved result">…</div> aka getByRole('status', { name: 'Latest task status' })
    2) <strong aria-label="Task status">Opening the saved result</strong> aka getByLabel('Task status', { exact: true })

Call log:
  - Expect "toHaveText" with timeout 5000ms
  - waiting for getByRole('complementary', { name: 'GeoAI Assistant' }).getByLabel('Task status')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e5]:
    - banner [ref=e6]:
      - link "GeoAI home" [ref=e7] [cursor=pointer]:
        - /url: /
        - generic "GeoAI" [ref=e8]:
          - img [ref=e9]
          - generic [ref=e11]: GeoAI
      - heading "Unequal CAD frame — gravity and distributed load verification" [level=1] [ref=e14]
      - generic [ref=e15]:
        - link "3D Sandbox editor" [ref=e16] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
          - img [ref=e17]
          - text: 3D Sandbox editor
        - link "Projects" [ref=e20] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=e21]:
          - button "Save site geometry" [ref=e22]:
            - img [ref=e23]
            - text: Save site geometry
          - link "Export" [ref=e27] [cursor=pointer]:
            - /url: /projects/793/report
            - button "Export" [ref=e28]:
              - img [ref=e29]
              - text: Export
        - link "New concept" [ref=e32] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=e33]:
            - img [ref=e34]
            - text: New concept
        - link "Open settings" [ref=e35] [cursor=pointer]:
          - /url: /settings
          - img [ref=e36]
    - main [ref=e39]:
      - generic [ref=e42]:
        - generic [ref=e43]:
          - generic "Design workflow" [ref=e47]:
            - button "1 Site" [ref=e48]
            - group [ref=e49]:
              - generic "Workflow help" [ref=e50] [cursor=pointer]
            - group [ref=e51]:
              - generic "2 Create / Import" [ref=e52] [cursor=pointer]
            - button "3 Review 3D" [ref=e53]
            - button "4 Edit" [ref=e54]
            - button "5 Analyze / Results" [ref=e55]
            - button "6 Review" [ref=e56]
            - status [ref=e57]: Saved · v2
            - button "Save model" [disabled]
          - generic [ref=e58]:
            - generic [ref=e59]:
              - generic [ref=e62]:
                - generic:
                  - img
                  - generic: 12.97160° N · 77.59460° E
                - generic [ref=e63]:
                  - status [ref=e64]:
                    - text: Saved-result isolation is active. Other geometry is preserved.
                    - button "Restore full model" [ref=e65]
                  - generic "Mouse navigation" [ref=e66]:
                    - button "Select" [pressed] [ref=e67]
                    - button "Orbit" [ref=e68]
                    - button "Pan" [ref=e69]
                    - button "Mouse controls" [ref=e70]
                  - generic "Viewport presentation" [ref=e71]:
                    - generic [ref=e72]:
                      - button "Model view" [pressed] [ref=e73]
                      - generic [ref=e74]: /
                      - button "Site view" [ref=e75]
                      - generic [ref=e76]: Illustrative finishes · not material evidence
                    - generic [ref=e77]:
                      - group [ref=e78]:
                        - generic "Standard views" [ref=e79] [cursor=pointer]
                      - button "Focus Structure" [ref=e80]
                      - button "Fit All" [ref=e81]
                      - button "Fit selection" [ref=e82]
                      - button "Dimensions off" [ref=e83]
                      - group [ref=e84]:
                        - generic "Display legend" [ref=e85] [cursor=pointer]
                  - generic [ref=e87]:
                    - generic "3D workspace viewport" [ref=e90]
                    - button "Full screen" [ref=e92] [cursor=pointer]
              - generic [ref=e95]:
                - complementary "Workspace tools" [ref=e96]:
                  - group "Object editing" [ref=e97]:
                    - generic [ref=e98]: Edit
                    - generic "Click to select and inspect · Ctrl to add · V" [ref=e99]:
                      - button "Select object" [pressed] [ref=e100]:
                        - img [ref=e101]
                      - generic [ref=e103]: Click to select and inspect · Ctrl to add · V
                    - generic "Move selected objects · G · changes geometry; undo with Ctrl+Z" [ref=e104]:
                      - button "Move selection" [ref=e105]:
                        - img [ref=e106]
                      - generic [ref=e111]: Move selected objects · G · changes geometry; undo with Ctrl+Z
                    - generic "Rotate selected objects · R · review local/global axes" [ref=e112]:
                      - button "Rotate selection" [ref=e113]:
                        - img [ref=e114]
                      - generic [ref=e117]: Rotate selected objects · R · review local/global axes
                    - generic "Scale selected objects · S · changes dimensions; engineering results may become stale" [ref=e118]:
                      - button "Scale selection" [ref=e119]:
                        - img [ref=e120]
                      - generic [ref=e125]: Scale selected objects · S · changes dimensions; engineering results may become stale
                  - group "Site geometry" [ref=e127]:
                    - generic [ref=e128]: Site
                    - generic "Draw a rectangular site boundary" [ref=e129]:
                      - button "Draw rectangular boundary" [ref=e130]:
                        - img [ref=e131]
                      - generic [ref=e133]: Draw a rectangular site boundary
                    - generic "Draw a closed site boundary" [ref=e134]:
                      - button "Draw site boundary" [ref=e135]:
                        - img [ref=e136]
                      - generic [ref=e138]: Draw a closed site boundary
                    - generic "Drag existing boundary vertices" [ref=e139]:
                      - button "Edit site boundary" [ref=e140]:
                        - img [ref=e141]
                      - generic [ref=e144]: Drag existing boundary vertices
                    - generic "Draw a road or infrastructure centerline" [ref=e145]:
                      - button "Draw alignment" [ref=e146]:
                        - img [ref=e147]
                      - generic [ref=e151]: Draw a road or infrastructure centerline
                    - generic "Edit alignment · Draw an alignment first" [ref=e152]:
                      - button "Edit alignment" [disabled] [ref=e153]:
                        - img [ref=e154]
                      - generic [ref=e161]: Edit alignment · Draw an alignment first
                  - generic [ref=e163]: View
                  - generic "Measure distance, elevation, slope, area or clearance · M" [ref=e164]:
                    - button "Measure" [ref=e165]:
                      - img [ref=e166]
                    - generic [ref=e172]: Measure distance, elevation, slope, area or clearance · M
                  - generic "Focus the selected object · F" [ref=e173]:
                    - button "Frame selection" [ref=e174]:
                      - img [ref=e175]
                    - generic [ref=e181]: Focus the selected object · F
                  - generic [ref=e183]: Actions
                  - generic "Duplicate selected objects" [ref=e184]:
                    - button "Duplicate selection" [ref=e185]:
                      - img [ref=e186]
                    - generic [ref=e189]: Duplicate selected objects
                  - generic "Delete selected objects · Del" [ref=e190]:
                    - button "Delete selection" [ref=e191]:
                      - img [ref=e192]
                    - generic [ref=e195]: Delete selected objects · Del
                  - generic "Undo · No object edits to undo" [ref=e197]:
                    - button "Undo" [disabled] [ref=e198]:
                      - img [ref=e199]
                    - generic [ref=e202]: Undo · No object edits to undo
                  - generic "Redo · No object edits to redo" [ref=e203]:
                    - button "Redo" [disabled] [ref=e204]:
                      - img [ref=e205]
                    - generic [ref=e208]: Redo · No object edits to redo
                - status [ref=e209]:
                  - paragraph [ref=e210]: 1 selected · select
                  - button "Inspect selection" [ref=e211]
                  - paragraph [ref=e212]: Step 0.5 m · Esc cancels · Ctrl+Z undoes
                  - generic [ref=e213]:
                    - button "Move west one step" [ref=e214]: E−
                    - button "Move east one step" [ref=e215]: E+
                    - button "Move north one step" [ref=e216]: N+
                  - button "Clear selection" [ref=e217]
              - generic [ref=e218]:
                - generic "Scene / Sun study" [ref=e219]:
                  - button "Scene / Sun study" [ref=e220]:
                    - img [ref=e221]
                - button "Search workspace" [ref=e228]:
                  - img [ref=e229]
                - group [ref=e232]:
                  - generic "Import site geometry" [ref=e233] [cursor=pointer]:
                    - img [ref=e234]
                    - text: Import
              - group "Camera orientation gizmo" [ref=e237]:
                - generic [ref=e238]:
                  - img
                  - button "Negative Y axis view" [ref=e239]: −Y
                  - button "Negative Z axis view" [disabled] [ref=e240]: −Z
                  - button "Positive X axis view" [ref=e241]: +X
                  - button "Negative X axis view" [ref=e242]: −X
                  - button "Positive Z axis view" [ref=e243]: +Z
                  - button "Positive Y axis view" [ref=e244]: +Y
            - complementary [ref=e246]:
              - generic [ref=e248]:
                - generic [ref=e249]:
                  - generic [ref=e251]:
                    - generic [ref=e252]: Analysis
                    - button "Close inspector" [ref=e253]:
                      - img [ref=e254]
                  - tabpanel "Analysis" [ref=e257]:
                    - region "Guided Analysis" [ref=e258]:
                      - generic [ref=e259]:
                        - generic [ref=e260]:
                          - heading "Guided workflow" [level=2] [ref=e261]
                          - button "Advanced mode" [ref=e262]
                        - generic "Current analysis context" [ref=e263]:
                          - paragraph [ref=e264]: Structural analysis · Linear planar frame · Step 4 of 4
                          - paragraph [ref=e265]: "Selected: CAD column SW · 51 CAD components"
                          - paragraph [ref=e266]: "Active result: #421 · Numerically verified · revision 103 · case Horizontal"
                          - paragraph [ref=e267]: "Next: Inspect a saved result in 3D"
                          - link "Diagnostics for this saved model" [ref=e268] [cursor=pointer]:
                            - /url: /diagnostics?project_id=793&model_revision_id=103
                          - button "Refresh saved analysis" [ref=e269]
                          - button "Restore model" [ref=e270]
                        - navigation "Analysis steps" [ref=e271]:
                          - button "1 SELECT" [ref=e272]
                          - button "2 INPUTS" [ref=e273]
                          - button "3 ANALYZE" [ref=e274]
                          - button "4 RESULTS" [ref=e275]
                      - heading "Explore saved results" [level=3] [ref=e276]
                      - generic [ref=e277]:
                        - text: Saved result
                        - combobox "Current saved analysis result" [ref=e278]:
                          - option "Select a current saved result"
                          - option "#421 · Numerically verified" [selected]
                      - group [ref=e279]:
                        - generic "Historical and failed evidence — not current results" [ref=e280] [cursor=pointer]
                      - generic "Guided visual results" [ref=e281]:
                        - paragraph [ref=e282]: "Numerically verified · saved result #421. No safety or code approval."
                        - generic "Visual result cards" [ref=e283]:
                          - button "Loads and reactions" [ref=e284]
                          - button "Deformation" [ref=e285]
                          - button "Bending / shear / axial" [pressed] [ref=e286]
                          - button "Slab or soil response" [disabled] [ref=e287]
                          - button "Warnings and unsupported checks" [ref=e288]
                        - generic [ref=e289]:
                          - text: Saved load case
                          - combobox "Guided saved load case" [ref=e290]:
                            - option "Linear sum"
                            - option "Horizontal" [selected]
                            - option "Gravity"
                            - option "Self weight"
                        - generic [ref=e291]:
                          - text: Member action
                          - combobox "Guided member action" [ref=e292]:
                            - option "Bending · kN·m" [selected]
                            - option "Shear · kN"
                            - option "Axial · kN"
                        - paragraph [ref=e293]: Amber bending · cyan shear · violet axial/torsion. Values retain saved signs and local axes. Diagram offsets are normalized display ordinates, not deformation.
                        - generic [ref=e294]:
                          - text: Inspect a component
                          - combobox "Guided inspect component" [ref=e295]:
                            - option "Click in 3D or choose here"
                            - option "beam-east"
                            - option "beam-north"
                            - option "beam-south"
                            - option "beam-west"
                            - option "column-ne"
                            - option "column-nw"
                            - option "column-se"
                            - option "column-sw"
                            - option "platform-deck"
                            - option "foundation c9e0e256-1608-4be2-b1ab-adafa10424c0 · body"
                            - option "connection 149f0f5d-b98f-4260-a428-b2fc50959cf2 · joint"
                            - option "foundation b1ad97d4-faca-46e7-87c9-f5eebb37575f · body"
                            - option "connection 13ff4b82-88f8-4c41-9613-ad85bf72054b · joint"
                            - option "foundation 9c6c5059-9557-4c35-887a-a66e95606df4 · body"
                            - option "connection a1f8b089-a278-4474-8596-ff0dade18975 · joint"
                            - option "foundation 850c983b-9d8c-416d-8785-eb7106e068bb · body"
                            - option "connection ed0730b0-c13b-47ba-9753-b63f1e86d4ac · joint"
                            - option "CAD column SW" [selected]
                            - option "CAD column SE"
                            - option "CAD beam South"
                            - option "CAD slab"
                            - option "CAD footing SW"
                            - option "CAD footing SE"
                        - status [ref=e296]: "Selected: CAD column SW. Values apply only where saved analysis evidence exists."
                        - generic [ref=e297]:
                          - checkbox "Show only analyzed members" [checked] [ref=e298]
                          - text: Show only analyzed members
                        - button "Frame result" [ref=e300]
                        - paragraph [ref=e301]: "View: isolated analyzed system; other CAD geometry is preserved."
                        - group [ref=e302]:
                          - generic "Detailed calculations, limitations and download" [ref=e303] [cursor=pointer]
                      - generic [ref=e304]:
                        - button "Reload saved inputs and results" [ref=e305]
                        - paragraph [ref=e306]: Reopening restores browser view preferences and saved evidence only. It never authorizes or reruns a solver.
                - tablist "Inspector views" [ref=e307]:
                  - tab "Layers" [ref=e308]:
                    - img [ref=e309]
                    - generic [ref=e313]: Layers
                  - tab "Inspect" [ref=e314]:
                    - img [ref=e315]
                    - generic [ref=e317]: Inspect
                  - tab "History" [ref=e318]:
                    - img [ref=e319]
                    - generic [ref=e323]: History
                  - tab "Analysis" [selected] [ref=e324]:
                    - img [ref=e325]
                    - generic [ref=e328]: Analysis
                  - tab "Review" [ref=e329]:
                    - img [ref=e330]
                    - generic [ref=e333]: Review
        - region "Engineering dock" [ref=e334]:
          - generic [ref=e336]:
            - button "Engineering dock" [ref=e337]:
              - generic [ref=e338]: Engineering dock
              - img [ref=e339]
            - button "Cost —" [ref=e342]:
              - 'generic "Cost: —" [ref=e343]':
                - img [ref=e344]
                - generic [ref=e346]: Cost
                - generic [ref=e347]: —
            - button "Cement —" [ref=e349]:
              - 'generic "Cement: —" [ref=e350]':
                - img [ref=e351]
                - generic [ref=e354]: Cement
                - generic [ref=e355]: —
            - button "Steel —" [ref=e357]:
              - 'generic "Steel: —" [ref=e358]':
                - img [ref=e359]
                - generic [ref=e363]: Steel
                - generic [ref=e364]: —
            - button "Excavation —" [ref=e366]:
              - 'generic "Excavation: —" [ref=e367]':
                - img [ref=e368]
                - generic [ref=e372]: Excavation
                - generic [ref=e373]: —
            - button "Duration —" [ref=e375]:
              - 'generic "Duration: —" [ref=e376]':
                - img [ref=e377]
                - generic [ref=e380]: Duration
                - generic [ref=e381]: —
            - button "Area —" [ref=e383]:
              - 'generic "Area: —" [ref=e384]':
                - img [ref=e385]
                - generic [ref=e388]: Area
                - generic [ref=e389]: —
            - button "Risk —" [ref=e391]:
              - 'generic "Risk: —" [ref=e392]':
                - img [ref=e393]
                - generic [ref=e396]: Risk
                - generic [ref=e397]: —
  - alert [ref=e398]
  - complementary "GeoAI Assistant" [ref=e399]:
    - separator "Resize assistant" [ref=e400]
    - generic [ref=e401]:
      - generic [ref=e402]:
        - img [ref=e403]
        - heading "GeoAI Assistant" [level=2] [ref=e406]
      - generic [ref=e407]:
        - button "Expand assistant" [ref=e408] [cursor=pointer]:
          - img [ref=e409]
        - button "Close site assistant" [ref=e414] [cursor=pointer]:
          - img [ref=e415]
    - status "Latest task status" [ref=e418]:
      - strong [ref=e420]: Completed
    - generic "AI availability" [ref=e421]: New AI messages available
    - generic "Assistant task history" [ref=e422]:
      - article [ref=e423]:
        - generic [ref=e424]:
          - generic [ref=e425]: You
          - paragraph [ref=e426]: Select CAD column SW, focus it, and show saved result 421, Horizontal bending.
        - generic [ref=e427]:
          - generic [ref=e428]: GeoAI
          - paragraph [ref=e430]: "Automated provider fixture: inspect exact saved geometry and result evidence; no calculation or model save."
          - generic [ref=e431]:
            - paragraph [ref=e432]: Selected CAD column SW.
            - group [ref=e433]:
              - generic "Evidence" [ref=e434] [cursor=pointer]
          - generic [ref=e435]:
            - paragraph [ref=e436]: Camera focused on the requested saved geometry.
            - group [ref=e437]:
              - generic "Evidence" [ref=e438] [cursor=pointer]
          - generic [ref=e439]:
            - paragraph [ref=e440]: "Displayed saved result #421 · frame · Horizontal · forces. No calculation was run."
            - group [ref=e441]:
              - generic "Evidence" [ref=e442] [cursor=pointer]
          - group [ref=e443]:
            - generic "Message details" [ref=e444] [cursor=pointer]
    - paragraph [ref=e446]: "Displayed saved result #421 · frame · Horizontal · forces. No calculation was run."
    - group [ref=e447]:
      - generic "Details" [ref=e448] [cursor=pointer]
      - option "GLM-5.3-Flash" [selected]
    - generic [ref=e449]:
      - generic [ref=e450]: Message GeoAI Assistant
      - textbox "Message GeoAI Assistant" [ref=e451]:
        - /placeholder: Ask GeoAI…
      - generic [ref=e452]:
        - generic [ref=e453]: Changes need your review
        - button "Send" [disabled] [ref=e454]:
          - img [ref=e455]
          - text: Send
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {readFileSync,writeFileSync} from 'node:fs';
  3  | import type {WorkspaceCommand} from '../lib/workspace-assistant';
  4  | const commands=JSON.parse(readFileSync('../docs/milestone-7/commands.json','utf8')) as Record<string,WorkspaceCommand>;
  5  | for(const width of [1280,1600])test(`confirmed workspace inspection ${width}`,async({page})=>{
  6  |  await page.setViewportSize({width,height:900});let batch=['select','focus','result'],sends=0,validations=0;const writes:string[]=[],errors:string[]=[];
  7  |  const tasks:unknown[]=[],outcomes:unknown[]=[];page.on('pageerror',e=>errors.push(e.message));
  8  |  await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  9  |   if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  10 |   if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Automated mock only; real inference is disabled.',models:['zai-org/GLM-5.3-Flash']}});
  11 |   if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks}});
  12 |   if(u.pathname.endsWith('/api/assistant/workspace/history'))return route.fulfill({json:{outcomes}});
  13 |   if(u.pathname.endsWith('/api/assistant/workspace/outcome')){const p=r.postDataJSON();outcomes.push({...p,taskId:p.task_id,actionId:p.action_id});return route.fulfill({json:{retained:true}});}
  14 |   if(u.pathname.endsWith('/api/assistant/workspace/validate')){validations++;return route.continue();}
  15 |   if(u.pathname.endsWith('/api/assistant/turn')){sends++;const p=r.postDataJSON();const events=[{type:'delta',text:'Automated provider fixture: inspect exact saved geometry and result evidence; no calculation or model save.'},...batch.map(key=>({type:'tool_result',name:commands[key].operation,ok:true,result:commands[key]}))];const task={id:p.request_id,request:p,status:'SUCCEEDED',model:p.model,reply:'Automated provider fixture; no inference.',events};tasks.push(task);return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});}
  16 |   if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}return route.continue();
  17 |  });
  18 |  await page.goto('/projects/793/workspace');const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  19 |  await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'GeoAI Assistant'});
  20 |  await panel.getByRole('textbox').fill('Select CAD column SW, focus it, and show saved result 421, Horizontal bending.');await panel.getByRole('button',{name:'Send',exact:true}).click();
  21 |  await expect(canvas).toHaveAttribute('data-assistant-result',JSON.stringify({projectId:793,revisionId:103,resultId:421,method:'frame',loadCase:'Horizontal',mode:'forces'}),{timeout:30000});
> 22 |  await expect(panel.getByLabel('Task status')).toHaveText('Completed');await expect(panel).toContainText('Camera focused on the requested saved geometry.');
     |                                                ^ Error: expect(locator).toHaveText(expected) failed
  23 |  await expect(panel).toContainText('Displayed saved result #421');await page.screenshot({path:`../docs/milestone-7/moments-${width}.png`});
  24 |  batch=['deformation'];await panel.getByRole('textbox').fill('Show the saved Horizontal deformation for result 421.');await panel.getByRole('button',{name:'Send',exact:true}).click();
  25 |  await expect(canvas).toHaveAttribute('data-assistant-result',JSON.stringify({projectId:793,revisionId:103,resultId:421,method:'frame',loadCase:'Horizontal',mode:'deformation'}),{timeout:30000});
  26 |  await page.screenshot({path:`../docs/milestone-7/deformation-${width}.png`});
  27 |  // Open an actual owned project after an isolated result: the overlay must not leak.
  28 |  batch=['open'];await panel.getByRole('textbox').fill('Open project 804 at its current saved revision.');await panel.getByRole('button',{name:'Send',exact:true}).click();
  29 |  await expect(page).toHaveURL(/projects\/804\/workspace/);await expect(canvas).toHaveAttribute('data-model-project','804',{timeout:30000});
  30 |  await expect(panel).toContainText(`Opened ${commands.open.projectName} · saved revision 124.`,{timeout:30000});
  31 |  await expect(page.getByText('Saved-result isolation is active. Other geometry is preserved.')).toHaveCount(0);
  32 |  await page.screenshot({path:`../docs/milestone-7/project-804-${width}.png`});
  33 |  const before=sends;await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history',exact:true}).click();await panel.getByText('Details',{exact:true}).click();await page.waitForTimeout(300);expect(sends).toBe(before);
  34 |  expect(outcomes).toHaveLength(5);expect(validations).toBeGreaterThanOrEqual(10);expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  35 |  writeFileSync(`../docs/milestone-7/browser-${width}.json`,JSON.stringify({width,height:900,mockedTurns:sends,paidInferenceRequests:0,validatedReads:validations,outcomes,errors,forbiddenWrites:writes},null,2));
  36 | });
  37 | for(const width of [1280,1600])test(`saved loading error and disabled AI ${width}`,async({page})=>{
  38 |  await page.setViewportSize({width,height:900});let fail=true,sends=0;
  39 |  await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();if(u.pathname.endsWith('/model-revisions/latest')&&fail)return route.fulfill({status:503,json:{detail:'Saved revision unavailable (automated fixture)'}});
  40 |   if(u.pathname.endsWith('/api/assistant/turn')){sends++;return route.abort();}
  41 |   if(!['GET','HEAD','OPTIONS'].includes(r.method()))return route.abort();return route.continue();});
  42 |  await page.goto('/projects/804/workspace');await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toBeVisible({timeout:30000});
  43 |  await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'GeoAI Assistant'});
  44 |  await expect(panel.getByLabel('AI availability')).toContainText('New AI messages unavailable');await panel.getByRole('textbox').fill('A disabled message');await expect(panel.getByRole('button',{name:'Send',exact:true})).toBeDisabled();expect(sends).toBe(0);
  45 |  await page.screenshot({path:`../docs/milestone-7/load-error-${width}.png`});fail=false;
  46 |  await panel.getByRole('button',{name:'Close site assistant'}).click();await page.getByRole('button',{name:'Retry saved model',exact:true}).click();await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:30000});
  47 |  await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toHaveCount(0);
  48 | });
  49 | 
```