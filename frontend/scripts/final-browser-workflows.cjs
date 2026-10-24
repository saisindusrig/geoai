const { chromium, expect }=require('@playwright/test');
const fs=require('node:fs');const path=require('node:path');
const fixture=require('./final-acceptance-fixtures.cjs');
const out=path.resolve('../docs/ui-audit');
const checks=[];
(async()=>{
 const browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true,reducedMotion:'reduce'});
 let createAttempts=0,saveAttempts=0,projectList=[fixture.project];const calls=[];
 await ctx.route('**/*',async r=>{
  const req=r.request(),u=new URL(req.url()),p=u.pathname;
  if(p.includes('/api/')){
   calls.push({method:req.method(),path:p,query:u.search});
   if(p.endsWith('/projects')&&req.method()==='POST'){
    createAttempts++;await new Promise(ok=>setTimeout(ok,200));
    return r.fulfill(createAttempts===1?{status:503,json:{detail:'Fixture offline'}}:{status:201,json:{...fixture.project,name:req.postDataJSON().name}});
   }
   if(p.endsWith('/assumptions')&&req.method()==='PUT'){
    saveAttempts++;await new Promise(ok=>setTimeout(ok,200));
    return r.fulfill(saveAttempts===1?{status:503,json:{detail:'Fixture save failed'}}:{json:{ok:true}});
   }
   if(req.method()!=='GET')return r.fulfill({status:409,json:{detail:'Fixture mutation blocked'}});
   let data;
   if(p.endsWith('/projects'))data=projectList;
   else if(p.endsWith('/project-folders'))data=[];
   else if(/\/projects\/999998$/.test(p))data=fixture.project;
   else if(p.endsWith('/scenarios'))data=fixture.scenarios;
   else if(p.endsWith('/exports/files'))data=[];
   else if(p.endsWith('/estimates'))data=fixture.estimate;
   else if(p.includes('/admin/usage')||p.includes('/admin/audit'))data={entries:Array.from({length:100},(_,i)=>({id:i,action:'fixture.read',event_type:'fixture',units:0,user_id:1,project_id:999998,created_at:fixture.project.created_at})),total:250,limit:100,offset:Number(u.searchParams.get('offset')||0)};
   else if(p.endsWith('/exports/json'))return r.fulfill({contentType:'application/json',headers:{'content-disposition':'attachment; filename="fixture-project.json"'},body:JSON.stringify({project:fixture.project,disclaimer:fixture.project.disclaimer})});
   else return r.fulfill({status:404,json:{detail:'Fixture: unavailable'}});
   return r.fulfill({json:data});
  }
  if(u.origin!=='http://localhost:3001')return r.abort();
  return r.continue();
 });
 const page=await ctx.newPage();page.setDefaultTimeout(15000);
 await page.addInitScript(()=>{window.__interactions=[];try{new PerformanceObserver(l=>{for(const e of l.getEntries())if(e.interactionId)window.__interactions.push({duration:e.duration,name:e.name});}).observe({type:'event',buffered:true,durationThreshold:16});}catch{}});
 async function check(name,fn){try{const detail=await fn();checks.push({name,status:'PASS',detail});console.log('PASS',name);}catch(e){checks.push({name,status:'FAIL',error:String(e)});console.log('FAIL',name,String(e));}fs.writeFileSync(path.join(out,'final-workflow-browser.json'),JSON.stringify({checks,calls},null,2));}
 await check('project dialog keyboard trap, Escape and focus return',async()=>{
  await page.goto('http://localhost:3001/dashboard');const button=page.getByRole('button',{name:'New Project',exact:true});await button.click();
  const dialog=page.getByRole('dialog');await expect(page.getByLabel('Project name',{exact:true})).toBeFocused();
  await page.keyboard.press('Shift+Tab');await expect(dialog.getByRole('button',{name:'Cancel'})).toBeFocused();
  await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(button).toBeFocused();
 });
 await check('project create failure retains name; retry posts once and opens same project',async()=>{
  await page.setViewportSize({width:390,height:1000});await page.getByRole('button',{name:'New Project',exact:true}).click();await page.getByLabel('Project name',{exact:true}).fill('Disposable browser fixture');
  await page.getByRole('button',{name:'Create Project',exact:true}).click();await expect(page.getByRole('dialog').getByRole('alert')).toBeVisible();await expect(page.getByLabel('Project name',{exact:true})).toHaveValue('Disposable browser fixture');
  await page.getByRole('button',{name:'Create Project',exact:true}).click();await expect(page.getByRole('heading',{name:'Desktop Required',exact:true})).toBeVisible();expect(createAttempts).toBe(2);expect(await page.locator('canvas').count()).toBe(0);
  await page.getByRole('link',{name:'Back to Dashboard'}).click();await expect(page).toHaveURL(/returnTo=/);await expect(page.getByRole('link',{name:/Return to/})).toBeVisible();
 });
 await check('populated cost table scrolls by keyboard',async()=>{
  await page.goto('http://localhost:3001/projects/999998/cost');const region=page.getByRole('region',{name:'Cost line items'});await expect(region).toBeVisible();await region.focus();await page.keyboard.press('ArrowRight');await page.waitForTimeout(300);expect(await region.evaluate(e=>e.scrollLeft)).toBeGreaterThan(0);
 });
 await check('usage pagination reads offset=100 and preserves table',async()=>{
  await page.goto('http://localhost:3001/admin/usage');await page.getByRole('button',{name:'Next',exact:true}).click();await expect(page.getByText(/101.*200/)).toBeVisible();expect(calls.some(x=>x.path.endsWith('/admin/usage')&&x.query.includes('offset=100'))).toBe(true);
 });
 await check('mobile report is read-only; timeline download contains exact fixture',async()=>{
  await page.goto('http://localhost:3001/projects/999998/report');await expect(page.getByText('Report preview',{exact:true})).toBeVisible();expect(await page.getByRole('button',{name:'Edit',exact:true}).count()).toBe(0);
  await page.goto('http://localhost:3001/projects/999998/timeline');const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download Timeline',exact:true}).click();const download=await pending;expect(download.suggestedFilename()).toMatch(/-timeline\.json$/);const file=await download.path();const data=JSON.parse(fs.readFileSync(file,'utf8'));expect(data.construction_sequence).toEqual(fixture.design.construction_sequence);expect(data.timeline).toEqual(fixture.design.calculated.timeline);expect(data.disclaimer).toContain('not for construction approval');
  return {filename:download.suggestedFilename(),phases:data.construction_sequence.length};
 });
 await check('report export attachment has expected format, filename and fixture content',async()=>{
  await page.goto('http://localhost:3001/projects/999998/report');const pending=page.waitForEvent('download');await page.getByRole('link',{name:'Download Project Data (JSON)',exact:true}).click();const d=await pending;expect(d.suggestedFilename()).toBe('fixture-project.json');expect(JSON.parse(fs.readFileSync(await d.path(),'utf8')).project.id).toBe(999998);return {filename:d.suggestedFilename(),backend:'mocked'};
 });
 await check('desktop report save failure preserves draft and successful retry recovers',async()=>{
  await page.setViewportSize({width:1440,height:1000});await page.goto('http://localhost:3001/projects/999998/report');await page.getByRole('button',{name:'Edit',exact:true}).click();await page.getByLabel('Assumption 1',{exact:true}).fill('Draft retained');await page.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByRole('alert').filter({hasText:'Fixture save failed'})).toBeVisible();await expect(page.getByLabel('Assumption 1',{exact:true})).toHaveValue('Draft retained');await page.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByRole('button',{name:'Edit',exact:true})).toBeVisible();expect(saveAttempts).toBe(2);
 });
 await check('forced-colors and reduced-motion keyboard focus',async()=>{
  await page.emulateMedia({forcedColors:'active',reducedMotion:'reduce'});await page.goto('http://localhost:3001/login');await page.keyboard.press('Tab');const result=await page.evaluate(()=>({forced:matchMedia('(forced-colors: active)').matches,reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle}));expect(result.forced).toBe(true);expect(result.reduced).toBe(true);expect(result.outline).not.toBe('none');await page.screenshot({path:path.join(out,'screenshots/final/forced-colors-login.png')});return result;
 });
 await check('150-project library renderer and memory observation',async()=>{
  projectList=Array.from({length:150},(_,i)=>({...fixture.project,id:999998+i,name:'Fixture '+i}));await page.emulateMedia({forcedColors:'none'});await page.goto('http://localhost:3001/dashboard');await page.getByRole('button',{name:'Projects',exact:true}).click();await page.waitForTimeout(1500);
  const before=await page.evaluate(()=>({canvas:document.querySelectorAll('canvas').length,heap:performance.memory?.usedJSHeapSize}));
  for(let i=0;i<8;i++){await page.locator('.hub-main').evaluate((e,i)=>e.scrollTop=i*800,i);await page.locator('.hub-all-concepts').evaluate((e,i)=>e.scrollTop=i*800,i);await page.waitForTimeout(200);}
  const after=await page.evaluate(()=>({canvas:document.querySelectorAll('canvas').length,heap:performance.memory?.usedJSHeapSize}));return {before,after,interactions:await page.evaluate(()=>window.__interactions)};
 });
 await browser.close();console.log(JSON.stringify({passed:checks.filter(x=>x.status==='PASS').length,failed:checks.filter(x=>x.status==='FAIL').length}));
 process.exitCode=checks.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});

