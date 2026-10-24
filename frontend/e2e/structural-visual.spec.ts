import {test,expect as pwExpect} from '@playwright/test';
import {writeFileSync} from 'node:fs';
import slabFixture from '../../docs/structural-visual/project-794.json';
import foundationFixture from '../../docs/foundation-visual/demo.json';
const expect=pwExpect.configure({timeout:30000});
const modes=[['path','Structural load paths'],['loads','Applied loads and reactions'],['deformation','Deformed versus original'],['forces','Beam and column forces'],['slab','Slab-to-beam distribution'],['foundation','Foundation and soil response'],['warnings','Warnings and connections']] as const;
test.use({trace:'off'});
for(const width of [1280,1600])for(const project of [793,794,804])test(`saved structural visual workflow project ${project} at ${width}`,async({page})=>{
 test.setTimeout(240000);page.setDefaultTimeout(30000);await page.setViewportSize({width,height:1000});
 const writes:string[]=[],errors:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request();if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+r.url().split('?')[0]);return route.abort('blockedbyclient');}if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
 await page.goto(`/projects/${project}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});
 await page.getByRole('tab',{name:'Analysis',exact:true}).click();const panel=page.getByRole('region',{name:'Structural visual engineering'});
 await expect(panel).toHaveAttribute('data-blocked','false',{timeout:60000});
 if(project!==804)await expect(panel.getByLabel('Structural saved load case')).toBeVisible();else await expect(panel).toContainText('No current verified structural solver result');
 for(const [key,label] of modes){await panel.getByRole('button',{name:label,exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode',key);await expect(panel.getByLabel('Structural visual legend')).toBeVisible();
  if(key==='deformation'&&project!==804){await panel.getByLabel('Displacement magnification').fill('200');await expect(panel).toContainText('magnification ×200');await panel.getByLabel('Show original structure').uncheck();await panel.getByLabel('Show original structure').check();}
  if(key==='forces'&&project!==804){for(const f of ['shear','axial','moment'])await panel.getByLabel('Structural force diagram').selectOption(f);}
  if((project===793&&['loads','deformation','forces'].includes(key))||(project===794&&['path','slab'].includes(key))||(project===804&&key==='foundation')){await page.waitForTimeout(400);await page.screenshot({path:`../docs/structural-visual/${project}-${key}-${width}.png`});}
 }
 if(project===793){await panel.getByRole('button',{name:'Deformed versus original',exact:true}).click();for(const c of ['Horizontal','Gravity','Self weight','Linear sum'])await panel.getByLabel('Structural saved load case').selectOption(c);
  await panel.getByRole('button',{name:'Frame view',exact:true}).click();await page.waitForTimeout(300);
  const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(p=>p.x>70&&p.x<width-460&&p.y>150&&p.y<900);expect(pick).toBeTruthy();const bounds=await canvas.boundingBox();await page.mouse.click(bounds!.x+pick!.x,bounds!.y+pick!.y);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toBeVisible();await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('Available saved planar samples');
  await panel.getByText('Compare available saved load cases',{exact:true}).click();await panel.getByRole('button',{name:/^Gravity ·/}).click();await expect(panel.getByLabel('Structural saved load case')).toHaveValue('Gravity');
 }
 if(project===794){await panel.getByRole('button',{name:'Slab-to-beam distribution',exact:true}).click();await expect(panel).toContainText('kN applied');const select=panel.getByLabel('Inspect structural component');await select.selectOption(slabFixture.rows[0].result.transfer!.slab_id);await expect(panel.getByRole('article',{name:'Selected structural evidence'})).toContainText('one-way tributary allocation');}
 await panel.getByRole('button',{name:'Restore full structure',exact:true}).click();await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);await expect(panel.getByLabel('Isolate analyzed structural system')).not.toBeChecked();
 expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync(`../docs/structural-visual/acceptance-${project}-${width}.json`,JSON.stringify({project,width,modes:7,write_requests:writes,page_errors:errors,restored_visibility:true},null,2));
});
test('isolated foundation and whole-structure views retain independent inspection and overlay ownership',async({page,request})=>{
 test.setTimeout(180000);const a=await(await request.get('http://127.0.0.1:18001/__foundation_validation')).json();expect(a.database).toBe(foundationFixture.attestation.database);
 const writes:string[]=[],errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{const r=route.request();if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.url());return route.abort('blockedbyclient');}if(r.url().includes('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});return route.continue();});
 await page.setViewportSize({width:1600,height:1000});await page.goto(`http://localhost:13001/projects/${foundationFixture.study.project_id}/workspace`);const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:120000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();
 const visual=page.getByRole('article',{name:'Foundation visual analysis'});await expect(visual).toBeVisible();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');
 await page.getByText('Whole-structure evidence and unsupported transfers',{exact:true}).click();const structure=page.getByRole('region',{name:'Structural visual engineering'});await expect(structure).toHaveAttribute('data-blocked','false');
 await structure.getByRole('button',{name:'Foundation and soil response',exact:true}).click();await expect(canvas).toHaveAttribute('data-structural-mode','foundation');await expect(structure).toContainText('Saved synthetic soil:');
 const labels=JSON.parse(await canvas.getAttribute('data-foundation-label-points')||'[]') as {key:string;x:number;y:number}[];const pick=labels.find(p=>p.x>100&&p.x<1100&&p.y>100&&p.y<900);expect(pick).toBeTruthy();const box=await canvas.boundingBox();await page.mouse.click(box!.x+pick!.x,box!.y+pick!.y);await expect(structure.getByRole('article',{name:'Selected structural evidence'})).toContainText('Saved synthetic footing:');await expect(canvas).toHaveAttribute('data-structural-mode','foundation');
 await visual.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await expect(canvas).not.toHaveAttribute('data-structural-mode',/./);
 await page.waitForTimeout(16000);await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');
 for(const name of ['Loads and reactions','Soil pressure and settlement','Bending moments','One-way shear','Punching shear','Reinforcement and anchorage']){await visual.getByRole('button',{name,exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');}
 await page.screenshot({path:'../docs/structural-visual/foundation-interoperability-1600.png'});expect(writes).toEqual([]);expect(errors).toEqual([]);writeFileSync('../docs/structural-visual/foundation-interoperability.json',JSON.stringify({independent_component_inspection:true,foundation_mode_reclaims_view:true,poll_does_not_steal_view:true,original_foundation_modes:true,write_requests:writes,page_errors:errors},null,2));
});
