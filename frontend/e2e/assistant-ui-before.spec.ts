import { test, expect } from "@playwright/test";
const fixture = { id:"ui-recorded-shape", request:{ message:"Where can I inspect saved analysis results?", project_id:805, revision_id:null, selected_ids:[],dirty:false,page:"/projects/805/workspace",model:"zai-org/GLM-5.3-Flash" }, status:"SUCCEEDED",model:"zai-org/GLM-5.3-Flash", reply:"Open **Analyze / Results** to inspect saved evidence.\n\n- Choose a saved result.\n- Check its current or stale label.\n\nOpening results does **not** start a calculation.",events:[] };
fixture.events = [];
for (const width of [1280,1600]) test(`before assistant UI ${width}`, async ({page})=>{
 await page.setViewportSize({width,height:900});
 await page.route("**/*",async route=>{
  const r=route.request(),u=new URL(r.url());
  if(!["localhost","127.0.0.1"].includes(u.hostname))return route.abort();
  if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:[{...fixture,events:[{type:"delta",text:fixture.reply}]}]}});
  if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:false,state:"RATE_LIMITED",code:"DAILY_REQUEST_LIMIT",message:"Approved live-test limit reached: 3 of 3 turns used. No additional inference is approved.",requestAllowance:3,usage:{daily_requests:3,accounted_daily_tokens:14487,accounted_usd:.0024219},dailyTokenAllowance:200000}});
  if(!['GET','HEAD','OPTIONS'].includes(r.method()))return route.abort();
  return route.continue();
 });
 await page.goto('/projects/805/workspace');
 await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
 await page.getByRole('button',{name:'StruvoCivil Assistant',exact:true}).click();
 await expect(page.getByRole('complementary',{name:'StruvoCivil Assistant'})).toContainText('Analyze / Results');
 await page.screenshot({path:`../docs/assistant-ui/before-${width}.png`});
});
