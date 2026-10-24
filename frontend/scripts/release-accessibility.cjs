const {chromium,request,expect}=require('@playwright/test'),fs=require('fs'),path=require('path');
const out=path.resolve('../docs/release'),WEB='http://localhost:3002',API='http://127.0.0.1:8022';
(async()=>{
 const auth=await request.newContext({baseURL:API});const token=(await(await auth.post('/api/auth/login',{data:{email:'release1001@example.invalid',password:'Disposable-fixture-2026'}})).json()).access_token;
 const pid=JSON.parse(fs.readFileSync(path.join(out,'fullstack-results.json'))).projectId;
 const extension=path.resolve('scripts/zoom-fixture-extension');
 const ctx=await chromium.launchPersistentContext(path.join(out,'a11y-test-profile'),{channel:'chromium',headless:true,viewport:{width:1440,height:900},args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
 await ctx.addInitScript(token=>localStorage.setItem('geoai_access_token',token),token);
 await ctx.route('**/*',r=>[WEB,API].includes(new URL(r.request().url()).origin)?r.continue():r.abort());
 const results=[];const page=ctx.pages()[0]||await ctx.newPage();
 for(const width of [390,1280,1440,1920])for(const route of ['/login','/dashboard',`/projects/${pid}/workspace`,`/projects/${pid}/report`]){
  await page.setViewportSize({width,height:900});await page.goto(WEB+route);await page.waitForTimeout(1000);await page.addScriptTag({path:require.resolve('axe-core')});
  const axe=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return{violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(x=>x.id)}});
  results.push({route,width,axe,canvas:await page.locator('canvas').count()});console.log(route,width,axe.violations.map(x=>x.id));
  if(route.endsWith('workspace'))await page.screenshot({path:path.join(out,`screenshots/a11y-workspace-${width}.png`)});
 }
 const worker=ctx.serviceWorkers()[0]||await ctx.waitForEvent('serviceworker');const zoom=[];
 await page.setViewportSize({width:1440,height:900});
 for(const route of ['/login','/dashboard',`/projects/${pid}/report`,`/projects/${pid}/workspace`]){
  await page.goto(WEB+route);await worker.evaluate(async()=>{const tabs=await chrome.tabs.query({url:'http://localhost:3002/*'});await chrome.tabs.setZoom(tabs[0].id,2)});await page.waitForTimeout(400);const actual=await worker.evaluate(async()=>{const tabs=await chrome.tabs.query({url:'http://localhost:3002/*'});return chrome.tabs.getZoom(tabs[0].id)});const state=await page.evaluate(()=>({width:innerWidth,desktopRequired:document.body.innerText.includes('Desktop Required')}));expect(actual).toBe(2);expect(state.width).toBe(720);zoom.push({route,actual,...state});await page.screenshot({path:path.join(out,`screenshots/zoom-${route.replace(/\W+/g,'_')}.png`)})
 }
 await worker.evaluate(async()=>{const tabs=await chrome.tabs.query({url:'http://localhost:3002/*'});await chrome.tabs.setZoom(tabs[0].id,1)});
 await page.emulateMedia({forcedColors:'active',reducedMotion:'reduce'});await page.goto(`${WEB}/projects/${pid}/workspace`);const group=page.getByRole('group',{name:'Camera orientation gizmo'});await group.getByRole('button',{name:'Positive Z axis view'}).focus();const focus=await group.getByRole('button',{name:'Positive Z axis view'}).evaluate(e=>({outline:getComputedStyle(e).outlineStyle,focused:document.activeElement===e,forced:matchMedia('(forced-colors: active)').matches,reduced:matchMedia('(prefers-reduced-motion: reduce)').matches}));expect(focus.outline).not.toBe('none');expect(focus.focused).toBe(true);await page.screenshot({path:path.join(out,'screenshots/forced-colors-gizmo.png')});
 await page.emulateMedia({forcedColors:'none'});
 const f=require('./final-acceptance-fixtures.cjs');await ctx.route('**/api/projects',r=>r.request().method()==='GET'?r.fulfill({json:Array.from({length:150},(_,i)=>({...f.project,id:100000+i,name:'Large library fixture '+i}))}):r.continue());await page.goto(WEB+'/dashboard');await page.getByRole('button',{name:'Projects',exact:true}).click();await page.waitForTimeout(1000);const before=await page.evaluate(()=>({canvas:document.querySelectorAll('canvas').length,heap:performance.memory?.usedJSHeapSize}));for(let i=0;i<8;i++){await page.locator('.hub-main').evaluate((e,i)=>e.scrollTop=i*800,i);await page.locator('.hub-all-concepts').evaluate((e,i)=>e.scrollTop=i*800,i);await page.waitForTimeout(200)}const after=await page.evaluate(()=>({canvas:document.querySelectorAll('canvas').length,heap:performance.memory?.usedJSHeapSize}));
 fs.writeFileSync(path.join(out,'accessibility-results.json'),JSON.stringify({results,zoom,focus,library:{before,after}},null,2));console.log(JSON.stringify({states:results.length,violations:results.reduce((s,x)=>s+x.axe.violations.length,0),zoom:zoom.length,library:{before,after}}));await ctx.close();await auth.dispose();
})().catch(e=>{console.error(e);process.exitCode=1});

