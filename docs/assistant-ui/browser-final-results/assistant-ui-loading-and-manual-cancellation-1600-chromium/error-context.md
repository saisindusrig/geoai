# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: assistant-ui.spec.ts >> loading and manual cancellation 1600
- Location: e2e\assistant-ui.spec.ts:71:37

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('complementary', { name: 'GeoAI Assistant' }).getByRole('alert')
Expected substring: "Usage may be unknown"
Received string:    "Failed to fetchRefresh availability"
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for getByRole('complementary', { name: 'GeoAI Assistant' }).getByRole('alert')
    13 × locator resolved to <div role="alert" class="assistant-notice">…</div>
       - unexpected value "Failed to fetchRefresh availability"

```

```yaml
- alert:
  - paragraph: Failed to fetch
  - button "Refresh availability"
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | const model="zai-org/GLM-5.3-Flash";
  3  | const reply="You can inspect **saved analysis results** without starting a calculation.\n\n1. Open **Analyze / Results**.\n2. Select a saved evidence record.\n3. Check whether the source is current.\n\n[Open diagnostics](/diagnostics) for existing service information.\n\nOpening a result does **not** run a solver or save a model.";
  4  | const oldTask={id:"sanitized-ui-history",request:{message:"Where are my saved results?",project_id:805,revision_id:null,selected_ids:[],dirty:false,page:"/projects/805/workspace",model},status:"SUCCEEDED",reply,events:[{type:"delta",text:reply}],model};
  5  | for(const width of [1280,1600]) test(`conversation, actions and blocked states ${width}`,async({page})=>{
  6  |  await page.setViewportSize({width,height:900});
  7  |  let sends=0,mode="success"; let history:unknown[]=[oldTask]; const writes:string[]=[],errors:string[]=[];
  8  |  page.on('pageerror',e=>errors.push(e.message));
  9  |  await page.route('**/*',async route=>{
  10 |   const r=route.request(),u=new URL(r.url());
  11 |   if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  12 |   if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  13 |   if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock availability. No provider request.',models:[model],requestAllowance:3,usage:{daily_requests:0,accounted_daily_tokens:14487,accounted_usd:.0024219},dailyTokenAllowance:200000}});
  14 |   if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:history}});
  15 |   if(u.pathname.endsWith('/api/assistant/turn')){
  16 |    sends++; const p=r.postDataJSON();expect(p.model).toBe(model);
  17 |    if(mode==='quota')return route.fulfill({status:429,json:{detail:{code:'DAILY_REQUEST_LIMIT',availability:'RATE_LIMITED',message:'Assistant daily request limit reached.'}}});
  18 |    if(mode==='failure')return route.fulfill({status:503,json:{detail:{code:'PROVIDER_FAILURE',availability:'DISABLED',message:'Nebius connection failed. Retry manually.'}}});
  19 |    const events=[{type:'progress',text:'Reading saved context and checking selected Nebius model availability'},{type:'tool_start',name:'read_context'},{type:'delta',text:reply},{type:'tool_result',name:'read_context',ok:true,result:{kind:'context',notice:'Sanitized recorded event shape; automated fixture.'}},{type:'tool_result',name:'navigate',ok:true,result:{kind:'navigation',projectId:805,href:'/projects/805/workspace',destination:'results'}}];
  20 |    const task={...oldTask,id:p.request_id,request:p,events};history=[...history,task];
  21 |    return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});
  22 |   }
  23 |   if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}
  24 |   return route.continue();
  25 |  });
  26 |  await page.goto('/projects/805/workspace');
  27 |  await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  28 |  await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();
  29 |  const panel=page.getByRole('complementary',{name:'GeoAI Assistant'}),pane=panel.getByLabel('Assistant task history');
  30 |  await expect(panel.getByText('saved analysis results',{exact:true})).toBeVisible();
  31 |  await expect(panel.locator('strong').filter({hasText:'saved analysis results'})).toHaveCount(1);
  32 |  await expect(panel.getByRole('link',{name:'Open diagnostics'})).toHaveAttribute('href','/diagnostics');
  33 |  await expect(panel.getByLabel('Assistant model')).not.toBeVisible();
  34 |  await page.screenshot({path:`../docs/assistant-ui/after-${width}.png`});
  35 |  await panel.getByRole('button',{name:'Expand assistant'}).click();
  36 |  const separator=panel.getByRole('separator',{name:'Resize assistant'});await separator.focus();await page.keyboard.press('ArrowLeft');
  37 |  await expect(separator).toHaveAttribute('aria-valuenow','664');
  38 |  const box=await panel.boundingBox();expect(box!.width).toBeLessThanOrEqual(width/2+1);expect(width-box!.width).toBeGreaterThanOrEqual(width/2-1);
  39 |  await page.screenshot({path:`../docs/assistant-ui/expanded-${width}.png`});
  40 |  await panel.getByRole('textbox').fill('Show existing saved results');
  41 |  await panel.getByRole('button',{name:'Send',exact:true}).click();
  42 |  await expect(panel.getByText('Checked saved project evidence',{exact:true})).toBeVisible();
  43 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Completed');
  44 |  await panel.getByRole('button',{name:'Open results',exact:true}).click();
  45 |  await expect(panel.locator('.assistant-action-status')).toContainText('Opened');
  46 |  await expect(panel.locator('.assistant-action-status')).toContainText('No calculation was started or model saved');
  47 |  await page.screenshot({path:`../docs/assistant-ui/action-${width}.png`});
  48 |  // History grows through explicit manual refresh; it never sends an inference request.
  49 |  history=[...history,...Array.from({length:8},(_,i)=>({...oldTask,id:'older-'+i,request:{...oldTask.request,message:'Recorded question '+i}}))];
  50 |  await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();
  51 |  await expect(panel.locator('article')).toHaveCount(10);
  52 |  await panel.getByText('Details',{exact:true}).click();
  53 |  await pane.evaluate(el=>{el.scrollTop=0;el.dispatchEvent(new Event('scroll'));});
  54 |  const top=await pane.evaluate(el=>el.scrollTop);expect(top).toBe(0);
  55 |  await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();await panel.getByText('Details',{exact:true}).click();
  56 |  expect(await pane.evaluate(el=>el.scrollTop)).toBeLessThan(10);
  57 |  await panel.getByRole('button',{name:'New message ↓'}).click();
  58 |  expect(await pane.evaluate(el=>el.scrollHeight-el.clientHeight-el.scrollTop)).toBeLessThan(65);
  59 |  mode='quota';await panel.getByRole('textbox').fill('A blocked request');await panel.getByRole('button',{name:'Send',exact:true}).click();
  60 |  await expect(panel.getByRole('alert')).toContainText('approved live test has used all 3 turns');
  61 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Usage limit reached');
  62 |  await expect(panel.getByRole('alert')).toContainText('not a token or money limit');
  63 |  await page.screenshot({path:`../docs/assistant-ui/quota-${width}.png`});
  64 |  expect(sends).toBe(2);await page.waitForTimeout(300);expect(sends).toBe(2);
  65 |  mode='failure';await panel.getByRole('textbox').fill('Manual service failure fixture');await panel.getByRole('button',{name:'Send',exact:true}).click();
  66 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Connection error');await expect(panel.getByRole('alert')).toContainText('Nebius connection failed');
  67 |  await page.screenshot({path:`../docs/assistant-ui/failure-${width}.png`});expect(sends).toBe(3);
  68 |  await page.keyboard.press('Escape');await expect(panel).toHaveCount(0);
  69 |  expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  70 | });
  71 | for(const width of [1280,1600]) test(`loading and manual cancellation ${width}`,async({page})=>{
  72 |  await page.setViewportSize({width,height:900});let sends=0,release!:()=>void;const gate=new Promise<void>(r=>release=r);
  73 |  await page.route('**/*',async route=>{const req=route.request(),url=new URL(req.url());if(!['localhost','127.0.0.1'].includes(url.hostname))return route.abort();
  74 |   if(url.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:[]}});
  75 |   if(url.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock only',models:[model]}});
  76 |   if(url.pathname.endsWith('/api/assistant/turn')){sends++;await gate;return route.abort().catch(()=>{});}
  77 |   if(!['GET','HEAD','OPTIONS'].includes(req.method()))return route.abort();return route.continue();});
  78 |  await page.goto('/projects/805/workspace');await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'GeoAI Assistant'});
  79 |  await panel.getByRole('textbox').fill('Explain this project');await panel.getByRole('button',{name:'Send',exact:true}).click();await expect(panel.getByLabel('Assistant availability')).toHaveText('Thinking');
  80 |  await page.screenshot({path:`../docs/assistant-ui/thinking-${width}.png`});await panel.getByRole('button',{name:'Stop response'}).click();release();
> 81 |  await expect(panel.getByRole('alert')).toContainText('Usage may be unknown');await expect(panel.getByRole('textbox')).toHaveValue('Explain this project');await expect(panel.getByLabel('Assistant availability')).toHaveText('Ready');
     |                                         ^ Error: expect(locator).toContainText(expected) failed
  82 |  await page.screenshot({path:`../docs/assistant-ui/stopped-${width}.png`});await page.waitForTimeout(250);expect(sends).toBe(1);
  83 | });
  84 | 
```