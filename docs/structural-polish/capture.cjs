const {chromium}=require('../../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const phase=process.argv[2]||'before',browser=await chromium.launch({headless:true}),errors=[],writes=[],modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']];
 for(const width of [1280,1600]){
 const context=await browser.newContext({viewport:{width,height:1000}}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async r=>{if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){writes.push(r.request().url());return r.abort();}if(r.request().url().includes('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return r.continue();});
 const open=async(id,port=3001)=>{await page.goto(`http://localhost:${port}/projects/${id}/workspace`);await page.locator('canvas[data-sandbox-ready="true"]').waitFor({timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();};
 await open(793);const panel=page.getByRole('region',{name:'Structural visual engineering'});
 for(const [key,name]of modes){await panel.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(900);if(key==='deformation')await panel.getByLabel('Displacement magnification').fill('200');await page.screenshot({path:path.join(__dirname,`${phase}-793-${key}-${width}.png`)});if(key==='forces')for(const force of ['shear','axial']){await panel.getByLabel('Structural force diagram').selectOption(force);await page.waitForTimeout(300);await page.screenshot({path:path.join(__dirname,`${phase}-793-${force}-${width}.png`)});}}
 await open(794);await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await page.waitForTimeout(900);await page.screenshot({path:path.join(__dirname,`${phase}-794-slab-${width}.png`)});
 const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'../foundation-visual/demo.json'),'utf8'));await open(fixture.study.project_id,13001);await page.getByText('Whole-structure evidence and unsupported transfers',{exact:true}).click();await panel.getByRole('button',{name:'Foundation and soil response',exact:true}).click();await page.waitForTimeout(900);await page.screenshot({path:path.join(__dirname,`${phase}-814-foundation-${width}.png`)});await context.close();
 }
 await browser.close();fs.writeFileSync(path.join(__dirname,`${phase}-capture.json`),JSON.stringify({widths:[1280,1600],modes:7,errors,writes},null,2));if(errors.length||writes.length)throw new Error(JSON.stringify({errors,writes}));
})().catch(e=>{console.error(e);process.exit(1);});
