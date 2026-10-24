# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: disk-validation.spec.ts >> saved CAD frame renders and existing footing results load
- Location: e2e\disk-validation.spec.ts:14:6

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Footing bending demand' })
Expected substring: "10.125000"
Received string:    "CAD footing · column-face bending demandSYNTHETIC VERIFICATION ONLY. Actual steel/base-plate/RC load transfer and footing safety BLOCKED. Saved envelopes are not verified concrete or structural sections.One-way full-width cantilever cuts: a=(B−c)/2; m=q_net·a²/2 kN·m/m; M=m·cut width. Four face cuts are alternative overlapping sections, not four separate reaction areas. Pressure must independently equilibrate N. No bearing-capacity result is imported.Loading saved geometry and immutable demand evidence…Load synthetic CAD footing demand inputsAuthorize this exact synthetic demand calculation onlyCalculate authorized footing demandRestore complete CAD modelAnalysis focus temporarily shows the selected footing/column; restore returns all existing visibility. Arrows have illustrative lengths; diagram heights are scaled demand ordinates, not displacement. Reinforcement strength, one-way/punching shear, soil capacity, connection adequacy, IS/US checks and engineering approval remain DISABLED."
Timeout: 30000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Footing bending demand' }) with timeout 30000ms
  - waiting for getByRole('region', { name: 'Footing bending demand' })
    57 × locator resolved to <section data-busy="true" aria-label="Footing bending demand" class="mb-4 space-y-3 rounded border border-border p-3 text-sm [&_input:not([type=checkbox])]:w-full [&_input]:bg-background [&_textarea]:w-full [&_textarea]:bg-background [&_select]:w-full [&_select]:bg-background [&_button]:rounded [&_button]:border [&_button]:border-border [&_button]:p-2">…</section>
       - unexpected value "CAD footing · column-face bending demandSYNTHETIC VERIFICATION ONLY. Actual steel/base-plate/RC load transfer and footing safety BLOCKED. Saved envelopes are not verified concrete or structural sections.One-way full-width cantilever cuts: a=(B−c)/2; m=q_net·a²/2 kN·m/m; M=m·cut width. Four face cuts are alternative overlapping sections, not four separate reaction areas. Pressure must independently equilibrate N. No bearing-capacity result is imported.Loading saved geometry and immutable demand evidence…Load synthetic CAD footing demand inputsAuthorize this exact synthetic demand calculation onlyCalculate authorized footing demandRestore complete CAD modelAnalysis focus temporarily shows the selected footing/column; restore returns all existing visibility. Arrows have illustrative lengths; diagram heights are scaled demand ordinates, not displacement. Reinforcement strength, one-way/punching shear, soil capacity, connection adequacy, IS/US checks and engineering approval remain DISABLED."

