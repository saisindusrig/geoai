import {test, expect, type Page} from "@playwright/test";

test.skip(process.env.CAD_WORKSPACE_ACCEPTANCE !== "1", "Explicit isolated CAD workspace acceptance only");

async function observeEngine(page: Page) {
  // Observe the actual engine instance in this test only; no renderer mocks.
  await page.addInitScript(() => {
    let engine: unknown;
    Object.defineProperty(window,"Cesium",{configurable:true,get:()=>engine,set:(value)=>{
      const observedViewer = new Proxy(value.Viewer,{construct:(target,args)=>{
        const viewer = Reflect.construct(target,args) as object;
        (window as unknown as {cadAcceptanceViewer:unknown}).cadAcceptanceViewer = viewer;
        return viewer;
      }});
      const primitives = new Map();
      (window as unknown as {cadAcceptancePrimitives:unknown}).cadAcceptancePrimitives = primitives;
      const observedPrimitive = new Proxy(value.Primitive,{construct:(target,args)=>{
        const instance = args[0]?.geometryInstances;
        const id = instance?.id?.properties?.getValue(value.JulianDate.now()).editableComponentId;
        const primitive = Reflect.construct(target,args) as object;
        if (id) primitives.set(id,{geometry:instance.geometry,primitive,entity:instance.id});
        return primitive;
      }});
      engine = new Proxy(value,{get:(target,property)=>property === "Viewer" ? observedViewer : property === "Primitive" ? observedPrimitive : Reflect.get(target,property)});
    }});
  });
}

