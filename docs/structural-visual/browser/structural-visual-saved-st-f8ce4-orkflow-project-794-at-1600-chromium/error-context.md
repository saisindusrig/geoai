# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: structural-visual.spec.ts >> saved structural visual workflow project 794 at 1600
- Location: e2e\structural-visual.spec.ts:6:71

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Structural visual engineering' }).getByRole('article', { name: 'Selected structural evidence' })
Timeout: 30000ms
- Expected substring  - 1
+ Received string     + 4

- one-way tributary allocation
+ platform-deckNot verified: no current saved member forces or displacement for this component.Calculation evidence and source identityComponent industrial-platform-5x3:platform-deck · revision 105 · records 431 · case Slab tributary{
+   "connections": [],
+   "samples": []
+ }

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Structural visual engineering' }).getByRole('article', { name: 'Selected structural evidence' }) with timeout 30000ms
  - waiting for getByRole('region', { name: 'Structural visual engineering' }).getByRole('article', { name: 'Selected structural evidence' })
    60 × locator resolved to <article aria-label="Selected structural evidence" class="space-y-2 rounded border border-border p-2">…</article>
       - unexpected value "platform-deckNot verified: no current saved member forces or displacement for this component.Calculation evidence and source identityComponent industrial-platform-5x3:platform-deck · revision 105 · records 431 · case Slab tributary{
  "connections": [],
  "samples": []
}"

```

```yaml
- article "Selected structural evidence":
  - text: platform-deck
  - paragraph: "Not verified: no current saved member forces or displacement for this component."
  - group: Calculation evidence and source identity
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | import slabFixture from '../../docs/structural-visual/project-794.json';
  4  | const expect=pwExpect.configure({timeout:30000});
  5  | const modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
  6  | test.use({trace:'off'});
  7  | for(const width of [1280,1600])for(const project of [793,794,804])test(`saved structural visual workflow project ${project} at ${width}`,async({page})=>{
  8  |  test.setTimeout(240000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
  9  |  const writes:string[]=[],errors:string[]=[];
  10 |  page.on('pageerror',e=>errors.push(e.message));
  11 |  await page.route('**/*',async route=>{const r=route.request();if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+r.url().split('?')[0]);return route.abort('blockedbyclient');}if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
  12 |  await page.goto(`/projects/${project}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
  13 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Structural visual engineering'});
  14 |  await expect(panel).toHaveAttribute('data-blocked','false',{timeout:60000});
  15 |  if(project!==804)await expect(panel.getByLabel('Structural saved load case')).toBeVisible();else await expect(panel).toContainText('No current verified structural solver result');
  16 |  for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(panel.getByLabel('Structural visual legend')).toBeVisible();
  17 |   if(key==='deformation'&&project!==804){await panel.getByLabel('Displacement magnification').fill('200');await expect(panel).toContainText('magnification ×200');await panel.getByLabel('Show original structure').uncheck();await panel.getByLabel('Show original structure').check();}
  18 |   if(key==='forces'&&project!==804){for(const f of ['shear','axial','moment'])await panel.getByLabel('Structural force diagram').selectOption(f);}
  19 |   if((project===793&&['loads','deformation','forces'].includes(key))||(project===794&&['path','slab'].includes(key))||(project===804&&key==='foundation')){await page.waitForTimeout(400);await page.screenshot({path:`../docs/structural-visual/${project}-${key}-${width}.png`});}
  20 |  }
  21 |  if(project===793){await panel.getByRole('button',{name:'Deformed versus original',exact:true}).click();for(const c of ['Horizontal','Gravity','Self weight','Linear sum'])await panel.getByLabel('Structural saved load case').selectOption(c);
  22 |   await panel.getByRole('button',{name:'Frame view',exact:true}).click();await page.waitForTimeout(300);
  23 |   const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(p=>p.x>70&&p.x<width-460&&p.y>150&&p.y<900);expect(pick).toBeTruthy();const bounds=await canvas.boundingBox();await page.mouse.click(bounds!.x+pick!.x,bounds!.y+pick!.y);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toBeVisible();await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('Available saved planar samples');
> 24 |  }
     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                   ^ Error: expect(locator).toContainText(expected) failed
  25 |  if(project===794){await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await expect(panel).toContainText('kN applied');const select=panel.getByLabel('Inspect structural component');await select.selectOption(slabFixture.rows[0].result.transfer!.slab_id);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('one-way tributary allocation');}
  26 |  await panel.getByRole('button',{name:'Restore full structure',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);await expect(panel.getByLabel('Isolate analyzed structural system')).not.toBeChecked();
  27 |  expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/structural-visual/acceptance-${project}-${width}.json`,JSON.stringify({project,width,modes:7,write_requests:writes,page_errors:errors,restored_visibility:true},null,2));
  28 | });
  29 | 
```