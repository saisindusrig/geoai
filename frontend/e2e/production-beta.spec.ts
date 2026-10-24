import {test,expect,type Page} from '@playwright/test';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const API='http://127.0.0.1:8011', OUT='../docs/production-beta';
async function assistant(page:Page){
  const region=page.getByRole('region',{name:'Project assistant',exact:true});
  const opener=page.getByRole('button',{name:'Show AI Copilot panel',exact:true});
  await expect(region.or(opener).first()).toBeVisible();
  if(!await region.isVisible())await opener.click();
  await expect(region).toBeVisible();return region;
}
async function analysis(page:Page){
  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  const advanced=page.getByText('Advanced analysis · inputs, tools and evidence',{exact:true});
  if(await advanced.isVisible())await advanced.click();
  const task=page.getByText('Analysis tasks and saved results',{exact:true});
  if(await task.isVisible())await task.click();
  const frame=page.getByText('Frame analysis and saved results',{exact:true});
  if(await frame.isVisible())await frame.click();
  return page.getByLabel('Saved physical frame analysis');
}

test('fresh normal website: project, approved geometry, edit, DXF, exact solver consent, diagrams, report and reload',async({page,request})=>{
  test.setTimeout(600000);page.setDefaultTimeout(30000);mkdirSync(OUT,{recursive:true});
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1600,height:900});
  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto('/dashboard');
  await page.getByRole('button',{name:'New Project',exact:true}).first().click();
  await page.getByLabel('Project name',{exact:true}).fill(`Beta acceptance ${Date.now()}`);
  await page.getByRole('button',{name:'Create Project',exact:true}).click();
  await expect(page).toHaveURL(/\/projects\/\d+\/workspace/);
  const pid=Number(page.url().match(/projects\/(\d+)/)![1]);
  writeFileSync(`${OUT}/journey-progress.json`,JSON.stringify({projectId:pid,stage:'created'}));
  // Site coordinates are explicit synthetic test inputs; geometry is generated
  // below through the normal reviewed proposal flow, without database seeding.
  expect((await request.put(`${API}/api/projects/${pid}`,{data:{center_lng:77,center_lat:12,boundary_geojson:{type:'Polygon',coordinates:[[[77,12],[77.002,12],[77.002,12.002],[77,12.002],[77,12]]]}}})).ok()).toBeTruthy();
  await page.reload();const chat=await assistant(page);
  await chat.getByRole('button',{name:'Assistant settings',exact:true}).click();
  await chat.getByText('Context & requirements',{exact:true}).click();
  await chat.getByRole('button',{name:'Refresh site',exact:true}).click();
  await expect(chat.getByLabel('Site readiness')).toContainText('Current',{timeout:60000});
  await chat.getByRole('button',{name:'Use offline platform template',exact:true}).click();
  await chat.getByRole('button',{name:'Send message',exact:true}).click();
  await page.getByRole('button',{name:'Review proposal',exact:true}).click({timeout:60000});
  const review=page.getByLabel('Proposal review');
  await expect(review).toContainText('structural adequacy and code compliance are unverified');
  await review.getByRole('checkbox').check();
  await review.getByRole('button',{name:'Approve proposal',exact:true}).click();
  const built=page.waitForResponse(r=>r.url().endsWith('/build')&&r.request().method()==='POST');
  await review.getByRole('button',{name:'Approve & Generate 3D',exact:true}).click();
  const builtResponse=await built;expect(builtResponse.ok(),await builtResponse.text()).toBeTruthy();
  await page.reload();
  const scenarios=await(await request.get(`${API}/api/projects/${pid}/scenarios`)).json();
  const sid=scenarios.scenarios[0].scenario_id;
  let revision=await(await request.get(`${API}/api/projects/${pid}/scenarios/${sid}/model-revisions/latest`)).json();
  expect(revision.document.components).toHaveLength(9);
  writeFileSync(`${OUT}/journey-progress.json`,JSON.stringify({projectId:pid,scenarioId:sid,stage:'geometry generated'}));
  await page.getByRole('tab',{name:'Layers',exact:true}).click();
  await page.getByLabel('Search scene components').fill('platform-deck');
  await page.locator('[id="layer-row-industrial-platform-5x3:platform-deck"] button[aria-pressed]').click();
  await page.getByRole('tab',{name:'Inspect',exact:true}).click();
  const east=page.getByLabel('Position · metres East',{exact:true}),original=await east.inputValue();
  await east.fill(String(Number(original)+.1));await east.press('Tab');
  await page.getByRole('button',{name:'Apply',exact:true}).click();
  await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(east).toHaveValue(original);
  await page.getByRole('button',{name:'Redo',exact:true}).click();
  const saved=page.waitForResponse(r=>r.url().endsWith('/model-revisions')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Save model',exact:true}).click();expect((await saved).ok()).toBeTruthy();
  await page.reload();revision=await(await request.get(`${API}/api/projects/${pid}/scenarios/${sid}/model-revisions/latest`)).json();
  // Select a real generated beam and its two columns through Layers.
  await page.getByRole('tab',{name:'Layers',exact:true}).click();
  const search=page.getByLabel('Search scene components');await search.fill('');
  await page.locator('[id="layer-row-industrial-platform-5x3:column-sw"] button[aria-pressed]').click();
  await page.locator('[id="layer-row-industrial-platform-5x3:column-se"] button[aria-pressed]').click({modifiers:['Control']});
  await page.locator('[id="layer-row-industrial-platform-5x3:beam-south"] button[aria-pressed]').click({modifiers:['Control']});
  const frame=await analysis(page);
  await frame.getByLabel('Inspect eccentric candidates').check();
  const graphResponse=page.waitForResponse(r=>r.url().endsWith('/assembly/preview')&&r.request().method()==='POST');
  await frame.getByRole('button',{name:'Preview selected physical graph',exact:true}).click();
  const graphReply=await graphResponse;expect(graphReply.ok(),await graphReply.text()).toBeTruthy();const graph=await graphReply.json();
  for(const m of graph.members){for(const [key,value] of Object.entries({area_m2:m.solid_rectangle_area_m2,inertia_m4:m.solid_rectangle_inertia_m4,elastic_modulus_pa:200e9,material_name:'Synthetic elastic verification material',material_source:'Explicit synthetic beta verification E only; no site material evidence',section_source:'Explicit synthetic solid rectangle matching saved envelope; not a designed section'}))await frame.getByLabel(`${m.name} ${key}`,{exact:true}).fill(String(value));}
  await frame.getByLabel('Assembly joints').selectOption('rigid_offset');
  await frame.getByLabel('Approve left rigid offset').check();await frame.getByLabel('Approve right rigid offset').check();
  await frame.getByLabel('Assembly joint source').fill('Synthetic reviewed rigid arms only; physical connection capacity unverified');
  await frame.getByLabel('Assembly supports').selectOption('both_column_bases_fixed');
  await frame.getByLabel('Assembly support source').fill('Synthetic fixed bases only; foundation and soil behavior excluded');
  await frame.getByLabel('Assembly load pattern').selectOption('equal_horizontal_column_head_loads');
  await frame.getByLabel('Assembly load N',{exact:true}).fill('20000');
  await frame.getByLabel('Assembly load source').fill('Synthetic total East load 20000 N, shared equally; no self weight');
  await frame.getByRole('button',{name:'Save explicit assembly inputs',exact:true}).click();
  const prepared=page.waitForResponse(r=>r.url().endsWith('/assembly/proposals')&&r.request().method()==='POST');
  await frame.getByRole('button',{name:'Offline AI: prepare selected frame proposal',exact:true}).click();
  const proposal=await(await prepared).json();expect(proposal.status).toBe('AWAITING_AUTHORIZATION');
  await expect(frame.getByRole('button',{name:'Authorize and run saved frame OpenSees',exact:true})).toBeDisabled();
  expect((await request.post(`${API}/api/projects/${pid}/engineering/assembly/authorize-run`,{data:{proposal_id:proposal.id,proposal_sha256:'0'.repeat(64),authorize_solver:true}})).status()).toBe(409);
  await frame.getByLabel('Authorize exact assembly proposal').check();
  const solved=page.waitForResponse(r=>r.url().endsWith('/assembly/authorize-run')&&r.request().method()==='POST',{timeout:120000});
  await frame.getByRole('button',{name:'Authorize and run saved frame OpenSees',exact:true}).click();
  const solvedResponse=await solved;expect(solvedResponse.ok(),await solvedResponse.text()).toBeTruthy();const result=await solvedResponse.json();expect(result.status).toBe('VERIFIED');
  const results=page.getByLabel('Computed saved frame results');
  await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  for(const [view,mode] of [['Displacement','deformation'],['Axial Force','axial'],['Shear','shear'],['Bending Moment','moment'],['Reactions','reactions']]){await results.getByRole('tab',{name:view,exact:true}).click();await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-elastic-diagram',mode);}
  await results.getByRole('tab',{name:'Bending Moment',exact:true}).click();
  await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  for(const width of [1600,1280]){await page.setViewportSize({width,height:900});await page.waitForTimeout(800);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:`${OUT}/results-${width}.png`});}
  await results.getByRole('button',{name:'Offline AI: explain saved frame evidence',exact:true}).click();
  await expect(frame.getByLabel('Assembly explanation')).toContainText('Unverified offline AI text');
  const downloaded=page.waitForEvent('download');await results.getByRole('button',{name:'Download saved frame report',exact:true}).click();await(await downloaded).saveAs(`${OUT}/saved-frame-report.json`);
  const report=JSON.parse(readFileSync(`${OUT}/saved-frame-report.json`,'utf8'));expect(report.analysis_id).toBe(result.id);expect(report.engineering_approval).toBe('DISABLED');
  // Normal saved models can now import reference DXF without fixture metadata.
  await page.getByText('Import and review a drawing reference',{exact:true}).click();
  const drawing=page.getByLabel('Drawing engineering review');await drawing.getByLabel('Import engineering drawing DXF').setInputFiles('../docs/drawing-strength/sources/GeoAI_Practice_Platform_Plan_mm.dxf');
  await expect(drawing).toContainText('REFERENCE_IMPORTED_NOT_ANALYTICAL_MODEL');
  await drawing.getByRole('button',{name:/Show.*drawing|Show.*reference/i}).first().click();
  await page.screenshot({path:`${OUT}/drawing-reference.png`});
  await frame.getByText('Physical frame engineering inputs',{exact:true}).click();
  await frame.getByText('Loads',{exact:true}).click();await frame.getByLabel('Assembly load N',{exact:true}).fill('10000');
  await expect(results).toContainText('STALE');await expect(results.getByRole('button',{name:'Download saved frame report',exact:true})).toBeDisabled();
  await page.screenshot({path:`${OUT}/stale-draft.png`});
  await page.reload();await analysis(page);await expect(page.getByLabel('Computed saved frame results')).toContainText('VERIFIED');
  expect(errors).toEqual([]);
  writeFileSync(`${OUT}/journey.json`,JSON.stringify({projectId:pid,scenarioId:sid,revisionId:revision.id,analysisId:result.id,solverVersion:result.result.solver_version,source:'Fresh project through normal APIs and website; synthetic site and material assumptions',pageErrors:errors},null,2));
});

