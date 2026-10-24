import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
import type {WorkspaceCommand} from '../lib/workspace-assistant';
const fixtures=JSON.parse(readFileSync('../docs/milestone-9/commands.json','utf8')) as Record<string,Record<string,WorkspaceCommand>>;
for(const width of [1280,1600])test(`supervised isolated beam ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});const commands=fixtures[width],pid=commands.first.projectId;
 let batch='first',saves=0,approved=false,rejectApply=false;const forbidden:string[]=[],errors:string[]=[],tasks:unknown[]=[],outcomes:unknown[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url()),path=u.pathname;
  const forward=async()=>{const i=path.indexOf('/api/');if(i>=0)return route.fulfill({response:await route.fetch({url:'http://127.0.0.1:8003'+path.slice(i)+u.search})});return route.continue();};
  if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(path.includes('/files/')||/\/exports\/.+\.(glb|zip|json)/.test(path)){forbidden.push('download '+path);return route.abort();}
  if(path.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  if(path.endsWith('/site-suggestions'))return route.fulfill({json:{suggestions:[]}});
  if(path.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock-only browser fixture. Real inference disabled.',models:['zai-org/GLM-5.3-Flash']}});
  if(path.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks}});
  if(path.endsWith('/api/assistant/workspace/history'))return route.fulfill({json:{outcomes}});
  if(path.endsWith('/api/assistant/workspace/outcome')){const body=r.postDataJSON();outcomes.push({...body,taskId:body.task_id,actionId:body.action_id});return route.fulfill({json:{retained:true}});}
  if(path.endsWith('/api/assistant/turn')){const body=r.postDataJSON(),command=commands[batch],events=[{type:'delta',text:'Synthetic provider fixture. Prepare the exact requested conceptual beam. Apply and Save require separate editor clicks; this message is not approval.'},{type:'tool_result',name:command.operation,ok:true,result:command}];const task={id:body.request_id,request:body,status:'SUCCEEDED',events,model:body.model,reply:'Synthetic fixture; no inference.'};tasks.push(task);return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});}
  if(path.endsWith('/api/assistant/workspace/validate')){if(rejectApply)return route.fulfill({status:409,json:{detail:'Saved source changed (isolated fixture); stale approval rejected.'}});return forward();}
  if(r.method()==='POST'&&path.endsWith(`/projects/${pid}/scenarios/${pid}/model-revisions`)){if(!approved)forbidden.push('save before explicit Apply');saves++;return forward();}
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){forbidden.push(r.method()+' '+path);return route.abort();}return forward();
 });
 await page.goto(`/projects/${pid}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();const chat=page.getByRole('complementary',{name:'StruvoCivil Assistant'}),review=page.getByRole('region',{name:'Supervised beam review'});
 const send=async(key:string,message:string)=>{batch=key;await chat.getByRole('textbox').fill(message);await chat.getByRole('button',{name:'Send',exact:true}).click();};
 const preview=async(key:string)=>{await send(key,'Preview a 300 mm by 450 mm independent beam from ENU [-2000,0,3500] mm to [2000,2000,4500] mm. No parent or connections; user supplied conceptual geometry.');await expect(canvas).toHaveAttribute('data-primitive-preview',commands[key].actionId,{timeout:30000});await expect(review).toHaveAttribute('data-proposal-state','preview_pending');await expect(review).toContainText('Length: 4.582576 m');await expect(review).toContainText('width: 0.3 m');await expect(review).toContainText('depth: 0.45 m');await expect(review.getByRole('button',{name:'Apply beam',exact:true})).toBeEnabled();};
 await preview('first');expect(saves).toBe(0);await page.screenshot({path:`../docs/milestone-9/preview-${width}.png`});
 await review.getByRole('button',{name:'Cancel proposal',exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','canceled');await expect(review.getByRole('button',{name:'Apply beam',exact:true})).toHaveCount(0);await expect(canvas).not.toHaveAttribute('data-primitive-preview');await expect(chat.getByLabel('Task status',{exact:true})).toHaveText('Canceled');await page.screenshot({path:`../docs/milestone-9/canceled-${width}.png`});
 await send('first','Replay the exact old proposal.');await expect(chat).toContainText('Duplicate proposal replay rejected');await expect(chat.getByLabel('Task status',{exact:true})).toHaveText('Rejected or stale');
 await preview('second');await send('cancel','Cancel that temporary beam.');await expect(review).toHaveAttribute('data-proposal-state','canceled');await expect(review.getByRole('button',{name:'Apply beam',exact:true})).toHaveCount(0);expect(saves).toBe(0);
 await preview('stale');rejectApply=true;await review.getByRole('button',{name:'Apply beam',exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','rejected_stale');await expect(review.getByRole('button',{name:'Apply beam',exact:true})).toHaveCount(0);expect(saves).toBe(0);await page.screenshot({path:`../docs/milestone-9/stale-${width}.png`});rejectApply=false;
 await preview('final');approved=true;await review.getByRole('button',{name:'Apply beam',exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','applied_unsaved');await expect(chat.getByLabel('Task status',{exact:true})).toHaveText('Applied but unsaved');expect(saves).toBe(0);
 await send('cancel','Cancel the already applied beam.');await expect(chat).toContainText('No temporary component preview is active');await expect(review).toHaveAttribute('data-proposal-state','applied_unsaved');
 await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','rejected_stale');await page.getByRole('button',{name:'Redo',exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','applied_unsaved');expect(saves).toBe(0);await page.screenshot({path:`../docs/milestone-9/applied-${width}.png`});
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith(`/projects/${pid}/scenarios/${pid}/model-revisions`));await review.getByRole('button',{name:'Save model revision',exact:true}).click();const saveResponse=await response;expect(saveResponse.status()).toBe(200);const saved=await saveResponse.json();expect(saved.document.components).toHaveLength(3);expect(saved.document.components[2]).toEqual(commands.final.candidate);
 await expect(review).toHaveAttribute('data-proposal-state','saved');await expect(chat.getByLabel('Task status',{exact:true})).toHaveText(`Saved in revision ${saved.id}`);await expect(review.getByRole('button',{name:'Apply beam',exact:true})).toHaveCount(0);await expect(review.getByRole('button',{name:'Cancel proposal',exact:true})).toHaveCount(0);
 await expect(page.getByRole('status').filter({hasText:'Loading the 3D workspace'})).toHaveCount(0);await expect(canvas).toHaveAttribute('data-sandbox-ready','true');await page.screenshot({path:`../docs/milestone-9/saved-${width}.png`});
 await chat.getByText('Details',{exact:true}).click();await chat.getByRole('button',{name:'Refresh history',exact:true}).click();await chat.getByText('Details',{exact:true}).click();await expect(review).toHaveAttribute('data-proposal-state','saved');expect(saves).toBe(1);expect(forbidden).toEqual([]);expect(errors).toEqual([]);expect(outcomes).toHaveLength(7);
 writeFileSync(`../docs/milestone-9/browser-${width}.json`,JSON.stringify({width,height:900,isolatedProject:pid,savedRevision:saved.id,explicitSaves:saves,mockedTurns:tasks.length,paidInferenceRequests:0,forbidden,errors,outcomes},null,2));
});
for(const width of [1280,1600])test(`saved beam read failure preserves source ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});const pid=fixtures[width].final.projectId,forbidden:string[]=[];
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url()),path=u.pathname;
  if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(path.includes('/files/')){forbidden.push('download '+path);return route.abort();}
  if(path.endsWith('/model-revisions/latest'))return route.fulfill({status:503,json:{detail:'Exact saved beam revision unavailable (synthetic fixture)'}});
  if(path.endsWith('/site-suggestions'))return route.fulfill({json:{suggestions:[]}});
  if(path.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){forbidden.push(r.method()+' '+path);return route.abort();}
  const i=path.indexOf('/api/');if(i>=0)return route.fulfill({response:await route.fetch({url:'http://127.0.0.1:8003'+path.slice(i)+u.search})});return route.continue();
 });
 await page.goto(`/projects/${pid}/workspace`);await expect(page.getByRole('alert').filter({hasText:'Saved model could not load'})).toBeVisible({timeout:60000});
 await expect(page.getByRole('region',{name:'Supervised beam review'})).toHaveCount(0);
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();await expect(page.getByLabel('AI availability')).toContainText('New AI messages unavailable');
 await page.screenshot({path:`../docs/milestone-9/load-error-${width}.png`});expect(forbidden).toEqual([]);
});
