// Read-only normal website check. All modifying browser requests are blocked.
const {chromium}=require('../../frontend/node_modules/playwright');
const {writeFileSync}=require('node:fs');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});
 const writes=[],errors=[];
 await page.route('**/*',async route=>{
  const r=route.request();
  if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push({method:r.method(),url:r.url().split('?')[0]});return route.abort('blockedbyclient');}
  if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  return route.continue();
 });
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:3001/projects/804/workspace');
 await page.locator('.cesium-widget canvas[data-sandbox-ready="true"]').waitFor({timeout:90000});
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();
 await page.getByRole('button',{name:'Create separate foundation study from 804'}).waitFor({timeout:30000});
 await page.screenshot({path:path.join(__dirname,'normal-website-3001.png')});
 writeFileSync(path.join(__dirname,'normal-website.json'),JSON.stringify({url:page.url(),canvas_ready:true,foundation_module_available:true,write_requests_blocked:writes,page_errors:errors},null,2));
 await browser.close();
 if(errors.length)throw new Error(JSON.stringify(errors));
 console.log('Normal localhost:3001 read-only smoke passed');
})().catch(e=>{console.error(e);process.exitCode=1});
