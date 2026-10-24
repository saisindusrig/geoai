const {chromium}=require('../../frontend/node_modules/@playwright/test');
const fs=require('fs');
(async()=>{const b=await chromium.launch({channel:'chrome',args:['--use-angle=swiftshader']});const evidence=[];
for(const width of [1280,1600,390]){const p=await b.newPage({viewport:{width,height:900},reducedMotion:'reduce'});const errors=[];const mutations=[];p.on('pageerror',e=>errors.push(String(e)));await p.route('**/*',async r=>{const u=new URL(r.request().url());if(u.pathname.endsWith('/site-suggestions'))return r.fulfill({json:{suggestions:[]}});if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});if(!['GET','HEAD','OPTIONS'].includes(r.request().method())){mutations.push(u.pathname);return r.abort();}if(u.pathname.includes('/api/') && (p.url().includes('/projects/') || u.pathname.includes('/projects/'))) {const i=u.pathname.indexOf('/api/'); return r.fulfill({response:await r.fetch({url:'http://127.0.0.1:8003'+u.pathname.slice(i)+u.search})});}return r.continue();});
await p.goto('http://127.0.0.1:3001');await p.waitForTimeout(1800);
if(await p.title()!=='Struvo Civil — Structural Engineering Software')throw Error('title '+await p.title());
if(!await p.getByRole('heading',{level:1}).textContent().then(s=>s.replace(/\s+/g,'')==='Model.Analyze.Design.'))throw Error('tagline');
const canonical=await p.locator('link[rel=canonical]').getAttribute('href');if(new URL(canonical).href!=='https://struvocivil.com/')throw Error('canonical '+canonical);
await p.screenshot({path:`docs/milestone-9.1/after-home-${width}.png`});
const routes=width===390?['/dashboard']:['/dashboard','/settings','/diagnostics','/projects/991600/workspace'];const screens=[];
for(const route of routes){await p.goto('http://127.0.0.1:3001'+route);await p.waitForTimeout(2000);if(route.endsWith('workspace')){await p.waitForFunction(()=>document.querySelector('.cesium-widget canvas')?.getAttribute('data-sandbox-ready')==='true',null,{timeout:90000});await p.getByRole('button',{name:'Fit All',exact:true}).click();await p.waitForTimeout(1200);}
const text=await p.locator('body').innerText();const old=/\bGeoAI\b/i.test(text);screens.push({route,title:await p.title(),legacyVisible:old,horizontalOverflow:await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});if(old)throw Error('old brand '+route);
await p.screenshot({path:`docs/milestone-9.1/after-${route.split('/').pop()}-${width}.png`});}
if(width!==390){await p.getByRole('button',{name:'Struvo Assistant',exact:true}).click();await p.getByRole('complementary',{name:'Struvo Assistant'}).waitFor();await p.screenshot({path:`docs/milestone-9.1/after-assistant-${width}.png`});}
evidence.push({width,canonical,screens,errors,blockedMutations:mutations});await p.close();}
const p=await b.newPage();const manifest=await (await p.request.get('http://127.0.0.1:3001/manifest.webmanifest')).json();if(manifest.name!=='Struvo Civil')throw Error('manifest');evidence.push({manifest});fs.writeFileSync('docs/milestone-9.1/browser.json',JSON.stringify(evidence,null,2));await b.close();})().catch(e=>{console.error(e);process.exit(1)});



