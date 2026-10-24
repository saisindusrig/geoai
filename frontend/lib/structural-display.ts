/** Display-only framing and label layout. No engineering response calculation. */
export const FORCE_DISPLAY={moment:{symbol:'M',name:'Bending moment',unit:'kN·m',color:'#ffbd69',style:'Amber ribbon'},shear:{symbol:'V',name:'Shear force',unit:'kN',color:'#63ddff',style:'Cyan comb'},axial:{symbol:'N',name:'Axial force',unit:'kN',color:'#dca0ff',style:'Violet dashed ribbon'}} as const;
export function diagramDisplayScales(frames:{elements?:{samples:{moment_nm:number;shear_n:number;axial_n:number}[]}[]}[],force:keyof typeof FORCE_DISPLAY){
 return frames.map(f=>{const values=(f.elements??[]).flatMap(e=>e.samples).map(s=>Math.abs(force==='moment'?s.moment_nm:force==='shear'?s.shear_n:s.axial_n));const peak=Math.max(0,...values);return {peak:peak/1000,reference:Math.max(1,peak)/1000,offset_m:.75,mmPerUnit:750/(Math.max(1,peak)/1000)};});
}
/** Join adjacent display quads into a few ribbons; retain gaps at sign changes. */
export function diagramRibbons(base:number[][],diagram:number[][],values:number[]){
 const regions:number[][][]= [];let start=-1,end=0,sign=0;
 const flush=()=>{if(start>=0)regions.push([...base.slice(start,end+1),...diagram.slice(start,end+1).reverse()]);start=-1;};
 for(let i=1;i<values.length;i++){const next=Math.sign(values[i-1]||values[i]);if(values[i]*values[i-1]<0||Math.max(Math.abs(values[i]),Math.abs(values[i-1]))<1e-12){flush();continue;}if(start>=0&&next!==sign)flush();if(start<0){start=i-1;sign=next;}end=i;}
 flush();return regions;
}
export function structuralFitRange(radius:number,aspect:number,verticalFov:number){
 const half=Math.min(verticalFov/2,Math.atan(Math.tan(verticalFov/2)*Math.max(.2,aspect)));
 return Math.max(1, radius/Math.sin(Math.max(.1,half)) * 1.20);
}
export type LabelBox={key:string;x:number;y:number;width:number;height:number;priority?:boolean};
export function layoutEngineeringLabels(labels:LabelBox[],width:number,height:number,obstacles:Pick<LabelBox,'x'|'y'|'width'|'height'>[]=[]){
 const placed:LabelBox[]=[];
 for(const label of [...labels].sort((a,b)=>Number(!!b.priority)-Number(!!a.priority))){
  const {x,y}=label;const w=Math.min(label.width,Math.max(60,width-40)),h=label.height;
  const candidates=[[12,14],[12,-h-12],[-w-12,14],[-w-12,-h-12],[12,32+h],[-w-12,32+h],[12,-h*2-30],[-w-12,-h*2-30]];
  for(const [dx,dy] of candidates){const b={...label,x:x+dx,y:y+dy,width:w};if(b.x<90||b.x+w>width-32||b.y<110||b.y+h>height-120)continue;
   if(placed.some(p=>b.x<p.x+p.width+8&&b.x+w+8>p.x&&b.y<p.y+p.height+8&&b.y+h+8>p.y))continue;
   if(obstacles.some(p=>b.x<p.x+p.width&&b.x+w>p.x&&b.y<p.y+p.height&&b.y+h>p.y))continue;
   placed.push(b);break;
  }
 }
 return placed;
}
export function engineeringLabelText(text:string,selected=false){
 // Keep the warning reason verbatim; defer long generated component names to selection.
 const warning=text.match(/ · (No current verified solver transfer|Connection capacity unverified)$/)?.[1];
 const compact=selected?text:warning??text.replace(/ · signed sample peak$/,'').replace(/^moment /,'M ').replace(/^shear /,'V ').replace(/^axial /,'N ').replace(/^.* · \|u\|max /,'|u|max ');
 return compact.split('\n').flatMap(line=>{const words=line.split(' '),lines:string[]=[];let current='';for(const word of words){if(current&&current.length+word.length+1>36){lines.push(current);current=word;}else current+=(current?' ':'')+word;}if(current)lines.push(current);return lines;}).join('\n');
}
