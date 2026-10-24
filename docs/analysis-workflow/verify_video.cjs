const {chromium}=require('../../frontend/node_modules/playwright');
const {pathToFileURL}=require('node:url'),path=require('node:path'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}});
 await page.goto(pathToFileURL(path.join(__dirname,'guided-analysis-walkthrough.webm')).href);await page.waitForFunction(()=>document.querySelector('video')?.readyState>=1);
 let metadata=await page.evaluate(()=>{const v=document.querySelector('video');v.pause();return {duration_seconds:v.duration,width:v.videoWidth,height:v.videoHeight};});
 if(!Number.isFinite(metadata.duration_seconds)){await page.evaluate(()=>{document.querySelector('video').currentTime=1e6;});await page.waitForFunction(()=>Number.isFinite(document.querySelector('video').duration));metadata=await page.evaluate(()=>{const v=document.querySelector('video');return {duration_seconds:v.duration,width:v.videoWidth,height:v.videoHeight};});}
 await page.evaluate(t=>{document.querySelector('video').currentTime=t;},metadata.duration_seconds*.45);await page.waitForTimeout(500);await page.screenshot({path:path.join(__dirname,'walkthrough-frame.png')});
 fs.writeFileSync(path.join(__dirname,'video-metadata.json'),JSON.stringify(metadata,null,2));console.log(JSON.stringify(metadata));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});


