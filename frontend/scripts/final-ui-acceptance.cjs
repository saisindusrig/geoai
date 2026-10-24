/* Read-only acceptance sweep. All application API requests are intercepted. */
const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const out = path.resolve('../docs/ui-audit');
const base = process.env.FINAL_BASE_URL || 'http://localhost:3001';
const widths = (process.env.FINAL_WIDTHS || '390,768,1024,1280,1440,1920').split(',').map(Number);
const loaded=process.env.FINAL_STATE==='loaded';
const fixtures=require('./final-acceptance-fixtures.cjs');
const suffix=loaded?'loaded':'errors';
const routes = ['/', '/login','/privacy','/dashboard','/settings','/settings/api-keys','/admin/rates','/admin/templates','/admin/usage','/admin/audit','/projects/999998/cost','/projects/999998/timeline','/projects/999998/report'];
const project = {id:999998,name:'Acceptance fixture — '+ 'Long project name '.repeat(12),project_type:'building',status:'draft',units:'metric',location_name:'Synthetic site',center_lat:null,center_lng:null,boundary_geojson:null,alignment_geojson:null,folder_id:null,created_at:'2026-10-22T00:00:00Z',updated_at:'2026-10-22T00:00:00Z',disclaimer:'Synthetic acceptance fixture; no engineering approval'};
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots/final'),{recursive:true});
 const browser = await chromium.launch({headless:true});
 const results=[];
 try {
 for(const width of widths){
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  await context.route('**/*',async route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.pathname.includes('/api/')){
    const p=url.pathname; let data={}; let status=200;
    if(req.method()!=='GET'){status=409;data={detail:'Read-only acceptance fixture'};}
    else if(p.endsWith('/projects'))data=Array.from({length:150},(_,i)=>({...project,id:999998+i}));
    else if(p.endsWith('/project-folders'))data=[];
    else if(p.endsWith('/auth/me'))data={id:999998,name:'Acceptance user',email:'fixture@example.invalid',role:'admin'};
    else if(/\/projects\/999998$/.test(p))data=project;
    else if(p.endsWith('/scenarios'))data={scenarios:[]};
    else if(p.endsWith('/rates')||p.endsWith('/templates'))data=[];
    else if(p.includes('/admin/usage')||p.includes('/admin/audit'))data={items:[],total:0,limit:100,offset:0};
    else {status=503;data={detail:'Acceptance fixture: unavailable evidence'};}
    if(loaded&&req.method()==='GET'){
     if(/\/projects\/999998$/.test(p)){status=200;data=fixtures.project;}
     else if(p.endsWith('/scenarios')){status=200;data=fixtures.scenarios;}
     else if(p.endsWith('/exports/files')){status=200;data=[];}
     else if(p.endsWith('/estimates')){status=200;data=fixtures.estimate;}
     else if(p.endsWith('/site-analysis')||p.endsWith('/survey/status')){status=404;data={detail:'Not available'};}
     else if(p.endsWith('/rates')){status=200;data=Array.from({length:100},(_,i)=>({id:i+1,item_code:'FIX-'+i,item_name:'Synthetic long rate name '.repeat(7),unit:'m3',rate:2,currency:'INR'}));}
     else if(p.includes('/admin/usage')||p.includes('/admin/audit')){status=200;data={entries:Array.from({length:100},(_,i)=>({id:i,user_id:1,project_id:999998,event_type:'fixture_read',action:'fixture.read',entity_type:'project',entity_id:999998,units:0,metadata:{note:'Long fixture metadata '.repeat(20)},created_at:fixtures.project.created_at})),total:250,limit:100,offset:Number(url.searchParams.get('offset')||0)};}
    }
    return route.fulfill({status,json:data});
   }
   if(url.origin!==base && !url.hostname.match(/^(localhost|127\.0\.0\.1)$/))return route.abort();
   return route.continue();
  });
  for(const route of [...routes,...(width<1280||loaded?['workspace','map','model','analysis','estimate','scenarios'].map(x=>'/projects/999998/'+x):[])]){
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   try{
    await page.addInitScript(()=>{window.__metrics={lcp:null,cls:0,longTasks:[],events:[]}; for(const type of ['largest-contentful-paint','layout-shift','longtask','event'])try{new PerformanceObserver(list=>{for(const e of list.getEntries()){if(type==='largest-contentful-paint')window.__metrics.lcp=e.startTime;if(type==='layout-shift'&&!e.hadRecentInput)window.__metrics.cls+=e.value;if(type==='longtask')window.__metrics.longTasks.push(e.duration);if(type==='event'&&e.interactionId)window.__metrics.events.push(e.duration);}}).observe({type,buffered:true,...(type==='event'?{durationThreshold:16}:{})});}catch{}});
    await page.goto(base+route,{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForTimeout(1600);
    await page.addScriptTag({path:require.resolve('axe-core')});
    const axe=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary})).slice(0,12)})),incomplete:r.incomplete.map(v=>v.id)};});
    const dom=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,main:document.querySelectorAll('main').length,canvas:document.querySelectorAll('canvas').length,desktopRequired:document.body.innerText.includes('Desktop Required'),metrics:window.__metrics,jsBytes:performance.getEntriesByType('resource').filter(x=>x.initiatorType==='script').reduce((n,x)=>n+x.encodedBodySize,0),heap:performance.memory?.usedJSHeapSize,overflow:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+2&&getComputedStyle(e).position!=='absolute';}).slice(0,8).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent?.slice(0,60)}))}));
    const row={route,width,...dom,axe,errors};results.push(row);
    if(width===390||width===1440)await page.screenshot({path:path.join(out,'screenshots/final',`${suffix}-${route.replace(/\W+/g,'_')||'home'}-${width}.png`),fullPage:true});
    console.log(JSON.stringify({route,width,violations:axe.violations.map(v=>v.id),errors,canvas:dom.canvas}));
   }catch(e){results.push({route,width,error:String(e)});console.log(route,width,String(e));}
   await page.close();fs.writeFileSync(path.join(out,`final-browser-${suffix}.json`),JSON.stringify(results,null,2));
  }
  await context.close();
 }
 } finally {await browser.close();}
})();
