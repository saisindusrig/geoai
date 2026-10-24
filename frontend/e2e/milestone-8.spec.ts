import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
import type {WorkspaceCommand} from '../lib/workspace-assistant';
const fixtures=JSON.parse(readFileSync('../docs/milestone-8/commands.json','utf8')) as Record<string,Record<string,WorkspaceCommand>>;
for(const width of [1280,1600])test(`supervised isolated column ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});const commands=fixtures[width],pid=commands.first.projectId;
 let batch='first',saves=0,applied=false;const forbidden:string[]=[],errors:string[]=[],tasks:unknown[]=[],outcomes:unknown[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url()),path=u.pathname;
  const forward=async()=>{const i=path.indexOf('/api/');if(i>=0)return route.fulfill({response:await route.fetch({url:'http://127.0.0.1:8002'+path.slice(i)+u.search})});return route.continue();};
  if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(path.includes('/files/')||/\/exports\/.+\.(glb|zip|json)/.test(path)){forbidden.push('download '+path);return route.abort();}
  if(path.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  if(path.endsWith('/site-suggestions'))return route.fulfill({json:{suggestions:[]}});
  if(path.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock-only browser fixture. Real inference disabled.',models:['zai-org/GLM-5.3-Flash']}});
  if(path.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks}});
  if(path.endsWith('/api/assistant/workspace/history'))return route.fulfill({json:{outcomes}});
  if(path.endsWith('/api/assistant/workspace/outcome')){const body=r.postDataJSON();outcomes.push({...body,taskId:body.task_id,actionId:body.action_id});return route.fulfill({json:{retained:true}});}
  if(path.endsWith('/api/assistant/turn')){const body=r.postDataJSON(),command=commands[batch],events=[{type:'delta',text:'Synthetic provider fixture. Review the explicit column geometry in the existing editor. Apply and Save are separate user actions.'},{type:'tool_result',name:command.operation,ok:true,result:command}];const task={id:body.request_id,request:body,status:'SUCCEEDED',events,model:body.model,reply:'Synthetic fixture; no inference.'};tasks.push(task);return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});}
  if(path.endsWith('/api/assistant/workspace/validate'))return forward();
  if(r.method()==='POST'&&path.endsWith(`/projects/${pid}/scenarios/${pid}/model-revisions`)){if(!applied)forbidden.push('save before explicit Apply');saves++;return forward();}
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){forbidden.push(r.method()+' '+path);return route.abort();}
  return forward();
 });
 await page.goto(`/projects/${pid}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();const chat=page.getByRole('complementary',{name:'StruvoCivil Assistant'}),review=page.getByRole('region',{name:'Supervised column review'});
 const send=async(key:string,message:string)=>{batch=key;await chat.getByRole('textbox').fill(message);await chat.getByRole('button',{name:'Send',exact:true}).click();};
 const preview=async(key:string)=>{await send(key,'Preview an independent 400 × 500 × 3000 mm column, centre ENU [3000,0,1500] mm, upright with yaw 15 degrees, no parent; user supplied conceptual geometry only.');await expect(canvas).toHaveAttribute('data-primitive-preview',commands[key].actionId,{timeout:30000});await expect(review).toContainText('0.4 × 0.5 × 3 m');await expect(review).toContainText('not applied or saved');};
 await preview('first');expect(saves).toBe(0);await page.screenshot({path:`../docs/milestone-8/preview-${width}.png`});
 await review.getByRole('button',{name:'Cancel proposal',exact:true}).click();await expect(review).toHaveCount(0);await expect(canvas).not.toHaveAttribute('data-primitive-preview');expect(saves).toBe(0);
 await send('first','Replay that exact proposal.');await expect(chat).toContainText('Duplicate proposal replay rejected');await expect(chat.getByLabel('Task status',{exact:true})).toHaveText('Action not completed');
 await preview('second');await send('cancel','Cancel that temporary proposal.');await expect(review).toHaveCount(0);await expect(chat).toContainText('Temporary column proposal cancelled');expect(saves).toBe(0);
 await preview('final');
 applied=true;await review.getByRole('button',{name:'Apply column',exact:true}).click();await expect(review).toContainText('applied to the editor draft · not saved');expect(saves).toBe(0);
 await expect.poll(()=>canvas.evaluate((c,id)=>Object.keys(JSON.parse((c as HTMLElement).dataset.componentPickPoints||'{}')).includes(id),commands.final.candidate!.id)).toBe(true);
 await page.screenshot({path:`../docs/milestone-8/applied-${width}.png`});
 await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(review).toContainText('absent from the current draft');
 await page.getByRole('button',{name:'Redo',exact:true}).click();await expect(review).toContainText('applied to the editor draft');expect(saves).toBe(0);
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith(`/projects/${pid}/scenarios/${pid}/model-revisions`));
 await review.getByRole('button',{name:'Save model revision',exact:true}).click();const saveResponse=await response;expect(saveResponse.status()).toBe(200);const saved=await saveResponse.json();expect(saved.document.components).toHaveLength(3);expect(saved.document.components.slice(0,2).map((c:{id:string})=>c.id)).toEqual(['original-0','original-1']);
 await expect(review).toContainText(`Saved column in revision ${saved.id}`);await expect(review.getByRole('button',{name:'Saved',exact:true})).toBeDisabled();await expect(page.getByRole('status').filter({hasText:'Loading the 3D workspace'})).toHaveCount(0);await expect(canvas).toHaveAttribute('data-sandbox-ready','true');await page.screenshot({path:`../docs/milestone-8/saved-${width}.png`});
 expect(saves).toBe(1);expect(forbidden).toEqual([]);expect(errors).toEqual([]);expect(outcomes).toHaveLength(5);
 writeFileSync(`../docs/milestone-8/browser-${width}.json`,JSON.stringify({width,height:900,isolatedProject:pid,savedRevision:saved.id,explicitSaves:saves,mockedTurns:tasks.length,paidInferenceRequests:0,forbidden,errors,outcomes},null,2));
});
