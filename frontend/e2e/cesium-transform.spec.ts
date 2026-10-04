import {expect,test} from "@playwright/test";

test("Cesium move previews, commits once, cancels exactly and restores camera",async({page})=>{
  const errors:string[]=[];page.on("pageerror",error=>errors.push(error.message));
  await page.route("**/api/geocode/map-runtime-config",route=>route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto("/projects/999999/workspace?local=1");
  await page.getByRole("button",{name:/^building \d/i}).click();
  const grid=page.locator('main[aria-label="Layout scene"] canvas').first();
  await expect(grid).toHaveAttribute("data-sandbox-ready","true");
  const bounds=(await grid.boundingBox())!;await page.mouse.click(bounds.x+bounds.width*.5,bounds.y+bounds.height*.6);
  await page.getByRole("button",{name:"Map",exact:true}).click();
  const canvas=page.locator(".cesium-widget canvas");await expect(canvas).toHaveAttribute("data-sandbox-ready","true",{timeout:60000});
  await page.getByRole("button",{name:"building 1",exact:true}).click();
  await page.getByRole("button",{name:"Fit all",exact:true}).click();
  await page.getByRole("button",{name:"Move",exact:true}).click();
  await expect(canvas).toHaveAttribute("data-transform-ready","true");
  const east=page.getByLabel("Position (m) East",{exact:true}),north=page.getByLabel("Position (m) North",{exact:true});
  const initial=[await east.inputValue(),await north.inputValue()];
  const drag=async()=>{
    await expect(canvas).toHaveAttribute("data-sandbox-ready","true");
    await expect.poll(async()=>JSON.parse(await canvas.getAttribute("data-transform-handles")||"{}").X!==undefined).toBe(true);
    const handles=JSON.parse((await canvas.getAttribute("data-transform-handles"))!) as Record<string,{x:number;y:number}>;
    const rectangle=(await canvas.boundingBox())!,point=handles.X;
    await page.mouse.move(rectangle.x+point.x,rectangle.y+point.y);await page.mouse.down();
    const dx=point.x-handles.pivot.x,dy=point.y-handles.pivot.y,length=Math.hypot(dx,dy);
    await page.mouse.move(rectangle.x+point.x+dx/length*60,rectangle.y+point.y+dy/length*60,{steps:10});
    await expect(canvas).toHaveAttribute("data-transform-camera-enabled","false");
  };
  await drag();await expect(east).toHaveValue(initial[0]);await page.mouse.up();
  await expect(east).not.toHaveValue(initial[0]);await expect(north).toHaveValue(initial[1]);
  await expect(canvas).toHaveAttribute("data-transform-camera-enabled","true");
  await page.getByRole("button",{name:"Undo",exact:true}).click();await expect(east).toHaveValue(initial[0]);
  await page.getByRole("button",{name:"building 1",exact:true}).click();await page.getByRole("button",{name:"Move",exact:true}).click();
  await drag();await page.keyboard.press("Escape");await page.mouse.up();await expect(east).toHaveValue(initial[0]);await expect(north).toHaveValue(initial[1]);
  await expect(canvas).toHaveAttribute("data-transform-camera-enabled","true");
  expect(errors).toEqual([]);
});

