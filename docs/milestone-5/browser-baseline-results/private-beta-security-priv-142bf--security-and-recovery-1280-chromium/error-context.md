# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: private-beta-security.spec.ts >> private-beta read-only security and recovery 1280
- Location: e2e\private-beta-security.spec.ts:4:36

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.')
Expected: visible
Timeout: 90000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.') with timeout 90000ms
  - waiting for getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.')

```

```yaml
- text: missing required error components, refreshing...
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const evidence='../docs/private-beta-security/';
  4  | for(const width of [1280,1600])test(`private-beta read-only security and recovery ${width}`,async({page})=>{
  5  |  test.setTimeout(180000);await page.setViewportSize({width,height:900});
  6  |  const errors:string[]=[],writes:string[]=[];let blocked=false,reads=0;
  7  |  page.on('pageerror',e=>errors.push(e.message));
  8  |  await page.route('**/*',async route=>{
  9  |   const req=route.request(),url=new URL(req.url());
  10 |   if(!['GET','HEAD','OPTIONS'].includes(req.method())){writes.push(req.method()+' '+url.pathname);return route.abort();}
  11 |   if(!['localhost','127.0.0.1'].includes(url.hostname))return route.abort();
  12 |   if(url.pathname.endsWith('/api/system/diagnostics')){reads++;if(blocked)return route.abort('connectionrefused');}
  13 |   return route.continue();
  14 |  });
  15 |  await page.goto('/diagnostics?project_id=793&model_revision_id=103');
> 16 |  await expect(page.getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.')).toBeVisible({timeout:90000});
     |                                                                                                ^ Error: expect(locator).toBeVisible() failed
  17 |  await expect(page.getByRole('heading',{name:'Saved engineering capabilities'})).toBeVisible();
  18 |  await expect(page.getByText('Supported',{exact:true})).toBeVisible();
  19 |  await expect(page.getByText('Unsupported',{exact:true}).first()).toBeVisible();
  20 |  await page.getByTestId('diagnostics-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await expect(page.getByText('Planar frame',{exact:true})).toBeInViewport();await page.screenshot({path:evidence+`capabilities-${width}.png`});await page.getByTestId('diagnostics-scroll').evaluate(el=>el.scrollTop=0);
  21 |  expect(reads).toBe(1);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  22 |  await page.screenshot({path:evidence+`diagnostics-${width}.png`,fullPage:true});
  23 |  blocked=true;await page.getByRole('button',{name:'Refresh diagnostics'}).click();await expect(page.getByRole('main').getByRole('alert')).toContainText('Diagnostics unavailable');
  24 |  await expect(page.getByText('Unavailable',{exact:true})).toBeVisible();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toHaveCount(0);
  25 |  await page.waitForTimeout(400);expect(reads).toBe(2);await page.screenshot({path:evidence+`unavailable-${width}.png`,fullPage:true});
  26 |  blocked=false;await page.getByRole('button',{name:'Retry diagnostics'}).click();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toBeVisible();expect(reads).toBe(3);
  27 |  await page.getByRole('button',{name:'Refresh diagnostics'}).focus();await page.keyboard.press('Enter');await expect(page.getByRole('button',{name:'Refresh diagnostics'})).toBeEnabled();expect(reads).toBe(4);
  28 | 
  29 |  const security=await page.evaluate(async()=>{
  30 |   const base='/local-api/api/projects/793',capResponse=await fetch(base+'/engineering/capabilities?model_revision_id=103'),cap=await capResponse.json();
  31 |   const invalid=await fetch(base,{headers:{Authorization:'Bearer invalid'}});
  32 |   const foreign=await fetch(base,{headers:{'X-Mock-User-Id':'2'}});
  33 |   const current=cap.methods.frame.current_results[0],stale=cap.methods.frame.history.find((r:{status:string})=>r.status==='STALE');
  34 |   const url=base+'/engineering/assembly/'+current.id+'/report',report=await fetch(url),buffer=await report.arrayBuffer();
  35 |   const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(b=>b.toString(16).padStart(2,'0')).join('');
  36 |   const denied=await fetch(url,{headers:{'X-Mock-User-Id':'2'}});
  37 |   const missing=await fetch(base+'/engineering/assembly/'+current.id+'/artifacts/not-allowlisted.txt');
  38 |   const staleResponse=stale?await fetch(base+'/engineering/assembly/'+stale.id+'/report'):null;
  39 |   const doc=await fetch('/diagnostics');
  40 |   return {invalid:invalid.status,foreign:foreign.status,report:report.status,attachment:report.headers.get('content-disposition'),bytes:buffer.byteLength,sha256:hash,denied:denied.status,non_allowlisted:missing.status,stale_id:stale?.id,stale_rejected:staleResponse?.status,headers:{nosniff:doc.headers.get('x-content-type-options'),frame:doc.headers.get('x-frame-options'),csp:doc.headers.get('content-security-policy')},engineering_approval:cap.engineering_approval};
  41 |  });
  42 |  expect(security.invalid).toBe(401);expect(security.foreign).toBe(404);expect(security.report).toBe(200);expect(security.attachment).toContain('attachment');expect(security.denied).toBe(404);expect(security.non_allowlisted).toBe(404);expect(security.stale_rejected).toBe(409);expect(security.engineering_approval).toBe('DISABLED');
  43 |  writeFileSync(evidence+`security-${width}.json`,JSON.stringify(security,null,2));
  44 |  expect(errors).toEqual([]);expect(writes).toEqual([]);
  45 |  writeFileSync(evidence+`browser-${width}.json`,JSON.stringify({width,height:900,read_only:true,simulated_transport_outage:true,manual_recovery:true,keyboard_refresh:true,reads,writes,errors},null,2));
  46 | });
  47 | 
```