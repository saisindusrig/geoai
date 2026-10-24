const {chromium}=require('../../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1600,height:1000},recordVideo:{dir:path.join(__dirname,'recording'),size:{width:1600,height:1000}}}),page=await context.newPage(),errors=[],writes=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
 const open=async(id,port=3001)=>{await page.goto(`http://localhost:${port}/projects/${id}/workspace`);await page.locator('canvas[data-sandbox-ready="true"]').waitFor({timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();};
 const panel=page.getByRole('region',{name:'Structural visual engineering'}),canvas=page.locator('.cesium-widget canvas'),mode=async name=>{await panel.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(1000);};
 await open(793);await mode('Structural load paths');await mode('Applied loads and reactions');await mode('Deformed versus original');await panel.getByLabel('Displacement magnification').fill('200');await page.waitForTimeout(1000);await mode('Beam and column forces');
 for(const force of ['moment','shear','axial']){await panel.getByLabel('Structural force diagram').selectOption(force);await page.waitForTimeout(1400);}
 const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]'),pick=labels.find(p=>p.x>100&&p.x<1000&&p.y>150&&p.y<800);if(pick){const b=await canvas.boundingBox();await page.mouse.click(b.x+pick.x,b.y+pick.y);await page.waitForTimeout(1200);}
 await mode('Warnings and connections');await mode('Slab-to-beam distribution');await mode('Foundation and soil response');
 await open(794);await mode('Slab-to-beam distribution');await mode('Structural load paths');
 const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'../foundation-visual/demo.json'),'utf8'));await open(fixture.study.project_id,13001);await page.getByText('Whole-structure evidence and unsupported transfers',{exact:true}).click();await mode('Foundation and soil response');
 const video=page.video();await context.close();await video.saveAs(path.join(__dirname,'visual-polish-demo.webm'));await browser.close();fs.writeFileSync(path.join(__dirname,'demonstration.json'),JSON.stringify({real_browser_recording:true,viewport:[1600,1000],errors,writes},null,2));if(errors.length||writes.length)throw new Error(JSON.stringify({errors,writes}));console.log('Polished visual demonstration recorded.');
})().catch(e=>{console.error(e);process.exit(1);});