test("approved native SUPPORT_FRAME in the real workspace", async ({page, request}) => {
  await observeEngine(page);
  page.on("pageerror", error => console.log("BROWSER_ERROR", error.stack));
  page.on("requestfailed", failed => console.log("REQUEST_FAILED", new URL(failed.url()).pathname, failed.failure()?.errorText));
  const api = "http://127.0.0.1:8001";
  await page.setViewportSize({width:1626,height:982});
  await page.goto("/projects/9001/workspace");
  await expect(page.getByLabel("Search scene components")).toBeVisible({timeout:90000});
  await page.getByText("Experimental CAD review", {exact:true}).click();
  await page.getByRole("button",{name:"Review SUPPORT_FRAME · 5 m",exact:true}).click();
  await expect(page.getByText(/10 components · source revision/)).toBeVisible({timeout:30000});
  await page.getByText("Reviewed component definitions · metres",{exact:true}).click();
  await expect(page.getByText(/length: 5/).first()).toBeVisible();
  await page.getByRole("checkbox",{name:/I reviewed this exact snapshot/}).check();
  const execution = page.waitForResponse(r => /experimental-cad\/reviews\/[^/]+\/execute$/.test(r.url()),{timeout:45000});
  await page.getByRole("button",{name:"Explicitly approve and compile experimental CAD",exact:true}).click();
  const executed = await execution;
  expect(executed.ok()).toBeTruthy();
  const result = await (await request.post(executed.url())).json(); // Verified idempotent retry after the UI reload.
  expect(result.regeneratedComponentIds).toHaveLength(10);
  await expect(page.getByLabel("Search scene components")).toBeVisible({timeout:90000});
  const latestResponse = await request.get(`${api}/api/projects/9001/scenarios/9001/model-revisions/latest`);
  const latest = await latestResponse.json();
  expect(latest.document.components).toHaveLength(11);
  const cad = latest.document.components.filter((c: {geometry:{kind:string}}) => c.geometry.kind === "cad_mesh");
  for (const component of cad) {
    await page.getByRole("tab",{name:"Layers",exact:true}).click();
    await page.getByLabel("Search scene components").fill(component.name);
    await page.getByRole("button",{name:component.name,exact:true}).click();
    await page.getByRole("tab",{name:"Inspect",exact:true}).click();
    await expect(page.getByLabel("Component identity")).toContainText(component.metadata.componentId);
    await expect(page.getByLabel("Component identity")).toContainText("BREP_VALID_MESH_VERIFIED");
    await expect(page.getByLabel("Component identity")).toContainText("UNVERIFIED");
  }
  await page.getByRole("button",{name:"Frame selection",exact:true}).click();
  await expect(page.locator(".cesium-widget canvas[data-sandbox-ready='true']")).toBeVisible({timeout:45000});
  await expect(page.locator(".cesium-widget-errorPanel")).toHaveCount(0);
  await page.screenshot({path:"test-results/cad-frame-native.png"});
  const east = page.getByLabel("Position · metres East",{exact:true});
  await east.fill("0.1"); await east.press("Tab");
  const save = page.waitForResponse(r => /model-revisions$/.test(r.url()) && r.request().method() === "POST");
  await page.getByRole("button",{name:"Save",exact:true}).click();
  expect((await save).ok()).toBeTruthy();
  await page.reload();
  await page.getByRole("tab",{name:"Layers",exact:true}).click();
  await page.getByLabel("Search scene components").fill(cad.at(-1).name);
  await page.getByRole("button",{name:cad.at(-1).name,exact:true}).click();
  await page.getByRole("tab",{name:"Inspect",exact:true}).click();
  await expect(east).toHaveValue("0.1");
  await page.getByRole("tab",{name:"History",exact:true}).click();
  await page.getByRole("button",{name:"Compare",exact:true}).click();
  await expect(page.getByText("0 added · 0 removed · 1 modified",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Close compare",exact:true}).click();
  await page.getByRole("tab",{name:"Layers",exact:true}).click();
  await page.getByLabel("Search scene components").fill("primary-0");
  await page.getByRole("button",{name:"Hide primary-0",exact:true}).click();
  await expect(page.getByRole("button",{name:"Show primary-0",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Show primary-0",exact:true}).click();
  const visibilitySave = page.waitForResponse(r => /model-revisions$/.test(r.url()) && r.request().method() === "POST");
  await page.getByRole("button",{name:"Save",exact:true}).click();
  expect((await visibilitySave).ok()).toBeTruthy();
  const profiles = await (await request.get(`${api}/api/projects/9001/site-profiles`)).json();
  const profileId = profiles.profiles[0].id;
  expect((await request.post(`${api}/api/projects/9001/site-profiles/${profileId}/refresh`)).ok()).toBeTruthy();
  await expect.poll(async()=> (await (await request.get(`${api}/api/projects/9001/site-profiles/${profileId}`)).json()).current).toBe(true);
  await page.reload();
  await expect(page.getByLabel("Search scene components")).toBeVisible();
  await page.getByText("Experimental CAD review",{exact:true}).click();
  await page.getByRole("button",{name:"Review beam change · 6 m",exact:true}).click();
  await page.getByRole("checkbox",{name:/I reviewed this exact snapshot/}).check();
  const regeneration = page.waitForResponse(r=> /experimental-cad\/reviews\/[^/]+\/execute$/.test(r.url()),{timeout:45000});
  await page.getByRole("button",{name:"Explicitly approve and compile experimental CAD",exact:true}).click();
  const regenerated = await regeneration;
  expect(regenerated.ok()).toBeTruthy();
  expect((await (await request.post(regenerated.url())).json()).regeneratedComponentIds).toEqual(["primary-0","primary-1"]);
  const updated=await (await request.get(`${api}/api/projects/9001/scenarios/9001/model-revisions/latest`)).json();
  expect(updated.document.components[0]).toEqual(latest.document.components[0]);
  for(const component of cad){
    const next=updated.document.components.find((c:{id:string})=>c.id===component.id);
    expect(next.metadata.componentId).toBe(component.metadata.componentId);
    if(!["primary-0","primary-1"].includes(component.metadata.componentId)){
      expect(next.geometry.mesh_hash).toBe(component.geometry.mesh_hash);
      expect(next.geometry.brep_hash).toBe(component.geometry.brep_hash);
    }else expect(next.metadata.parameters.length).toBe(6);
  }
  expect(updated.document.components.find((c:{id:string})=>c.id===cad.at(-1).id).transform.position[0]).toBe(.1);
  await page.screenshot({path:"test-results/cad-regenerated.png"});
});

test("native triangle canvas picking for every saved CAD component", async ({page,request}) => {
  await observeEngine(page);
  await page.setViewportSize({width:1626,height:982});
  const latest = await (await request.get("http://127.0.0.1:8001/api/projects/9001/scenarios/9001/model-revisions/latest")).json();
  const cad = latest.document.components.filter((c:{geometry:{kind:string}})=>c.geometry.kind === "cad_mesh");
  expect(cad).toHaveLength(10);
  await page.goto("/projects/9001/workspace");
  await expect(page.locator(".cesium-widget canvas[data-sandbox-ready='true']")).toBeVisible({timeout:45000});
  for (const component of cad) {
    // Camera navigation uses the actual Cesium camera. Project actual triangle
    // centroids and require its depth-aware pick to identify the target object.
    let hit: {x:number;y:number}|null = null;
    for (const [heading,pitch] of [[0,-25],[90,-25],[180,-25],[270,-25],[0,-60]]) {
      await page.evaluate(async ({id,heading,pitch})=>{
        const w = window as unknown as {Cesium:typeof import("cesium");cadAcceptanceViewer:import("cesium").Viewer;cadAcceptancePrimitives:Map<string,{geometry:import("cesium").Geometry;primitive:import("cesium").Primitive}>};
        const sphere = w.cadAcceptancePrimitives.get(id)!.geometry.boundingSphere!;
        w.cadAcceptanceViewer.camera.flyToBoundingSphere(sphere,{duration:0,offset:new w.Cesium.HeadingPitchRange(w.Cesium.Math.toRadians(heading),w.Cesium.Math.toRadians(pitch),Math.max(1,sphere.radius*3))});
        await new Promise<void>(resolve=>{
          const remove=w.cadAcceptanceViewer.scene.postRender.addEventListener(()=>{remove();resolve();});
          w.cadAcceptanceViewer.scene.requestRender();
        });
      },{id:component.id,heading,pitch});
      await expect.poll(()=>page.evaluate(()=>{
        const w=window as unknown as {cadAcceptancePrimitives:Map<string,{primitive:import("cesium").Primitive}>};
        return [...w.cadAcceptancePrimitives.values()].every(p=>!p.primitive.isDestroyed() && p.primitive.ready);
      })).toBe(true);
      hit = await page.evaluate(id=>{
        const w = window as unknown as {Cesium:typeof import("cesium");cadAcceptanceViewer:import("cesium").Viewer;cadAcceptancePrimitives:Map<string,{geometry:import("cesium").Geometry}>};
        const {Cesium:C,cadAcceptanceViewer:v}=w;
        const geometry=w.cadAcceptancePrimitives.get(id)!.geometry;
        const positions=geometry.attributes.position!.values!;
        const indices=geometry.indices!;
        const candidates:{x:number;y:number;area:number}[]=[];
        for(let i=0;i<indices.length;i+=3){
          const point=new C.Cartesian3();
          const projected=[];
          for(let k=0;k<3;k++){const vertex=Number(indices[i+k])*3;const world=new C.Cartesian3(Number(positions[vertex]),Number(positions[vertex+1]),Number(positions[vertex+2]));point.x+=world.x/3;point.y+=world.y/3;point.z+=world.z/3;projected.push(C.SceneTransforms.worldToWindowCoordinates(v.scene,world));}
          const p=C.SceneTransforms.worldToWindowCoordinates(v.scene,point);
          if(!p || p.x<0 || p.y<0 || p.x>=v.canvas.clientWidth || p.y>=v.canvas.clientHeight)continue;
          const [a,b,c]=projected;
          if(!a || !b || !c)continue;
          const area=Math.abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2;
          const bounds=v.canvas.getBoundingClientRect();
          candidates.push({x:Math.round(p.x+bounds.left)-bounds.left,y:Math.round(p.y+bounds.top)-bounds.top,area});
        }
        // Prefer broad visible faces over a one-pixel flange/plate edge;
        // use the same integer DOM coordinates as the real mouse event.
        for(const p of candidates.sort((a,b)=>b.area-a.area)){
          const picked=v.scene.pick(new C.Cartesian2(p.x,p.y))?.id?.properties?.getValue(C.JulianDate.now());
          if(picked?.editableComponentId===id)return {x:p.x,y:p.y};
        }
        return null;
      },component.id);
      if(hit)break;
    }
    expect(hit,component.name+" has a pickable native triangle").not.toBeNull();
    const canvas=await page.locator(".cesium-widget canvas").boundingBox();
    await page.mouse.click(canvas!.x+hit!.x,canvas!.y+hit!.y);
    await page.getByRole("tab",{name:"Inspect",exact:true}).click();
    await expect(page.getByLabel("Component identity")).toContainText(component.metadata.componentId);
    await expect.poll(()=>page.evaluate(id=>{
      const w=window as unknown as {cadAcceptancePrimitives:Map<string,{primitive:import("cesium").Primitive;entity:import("cesium").Entity}>};
      return !!w.cadAcceptancePrimitives.get(id)?.entity.label && [...w.cadAcceptancePrimitives.values()].every(p=>!p.primitive.isDestroyed() && p.primitive.ready);
    },component.id)).toBe(true);
    console.log("NATIVE_TRIANGLE_PICK",component.metadata.componentId);
    if(component.metadata.componentId === "primary-0" || component.metadata.componentId === "platform")await page.screenshot({path:`test-results/cad-native-${component.metadata.componentId}.png`});
  }
  const scale=page.getByLabel("Scale X",{exact:true});
  await scale.fill("2"); await scale.press("Tab");
  await expect(page.getByRole("alert").filter({hasText:"CAD supports rigid transforms only"})).toContainText("reviewed regeneration");
  await scale.press("Escape"); // Discard the rejected numeric draft.
  await expect(scale).toHaveValue("1");
  const unchangedSave=page.waitForResponse(r=>/model-revisions$/.test(r.url()) && r.request().method()==="POST");
  await page.getByRole("button",{name:"Save",exact:true}).click();
  const saved=await unchangedSave;
  expect(saved.ok()).toBeTruthy();
  expect((await saved.json()).document.components.find((c:{id:string})=>c.id===cad.at(-1).id).transform.scale).toEqual([1,1,1]);
});
