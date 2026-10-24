import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
import type {WorkspaceCommand} from '../lib/workspace-assistant';
const commands=JSON.parse(readFileSync('../docs/milestone-7/commands.json','utf8')) as Record<string,WorkspaceCommand>;
async function visibleAnalysis(page:import('@playwright/test').Page,width:number){
 await expect.poll(async()=>page.locator('.cesium-widget canvas').evaluate((canvas,w)=>JSON.parse((canvas as HTMLElement).dataset.analysisPickPoints||'[]').some((p:{x:number;y:number}|null)=>p&&p.x>90&&p.x<w-500&&p.y>100&&p.y<800),width),{timeout:15000}).toBe(true);
}
for(const width of [1280,1600])test(`confirmed workspace inspection ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});let batch=['select','focus','result'],sends=0,validations=0;const writes:string[]=[],errors:string[]=[];
 const tasks:unknown[]=[],outcomes:unknown[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Automated mock only; real inference is disabled.',models:['zai-org/GLM-5.3-Flash']}});
  if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks}});
  if(u.pathname.endsWith('/api/assistant/workspace/history'))return route.fulfill({json:{outcomes}});
  if(u.pathname.endsWith('/api/assistant/workspace/outcome')){const p=r.postDataJSON();outcomes.push({...p,taskId:p.task_id,actionId:p.action_id});return route.fulfill({json:{retained:true}});}
  if(u.pathname.endsWith('/api/assistant/workspace/validate')){validations++;return route.continue();}
  if(u.pathname.endsWith('/api/assistant/turn')){sends++;const p=r.postDataJSON();const events=[{type:'delta',text:'Automated provider fixture: inspect exact saved geometry and result evidence; no calculation or model save.'},...batch.map(key=>({type:'tool_result',name:commands[key].operation,ok:true,result:commands[key]}))];const task={id:p.request_id,request:p,status:'SUCCEEDED',model:p.model,reply:'Automated provider fixture; no inference.',events};tasks.push(task);return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});}
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}return route.continue();
 });
 await page.goto('/projects/793/workspace');const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'StruvoCivil Assistant'});
 await panel.getByRole('textbox').fill('Select CAD column SW, focus it, and show saved result 421, Horizontal bending.');await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(canvas).toHaveAttribute('data-assistant-result',JSON.stringify({projectId:793,revisionId:103,resultId:421,method:'frame',loadCase:'Horizontal',mode:'forces'}),{timeout:30000});
 await expect(panel.getByLabel('Task status',{exact:true})).toHaveText('Completed');await expect(panel).toContainText('Camera focused on the requested saved geometry.');
 await expect(panel).toContainText('Displayed saved result #421');await visibleAnalysis(page,width);await page.screenshot({path:`../docs/milestone-7/moments-${width}.png`});
 batch=['deformation'];await panel.getByRole('textbox').fill('Show the saved Horizontal deformation for result 421.');await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(canvas).toHaveAttribute('data-assistant-result',JSON.stringify({projectId:793,revisionId:103,resultId:421,method:'frame',loadCase:'Horizontal',mode:'deformation'}),{timeout:30000});
 await visibleAnalysis(page,width);await page.screenshot({path:`../docs/milestone-7/deformation-${width}.png`});
 // Open an actual owned project after an isolated result: the overlay must not leak.
 batch=['open'];await panel.getByRole('textbox').fill('Open project 804 at its current saved revision.');await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(page).toHaveURL(/projects\/804\/workspace/);await expect(canvas).toHaveAttribute('data-model-project','804',{timeout:30000});await expect(canvas).toHaveAttribute('data-sandbox-ready','true');
 await expect(panel).toContainText(`Opened ${commands.open.projectName} · saved revision 124.`,{timeout:30000});
 await expect(page.getByText('Saved-result isolation is active. Other geometry is preserved.')).toHaveCount(0);
 await page.screenshot({path:`../docs/milestone-7/project-804-${width}.png`});
 const before=sends;await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history',exact:true}).click();await panel.getByText('Details',{exact:true}).click();await page.waitForTimeout(300);expect(sends).toBe(before);
 expect(outcomes).toHaveLength(5);expect(validations).toBeGreaterThanOrEqual(10);expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 writeFileSync(`../docs/milestone-7/browser-${width}.json`,JSON.stringify({width,height:900,mockedTurns:sends,paidInferenceRequests:0,validatedReads:validations,outcomes,errors,forbiddenWrites:writes},null,2));
});
for(const state of ['empty','hidden'] as const)test(`distinguishes ${state} saved geometry`,async({page})=>{
 await page.setViewportSize({width:1280,height:900});
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());
  if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(u.pathname.endsWith('/model-revisions/latest')){const response=await route.fetch();const body=await response.json();body.document.components=state==='empty'?[]:body.document.components.map((c:Record<string,unknown>)=>({...c,visible:false}));return route.fulfill({json:body});}
  if(!['GET','HEAD','OPTIONS'].includes(r.method()))return route.abort();return route.continue();
 });
 await page.goto('/projects/804/workspace');
 await expect(page.getByRole('status').filter({hasText:state==='empty'?'This saved model contains no components':'All model components are hidden'})).toBeVisible({timeout:90000});
 await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toHaveCount(0);
 await page.screenshot({path:`../docs/milestone-7/${state}-1280.png`});
});
for(const width of [1280,1600])test(`saved loading error and disabled AI ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});let fail=true,sends=0;
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();if(u.pathname.endsWith('/model-revisions/latest')&&fail)return route.fulfill({status:503,json:{detail:'Saved revision unavailable (automated fixture)'}});
  if(u.pathname.endsWith('/api/assistant/turn')){sends++;return route.abort();}
  if(u.pathname.includes('/files/')&&u.pathname.endsWith('model.glb'))throw Error('Saved-model failure must not fetch a legacy GLB or append download usage.');
  if(!['GET','HEAD','OPTIONS'].includes(r.method()))return route.abort();return route.continue();});
 await page.goto('/projects/804/workspace');await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toBeVisible({timeout:30000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'StruvoCivil Assistant'});
 await expect(panel.getByLabel('AI availability')).toContainText('New AI messages unavailable');await panel.getByRole('textbox').fill('A disabled message');await expect(panel.getByRole('button',{name:'Send',exact:true})).toBeDisabled();expect(sends).toBe(0);
 await page.screenshot({path:`../docs/milestone-7/load-error-${width}.png`});fail=false;
 await panel.getByRole('button',{name:'Close site assistant'}).click();await page.getByRole('button',{name:'Retry saved model',exact:true}).click();await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:30000});
 await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toHaveCount(0);
});
