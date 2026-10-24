import {test,expect} from '@playwright/test';
import {writeFileSync} from 'node:fs';
const evidence='../docs/runtime-diagnostics/';
for(const width of [1280,1600])test(`read-only diagnostics and manual recovery ${width}`,async({page})=>{
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
 expect(errors).toEqual([]);expect(writes).toEqual([]);
 writeFileSync(evidence+`browser-${width}.json`,JSON.stringify({width,height:900,read_only:true,simulated_transport_outage:true,manual_recovery:true,keyboard_refresh:true,reads,writes,errors},null,2));
});
test('normal saved-result workspace remains accessible without mode-driven history reads',async({page})=>{
 test.setTimeout(180000);await page.setViewportSize({width:1600,height:900});let histories=0;const writes:string[]=[];
 await page.route('**/*',async route=>{const r=route.request(),u=new URL(r.url());if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();if(u.pathname.endsWith('/engineering/assembly')||u.pathname.endsWith('/engineering/slab-transfer'))histories++;return route.continue();});
 await page.addInitScript(()=>localStorage.setItem('geoai:analysis-guided:793',JSON.stringify({family:'structure',step:'results',mode:'loads',caseName:''})));
 await page.goto('/projects/793/workspace');await page.getByRole('tab',{name:'Analysis',exact:true}).click({timeout:120000});
 const panel=page.getByRole('region',{name:'Guided Analysis',exact:true});await expect(panel.getByLabel('Guided visual results')).toBeVisible({timeout:90000});
 await expect(panel.getByLabel('Current analysis context')).toContainText('Numerically verified');
 const before=histories;await panel.getByRole('button',{name:'Bending / shear / axial',exact:true}).click();await page.waitForTimeout(500);expect(histories).toBe(before);
 await expect(panel.getByRole('link',{name:'Diagnostics for this saved model'})).toHaveAttribute('href','/diagnostics?project_id=793&model_revision_id=103');
 await page.screenshot({path:evidence+'normal-results-1600.png'});expect(writes).toEqual([]);
 writeFileSync(evidence+'workspace-smoke.json',JSON.stringify({project:793,revision:103,histories_before_mode:before,histories_after_mode:histories,writes},null,2));
});
