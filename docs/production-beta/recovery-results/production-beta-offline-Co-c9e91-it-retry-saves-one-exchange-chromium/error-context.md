# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: production-beta.spec.ts >> offline Copilot retains a failed draft and explicit retry saves one exchange
- Location: e2e\production-beta.spec.ts:151:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Project assistant', exact: true }).getByRole('alert')
Expected substring: "Cannot reach the local API"
Received string:    "Site changed. Save the boundary and Refresh site before sending a new request.Retry"
Timeout: 5000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Project assistant', exact: true }).getByRole('alert') with timeout 5000ms
  - waiting for getByRole('region', { name: 'Project assistant', exact: true }).getByRole('alert')
    13 × locator resolved to <div role="alert" class="space-y-2 text-destructive">…</div>
       - unexpected value "Site changed. Save the boundary and Refresh site before sending a new request.Retry"

```

```yaml
- alert:
  - paragraph: Site changed. Save the boundary and Refresh site before sending a new request.
  - button "Retry"
```

# Test source

```ts
  63  |   await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(east).toHaveValue(original);
  64  |   await page.getByRole('button',{name:'Redo',exact:true}).click();
  65  |   const saved=page.waitForResponse(r=>r.url().endsWith('/model-revisions')&&r.request().method()==='POST');
  66  |   await page.getByRole('button',{name:'Save model',exact:true}).click();expect((await saved).ok()).toBeTruthy();
  67  |   await page.reload();revision=await(await request.get(`${API}/api/projects/${pid}/scenarios/${sid}/model-revisions/latest`)).json();
  68  |   // Select a real generated beam and its two columns through Layers.
  69  |   await page.getByRole('tab',{name:'Layers',exact:true}).click();
  70  |   const search=page.getByLabel('Search scene components');await search.fill('');
  71  |   await page.locator('[id="layer-row-industrial-platform-5x3:column-sw"] button[aria-pressed]').click();
  72  |   await page.locator('[id="layer-row-industrial-platform-5x3:column-se"] button[aria-pressed]').click({modifiers:['Control']});
  73  |   await page.locator('[id="layer-row-industrial-platform-5x3:beam-south"] button[aria-pressed]').click({modifiers:['Control']});
  74  |   const frame=await analysis(page);
  75  |   await frame.getByLabel('Inspect eccentric candidates').check();
  76  |   const graphResponse=page.waitForResponse(r=>r.url().endsWith('/assembly/preview')&&r.request().method()==='POST');
  77  |   await frame.getByRole('button',{name:'Preview selected physical graph',exact:true}).click();
  78  |   const graphReply=await graphResponse;expect(graphReply.ok(),await graphReply.text()).toBeTruthy();const graph=await graphReply.json();
  79  |   for(const m of graph.members){for(const [key,value] of Object.entries({area_m2:m.solid_rectangle_area_m2,inertia_m4:m.solid_rectangle_inertia_m4,elastic_modulus_pa:200e9,material_name:'Synthetic elastic verification material',material_source:'Explicit synthetic beta verification E only; no site material evidence',section_source:'Explicit synthetic solid rectangle matching saved envelope; not a designed section'}))await frame.getByLabel(`${m.name} ${key}`,{exact:true}).fill(String(value));}
  80  |   await frame.getByLabel('Assembly joints').selectOption('rigid_offset');
  81  |   await frame.getByLabel('Approve left rigid offset').check();await frame.getByLabel('Approve right rigid offset').check();
  82  |   await frame.getByLabel('Assembly joint source').fill('Synthetic reviewed rigid arms only; physical connection capacity unverified');
  83  |   await frame.getByLabel('Assembly supports').selectOption('both_column_bases_fixed');
  84  |   await frame.getByLabel('Assembly support source').fill('Synthetic fixed bases only; foundation and soil behavior excluded');
  85  |   await frame.getByLabel('Assembly load pattern').selectOption('equal_horizontal_column_head_loads');
  86  |   await frame.getByLabel('Assembly load N',{exact:true}).fill('20000');
  87  |   await frame.getByLabel('Assembly load source').fill('Synthetic total East load 20000 N, shared equally; no self weight');
  88  |   await frame.getByRole('button',{name:'Save explicit assembly inputs',exact:true}).click();
  89  |   const prepared=page.waitForResponse(r=>r.url().endsWith('/assembly/proposals')&&r.request().method()==='POST');
  90  |   await frame.getByRole('button',{name:'Offline AI: prepare selected frame proposal',exact:true}).click();
  91  |   const proposal=await(await prepared).json();expect(proposal.status).toBe('AWAITING_AUTHORIZATION');
  92  |   await expect(frame.getByRole('button',{name:'Authorize and run saved frame OpenSees',exact:true})).toBeDisabled();
  93  |   expect((await request.post(`${API}/api/projects/${pid}/engineering/assembly/authorize-run`,{data:{proposal_id:proposal.id,proposal_sha256:'0'.repeat(64),authorize_solver:true}})).status()).toBe(409);
  94  |   await frame.getByLabel('Authorize exact assembly proposal').check();
  95  |   const solved=page.waitForResponse(r=>r.url().endsWith('/assembly/authorize-run')&&r.request().method()==='POST',{timeout:120000});
  96  |   await frame.getByRole('button',{name:'Authorize and run saved frame OpenSees',exact:true}).click();
  97  |   const solvedResponse=await solved;expect(solvedResponse.ok(),await solvedResponse.text()).toBeTruthy();const result=await solvedResponse.json();expect(result.status).toBe('VERIFIED');
  98  |   const results=page.getByLabel('Computed saved frame results');
  99  |   await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  100 |   for(const [view,mode] of [['Displacement','deformation'],['Axial Force','axial'],['Shear','shear'],['Bending Moment','moment'],['Reactions','reactions']]){await results.getByRole('tab',{name:view,exact:true}).click();await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-elastic-diagram',mode);}
  101 |   await results.getByRole('tab',{name:'Bending Moment',exact:true}).click();
  102 |   await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  103 |   for(const width of [1600,1280]){await page.setViewportSize({width,height:900});await page.waitForTimeout(800);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:`${OUT}/results-${width}.png`});}
  104 |   await results.getByRole('button',{name:'Offline AI: explain saved frame evidence',exact:true}).click();
  105 |   await expect(frame.getByLabel('Assembly explanation')).toContainText('Unverified offline AI text');
  106 |   const downloaded=page.waitForEvent('download');await results.getByRole('button',{name:'Download saved frame report',exact:true}).click();await(await downloaded).saveAs(`${OUT}/saved-frame-report.json`);
  107 |   const report=JSON.parse(readFileSync(`${OUT}/saved-frame-report.json`,'utf8'));expect(report.analysis_id).toBe(result.id);expect(report.engineering_approval).toBe('DISABLED');
  108 |   // Normal saved models can now import reference DXF without fixture metadata.
  109 |   await page.getByText('Import and review a drawing reference',{exact:true}).click();
  110 |   const drawing=page.getByLabel('Drawing engineering review');await drawing.getByLabel('Import engineering drawing DXF').setInputFiles('../docs/drawing-strength/sources/GeoAI_Practice_Platform_Plan_mm.dxf');
  111 |   await expect(drawing).toContainText('REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL');
  112 |   await drawing.getByRole('button',{name:/Show.*drawing|Show.*reference/i}).first().click();
  113 |   await page.screenshot({path:`${OUT}/drawing-reference.png`});
  114 |   await frame.getByText('Physical frame engineering inputs',{exact:true}).click();
  115 |   await frame.getByText('Loads',{exact:true}).click();await frame.getByLabel('Assembly load N',{exact:true}).fill('10000');
  116 |   await expect(results).toContainText('STALE');await expect(results.getByRole('button',{name:'Download saved frame report',exact:true})).toBeDisabled();
  117 |   await page.screenshot({path:`${OUT}/stale-draft.png`});
  118 |   await page.reload();await analysis(page);await expect(page.getByLabel('Computed saved frame results')).toContainText('VERIFIED');
  119 |   expect(errors).toEqual([]);
  120 |   writeFileSync(`${OUT}/journey.json`,JSON.stringify({projectId:pid,scenarioId:sid,revisionId:revision.id,analysisId:result.id,solverVersion:result.result.solver_version,source:'Fresh project through normal APIs and website; synthetic site and material assumptions',pageErrors:errors},null,2));
  121 | });
  122 | 
  123 | test('existing foundation workflow: separate study, exact consent, report and offline explanation',async({page,request})=>{
  124 |   test.setTimeout(180000);page.setDefaultTimeout(30000);
  125 |   await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  126 |   await page.setViewportSize({width:1600,height:900});
  127 |   await page.goto('/projects/804/workspace');await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  128 |   await page.getByRole('button',{name:'Create separate foundation study from 804',exact:true}).click();
  129 |   await expect(page).not.toHaveURL(/\/projects\/804\/workspace/);
  130 |   const pid=Number(page.url().match(/projects\/(\d+)/)![1]);
  131 |   await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByLabel('Integrated foundation workflow');
  132 |   await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  133 |   const preview=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');
  134 |   await panel.getByRole('button',{name:'Preview integrated foundation calculation',exact:true}).click();
  135 |   const previewReply=await preview;expect(previewReply.ok(),await previewReply.text()).toBeTruthy();
  136 |   await expect(panel.getByRole('button',{name:'Save reviewed foundation result',exact:true})).toBeDisabled();
  137 |   await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  138 |   const calculated=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');
  139 |   await panel.getByRole('button',{name:'Save reviewed foundation result',exact:true}).click();
  140 |   const calculatedReply=await calculated;expect(calculatedReply.ok(),await calculatedReply.text()).toBeTruthy();const result=await calculatedReply.json();
  141 |   for(const width of [1600,1280]){await page.setViewportSize({width,height:900});await page.waitForTimeout(600);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:`${OUT}/foundation-${width}.png`});}
  142 |   await panel.getByText('Reports, methods and immutable evidence',{exact:true}).click();
  143 |   const downloaded=page.waitForEvent('download');await panel.getByRole('button',{name:'Download calculation report',exact:true}).click();await(await downloaded).saveAs(`${OUT}/foundation-report.html`);
  144 |   const chat=await assistant(page);await chat.getByRole('textbox',{name:'Project message'}).fill('Explain this saved foundation result and its limitations.');await chat.getByRole('button',{name:'Send message',exact:true}).click();
  145 |   await expect(chat.getByRole('article',{name:'Assistant message'}).last()).toContainText(/foundation|footing|saved/i);
  146 |   await page.screenshot({path:`${OUT}/foundation-copilot.png`});
  147 |   writeFileSync(`${OUT}/foundation-acceptance.json`,JSON.stringify({projectId:pid,resultId:result.id,source:'Explicit separate study from existing synthetic reference 804 in isolated database'},null,2));
  148 |   expect((await request.get(`${API}/api/projects/${pid}`)).ok()).toBeTruthy();
  149 | });
  150 | 
  151 | test('offline Copilot retains a failed draft and explicit retry saves one exchange',async({page})=>{
  152 |   const {projectId:pid}=JSON.parse(readFileSync(`${OUT}/journey.json`,'utf8'));
  153 |   await page.setViewportSize({width:1280,height:900});
  154 |   await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  155 |   await page.goto(`/projects/${pid}/workspace`);const chat=await assistant(page),box=chat.getByRole('textbox',{name:'Project message'});
  156 |   await expect(box).toBeEnabled();const question=`Explain saved frame evidence and limitations. Recovery ${Date.now()}`;
  157 |   let fail=true,attempts=0;const bodies:string[]=[];
  158 |   await page.route(`**/local-api/api/projects/${pid}/conversations/*/messages`,async route=>{
  159 |     if(route.request().method()!=='POST'){await route.continue();return;}
  160 |     attempts++;bodies.push(route.request().postData()!);
  161 |     if(fail)await route.abort('connectionfailed');else await route.continue();
  162 |   });
> 163 |   await box.fill(question);await box.press('Enter');await expect(chat.getByRole('alert')).toContainText('Cannot reach the local API');
      |                                                                                           ^ Error: expect(locator).toContainText(expected) failed
  164 |   await expect(box).toHaveValue(question);expect(attempts).toBe(1);
  165 |   await page.screenshot({path:`OUT/network-recovery.png`.replace('OUT',OUT)});
  166 |   fail=false;await chat.getByRole('button',{name:'Retry',exact:true}).click();await expect(box).toHaveValue('');
  167 |   expect(attempts).toBe(2);expect(bodies[0]).toBe(bodies[1]);
  168 |   await page.reload();const reloaded=await assistant(page);await expect(reloaded.getByRole('article',{name:'Your message'}).filter({hasText:question})).toHaveCount(1);
  169 |   await expect(reloaded.getByRole('article',{name:'Assistant message'}).last()).toContainText(/saved|frame|drawing/i);
  170 | });
  171 | 
```