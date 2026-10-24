import { test, expect } from "@playwright/test";
const model="zai-org/GLM-5.3-Flash";
const reply="You can inspect **saved analysis results** without starting a calculation.\n\n1. Open **Analyze / Results**.\n2. Select a saved evidence record.\n3. Check whether the source is current.\n\n[Open diagnostics](/diagnostics) for existing service information.\n\nOpening a result does **not** run a solver or save a model.";
const oldTask={id:"sanitized-ui-history",request:{message:"Where are my saved results?",project_id:805,revision_id:null,selected_ids:[],dirty:false,page:"/projects/805/workspace",model},status:"SUCCEEDED",reply,events:[{type:"delta",text:reply}],model};
for(const width of [1280,1600]) test(`conversation, actions and blocked states ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});
 let sends=0,mode="success"; let history:unknown[]=[oldTask]; const writes:string[]=[],errors:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{
  const r=route.request(),u=new URL(r.url());
  if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock availability. No provider request.',models:[model],requestAllowance:3,usage:{daily_requests:0,accounted_daily_tokens:14487,accounted_usd:.0024219},dailyTokenAllowance:200000}});
  if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:history}});
  if(u.pathname.endsWith('/api/assistant/turn')){
   sends++; const p=r.postDataJSON();expect(p.model).toBe(model);
   if(mode==='quota')return route.fulfill({status:429,json:{detail:{code:'DAILY_REQUEST_LIMIT',availability:'RATE_LIMITED',message:'Assistant daily request limit reached.'}}});
   if(mode==='failure')return route.fulfill({status:503,json:{detail:{code:'PROVIDER_FAILURE',availability:'DISABLED',message:'Nebius connection failed. Retry manually.'}}});
   const events=[{type:'progress',text:'Reading saved context and checking selected Nebius model availability'},{type:'tool_start',name:'read_context'},{type:'delta',text:reply},{type:'tool_result',name:'read_context',ok:true,result:{kind:'context',notice:'Sanitized recorded event shape; automated fixture.'}},{type:'tool_result',name:'navigate',ok:true,result:{kind:'navigation',projectId:805,href:'/projects/805/workspace',destination:'results'}}];
   const task={...oldTask,id:p.request_id,request:p,events};history=[...history,task];
   return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});
  }
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}
  return route.continue();
 });
 await page.goto('/projects/805/workspace');
 await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();
 const panel=page.getByRole('complementary',{name:'StruvoCivil Assistant'}),pane=panel.getByLabel('Assistant task history');
 await expect(panel.getByText('saved analysis results',{exact:true})).toBeVisible();
 await expect(panel.locator('strong').filter({hasText:'saved analysis results'})).toHaveCount(1);
 await expect(panel.getByRole('link',{name:'Open diagnostics'})).toHaveAttribute('href','/diagnostics');
 await expect(panel.getByLabel('Assistant model')).not.toBeVisible();
 await page.screenshot({path:`../docs/assistant-ui/after-${width}.png`});
 await panel.getByRole('button',{name:'Expand assistant'}).click();
 const separator=panel.getByRole('separator',{name:'Resize assistant'});await separator.focus();await page.keyboard.press('ArrowLeft');
 await expect(separator).toHaveAttribute('aria-valuenow','664');
 const box=await panel.boundingBox();expect(box!.width).toBeLessThanOrEqual(width/2+1);expect(width-box!.width).toBeGreaterThanOrEqual(width/2-1);
 await page.screenshot({path:`../docs/assistant-ui/expanded-${width}.png`});
 await panel.getByRole('textbox').fill('Show existing saved results');
 await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(panel.getByText('Checked saved project evidence',{exact:true})).toBeVisible();
 await expect(panel.getByLabel('Task status')).toHaveText('Completed');
 await panel.getByRole('button',{name:'Open results',exact:true}).click();
 await expect(panel.locator('.assistant-action-status')).toContainText('Opened');
 await expect(panel.locator('.assistant-action-status')).toContainText('No calculation was started or model saved');
 await page.screenshot({path:`../docs/assistant-ui/action-${width}.png`});
 // History grows through explicit manual refresh; it never sends an inference request.
 history=[...history,...Array.from({length:8},(_,i)=>({...oldTask,id:'older-'+i,request:{...oldTask.request,message:'Recorded question '+i}}))];
 await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();
 await expect(panel.locator('article')).toHaveCount(10);
 await panel.getByText('Details',{exact:true}).click();
 await pane.evaluate(el=>{el.scrollTop=0;el.dispatchEvent(new Event('scroll'));});
 const top=await pane.evaluate(el=>el.scrollTop);expect(top).toBe(0);
 await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();await panel.getByText('Details',{exact:true}).click();
 expect(await pane.evaluate(el=>el.scrollTop)).toBeLessThan(10);
 await panel.getByRole('button',{name:'New message ↓'}).click();
 expect(await pane.evaluate(el=>el.scrollHeight-el.clientHeight-el.scrollTop)).toBeLessThan(65);
 mode='quota';await panel.getByRole('textbox').fill('A blocked request');await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(panel.getByRole('alert')).toContainText('approved live test has used all 3 turns');
 await expect(panel.getByLabel('Task status')).toHaveText('Usage limit reached');
 await expect(panel.getByRole('alert')).toContainText('not a token or money limit');
 await page.screenshot({path:`../docs/assistant-ui/quota-${width}.png`});
 expect(sends).toBe(2);await page.waitForTimeout(300);expect(sends).toBe(2);
 await panel.getByRole('button',{name:'Refresh availability',exact:true}).click();mode='failure';await panel.getByRole('textbox').fill('Manual service failure fixture');await panel.getByRole('button',{name:'Send',exact:true}).click();
 await expect(panel.getByLabel('Task status')).toHaveText('Connection error');await expect(panel.getByRole('alert')).toContainText('Nebius connection failed');
 await page.screenshot({path:`../docs/assistant-ui/failure-${width}.png`});expect(sends).toBe(3);
 await page.keyboard.press('Escape');await expect(panel).toHaveCount(0);
 expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
for(const width of [1280,1600]) test(`loading and manual cancellation ${width}`,async({page})=>{
 await page.setViewportSize({width,height:900});let sends=0,release!:()=>void;const gate=new Promise<void>(r=>release=r);
 await page.route('**/*',async route=>{const req=route.request(),url=new URL(req.url());if(!['localhost','127.0.0.1'].includes(url.hostname))return route.abort();
  if(url.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:[]}});
  if(url.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock only',models:[model]}});
  if(url.pathname.endsWith('/api/assistant/turn')){sends++;await gate;return route.abort().catch(()=>{});}
  if(!['GET','HEAD','OPTIONS'].includes(req.method()))return route.abort();return route.continue();});
 await page.goto('/projects/805/workspace');await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'StruvoCivil Assistant'});
 await panel.getByRole('textbox').fill('Explain this project');await panel.getByRole('button',{name:'Send',exact:true}).click();await expect(panel.getByLabel('Task status')).toHaveText('Thinking');
 await page.screenshot({path:`../docs/assistant-ui/thinking-${width}.png`});await panel.getByRole('button',{name:'Stop response'}).click();release();
 await expect(panel.getByRole('alert')).toContainText('Usage may be unknown');await expect(panel.getByRole('textbox')).toHaveValue('Explain this project');await expect(panel.getByLabel('Task status')).toHaveText('Ready');
 await page.screenshot({path:`../docs/assistant-ui/stopped-${width}.png`});await page.waitForTimeout(250);expect(sends).toBe(1);
});
