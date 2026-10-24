import {expect,it} from 'vitest';
import {displayMaterial} from './display-material';
import type {EditableModelComponent} from './types';
it('distinguishes display finishes without mutating engineering or saved inputs',()=>{
 const base={id:'a',name:'Concept',category:'building',material:{name:'Conceptual',color:'#808080',roughness:.75,metalness:0},metadata:{componentRole:'column',E_Pa:200e9}} as unknown as EditableModelComponent;
 const original=JSON.stringify(base);
 const column=displayMaterial(base);
 const slab=displayMaterial({...base,metadata:{...base.metadata,componentRole:'slab'}});
 const footing=displayMaterial({...base,metadata:{...base.metadata,componentRole:'footing'}});
 expect(column.finish).toContain('appearance');expect(column.color).not.toBe(slab.color);expect(slab.color).not.toBe(footing.color);
 expect(JSON.stringify(base)).toBe(original);expect(column).not.toHaveProperty('E_Pa');
});
