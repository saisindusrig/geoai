import {test,expect as pwExpect} from '@playwright/test';
const expect=pwExpect.configure({timeout:30000});
test.use({trace:'off'});
for(const project of [793,794,788])for(const width of [1280,1600])test(`workspace ${project} ${width}`,async({page})=>{
 test.setTimeout(120000);await page.setViewportSize({width,height:900});await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto(`/projects/${project}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:60000});await page.waitForTimeout(1200);const phase=process.env.GEOAI_SCREENSHOT_PHASE??'after';await page.screenshot({path:`../docs/workspace-quality/screenshots/${phase}-${project}-${width}.png`});
 if(phase==='before')return;
 await page.getByRole('tab',{name:'Layers',exact:true}).click();await page.getByLabel('Search scene components',{exact:true}).fill(project===788?'column':'CAD column SW');const row=page.locator('[id^="layer-row-"] button[aria-pressed]').first();await row.click();await expect(row).toHaveAttribute('aria-pressed','true');await page.getByRole('button',{name:'Fit selection',exact:true}).click();await page.waitForTimeout(500);await page.screenshot({path:`../docs/workspace-quality/screenshots/selected-${project}-${width}.png`});await page.getByRole('button',{name:'Focus Structure',exact:true}).click();await page.waitForTimeout(500);expect(await page.locator('body').evaluate(e=>e.scrollWidth<=window.innerWidth)).toBeTruthy();
});
