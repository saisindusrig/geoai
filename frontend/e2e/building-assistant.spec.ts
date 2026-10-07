import { expect, test } from "@playwright/test";

// API fixtures isolate this browser regression from the user's saved projects and AI quota.
test("building workspace reviews a proposal before rendering its approved model", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  const spec = {
    summary: "A single-floor living space with a conceptual concrete frame.", floors: 1, floor_height: 3,
    footprint: { x: -5, y: -4, width: 10, depth: 8 },
    rooms: [{ id: "living", name: "Living room", floor: 0, x: -5, y: -4, width: 10, depth: 8 }],
    walls: [{ id: "south", floor: 0, start: [-5,-4], end: [5,-4], thickness: .15 }],
    openings: [{ id: "entry", kind: "door", wall_id: "south", offset: 1, width: 1, height: 2.1, sill: 0 }],
    columns: [{ x: -4, y: -3, size: .3 }], beams: [], slab_thickness: .15, foundation_width: 1,
    foundation_depth: 1, assumptions: ["No verified survey; conceptual frame only."],
  };
  const document = {
    schema_version: 1, project_id: 9801, scenario_id: 9901, project_type: "building", units: "metric",
    origin: { lng: 77.595, lat: 12.972, elevation_m: 0, heading_deg: 0 }, generator_parameters: {},
    metadata: { source: "ai_generate", frame: "local_enu_meters", building_plan_id: 1, elevation_known: false },
    structural_layout: { assumptions: spec.assumptions },
    components: [
      { id: "room-living", name: "Living room", category: "room", visible: true, locked: false, parent_id: null,
        geometry: { kind: "box", size: [10,8,.02] }, transform: { position: [0,0,.01], rotation_deg: [0,0,0], scale: [1,1,1] },
        material: { name: "Floor", color: "#CCC3AE", roughness: .8, metalness: 0 }, quantity: { included: false } },
      { id: "column-1", name: "Column 1", category: "column", visible: true, locked: false, parent_id: null,
        geometry: { kind: "box", size: [.3,.3,3] }, transform: { position: [-4,-3,1.5], rotation_deg: [0,0,0], scale: [1,1,1] },
        material: { name: "Concrete", color: "#8EACC7", roughness: .8, metalness: 0 }, quantity: { included: true } },
    ],
  };
  const revision = { id: 9951, revision_number: 1, source: "ai_generate", document, created_at: "2026-10-07T00:00:00Z" };
  let proposed = false, built = false;
  let builds = 0;
  const plan = () => ({ id: 1, prompt: "Build a small house", stale: false, base_revision_id: null, job_id: built ? "building-e2e" : null,
    scenario_id: built ? 9901 : null, spec, model: "fixture", elevation_known: false });
  await page.route("**/api/projects/9801**", async route => {
    const url = new URL(route.request().url()).pathname;
    let json: unknown = {};
    if (url.endsWith("/ai/building-plans/1/build")) {
      expect(route.request().postDataJSON()).toEqual({ approve: true });
      builds++; built = true; json = { job_id: "building-e2e", scenario_id: 9901 };
    } else if (url.endsWith("/ai/building-plans")) {
      if (route.request().method() === "POST") { proposed = true; json = plan(); }
      else json = { plans: proposed ? [plan()] : [] };
    } else if (url.endsWith("/model-revisions/latest")) json = revision;
    else if (url.endsWith("/model-revisions")) json = { revisions: [revision] };
    else if (url.endsWith("/scenarios")) json = built ? [{ id: 9901, name: "Approved house", status: "completed", created_at: "2026-10-07T00:00:00Z", input_parameters_json: {}, design_output_json: { summary: spec.summary, geometry_spec: { objects: [], frame: "local_meters" }, assumptions: spec.assumptions } }] : [];
    else if (url.endsWith("/exports/files")) json = [];
    else if (url.endsWith("/9801")) json = { id: 9801, name: "Building assistant browser test", project_type: "building", status: "draft", units: "metric", center_lng: 77.595, center_lat: 12.972,
      boundary_geojson: { type: "Polygon", coordinates: [[[77.5948,12.9718],[77.5952,12.9718],[77.5952,12.9722],[77.5948,12.9722],[77.5948,12.9718]]] } };
    else if (/site-analysis|estimates/.test(url)) { await route.fulfill({ status: 404, json: { detail: "No data" } }); return; }
    else if (url.includes("/placements/")) json = { placement: null };
    else if (url.endsWith("/evidence")) json = { readiness: "VISUAL_REFERENCE", measurement_class: "VISUAL", evidence: Object.fromEntries(["horizontal_crs", "vertical_reference", "units", "terrain", "coverage", "spatial_backend", "authoritative_raster"].map(key => [key, { status: "MISSING" }])) };
    else if (url.includes("/cameras")) json = [];
    await route.fulfill({ json });
  });
  await page.route("**/api/jobs/building-e2e", route => route.fulfill({ json: { job_id: "building-e2e", status: "completed", stage: "completed", progress: 100, message: "Completed", result: { scenario_id: 9901 }, error: null } }));
  await page.route("**/api/geocode/map-runtime-config", route => route.fulfill({ json: { cesium_ion_token: null, google_maps_api_key: null } }));
  await page.goto("/projects/9801/workspace");
  await page.getByRole("button", { name: "AI Building Assistant", exact: true }).click();
  const panel = page.getByRole("region", { name: "AI Building Assistant" });
  await expect(panel).toBeVisible();
  await panel.getByRole("textbox").fill("Build a small house");
  await panel.getByRole("button", { name: "Create plan", exact: true }).click();
  await expect(panel.getByText("Review plan 1")).toBeVisible();
  expect(builds).toBe(0);
  await expect(panel.getByRole("img", { name: "Proposed floor layout" })).toBeVisible();
  const bounds = (await panel.boundingBox())!;
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(1440);
  await page.screenshot({ path: "test-results/building-assistant-review.png" });
  await panel.getByRole("button", { name: "Approve and build" }).click();
  await expect(page.getByRole("button", { name: "Architecture", exact: true })).toBeVisible();
  await expect(page.locator(".cesium-widget canvas")).toBeVisible();
  await expect(page.locator(".cesium-widget canvas")).toHaveAttribute("data-sandbox-ready", "true", { timeout: 60000 });
  expect(builds).toBe(1);
  await panel.getByRole("button", { name: "Close building assistant" }).click();
  await page.screenshot({ path: "test-results/building-assistant-model.png" });
  expect(errors).toEqual([]);
});