```

```yaml
- region "Footing bending demand":
  - heading "CAD footing · column-face bending demand" [level=3]
  - paragraph: SYNTHETIC VERIFICATION ONLY. Actual steel/base-plate/RC load transfer and footing safety BLOCKED. Saved envelopes are not verified concrete or structural sections.
  - paragraph: "One-way full-width cantilever cuts: a=(B−c)/2; m=q_net·a²/2 kN·m/m; M=m·cut width. Four face cuts are alternative overlapping sections, not four separate reaction areas. Pressure must independently equilibrate N. No bearing-capacity result is imported."
  - status: Loading saved geometry and immutable demand evidence…
  - button "Load synthetic CAD footing demand inputs" [disabled]
  - checkbox "Authorize exact footing demand" [disabled]
  - text: Authorize this exact synthetic demand calculation only
  - button "Calculate authorized footing demand" [disabled]
  - button "Restore complete CAD model"
  - paragraph: Analysis focus temporarily shows the selected footing/column; restore returns all existing visibility. Arrows have illustrative lengths; diagram heights are scaled demand ordinates, not displacement. Reinforcement strength, one-way/punching shear, soil capacity, connection adequacy, IS/US checks and engineering approval remain DISABLED.
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {readFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000});
  4  | test.use({trace:'off'});
  5  | test('Assistant resize terminates on blur and keeps composer visible',async({page})=>{
  6  |  test.setTimeout(120000);await page.setViewportSize({width:1280,height:900});await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto('/projects/793/workspace');await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const assistant=page.getByRole('region',{name:'Project assistant',exact:true});await expect(assistant.getByRole('textbox',{name:'Project message'})).toBeEnabled();const aside=assistant.locator('xpath=ancestor::aside[1]'),handle=aside.getByRole('separator',{name:'Resize panel width'});const box=await handle.boundingBox(),before=(await aside.boundingBox())!.width;await page.mouse.move(box!.x+2,box!.y+100);await page.mouse.down();await page.mouse.move(box!.x-60,box!.y+100);await expect.poll(async()=>(await aside.boundingBox())!.width).toBeGreaterThan(before+20);await page.evaluate(()=>window.dispatchEvent(new Event('blur')));const width=(await aside.boundingBox())!.width;await page.mouse.move(box!.x-100,box!.y+100);await page.mouse.up();expect((await aside.boundingBox())!.width).toBeCloseTo(width,0);await expect(assistant.getByRole('textbox',{name:'Project message'})).toBeInViewport();await page.screenshot({path:'../docs/disk-optimization/browser/resized-assistant-1280.png'});
  7  | });
  8  | test('isolated component preview apply undo redo save reload and restore',async({page})=>{
  9  |  test.setTimeout(180000);const copy=JSON.parse(readFileSync('../.cache/copilot-m2-verification/qa-copy.json','utf8'));await page.setViewportSize({width:1600,height:900});await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto(`/projects/${copy.project_id}/workspace`);await page.getByRole('tab',{name:'Layers',exact:true}).click();await page.getByLabel('Search scene components',{exact:true}).fill(copy.component.name);await page.locator('[id^="layer-row-"] button[aria-pressed]').first().click();await page.getByRole('tab',{name:'Inspect',exact:true}).click();const form=page.getByLabel('Component edit form',{exact:true}),name=form.getByLabel('Component name',{exact:true});const changed=copy.component.name+' UX review';await name.fill(changed);await form.getByRole('button',{name:'Preview',exact:true}).click();await expect(form).toContainText('Edit preview');await form.getByRole('button',{name:'Apply',exact:true}).click();await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(name).toHaveValue(copy.component.name);await page.getByRole('button',{name:'Redo',exact:true}).click();await expect(name).toHaveValue(changed);await page.getByRole('button',{name:'Save model',exact:true}).click();await expect(page.getByRole('button',{name:'Save model',exact:true})).toBeDisabled();await page.reload();await page.getByRole('tab',{name:'Layers',exact:true}).click();await page.getByLabel('Search scene components',{exact:true}).fill(changed);await page.locator('[id^="layer-row-"] button[aria-pressed]').first().click();await page.getByRole('tab',{name:'Inspect',exact:true}).click();await expect(name).toHaveValue(changed);await name.fill(copy.component.name);await form.getByRole('button',{name:'Apply',exact:true}).click();await page.getByRole('button',{name:'Save model',exact:true}).click();await expect(page.getByRole('button',{name:'Save model',exact:true})).toBeDisabled();await page.screenshot({path:'../docs/disk-optimization/browser/isolated-save-reload.png'});
  10 | });
  11 | 
  12 |  test.beforeEach(async({request})=>{const response=await request.get('http://127.0.0.1:18001/__disk_validation');expect((await response.json()).mode).toBe('isolated-disk-optimization-20261015');});
  13 |  test('offline Assistant persists on isolated database',async({page})=>{await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto('/projects/793/workspace');const region=page.getByRole('region',{name:'Project assistant',exact:true});if(!await region.isVisible())await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const box=region.getByRole('textbox',{name:'Project message'});await expect(box).toBeEnabled();await box.fill('Show the beam bending moment. Disk optimization verification.');await box.press('Enter');await expect(region.getByRole('article',{name:'Assistant message'}).last()).toContainText('bending moment');await page.reload();await expect(page.getByRole('article',{name:'Your message'}).last()).toContainText('Disk optimization verification');});
> 14 |  test('saved CAD frame renders and existing footing results load',async({page,request})=>{await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));await page.goto('/projects/803/workspace');await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:60000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await page.getByText('Advanced analysis · inputs, tools and evidence',{exact:true}).click();await expect(page.getByRole('region',{name:'Footing bending demand'})).toContainText('10.125000');const response=await request.get('http://127.0.0.1:18001/api/projects/803/engineering/footing-flexure?model_revision_id=123');expect(response.ok()).toBeTruthy();expect((await response.json()).records.some((r:{type:string})=>r.type==='FOOTING_FLEXURE_RESULT')).toBeTruthy();await page.screenshot({path:'../docs/disk-optimization/browser/saved-results.png'});});
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       ^ Error: expect(locator).toContainText(expected) failed
  15 | 
```