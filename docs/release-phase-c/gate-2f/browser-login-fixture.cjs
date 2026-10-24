// Isolated build with SDK aliases only. These are NOT real Google/Firebase tests.
const {chromium}=require('../../../frontend/node_modules/@playwright/test');
const assert=require('node:assert/strict'),fs=require('node:fs');
const origin='http://127.0.0.1:3017';
const config={mode:'firebase',password_login_allowed:false,registration_allowed:false,firebase_project_id:'synthetic-auth-project',firebase:{enabled:true,ready:true,code:'OFFLINE_SDK_FIXTURE',message:'Offline synthetic fixture only'}};
(async()=>{const browser=await chromium.launch({channel:'chrome',ignoreDefaultArgs:['--no-sandbox','--enable-unsafe-swiftshader']});const evidence=[];
try{for(const width of [1280,1600,390]){const page=await browser.newPage({viewport:{width,height:900},serviceWorkers:'block',reducedMotion:'reduce'});page.setDefaultTimeout(15000);const errors=[],external=[],writes=[],downloads=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));page.on('download',d=>downloads.push(d.suggestedFilename()));
await page.route('**/*',async route=>{const request=route.request(),url=new URL(request.url());
 if(url.origin!==origin){external.push(url.origin);return route.abort();}
 if(!['GET','HEAD'].includes(request.method())){writes.push(url.pathname);return route.abort();}
 const path=url.pathname.replace(/^\/local-api/,'');
 if(path==='/api/auth/config')return route.fulfill({json:config});
 if(path==='/api/auth/me'){const token=request.headers().authorization;
   if(token==='Bearer offline-firebase-id-unlinked')return route.fulfill({status:403,json:{detail:'Synthetic unlinked identity'}});
   if(!['Bearer offline-firebase-id-google','Bearer offline-firebase-id-password'].includes(token))return route.fulfill({status:401,json:{detail:'Synthetic rejected ID token'}});
   return route.fulfill({json:{id:42,role:'user',name:'Synthetic approved account',email:'synthetic@example.test'}});}
 if(path.startsWith('/api/'))return route.fulfill({status:503,json:{detail:'Not part of offline login fixture'}});
 if(url.pathname.startsWith('/_next/')||url.pathname.startsWith('/fonts/')||url.pathname.startsWith('/brand/')||['/login','/icon.svg','/favicon.ico'].includes(url.pathname))return route.continue();
 return route.abort();
});
await page.goto(origin+'/login?next=/login');await page.getByRole('button',{name:'Continue with Google',exact:true}).waitFor();
await page.waitForFunction(()=>getComputedStyle(document.querySelector('.auth-form-panel')).opacity==='1');
await page.evaluate(()=>{const label=document.createElement('div');label.textContent='OFFLINE SDK FIXTURE — no Google/Firebase connection';label.style.cssText='position:fixed;bottom:0;left:0;right:0;background:#161b15;color:#fff;padding:8px;text-align:center;font:12px sans-serif;z-index:9999';document.body.append(label);});
assert.equal(await page.getByRole('button',{name:'Register',exact:true}).count(),0);
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
await page.screenshot({path:`docs/release-phase-c/gate-2f/dual-provider-offline-${width}.png`});
for(const [outcome,text] of [['cancel','canceled'],['blocked','popup was blocked'],['collision','account linking'],['signup','public registration'],['unlinked','Access denied']]){
 await page.evaluate(value=>{window.__fixtureOutcome=value;},outcome);
 await page.getByRole('button',{name:'Continue with Google',exact:true}).click();
 await page.getByRole('alert').filter({hasText:text}).waitFor();
 assert.equal(new URL(page.url()).pathname,'/login');assert.equal(await page.getByText('SENSITIVE_MOCK_DETAIL').count(),0);
 checks.push({outcome,rejected:true});
}
await page.screenshot({path:`docs/release-phase-c/gate-2f/access-denied-offline-${width}.png`});
await page.evaluate(()=>{window.__fixtureOutcome='valid';});
const googleAuthorized=page.waitForResponse(response=>response.url().endsWith('/api/auth/me')&&response.status()===200);
await page.getByRole('button',{name:'Continue with Google',exact:true}).click();
await googleAuthorized;await page.waitForURL(origin+'/login');
await page.goto(origin+'/login?next=/login');
await page.getByRole('button',{name:'Continue with Google',exact:true}).waitFor();
await page.getByLabel('Email',{exact:true}).fill('synthetic@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password');
const passwordAuthorized=page.waitForResponse(response=>response.url().endsWith('/api/auth/me')&&response.status()===200);
await page.getByRole('button',{name:'Sign in',exact:true}).click();await passwordAuthorized;
await page.getByRole('button',{name:'Sign in',exact:true}).waitFor();
const persistent=await page.evaluate(()=>Object.keys(localStorage).filter(k=>/token|firebase.*auth/i.test(k)));
assert.deepEqual(persistent,[]);assert.deepEqual(errors,[]);assert.deepEqual(external,[]);assert.deepEqual(writes,[]);assert.deepEqual(downloads,[]);
evidence.push({width,checks,bothProviders:true,registrationHidden:true,persistentTokens:persistent,errors,external,writes,downloads,realFirebase:false});
fs.writeFileSync('docs/release-phase-c/gate-2f/browser-login-fixture.json',JSON.stringify(evidence,null,2));await page.close();}
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
