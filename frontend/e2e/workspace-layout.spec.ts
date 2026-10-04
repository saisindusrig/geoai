import {expect,test} from "@playwright/test";

for(const width of [1478,1280,1024])test(`workspace controls fit without overlap or horizontal scrolling at ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:982});
  await page.route("**/api/geocode/map-runtime-config",route=>route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto("/projects/5/workspace");
  await expect(page.getByRole("button",{name:"Scene / Sun study",exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByLabel("Search scene components")).toBeVisible();
  await expect(page.getByLabel("Filter scene objects")).toHaveCount(0);
  await expect(page.getByRole("button",{name:/^Site data/})).toHaveCount(0);
  await expect(page.getByRole("button",{name:"Inspect selected",exact:true})).toHaveCount(0);
  await expect(page.getByText("Select an object · Ctrl-click for multiple",{exact:true})).toHaveCount(0);
  await expect(page.locator(".workspace-terrain-status")).toHaveCount(0);
  await expect(page.getByText("Model on context ground · visual preview, not a saved survey placement",{exact:true})).toHaveCount(0);
  await expect(page.getByLabel("Map source attribution")).toBeHidden();
  const viewport=await page.locator(".workspace-map-viewport").boundingBox();
  const bottom=await page.locator(".workspace-bottom-controls").boundingBox();
  expect(bottom!.x+bottom!.width).toBeGreaterThan(viewport!.x+viewport!.width-30);
  expect(bottom!.y).toBeGreaterThan(viewport!.y+viewport!.height*.75);
  if(width>1024){
    await page.locator(".workspace-bottom-controls summary").click();
    await expect(page.getByLabel("Transform coordinates")).toBeVisible();
    await page.locator(".workspace-bottom-controls summary").click();
  }
  const tabs=page.getByRole("tablist",{name:"Inspector views"});
  await expect(tabs.getByRole("tab",{name:"Layers",exact:true})).toHaveCSS("background-color","rgba(0, 0, 0, 0)");
  await expect(tabs.getByRole("tab",{name:"Layers",exact:true})).toHaveCSS("box-shadow","none");
  await expect(tabs.getByRole("tab",{name:"Layers",exact:true})).toHaveCSS("border-radius","0px");
  const layout=await page.evaluate(()=>{
    const row=document.querySelector(".workspace-map-commandrow")!;
    const elements=[...row.querySelectorAll(".workspace-map-control > button, .workspace-commandbar summary, .workspace-commandbar > div > button")];
    const boxes=elements.map(element=>element.getBoundingClientRect());
    const overlaps=boxes.some((a,index)=>boxes.slice(index+1).some(b=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1));
    const dock=document.querySelector('[aria-label="Engineering dock"]')!;
    return {overlaps,inside:boxes.every(box=>box.left>=0 && box.right<=innerWidth),dockScroll:dock.scrollWidth>dock.clientWidth,pageScroll:document.documentElement.scrollWidth>innerWidth};
  });
  expect(layout).toEqual({overlaps:false,inside:true,dockScroll:false,pageScroll:false});
  if(width===1478){
    const tools=await page.locator(".workspace-main-tools").boundingBox();
    expect(Math.abs(tools!.x+tools!.width/2-(viewport!.x+viewport!.width/2))).toBeLessThan(40);
    expect(tools!.y).toBeLessThan(viewport!.y+30);
  }
  const header=await page.locator('[aria-label="Scene layer explorer"] > .sticky.top-0').boundingBox();
  expect(header!.height).toBeLessThan(120);
  await expect(page.getByRole("region",{name:"Engineering dock"}).getByText("PRELIMINARY",{exact:true})).toHaveCount(0);
  await page.screenshot({path:`test-results/workspace-layout-${width}.png`});
});
