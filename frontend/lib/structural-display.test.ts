import {it,expect} from 'vitest';
import {structuralFitRange,layoutEngineeringLabels,engineeringLabelText,diagramDisplayScales,diagramRibbons,FORCE_DISPLAY} from './structural-display';
it('fits the limiting horizontal or vertical field of view with bounded padding',()=>{
 for(const aspect of [.8,1.3,2]){const half=Math.min(Math.PI/6,Math.atan(Math.tan(Math.PI/6)*aspect)),range=structuralFitRange(3,aspect,Math.PI/3);expect(range*Math.sin(half)).toBeGreaterThan(3);expect(range).toBeLessThan(12);}
});
it('keeps placed labels separated and inside the readable viewport, prioritizing selection',()=>{
 const source=Array.from({length:20},(_,i)=>({key:String(i),x:400,y:350,width:180,height:44,priority:i===19}));const before=JSON.stringify(source);
 for(const width of [794,1110]){const boxes=layoutEngineeringLabels(source,width,864);expect(boxes[0].key).toBe('19');expect(boxes.length).toBeLessThan(source.length);for(const [i,a]of boxes.entries()){expect(a.x).toBeGreaterThanOrEqual(90);expect(a.x+a.width).toBeLessThanOrEqual(width-32);for(const b of boxes.slice(i+1))expect(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y).toBe(false);}}
 const free=layoutEngineeringLabels([source[19]],794,864)[0];const moved=layoutEngineeringLabels([source[19]],794,864,[free])[0];expect(moved.y!==free.y||moved.x!==free.x).toBe(true);
 expect(JSON.stringify(source)).toBe(before);
});
it('retains detailed signed values and warning words when wrapping selected labels',()=>{
 const text='CAD column SW · No current verified solver transfer';expect(engineeringLabelText(text).replaceAll('\n',' ')).toBe('No current verified solver transfer');expect(engineeringLabelText(text,true).replaceAll('\n',' ')).toBe(text);expect(engineeringLabelText('moment -28.810 kN·m · signed sample peak')).toBe('M -28.810 kN·m');
});
it('describes the unchanged per-frame ordinate normalization with dimensional units',()=>{
 const frames=[{elements:[{samples:[{moment_nm:-30000,shear_n:5000,axial_n:-12000}]}]}];const before=JSON.stringify(frames);
 expect(diagramDisplayScales(frames,'moment')[0]).toEqual({peak:30,reference:30,offset_m:.75,mmPerUnit:25});expect(diagramDisplayScales(frames,'shear')[0].reference).toBe(5);expect(FORCE_DISPLAY.axial.color).not.toBe(FORCE_DISPLAY.shear.color);expect(JSON.stringify(frames)).toBe(before);const base=[[0,0,0],[1,0,0],[2,0,0]],plot=[[0,0,1],[1,0,1],[2,0,1]];expect(diagramRibbons(base,plot,[1,1,1])).toEqual([[...base,...[...plot].reverse()]]);expect(diagramRibbons(base,plot,[0,0,0])).toEqual([]);
});
