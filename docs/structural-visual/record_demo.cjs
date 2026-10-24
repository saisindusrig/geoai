// Real browser capture. Original and isolated services are read-only here.
const {chromium}=require('../../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1600,height:1000},recordVideo:{dir:path.join(__dirname,'recording'),size:{width:1600,height:1000}}}),page=await context.newPage(),errors=[],writes=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request();if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+r.url().split('?')[0]);return route.abort('blockedbyclient');}if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
 const open=async(project,port=3001)=>{await page.goto(`http://localhost:${port}/projects/${project}/workspace`);await page.locator('canvas[data-sandbox-ready="true"]').waitFor({timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();};
 const panel=page.getByRole('region',{name:'Structural visual engineering'}),mode=async(name)=>{await panel.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(1400);};
 await open(793);await panel.locator('button').first().waitFor();await mode('Structural load paths');await mode('Applied loads and reactions');await mode('Deformed versus original');await panel.getByLabel('Displacement magnification').fill('500');await page.waitForTimeout(1400);await panel.getByLabel('Structural saved load case').selectOption('Horizontal');await page.waitForTimeout(1400);await panel.getByLabel('Show original structure').uncheck();await page.waitForTimeout(1000);await panel.getByLabel('Show original structure').check();await mode('Beam and column forces');await panel.getByLabel('Structural force diagram').selectOption('shear');await page.waitForTimeout(1200);await panel.getByLabel('Structural force diagram').selectOption('axial');await page.waitForTimeout(1200);await mode('Warnings and connections');await panel.getByRole('button',{name:'Restore full structure',exact:true}).click();await page.waitForTimeout(600);
 await open(794);await mode('Structural load paths');await mode('Slab-to-beam distribution');await page.screenshot({path:path.join(__dirname,'demo-slab-1600.png')});await mode('Applied loads and reactions');
 const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'../foundation-visual/demo.json'),'utf8'));
 await open(fixture.study.project_id,13001);await page.getByText('Whole-structure evidence and unsupported transfers',{exact:true}).click();await mode('Foundation and soil response');await page.screenshot({path:path.join(__dirname,'demo-foundation-1600.png')});await page.waitForTimeout(1600);
 const video=page.video();await context.close();await video.saveAs(path.join(__dirname,'structural-walkthrough.webm'));await browser.close();
 fs.writeFileSync(path.join(__dirname,'demonstration.json'),JSON.stringify({projects:[793,794,fixture.study.project_id],viewport:[1600,1000],write_requests:writes,page_errors:errors,real_browser_recording:true},null,2));
 if(errors.length||writes.length)throw new Error(JSON.stringify({errors,writes}));
 console.log('Recorded real read-only structural walkthrough.');
})().catch(e=>{console.error(e);process.exit(1);});
