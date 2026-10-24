import {test,expect} from "@playwright/test";
const projectId=process.env.ATTACHMENT_EXISTING_PROJECT_ID;
test.skip(!projectId,"Requires the saved local Milestone 2 assembly review project.");
test("saved assemblies retain editing, protected references, deletion preview and camera framing",async({page})=>{
  const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
  await page.setViewportSize({width:1626,height:982});
  await page.route("**/api/geocode/map-runtime-config",r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto(`/projects/${projectId}/workspace`);await page.getByRole("tab",{name:"Inspect",exact:true}).click();
  const panel=page.getByLabel("Attached platform components");await expect(panel.locator("summary")).toContainText("15 attached assemblies");
  await panel.locator("summary").click();await panel.getByRole("button",{name:/^Edit Stairs /}).click();await panel.locator("summary").click();
  await expect(panel.getByLabel("Stair draft dimensions")).toContainText("20 equal risers");await expect(panel.getByLabel("Attachment Tread going · m")).toHaveValue("0.32");
  // Generic delete on a selected generated tread opens a whole-flight preview.
  await page.getByRole("button",{name:"Delete selection",exact:true}).click();await expect(panel.getByRole("status")).toContainText("Delete attached assembly");
  await panel.getByRole("button",{name:"Cancel attachment preview",exact:true}).click();await expect(panel.locator("summary")).toContainText("15 attached assemblies");await expect(page.getByRole("button",{name:"Undo",exact:true})).toBeDisabled();
  // Moving one tread must retain the saved shape and explain the attachment constraint.
  await page.getByRole("button",{name:"Move east one step",exact:true}).click();await expect(page.getByRole("alert").filter({hasText:"disconnected"})).toBeVisible();await expect(page.getByRole("button",{name:"Undo",exact:true})).toBeDisabled();
  await page.getByRole("button",{name:"Clear selection",exact:true}).click();
  await panel.getByLabel("Attachment Tread going · m").fill("0.34");await panel.getByRole("button",{name:"Preview attachment edit",exact:true}).click();await expect(page.getByRole("button",{name:"Save 3D model revision",exact:true})).toBeDisabled();
  await panel.getByRole("button",{name:"Cancel attachment preview",exact:true}).click();await panel.getByLabel("Attachment Tread going · m").fill("0.32");
  const canvas=page.locator(".cesium-widget canvas");await expect(canvas).toHaveAttribute("data-sandbox-ready","true");
  // Let initial terrain/camera load settle before the explicit engineering frame.
  await page.waitForTimeout(1800);await panel.getByRole("button",{name:"Frame assembly",exact:true}).click();
  await expect.poll(async()=>{const points=JSON.parse(await canvas.getAttribute("data-component-pick-points")||"{}");return Object.keys(points).length;}).toBe(45);
  await page.waitForTimeout(900);await page.screenshot({path:"../docs/milestone2/screenshots/assembly-framed.png"});
  await expect(page.locator(".cesium-widget-errorPanel")).toHaveCount(0);expect(errors).toEqual([]);
});
