// Read-only replay of the acceptance project's saved evidence. No solver call.
const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const out=path.resolve(__dirname,'../../docs/production-beta');
(async()=>{
  const journey=JSON.parse(fs.readFileSync(path.join(out,'journey.json'),'utf8'));
  const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const context=await browser.newContext({viewport:{width:1600,height:900},recordVideo:{dir:path.join(out,'walkthrough-capture'),size:{width:1280,height:720}}});
  const page=await context.newPage();page.setDefaultTimeout(30000);
  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto(`http://localhost:3001/projects/${journey.projectId}/workspace`);
  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  for(const label of ['Advanced analysis · inputs, tools and evidence','Analysis tasks and saved results','Frame analysis and saved results'])await page.getByText(label,{exact:true}).click();
  const results=page.getByLabel('Computed saved frame results');
  await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  await page.waitForTimeout(2500);
  for(const name of ['Displacement','Axial Force','Shear','Bending Moment','Reactions']){
    await results.getByRole('tab',{name,exact:true}).click();
    await results.scrollIntoViewIfNeeded();await page.waitForTimeout(2600);
  }
  await results.getByRole('button',{name:/Support 1/}).click();
  await expect(results.getByLabel('Selected member solver inspection')).toContainText('column-sw');
  await results.getByRole('tab',{name:'Bending Moment',exact:true}).click();
  await results.getByRole('button',{name:'Fit Analysis',exact:true}).click();
  await results.scrollIntoViewIfNeeded();await page.waitForTimeout(2500);
  await page.screenshot({path:path.join(out,'walkthrough-overview.png')});
  await page.getByRole('tab',{name:'History',exact:true}).click();await page.waitForTimeout(2500);
  await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();await page.waitForTimeout(2500);
  const video=page.video();await context.close();
  fs.copyFileSync(await video.path(),path.join(out,'walkthrough.webm'));
  const verify=await browser.newPage();
  await verify.goto(require('node:url').pathToFileURL(path.join(out,'walkthrough.webm')).href);
  await verify.locator('video').waitFor();
  await verify.waitForFunction(()=>document.querySelector('video')?.readyState>=1);
  const metadata={projectId:journey.projectId,analysisId:journey.analysisId,
    ...await verify.locator('video').evaluate(v=>({duration_seconds:v.duration,width:v.videoWidth,height:v.videoHeight,readyState:v.readyState}))};
  fs.writeFileSync(path.join(out,'walkthrough-metadata.json'),JSON.stringify(metadata,null,2));
  console.log(JSON.stringify(metadata));await browser.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