test('existing foundation workflow: separate study, exact consent, report and offline explanation',async({page,request})=>{
  test.setTimeout(180000);page.setDefaultTimeout(30000);
  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.setViewportSize({width:1600,height:900});
  await page.goto('/projects/804/workspace');await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  await page.getByRole('button',{name:'Create separate foundation study from 804',exact:true}).click();
  await expect(page).not.toHaveURL(/\/projects\/804\/workspace/);
  const pid=Number(page.url().match(/projects\/(\d+)/)![1]);
  await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByLabel('Integrated foundation workflow');
  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  const preview=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');
  await panel.getByRole('button',{name:'Preview integrated foundation calculation',exact:true}).click();
  const previewReply=await preview;expect(previewReply.ok(),await previewReply.text()).toBeTruthy();
  await expect(panel.getByRole('button',{name:'Save reviewed foundation result',exact:true})).toBeDisabled();
  await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  const calculated=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');
  await panel.getByRole('button',{name:'Save reviewed foundation result',exact:true}).click();
  const calculatedReply=await calculated;expect(calculatedReply.ok(),await calculatedReply.text()).toBeTruthy();const result=await calculatedReply.json();
  for(const width of [1600,1280]){await page.setViewportSize({width,height:900});await page.waitForTimeout(600);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:`${OUT}/foundation-${width}.png`});}
  await panel.getByText('Reports, methods and immutable evidence',{exact:true}).click();
  const downloaded=page.waitForEvent('download');await panel.getByRole('button',{name:'Download calculation report',exact:true}).click();await(await downloaded).saveAs(`${OUT}/foundation-report.html`);
  const chat=await assistant(page);await chat.getByRole('textbox',{name:'Project message'}).fill('Explain this saved foundation result and its limitations.');await chat.getByRole('button',{name:'Send message',exact:true}).click();
  await expect(chat.getByRole('article',{name:'Assistant message'}).last()).toContainText(/foundation|footing|saved/i);
  await page.screenshot({path:`${OUT}/foundation-copilot.png`});
  writeFileSync(`${OUT}/foundation-acceptance.json`,JSON.stringify({projectId:pid,resultId:result.id,source:'Explicit separate study from existing synthetic reference 804 in isolated database'},null,2));
  expect((await request.get(`${API}/api/projects/${pid}`)).ok()).toBeTruthy();
});

