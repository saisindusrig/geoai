import {test,expect} from '@playwright/test';
import {writeFileSync,readdirSync} from 'node:fs';
const evidence='../docs/milestone-5/';
for(const width of [1280,1600])test(`patched runtime security and recovery ${width}`,async({page})=>{
 test.setTimeout(180000);await page.setViewportSize({width,height:900});
 const errors:string[]=[],writes:string[]=[];let blocked=false,reads=0;
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{
  const req=route.request(),url=new URL(req.url());
  if(!['GET','HEAD','OPTIONS'].includes(req.method())){writes.push(req.method()+' '+url.pathname);return route.abort();}
  if(!['localhost','127.0.0.1'].includes(url.hostname))return route.abort();
  if(url.pathname.endsWith('/api/system/diagnostics')){reads++;if(blocked)return route.abort('connectionrefused');}
  return route.continue();
 });
 await page.goto('/diagnostics?project_id=793&model_revision_id=103');
 await expect(page.getByText('OpenSees 3.8.0 answered a version-only probe. No FEA was run.')).toBeVisible({timeout:90000});
 await expect(page.getByRole('heading',{name:'Saved engineering capabilities'})).toBeVisible();
 await expect(page.getByText('Supported',{exact:true})).toBeVisible();
 await expect(page.getByText('Unsupported',{exact:true}).first()).toBeVisible();
 await page.getByTestId('diagnostics-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await expect(page.getByText('Planar frame',{exact:true})).toBeInViewport();await page.screenshot({path:evidence+`capabilities-${width}.png`});await page.getByTestId('diagnostics-scroll').evaluate(el=>el.scrollTop=0);
 expect(reads).toBe(1);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:evidence+`diagnostics-${width}.png`,fullPage:true});
 blocked=true;await page.getByRole('button',{name:'Refresh diagnostics'}).click();await expect(page.getByRole('main').getByRole('alert')).toContainText('Diagnostics unavailable');
 await expect(page.getByText('Unavailable',{exact:true})).toBeVisible();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toHaveCount(0);
 await page.waitForTimeout(400);expect(reads).toBe(2);await page.screenshot({path:evidence+`unavailable-${width}.png`,fullPage:true});
 blocked=false;await page.getByRole('button',{name:'Retry diagnostics'}).click();await expect(page.getByText(/OpenSees 3.8.0 answered/)).toBeVisible();expect(reads).toBe(3);
 await page.getByRole('button',{name:'Refresh diagnostics'}).focus();await page.keyboard.press('Enter');await expect(page.getByRole('button',{name:'Refresh diagnostics'})).toBeEnabled();expect(reads).toBe(4);

 const security=await page.evaluate(async()=>{
  const base='/local-api/api/projects/793',capResponse=await fetch(base+'/engineering/capabilities?model_revision_id=103'),cap=await capResponse.json();
  const invalid=await fetch(base,{headers:{Authorization:'Bearer invalid'}});
  const foreign=await fetch(base,{headers:{'X-Mock-User-Id':'2'}});
  const current=cap.methods.frame.current_results[0],stale=cap.methods.frame.history.find((r:{status:string})=>r.status==='STALE');
  const url=base+'/engineering/assembly/'+current.id+'/report',report=await fetch(url),buffer=await report.arrayBuffer();
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(b=>b.toString(16).padStart(2,'0')).join('');
  const denied=await fetch(url,{headers:{'X-Mock-User-Id':'2'}});
  const missing=await fetch(base+'/engineering/assembly/'+current.id+'/artifacts/not-allowlisted.txt');
  const staleResponse=stale?await fetch(base+'/engineering/assembly/'+stale.id+'/report'):null;
  const doc=await fetch('/diagnostics');
  return {invalid:invalid.status,foreign:foreign.status,report:report.status,attachment:report.headers.get('content-disposition'),bytes:buffer.byteLength,sha256:hash,denied:denied.status,non_allowlisted:missing.status,stale_id:stale?.id,stale_rejected:staleResponse?.status,headers:{nosniff:doc.headers.get('x-content-type-options'),frame:doc.headers.get('x-frame-options'),csp:doc.headers.get('content-security-policy')},engineering_approval:cap.engineering_approval};
 });
 expect(security.invalid).toBe(401);expect(security.foreign).toBe(404);expect(security.report).toBe(200);expect(security.attachment).toContain('attachment');expect(security.denied).toBe(404);expect(security.non_allowlisted).toBe(404);expect(security.stale_rejected).toBe(409);expect(security.engineering_approval).toBe('DISABLED');
 writeFileSync(evidence+`security-${width}.json`,JSON.stringify(security,null,2));
 expect(errors).toEqual([]);expect(writes).toEqual([]);
 writeFileSync(evidence+`browser-${width}.json`,JSON.stringify({width,height:900,read_only:true,simulated_transport_outage:true,manual_recovery:true,keyboard_refresh:true,reads,writes,errors},null,2));
});

for(const width of [1280,1600])test(`patched normal website CAD and saved models ${width}`,async({page})=>{
 test.setTimeout(240000);await page.setViewportSize({width,height:900});const writes:string[]=[],errors:string[]=[],external:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const request=route.request(),url=new URL(request.url());if(!['GET','HEAD','OPTIONS'].includes(request.method())){writes.push(request.method()+' '+url.pathname);return route.abort();}if(!['localhost','127.0.0.1'].includes(url.hostname)){external.push(url.hostname);return route.abort();}if(url.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
 await page.addInitScript(()=>{for(const [id,family,step] of [[793,'structure','results'],[794,'floors','results'],[804,'foundation','select']])localStorage.setItem(`geoai:analysis-guided:${id}`,JSON.stringify({family,step,mode:'loads',caseName:''}));});
 await page.goto('/dashboard');await expect(page.getByRole('heading').first()).toBeVisible();await expect(page.locator('body')).not.toContainText('missing required error components');await page.screenshot({path:evidence+`dashboard-${width}.png`});
 const worker=readdirSync('public/cesium/Workers').find(name=>name.endsWith('.js'))!;
 const asset=await page.evaluate(async path=>{const r=await fetch(path);return {status:r.status,bytes:(await r.arrayBuffer()).byteLength};},'/cesium/Workers/'+worker);expect(asset.status).toBe(200);expect(asset.bytes).toBeGreaterThan(100);
 for(const id of [793,794,804]){
  await page.goto(`/projects/${id}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
  await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Guided Analysis',exact:true});await expect(panel.getByRole('navigation',{name:'Analysis steps'})).toBeVisible();
  await expect(panel.getByText('Reading saved analysis — no calculation is running.',{exact:true})).toHaveCount(0,{timeout:60000});
  if(id!==804){await expect(panel.getByLabel('Guided visual results')).toBeVisible({timeout:60000});await expect(panel.getByLabel('Current analysis context')).toContainText('Numerically verified');await panel.getByRole('button',{name:'Bending / shear / axial',exact:true}).click();await expect(panel.getByRole('button',{name:'Bending / shear / axial',exact:true})).toHaveAttribute('aria-pressed','true');}
  else{await expect(panel.getByLabel('Guided visual results')).toHaveCount(0);await expect(panel.getByLabel('Current analysis context')).toContainText('None current');}
  await page.waitForTimeout(500);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);await page.screenshot({path:evidence+`project-${id}-${width}.png`});
 }
 expect(writes).toEqual([]);expect(errors).toEqual([]);
 writeFileSync(evidence+`normal-models-${width}.json`,JSON.stringify({width,height:900,projects:[793,794,804],dashboard:true,cesium_worker:worker,asset,writes,errors,external_requests_blocked:external,no_inference:true},null,2));
});
