# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-system.spec.ts >> isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits
- Location: e2e\foundation-system.spec.ts:5:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/Saved foundation evidence #/)
Expected: visible
Error: strict mode violation: getByText(/Saved foundation evidence #/) resolved to 2 elements:
    1) <div class="whitespace-pre-wrap break-words">Saved foundation evidence #614 · REVIEWED_SYNTHET…</div> aka getByText('Saved foundation evidence #').first()
    2) <p class="mt-3 whitespace-pre-wrap text-xs">Project 809 · saved revision 131 (v1).↵↵Saved fou…</p> aka getByText('Project 809 · saved revision')

Call log:
  - Expect "toBeVisible" getByText(/Saved foundation evidence #/) with timeout 60000ms
  - waiting for getByText(/Saved foundation evidence #/)

```

# Page snapshot

```yaml
- generic [ref=f1e1]:
  - link "Skip to main content" [ref=f1e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=f1e4]:
    - banner [ref=f1e5]:
      - link "GeoAI home" [ref=f1e6] [cursor=pointer]:
        - /url: /
        - generic "GeoAI" [ref=f1e7]
      - heading "Foundation integrated study · reference 804" [level=1] [ref=f1e13]
      - generic [ref=f1e14]:
        - link "3D Sandbox editor" [ref=f1e15] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
        - link "Projects" [ref=f1e19] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=f1e20]:
          - button "Save site geometry" [ref=f1e21]
          - link [ref=f1e26] [cursor=pointer]:
            - /url: /projects/809/report
            - button "Export" [ref=f1e27]
        - link [ref=f1e31] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=f1e32]
        - link "Open settings" [ref=f1e34] [cursor=pointer]:
          - /url: /settings
    - main [ref=f1e38]:
      - generic [ref=f1e41]:
        - generic [ref=f1e42]:
          - generic "Design workflow" [ref=f1e46]:
            - button "1 Site" [ref=f1e47]
            - group [ref=f1e48]:
              - generic "Workflow help" [ref=f1e49] [cursor=pointer]
            - group [ref=f1e50]:
              - generic "2 Create / Import" [ref=f1e51] [cursor=pointer]
            - button "3 Review 3D" [ref=f1e52]
            - button "4 Edit" [ref=f1e53]
            - button "5 Analyze / Results" [ref=f1e54]
            - button "6 Review" [ref=f1e55]
            - status [ref=f1e56]: Saved · v1
            - button "Save model" [disabled]
          - generic [ref=f1e57]:
            - generic [ref=f1e58]:
              - generic [ref=f1e61]:
                - generic: 12.97160° N · 77.59460° E
                - generic [ref=f1e62]:
                  - generic "Mouse navigation" [ref=f1e63]:
                    - button "Select" [pressed] [ref=f1e64]
                    - button "Orbit" [ref=f1e65]
                    - button "Pan" [ref=f1e66]
                    - button "Mouse controls" [ref=f1e67]
                  - generic "Viewport presentation" [ref=f1e68]:
                    - generic [ref=f1e69]:
                      - button "Model view" [pressed] [ref=f1e70]
                      - generic [ref=f1e71]: /
                      - button "Site view" [ref=f1e72]
                      - generic [ref=f1e73]: Illustrative finishes · not material evidence
                    - generic [ref=f1e74]:
                      - group [ref=f1e75]:
                        - generic "Standard views" [ref=f1e76] [cursor=pointer]
                      - button "Focus Structure" [ref=f1e77]
                      - button "Fit All" [ref=f1e78]
                      - button "Fit selection" [disabled] [ref=f1e79]
                      - button "Dimensions off" [ref=f1e80]
                      - group [ref=f1e81]:
                        - generic "Display legend" [ref=f1e82] [cursor=pointer]
                  - generic [ref=f1e84]:
                    - generic "3D workspace viewport" [ref=f1e87]
                    - button "Full screen" [ref=f1e89] [cursor=pointer]
              - complementary "Workspace tools" [ref=f1e93]:
                - group "Object editing" [ref=f1e94]:
                  - generic [ref=f1e95]: Edit
                  - generic "Click to select and inspect · Ctrl to add · V" [ref=f1e96]:
                    - button "Select object" [pressed] [ref=f1e97]
                  - generic "Move selection · Select an editable object first" [ref=f1e101]:
                    - button "Move selection" [disabled] [ref=f1e102]
                  - generic "Rotate selection · Select an editable object first" [ref=f1e109]:
                    - button "Rotate selection" [disabled] [ref=f1e110]
                  - generic "Scale selection · Select an editable object first" [ref=f1e115]:
                    - button "Scale selection" [disabled] [ref=f1e116]
                - group "Site geometry" [ref=f1e124]:
                  - generic [ref=f1e125]: Site
                  - generic "Draw a rectangular site boundary" [ref=f1e126]:
                    - button "Draw rectangular boundary" [ref=f1e127]
                  - generic "Draw a closed site boundary" [ref=f1e131]:
                    - button "Draw site boundary" [ref=f1e132]
                  - generic "Edit site boundary · Draw a site boundary first" [ref=f1e136]:
                    - button "Edit site boundary" [disabled] [ref=f1e137]
                  - generic "Draw a road or infrastructure centerline" [ref=f1e142]:
                    - button "Draw alignment" [ref=f1e143]
                  - generic "Edit alignment · Draw an alignment first" [ref=f1e149]:
                    - button "Edit alignment" [disabled] [ref=f1e150]
                - generic [ref=f1e160]: View
                - generic "Measure distance, elevation, slope, area or clearance · M" [ref=f1e161]:
                  - button "Measure" [ref=f1e162]
                - generic "Fit the project in view · F" [ref=f1e170]:
                  - button "Fit project" [ref=f1e171]
                - generic [ref=f1e180]: Actions
                - generic "Duplicate selection · Select an editable object first" [ref=f1e181]:
                  - button "Duplicate selection" [disabled] [ref=f1e182]
                - generic "Delete selection · Select an editable object first" [ref=f1e187]:
                  - button "Delete selection" [disabled] [ref=f1e188]
                - generic "Undo · No object edits to undo" [ref=f1e194]:
                  - button "Undo" [disabled] [ref=f1e195]
                - generic "Redo · No object edits to redo" [ref=f1e200]:
                  - button "Redo" [disabled] [ref=f1e201]
              - generic [ref=f1e206]:
                - generic "Scene / Sun study" [ref=f1e207]:
                  - button "Scene / Sun study" [ref=f1e208]
                - button "Search workspace" [ref=f1e216]
                - group [ref=f1e220]:
                  - generic "Import site geometry" [ref=f1e221] [cursor=pointer]: Import
              - group "Camera orientation gizmo" [ref=f1e225]:
                - button "Negative Y axis view" [ref=f1e232]
                - button "Negative Z axis view" [disabled] [ref=f1e233]
                - button "Negative X axis view" [ref=f1e234]
                - button "Positive X axis view" [ref=f1e235]: X
                - button "Positive Z axis view" [ref=f1e236]: Z
                - button "Positive Y axis view" [ref=f1e237]: "Y"
            - complementary "AI assistant sidebar" [ref=f1e238]:
              - separator "Resize panel width" [ref=f1e239]
              - generic [ref=f1e240]:
                - button "Close Assistant" [ref=f1e241]
                - tablist "AI conversation" [ref=f1e245]:
                  - tab "Assistant" [selected] [ref=f1e246]
                - region "Project assistant" [ref=f1e251]:
                  - generic [ref=f1e252]:
                    - generic [ref=f1e253]:
                      - generic [ref=f1e254]:
                        - heading "GeoAI Assistant" [level=2] [ref=f1e255]
                        - paragraph [ref=f1e256]: Offline · saved project data
                      - button "Assistant settings" [ref=f1e257]
                    - paragraph [ref=f1e261]: Ask about your model
                  - generic [ref=f1e262]:
                    - log "Conversation messages" [ref=f1e263]:
                      - article "Your message" [ref=f1e264]:
                        - generic [ref=f1e265]: You
                        - generic [ref=f1e267]: Explain saved foundation reinforcement, punching and supported alternatives
                      - article "Assistant message" [ref=f1e268]:
                        - generic [ref=f1e269]: GeoAI
                        - generic [ref=f1e271]: "Saved foundation evidence #614 · REVIEWED_SYNTHETIC_CALCULATION. Service column 144.0 kN; service gross soil action 160.2 kN; independently declared factored column 216.0 kN. No automatic load factors. EAST_WEST_LOWER: As 2513.274 mm², d 365.000 mm, spacing 147.143 mm; flexure WITHIN_IMPLEMENTED_CHECK; one-way shear DISABLED; development EXCEEDS_IMPLEMENTED_CHECK. NORTH_SOUTH_UPPER: As 2513.274 mm², d 345.000 mm, spacing 147.143 mm; flexure WITHIN_IMPLEMENTED_CHECK; one-way shear DISABLED; development EXCEEDS_IMPLEMENTED_CHECK. Punching: WITHIN_IMPLEMENTED_CHECK. Compare supported larger square widths, increased thickness and revised orthogonal bar counts using Compare alternatives in the foundation panel. Increased width reduces soil pressure but also changes cantilever projection; recalculate bending and shear. Increased thickness changes depth and self-weight. These are review proposals only; chat cannot apply or authorize changes. Winkler displacement is not site settlement approval. Disabled checks, physical load transfer and incomplete detailing prevent a whole-foundation conclusion."
                        - generic [ref=f1e272]:
                          - button "Review required inputs" [ref=f1e273]
                          - group [ref=f1e274]:
                            - generic "Details" [ref=f1e275] [cursor=pointer]
                    - generic [ref=f1e276]:
                      - button "Jump to latest message" [ref=f1e277]
                      - paragraph [ref=f1e278]: Numerical results are not structural design approval.
                      - generic [ref=f1e279]:
                        - textbox "Project message" [active] [ref=f1e280]:
                          - /placeholder: Ask about your model…
                        - generic [ref=f1e281]:
                          - generic [ref=f1e282]: Offline saved-evidence guidance · no inference
                          - button "Send message" [disabled]
                      - paragraph [ref=f1e283]: Enter to send · Shift+Enter for a new line
            - complementary [ref=f1e285]:
              - tablist "Inspector views" [ref=f1e288]:
                - tab "Layers" [ref=f1e289]
                - tab "Inspect" [ref=f1e295]
                - tab "History" [ref=f1e299]
                - tab "Analysis" [ref=f1e305]
                - tab "Review" [ref=f1e310]
        - region "Engineering dock" [ref=f1e315]:
          - generic [ref=f1e317]:
            - button "Engineering dock" [ref=f1e318]
            - button "Cost —" [ref=f1e323]:
              - 'generic "Cost: —" [ref=f1e324]':
                - generic [ref=f1e327]: Cost
                - generic [ref=f1e328]: —
            - button "Cement —" [ref=f1e330]:
              - 'generic "Cement: —" [ref=f1e331]':
                - generic [ref=f1e335]: Cement
                - generic [ref=f1e336]: —
            - button "Steel —" [ref=f1e338]:
              - 'generic "Steel: —" [ref=f1e339]':
                - generic [ref=f1e344]: Steel
                - generic [ref=f1e345]: —
            - button "Excavation —" [ref=f1e347]:
              - 'generic "Excavation: —" [ref=f1e348]':
                - generic [ref=f1e353]: Excavation
                - generic [ref=f1e354]: —
            - button "Duration —" [ref=f1e356]:
              - 'generic "Duration: —" [ref=f1e357]':
                - generic [ref=f1e361]: Duration
                - generic [ref=f1e362]: —
            - button "Area —" [ref=f1e364]:
              - 'generic "Area: —" [ref=f1e365]':
                - generic [ref=f1e369]: Area
                - generic [ref=f1e370]: —
            - button "Risk —" [ref=f1e372]:
              - 'generic "Risk: —" [ref=f1e373]':
                - generic [ref=f1e377]: Risk
                - generic [ref=f1e378]: —
  - button "Open Next.js Dev Tools" [ref=f1e384] [cursor=pointer]
  - alert [ref=f1e388]
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000}),API='http://127.0.0.1:18001';
  4  | test.use({trace:'off'});
  5  | test('isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits',async({page,request})=>{
  6  |  test.setTimeout(300000);page.setDefaultTimeout(30000);
  7  |  const attestation=await (await request.get(API+'/__foundation_validation')).json();expect(attestation.mode).toBe('foundation-isolated-20261015');expect(attestation.database.replaceAll('\\','/').endsWith('/docs/foundation-system/isolated/foundation.db')).toBe(true);
  8  |  expect(process.env.PLAYWRIGHT_BASE_URL).toContain(':13001');
  9  |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  10 |  await page.route('**/*',async r=>{const u=r.request().url();if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(u))throw new Error('Original backend forbidden in isolated browser');await r.fallback();});
  11 |  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  12 |  await page.setViewportSize({width:1600,height:1000});
  13 |  await page.goto('/projects/804/workspace');
  14 |  const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  15 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  16 |  let panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  17 |  await expect(panel).toBeVisible();
  18 |  const copyResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/copy')&&r.request().method()==='POST');
  19 |  await panel.getByRole('button',{name:'Create separate foundation study from 804'}).click();
  20 |  const response=await copyResponse;expect(response.ok(),await response.text()).toBeTruthy();const copy=await response.json();
  21 |  await page.waitForURL(`**/projects/${copy.project_id}/workspace`);
  22 |  await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  23 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  24 |  await expect(panel.getByLabel('Foundation code and edition')).toHaveValue('IS456-2000-A1A2');
  25 |  await expect(panel.getByRole('button',{name:'Preview integrated foundation calculation'})).toBeDisabled();
  26 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  27 |  const previewResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Preview integrated foundation calculation'}).click();
  28 |  const preview=await previewResponse;expect(preview.ok(),await preview.text()).toBeTruthy();const proposal=await preview.json();
  29 |  await expect(panel).toHaveAttribute('data-busy','false');
  30 |  await expect(panel.getByRole('button',{name:'Save reviewed foundation result'})).toBeDisabled();
  31 |  await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  32 |  const authResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Save reviewed foundation result'}).click();const auth=await authResponse;expect(auth.ok(),await auth.text()).toBeTruthy();const result=await auth.json();
  33 |  const output=panel.getByRole('article',{name:'Integrated foundation results'});await expect(output).toContainText('EXCEEDS_IMPLEMENTED_CHECK');await expect(output).toContainText('365.000');await expect(output).toContainText('345.000');
  34 |  await output.getByRole('button',{name:'Show foundation engineering 3D'}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(1000);
  35 |  await page.screenshot({path:'../docs/foundation-system/3d-foundation-1600.png'});
  36 |  const download=page.waitForEvent('download');await output.getByRole('button',{name:'Download calculation report'}).click();const file=await download;await file.saveAs('../docs/foundation-system/browser-calculation-report.html');
  37 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();await panel.getByRole('button',{name:'Compare foundation alternatives'}).click();await expect(panel.getByText('Unsaved alternatives · review required',{exact:true})).toBeVisible();
> 38 |  const assistant=page.getByRole('region',{name:'Project assistant',exact:true});if(!await assistant.isVisible())await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const input=assistant.getByRole('textbox',{name:'Project message'});await expect(input).toBeEnabled({timeout:30000});await input.fill('Explain saved foundation reinforcement, punching and supported alternatives');await page.getByRole('button',{name:'Send message',exact:true}).click();await expect(page.getByText(/Saved foundation evidence #/)).toBeVisible({timeout:60000});await expect(page.getByText(/chat cannot apply or authorize/)).toBeVisible();
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           ^ Error: expect(locator).toBeVisible() failed
  39 |  await page.screenshot({path:'../docs/foundation-system/offline-copilot-1600.png'});
  40 |  if(await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).isVisible())await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).click();await page.getByRole('tab',{name:'Analysis',exact:true}).click();await panel.getByText('Actions, materials, soil and detailing inputs',{exact:true}).click();await panel.getByLabel('Independent factored column action kN',{exact:true}).fill('432');await expect(output).toContainText('STALE');await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');await expect(output.getByRole('button',{name:'Download calculation report'})).toBeDisabled();
  41 |  await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(output).toContainText('REVIEWED_SYNTHETIC_CALCULATION');
  42 |  await page.setViewportSize({width:1280,height:900});await output.getByRole('button',{name:'Show foundation engineering 3D'}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(800);await page.screenshot({path:'../docs/foundation-system/3d-foundation-1280.png'});
  43 |  await panel.getByRole('button',{name:'Restore full model from foundation view'}).click();await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');
  44 |  expect(errors).toEqual([]);
  45 |  writeFileSync('../docs/foundation-system/browser-results.json',JSON.stringify({attestation,copy,proposal_id:proposal.id,result_id:result.id,two_mats:true,download:true,alternatives:true,offline_copilot:true,stale_edit_clears_overlay:true,reload:true,page_errors:errors},null,2));
  46 | });
  47 | 
```