test('offline Copilot retains a failed draft and explicit retry saves one exchange',async({page})=>{
  const {projectId:pid}=JSON.parse(readFileSync(`${OUT}/journey.json`,'utf8'));
  await page.setViewportSize({width:1280,height:900});
  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto(`/projects/${pid}/workspace`);const chat=await assistant(page),box=chat.getByRole('textbox',{name:'Project message'});
  await expect(box).toBeEnabled();const question=`Explain saved frame evidence and limitations. Recovery ${Date.now()}`;
  let fail=true,attempts=0;const bodies:string[]=[];
  await page.route(`**/local-api/api/projects/${pid}/conversations/*/messages`,async route=>{
    if(route.request().method()!=='POST'){await route.continue();return;}
    attempts++;bodies.push(route.request().postData()!);
    if(fail)await route.abort('connectionfailed');else await route.continue();
  });
  await box.fill(question);await box.press('Enter');await expect(chat.getByRole('alert')).toContainText('Cannot reach the local API');
  await expect(box).toHaveValue(question);expect(attempts).toBe(1);
  await page.screenshot({path:`${OUT}/network-recovery.png`});
  fail=false;await chat.getByRole('button',{name:'Retry',exact:true}).click();await expect(box).toHaveValue('');
  expect(attempts).toBe(2);expect(bodies[0]).toBe(bodies[1]);
  await page.reload();const reloaded=await assistant(page);await expect(reloaded.getByRole('article',{name:'Your message'}).filter({hasText:question})).toHaveCount(1);
  await expect(reloaded.getByRole('article',{name:'Assistant message'}).last()).toContainText(/saved|frame|drawing/i);
});
