# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: runtime-diagnostics.spec.ts >> read-only diagnostics and manual recovery 1600
- Location: e2e\runtime-diagnostics.spec.ts:4:36

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('alert')
Expected substring: "Diagnostics unavailable"
Error: strict mode violation: getByRole('alert') resolved to 2 elements:
    1) <p role="alert" class="text-sm">Diagnostics unavailable. No state-changing reques…</p> aka getByText('Diagnostics unavailable. No')
    2) <div role="alert" aria-live="assertive" id="__next-route-announcer__"></div> aka locator('[id="__next-route-announcer__"]')

Call log:
  - Expect "toContainText" getByRole('alert') with timeout 5000ms
  - waiting for getByRole('alert')
    - locator resolved to <div role="alert" aria-live="assertive" id="__next-route-announcer__"></div>
    - unexpected value ""

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e4]:
    - banner [ref=e5]:
      - generic [ref=e6]:
        - link "GeoAI home" [ref=e7] [cursor=pointer]:
          - /url: /
          - generic "GeoAI" [ref=e8]
        - paragraph [ref=e13]: AI-powered, site-aware construction concept visualization
      - generic [ref=e14]:
        - link "Projects" [ref=e15] [cursor=pointer]:
          - /url: /dashboard
        - link [ref=e16] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=e17]
        - link "Open settings" [ref=e19] [cursor=pointer]:
          - /url: /settings
    - main [ref=e23]:
      - main "Runtime diagnostics" [ref=e25]:
        - generic [ref=e26]:
          - generic [ref=e27]:
            - paragraph [ref=e28]: GeoAI / local runtime
            - heading "Runtime diagnostics" [level=1] [ref=e29]
            - paragraph [ref=e30]: Read-only checks. No FEA, inference, data repair or automatic retries.
          - generic [ref=e31]:
            - link "Return to model" [ref=e32] [cursor=pointer]:
              - /url: /projects/793/workspace
            - link "Settings" [ref=e33] [cursor=pointer]:
              - /url: /settings
            - button "Retry diagnostics" [ref=e34]
        - paragraph [ref=e35]: Healthy services do not imply engineering safety or production approval. Engineering approval remains disabled.
        - paragraph [ref=e36]: "Saved context: project 793 · revision 103"
        - alert [ref=e37]: Diagnostics unavailable. No state-changing request was retried. Use the manual recovery steps below.
        - generic [ref=e40]:
          - generic [ref=e41]:
            - heading "Frontend / API connection" [level=2] [ref=e42]
            - generic [ref=e43]: Unavailable
          - paragraph [ref=e44]: No current diagnostic response. The API may be stopped, unreachable, unauthorized or timed out. Previous health is not shown as current.
          - paragraph [ref=e45]: Confirm the backend on port 8001 and the same-origin proxy on port 3001. Use run-website.bat, check startup logs, then Retry. If sign-in is required, sign in first.
        - group [ref=e46]:
          - generic "Logs and manual recovery" [ref=e47] [cursor=pointer]
    - note [ref=e49]:
      - paragraph [ref=e52]: Preliminary planning only. Final construction drawings and quantities must be verified by licensed engineers and survey data.
  - generic "Page utilities" [ref=e53]:
    - button "Copy page link" [ref=e54]
  - button "Open Next.js Dev Tools" [ref=e63] [cursor=pointer]
  - alert [ref=e67]
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const evidence='../docs/runtime-diagnostics/';
  4  | for(const width of [1280,1600])test(`read-only diagnostics and manual recovery ${width}`,async({page})=>{
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
  16 |  await expect(page.getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.')).toBeVisible({timeout:90000});
  17 |  await expect(page.getByRole('heading',{name:'Saved engineering capabilities'})).toBeVisible();
  18 |  await expect(page.getByText('Supported',{exact:true})).toBeVisible();
  19 |  await expect(page.getByText('Unsupported',{exact:true}).first()).toBeVisible();
  20 |  expect(reads).toBe(1);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  21 |  await page.screenshot({path:evidence+`diagnostics-${width}.png`,fullPage:true});
> 22 |  blocked=true;await page.getByRole('button',{name:'Refresh diagnostics'}).click();await expect(page.getByRole('alert')).toContainText('Diagnostics unavailable');
     |                                                                                                                         ^ Error: expect(locator).toContainText(expected) failed
  23 |  await expect(page.getByText('Unavailable',{exact:true})).toBeVisible();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toHaveCount(0);
  24 |  await page.waitForTimeout(400);expect(reads).toBe(2);await page.screenshot({path:evidence+`unavailable-${width}.png`,fullPage:true});
  25 |  blocked=false;await page.getByRole('button',{name:'Retry diagnostics'}).click();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toBeVisible();expect(reads).toBe(3);
  26 |  await page.getByRole('button',{name:'Refresh diagnostics'}).focus();await page.keyboard.press('Enter');await expect(page.getByRole('button',{name:'Refresh diagnostics'})).toBeEnabled();expect(reads).toBe(4);
  27 |  expect(errors).toEqual([]);expect(writes).toEqual([]);
  28 |  writeFileSync(evidence+`browser-${width}.json`,JSON.stringify({width,height:900,read_only:true,simulated_transport_outage:true,manual_recovery:true,keyboard_refresh:true,reads,writes,errors},null,2));
  29 | });
  30 | test('normal saved-result workspace remains accessible without mode-driven history reads',async({page})=>{
  31 |  test.setTimeout(180000);await page.setViewportSize({width:1600,height:900});let histories=0;const writes:string[]=[];
  32 |  await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();if(u.pathname.endsWith('/engineering/assembly')||u.pathname.endsWith('/engineering/slab-transfer'))histories++;return route.continue();});
  33 |  await page.addInitScript(()=>localStorage.setItem('geoai:analysis-guided:793',JSON.stringify({family:'structure',step:'results',mode:'loads',caseName:''})));
  34 |  await page.goto('/projects/793/workspace');await page.getByRole('tab',{name:'Analysis',exact:true}).click({timeout:120000});
  35 |  const panel=page.getByRole('region',{name:'Guided Analysis',exact:true});await expect(panel.getByLabel('Guided visual results')).toBeVisible({timeout:90000});
  36 |  await expect(panel.getByLabel('Current analysis context')).toContainText('Numerically verified');
  37 |  const before=histories;await panel.getByRole('button',{name:'Bending / shear / axial',exact:true}).click();await page.waitForTimeout(500);expect(histories).toBe(before);
  38 |  await expect(panel.getByRole('link',{name:'Diagnostics for this saved model'})).toHaveAttribute('href','/diagnostics?project_id=793&model_revision_id=103');
  39 |  await page.screenshot({path:evidence+'normal-results-1600.png'});expect(writes).toEqual([]);
  40 |  writeFileSync(evidence+'workspace-smoke.json',JSON.stringify({project:793,revision:103,histories_before_mode:before,histories_after_mode:histories,writes},null,2));
  41 | });
  42 | 
```