const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');const path=require('node:path');
const fixture=require('./final-acceptance-fixtures.cjs');
const out=path.resolve('../docs/ui-audit');const ext=path.resolve('scripts/zoom-fixture-extension');
(async()=>{
 const ctx=await chromium.launchPersistentContext(path.join(out,'zoom-test-profile'),{channel:'chromium',headless:true,viewport:{width:1440,height:1000},args:[`--disable-extensions-except=${ext}`,`--load-extension=${ext}`]});
 try{
  const worker=ctx.serviceWorkers()[0]||await ctx.waitForEvent('serviceworker',{timeout:15000});
  const page=ctx.pages()[0]||await ctx.newPage();
  await ctx.route('**/*',r=>{
   const p=new URL(r.request().url()).pathname;
   if(!p.includes('/api/'))return r.continue();
   let data;
   if(p.endsWith('/projects'))data=Array.from({length:150},(_,i)=>({...fixture.project,id:999998+i}));
   else if(p.endsWith('/project-folders')||p.endsWith('/exports/files')||p.endsWith('/templates')||p.endsWith('/rates'))data=[];
   else if(/\/projects\/999998$/.test(p))data=fixture.project;
   else if(p.endsWith('/scenarios'))data=fixture.scenarios;
   else if(p.endsWith('/estimates'))data=fixture.estimate;
   else if(p.includes('/admin/usage')||p.includes('/admin/audit'))data={entries:[],total:0,limit:100,offset:0};
   else return r.fulfill({status:404,json:{detail:'Zoom fixture unavailable'}});
   return r.fulfill({json:data});
  });
  const results=[];
  for(const route of ['/','/login','/privacy','/dashboard','/settings','/settings/api-keys','/admin/rates','/admin/templates','/admin/usage','/admin/audit','/projects/999998/cost','/projects/999998/timeline','/projects/999998/report','/projects/999998/workspace']){
   await page.goto('http://localhost:3001'+route);await worker.evaluate(async()=>{const tabs=await chrome.tabs.query({url:'http://localhost:3001/*'});await chrome.tabs.setZoom(tabs[0].id,2);});await page.waitForTimeout(800);
   const zoom=await worker.evaluate(async()=>{const tabs=await chrome.tabs.query({url:'http://localhost:3001/*'});return chrome.tabs.getZoom(tabs[0].id);});
   const dom=await page.evaluate(()=>({width:innerWidth,dpr:devicePixelRatio,scrollWidth:document.documentElement.scrollWidth,desktopRequired:document.body.innerText.includes('Desktop Required'),canvas:document.querySelectorAll('canvas').length}));
   expect(zoom).toBe(2);expect(dom.width).toBe(720);results.push({route,zoom,...dom});
   if(route==='/login'||route.endsWith('/workspace'))await page.screenshot({path:path.join(out,'screenshots/final',`zoom200-${route.replace(/\W+/g,'_')}.png`)});
  }
  fs.writeFileSync(path.join(out,'final-zoom.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
 } finally {await ctx.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
