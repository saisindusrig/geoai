import {test,expect,type Page} from "@playwright/test";
const projectId=process.env.ATTACHMENT_PLATFORM_PROJECT_ID;
test.skip(!projectId,"Requires a separate local 5 x 3 maintenance-platform review project.");
async function inspect(page:Page){const tab=page.getByRole("tab",{name:"Inspect",exact:true});if(await tab.getAttribute("aria-selected")!=="true")await tab.click();}
test("connected solids: add, select, edit, delete, preview, resize, undo, save and compare",async({page,request})=>{
  test.slow();const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
  await page.setViewportSize({width:1920,height:1080});
  await page.route("**/api/geocode/map-runtime-config",r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  await page.goto(`/projects/${projectId}/workspace`);await inspect(page);
  const panel=page.getByLabel("Attached platform components"),prefix="industrial-platform-5x3:";
  await expect(panel).toBeVisible();
  const add=async(kind:string,refs:string[])=>{
    if(await panel.getByRole("button",{name:"New assembly",exact:true}).count())await panel.getByRole("button",{name:"New assembly",exact:true}).click();
    await panel.getByLabel("Attached component type").selectOption(kind);
    for(const [i,ref] of refs.entries())await panel.getByLabel(`Attachment reference ${i+1}`).selectOption(prefix+ref);
    await panel.getByRole("button",{name:"Preview addition",exact:true}).click();await expect(panel.getByRole("status")).toContainText("preview only, not applied");
    await panel.getByRole("button",{name:"Apply attachment",exact:true}).click();await expect(panel.getByRole("status")).toHaveCount(0);
  };
  // Invalid support size and cancellation have no document/history effect.
  await panel.getByLabel("Attachment Width · m").fill("0");await panel.getByRole("button",{name:"Preview addition",exact:true}).click();await expect(panel.getByRole("alert")).toContainText("positive");
  await panel.getByLabel("Attachment Width · m").fill("1.2");await panel.getByRole("button",{name:"Preview addition",exact:true}).click();await panel.getByRole("button",{name:"Cancel attachment preview",exact:true}).click();await expect(page.getByRole("button",{name:"Undo",exact:true})).toBeDisabled();
  for(const corner of ["sw","se","nw","ne"]){
    await add("foundation",[`column-${corner}`]);await add("base_plate",[`column-${corner}`]);await add("connection",[`column-${corner}`,corner.startsWith("s")?"beam-south":"beam-north"]);
  }
  await add("brace",["column-sw","column-nw"]);await add("brace",["column-se","column-ne"]);await add("stairs",["platform-deck"]);
  await expect(panel.locator("summary")).toContainText("15 attached assemblies");
  // Selecting a generated part in Layers exposes its parameter record in Inspect.
  await page.getByRole("tab",{name:"Layers",exact:true}).click();await page.getByLabel("Search scene components").fill("stairs");
  const tread=page.getByRole("button",{name:/^stairs .+ · tread-1$/}).first();await tread.click();await inspect(page);
  await panel.getByRole("button",{name:"Edit selected attachment",exact:true}).click();await panel.getByLabel("Attachment Tread going · m").fill("0.32");
  await panel.getByRole("button",{name:"Preview attachment edit",exact:true}).click();await panel.getByRole("button",{name:"Apply attachment",exact:true}).click();
  await expect(panel.getByLabel("Attachment Tread going · m")).toHaveValue("0.32");
  // A deletion removes all treads/stringers as one undoable assembly operation.
  await panel.getByRole("button",{name:"Preview deletion",exact:true}).click();await expect(panel.getByRole("status")).toContainText("Delete attached assembly");
  await panel.getByRole("button",{name:"Cancel attachment preview",exact:true}).click();await expect(panel.locator("summary")).toContainText("15 attached assemblies");
  await panel.getByRole("button",{name:"Preview deletion",exact:true}).click();await panel.getByRole("button",{name:"Apply attachment",exact:true}).click();await expect(panel.locator("summary")).toContainText("14 attached assemblies");
  await page.getByRole("button",{name:"Undo",exact:true}).click();await expect(panel.locator("summary")).toContainText("15 attached assemblies");
  await page.getByRole("button",{name:"Redo",exact:true}).click();await expect(panel.locator("summary")).toContainText("14 attached assemblies");await page.getByRole("button",{name:"Undo",exact:true}).click();
  const save=async()=>{const response=page.waitForResponse(r=>/model-revisions$/.test(r.url())&&r.request().method()==="POST");await page.getByRole("button",{name:"Save 3D model revision",exact:true}).click();const r=await response;expect(r.ok(),await r.text()).toBeTruthy();return r.json();};
  const before=await save();expect(before.document.components).toHaveLength(42);
  const model=page.getByLabel("Parametric maintenance platform");await model.getByLabel("Platform length · m",{exact:true}).fill("6");await model.getByLabel("Platform width · m",{exact:true}).fill("4");await model.getByLabel("Deck height · m",{exact:true}).fill("3.6");
  await model.getByRole("button",{name:"Preview platform",exact:true}).click();await model.getByRole("button",{name:"Apply platform",exact:true}).click();await page.getByRole("button",{name:"Undo",exact:true}).click();await expect(model.getByLabel("Platform length · m",{exact:true})).toHaveValue("5");
  await page.getByRole("button",{name:"Redo",exact:true}).click();const after=await save();expect(after.document.components).toHaveLength(45);
  expect(after.document.generator_parameters.platform_attachments.items).toHaveLength(15);
  const foundation=after.document.components.find((c:{category:string})=>c.category==="foundation");expect(foundation.transform.position[0]).toBeCloseTo(-2.85);
  const url=`http://127.0.0.1:8001/api/projects/${projectId}/scenarios/${after.scenario_id}/model-revisions`;
  const tampered=structuredClone(after.document);tampered.components.find((c:{category:string})=>c.category==="bracing").geometry.end[2]+=1;
  const rejected=await request.post(url,{data:{base_revision_id:after.id,document:tampered,source:"manual_edit"}});expect(rejected.status()).toBe(422);
  await page.reload();await inspect(page);await expect(panel.locator("summary")).toContainText("15 attached assemblies");await expect(page.getByLabel("Platform length · m",{exact:true})).toHaveValue("6");
  await page.getByRole("tab",{name:"History",exact:true}).click();await page.getByLabel("Revision A",{exact:true}).selectOption(String(before.id));await page.getByLabel("Revision B",{exact:true}).selectOption(String(after.id));await page.getByRole("button",{name:"Compare",exact:true}).click();await expect(page.getByText(/3 added · 0 removed · \d+ modified/)).toBeVisible();
  await page.screenshot({path:"../docs/milestone2/screenshots/comparison.png"});await page.getByRole("button",{name:"Close compare",exact:true}).click();
  await page.getByRole("tab",{name:"Layers",exact:true}).click();await page.getByLabel("Search scene components").fill("");await page.getByRole("button",{name:"platform-deck",exact:true}).click();await page.getByRole("button",{name:"Frame selection",exact:true}).click();await inspect(page);await page.waitForTimeout(1500);
  await page.screenshot({path:"../docs/milestone2/screenshots/model.png"});expect(errors).toEqual([]);await expect(page.locator(".cesium-widget-errorPanel")).toHaveCount(0);
});
