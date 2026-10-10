import { expect, test } from "@playwright/test";
const api=process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

for (const width of [1440,1920]) test(`boundary drawing, validation, retry and reversible editing at ${width}px`, async ({ page }) => {
  await page.setViewportSize({width,height:1000});
  const errors:string[]=[]; page.on("pageerror", e => errors.push(e.message));
  await page.route("**/api/geocode/map-runtime-config", r => r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  const created = await page.request.post(`${api}/api/projects`, {data:{name:`Boundary UX ${width} ${Date.now()}`,project_type:"building",center_lng:77,center_lat:12}});
  expect(created.ok(),`Create project HTTP ${created.status()}`).toBeTruthy();
  const project = await created.json();
  await page.goto(`/projects/${project.id}/workspace`);
  const canvas=page.locator(".cesium-widget canvas");
  const settled=async()=>{ await expect(canvas).toHaveAttribute("data-scene-camera",/.+/); await page.waitForTimeout(1200); };
  await settled();
  const drawing=page.getByLabel("Drawing tool options");
  const click=async(x:number,y:number) => { const b=(await canvas.boundingBox())!; await page.mouse.click(b.x+b.width*x,b.y+b.height*y); };
  await page.getByRole("button",{name:"Draw site boundary",exact:true}).click();
  await click(.45,.48); await click(.65,.48); await click(.65,.70); await click(.45,.70);
  await expect(drawing).toContainText("4 vertices");
  await drawing.getByRole("button",{name:"Undo vertex"}).click();
  await expect(drawing).toContainText("3 vertices");
  await page.screenshot({path:`test-results/boundary-drawing-${width}.png`});
  await drawing.getByRole("button",{name:"Finish drawing"}).click();
  const save=page.getByRole("button",{name:"Save boundary",exact:true});
  await expect(save).toBeVisible();
  await page.route(`**/api/projects/${project.id}`, async route => {
    if(route.request().method()==="PUT") { await route.fulfill({status:503,json:{detail:"Test save unavailable"}}); await page.unroute(`**/api/projects/${project.id}`); }
    else await route.continue();
  });
  await save.click();
  await expect(page.getByRole("alert").filter({hasText:"Your draft is retained"})).toBeVisible();
  await expect(save).toBeEnabled();
  const persisted=page.waitForResponse(r=>r.url().endsWith(`/api/projects/${project.id}`) && r.request().method()==="PUT" && r.ok());
  await save.click(); await persisted;
  await expect(save).toHaveCount(0);
  const readBoundary=async()=> (await (await page.request.get(`${api}/api/projects/${project.id}`)).json()).boundary_geojson;
  const original=await readBoundary(); expect(original.coordinates[0]).toHaveLength(4);
  await page.reload(); await settled();
  expect(await readBoundary()).toEqual(original);
  const edit=async()=>{
    await page.getByRole("button",{name:"Edit site boundary",exact:true}).click();
    await expect.poll(async()=>JSON.parse(await canvas.getAttribute("data-boundary-handles")||"[]").length).toBe(3);
    const p=JSON.parse((await canvas.getAttribute("data-boundary-handles"))!)[0], b=(await canvas.boundingBox())!;
    await page.mouse.move(b.x+p.x,b.y+p.y); await page.mouse.down();
    await page.mouse.move(b.x+p.x+35,b.y+p.y+25,{steps:8}); await page.mouse.up();
  };
  await edit(); await page.keyboard.press("Escape"); expect(await readBoundary()).toEqual(original);
  await edit(); await page.keyboard.press("Enter");
  await expect(save).toBeVisible();
  const edited=page.waitForResponse(r=>r.url().endsWith(`/api/projects/${project.id}`) && r.request().method()==="PUT" && r.ok());
  await save.click(); await edited; await expect(save).toHaveCount(0);
  const changed=await readBoundary(); expect(changed).not.toEqual(original);
  await page.reload(); await settled(); expect(await readBoundary()).toEqual(changed);
  await page.getByRole("button",{name:"Draw site boundary",exact:true}).click();
  await click(.45,.48); await click(.65,.70); await click(.45,.70); await click(.65,.48);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("alert").filter({hasText:"edges cross"})).toBeVisible();
  await expect(save).toHaveCount(0); await page.keyboard.press("Escape"); expect(await readBoundary()).toEqual(changed);
  // A double-click supplies one final vertex, rather than two near-identical vertices.
  await page.getByRole("button",{name:"Draw site boundary",exact:true}).click();
  await click(.45,.48); await click(.65,.48);
  const b=(await canvas.boundingBox())!; await page.mouse.dblclick(b.x+b.width*.65,b.y+b.height*.70);
  await expect(save).toBeVisible(); await page.getByRole("button",{name:"Discard draft"}).click();
  expect(await readBoundary()).toEqual(changed);
  await page.screenshot({path:`test-results/boundary-saved-${width}.png`});
  expect(errors).toEqual([]); await expect(page.locator(".cesium-widget-errorPanel")).toHaveCount(0);
});
