import {test,expect} from '@playwright/test';
test.use({trace:'off'});
for(const project of [793,794,788])for(const width of [1280,1600])test(`visualization ${project} ${width}`,async({page})=>{
 test.setTimeout(120000);await page.setViewportSize({width,height:900});await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto(`/projects/${project}/workspace`);await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:60000});await page.waitForTimeout(1200);
 const phase=process.env.GEOAI_SCREENSHOT_PHASE??'after';const shot=async(name:string)=>{await page.waitForTimeout(650);await page.screenshot({path:`../docs/model-visualization/screenshots/${phase}-${project}-${width}-${name}.png`});};await shot('default');
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('geoai:orient-view',{detail:{heading:25,pitch:-30}})));await shot('isometric');
 if(phase==='before')return;
 await page.getByRole('button',{name:'Fit All',exact:true}).click();await shot('all');await page.getByRole('button',{name:'Focus Structure',exact:true}).click();await shot('focus');
 for(const name of ['Front','Side','Top','Isometric']){await page.getByText('Standard views',{exact:true}).click();await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(500);}
 await page.getByRole('tab',{name:'Layers',exact:true}).click();await page.getByLabel('Search scene components',{exact:true}).fill(project===788?'column':'CAD column SW');const row=page.locator('[id^="layer-row-"] button[aria-pressed]').first();await row.click();await expect(row).toHaveAttribute('aria-pressed','true');await page.getByRole('button',{name:'Fit selection',exact:true}).click();await shot('closeup');
 const rect=await page.locator('.cesium-widget canvas').boundingBox();let hovered=false;
 if(rect)for(const fy of [.55,.4,.7,.25]){for(const fx of [.5,.4,.6,.3,.7]){await page.mouse.move(rect.x+rect.width*fx,rect.y+rect.height*fy);await page.waitForTimeout(80);if(await page.getByText(/ · click to select$/).isVisible()){hovered=true;await page.mouse.click(rect.x+rect.width*fx,rect.y+rect.height*fy);break;}}if(hovered)break;}
 expect(hovered).toBeTruthy();await page.mouse.move(0,0);
 await page.getByLabel('Search scene components',{exact:true}).fill('stair');const stair=page.locator('[id^="layer-row-"] button[aria-pressed]').first();await stair.click();await expect(stair).toHaveAttribute('aria-pressed','true');await page.getByRole('button',{name:'Fit selection',exact:true}).click();await shot('stair-closeup');expect(await page.locator('body').evaluate(e=>e.scrollWidth<=window.innerWidth)).toBeTruthy();
});
