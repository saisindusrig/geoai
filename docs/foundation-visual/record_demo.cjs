const {chromium}=require('../../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'demo.json'),'utf8'));
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1600,height:1000},recordVideo:{dir:path.join(__dirname,'recording'),size:{width:1600,height:1000}}});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
 await page.goto('http://localhost:13001/projects/'+fixture.study.project_id+'/workspace');
 await page.locator('canvas[data-sandbox-ready="true"]').waitFor({timeout:90000});
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();
 const visual=page.getByRole('article',{name:'Foundation visual analysis'});
 await visual.waitFor();
 const scenes=['Loads and reactions','Soil pressure and settlement','Bending moments','One-way shear','Punching shear','Reinforcement and anchorage'];
 for(const name of scenes){await visual.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(1500);}
 await visual.getByRole('button',{name:'Foundation alternatives',exact:true}).click();
 await visual.getByRole('button',{name:'Calculate validated comparisons'}).click();
 await visual.getByRole('button').filter({hasText:'1.50 m square × 0.54 m'}).click();await page.waitForTimeout(1800);
 await visual.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await page.waitForTimeout(1600);
 const video=page.video();await context.close();
 const target=path.join(__dirname,'foundation-visual-demo.webm');await video.saveAs(target);await browser.close();
 if(errors.length)throw new Error(JSON.stringify(errors));
 fs.writeFileSync(path.join(__dirname,'demonstration.json'),JSON.stringify({file:target,project_id:fixture.study.project_id,scenes:[...scenes,'Ghosted foundation alternative','Failed straight development'],saved_results_changed:false,page_errors:errors},null,2));
 console.log(target);
})().catch(e=>{console.error(e);process.exitCode=1});
