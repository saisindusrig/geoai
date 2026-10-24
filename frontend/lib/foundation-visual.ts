/** Saved numerical evidence -> temporary ENU display geometry. No solver or model writes. */
export const FOUNDATION_MODES = [
  ['loads','Loads and reactions'],['soil','Soil pressure and settlement'],['bending','Bending moments'],
  ['one-way','One-way shear'],['punching','Punching shear'],['reinforcement','Reinforcement and anchorage'],['alternatives','Foundation alternatives'],
] as const;
export type FoundationMode=typeof FOUNDATION_MODES[number][0];
export type FoundationCheck={status:string;demand?:number;resistance?:number;unit?:string;reason?:string;ratio?:number;required_mm?:number;available_mm?:number};
export type FoundationLayer={direction:string;effective_depth_mm:number;steel_area_mm2:number;bar_diameter_mm:number;bar_count:number;spacing_mm:number;clear_spacing_mm:number;one_way_section_from_center_mm:number;one_way_demand_kn:number;flexure:FoundationCheck;one_way:FoundationCheck;development:FoundationCheck;nominal:{nominal_moment_knm?:number;status?:string}};
export type FoundationData={geometry:{footing_id:string;column_id:string;center_east_north_m:number[];footing_size_m:number[];column_size_m:number[];column_face_up_m:number;bearing_up_m:number};actions:{service_column_kn:number;service_footing_weight_kn:number;service_gross_soil_kn:number;factored_column_kn:number;factored_net_pressure_kpa:number};contact:{pmin_pa:number;pmax_pa:number;delta_down_m:number;pressure_samples?:{x_m:number;p_pa:number;down_m:number}[]};factored_bending:{faces:{face:string;projection_m:number;full_cut_moment_knm:number;diagram:{distance_from_face_m:number;moment_knm_per_m:number}[]}[]};rc:{layers:FoundationLayer[];punching:FoundationCheck&{effective_depth_mm:number;perimeter_mm:number;demand_kn:number};quantities:{concrete_gross_m3:number;steel_mass_kg:number}};limitations:string[]};
export type FoundationAlternative={width_m:number;thickness_m:number;additional_bars_each_direction?:number;status?:string;reason?:string;factored_moment_knm?:number;settlement_mm?:number;punching?:FoundationCheck;layers?:FoundationLayer[];quantities?:{concrete_gross_m3:number;steel_mass_kg:number}};
type Point=number[];
export type FoundationOverlay={mode:'foundation-integrated';paths:Point[][];colors:string[];componentIds:string[];inspectionKeys:string[];polygons:{positions:Point[];color:string;componentId:string;alpha?:number;inspectionKey?:string}[];bars:{start:Point;end:Point;radius:number;color:string;inspectionKey:string;componentId:string}[];nodeMarkers:{name:string;position:Point;inspectionKey:string}[];fit:boolean;fitRange:number;fitPitch:number;fitHeadingOffset:number;focus:Point;focusComponentIds:string[];fitPoints:Point[];overlayThroughSolids:boolean;label:string;visualMode:FoundationMode};
export const FOUNDATION_COLORS={EW:'#ffd479',NS:'#83ddff',failure:'#ff6575',pressure:'#65d7bf',moment:'#ffc276',section:'#ffb878',punching:'#e6a0ff',ghost:'#8cf3ec',reference:'#b2b9c4'};
export function foundationStatus(check?:FoundationCheck){
 if(check?.status==='WITHIN_IMPLEMENTED_CHECK')return 'Within implemented check';
 if(check?.status==='EXCEEDS_IMPLEMENTED_CHECK')return 'Exceeds implemented check';
 if(check?.status==='DISABLED'||check?.status==='OUTSIDE_DOMAIN')return 'Not supported';
 return 'Not verified';
}
export function buildFoundationOverlay(data:FoundationData,input:{cover_mm:number},mode:FoundationMode,options:{direction?:'both'|'EW'|'NS';alternative?:FoundationAlternative;fit?:boolean}={}):FoundationOverlay{
 const g=data.geometry,[E,N]=g.center_east_north_m,[B,L,H]=g.footing_size_m,top=g.column_face_up_m,bottom=g.bearing_up_m,c=g.column_size_m[0],p=(x:number,y:number,z:number)=>[E+x,N+y,z];
 const o:FoundationOverlay={mode:'foundation-integrated',visualMode:mode,paths:[],colors:[],componentIds:[],inspectionKeys:[],polygons:[],bars:[],nodeMarkers:[],fit:options.fit!==false,fitRange:Math.max(B,L)*2.8,fitPitch:-43,fitHeadingOffset:2.4,focus:p(0,0,top-H/2),focusComponentIds:[g.footing_id,g.column_id],fitPoints:[],overlayThroughSolids:true,label:FOUNDATION_MODES.find(m=>m[0]===mode)![1]+' · saved synthetic evidence'};
 const line=(points:Point[],color:string,key:string)=>{o.paths.push(points);o.colors.push(color);o.componentIds.push(g.footing_id);o.inspectionKeys.push(key);};
 const mark=(name:string,position:Point,key:string)=>o.nodeMarkers.push({name,position,inspectionKey:key});
 const polygon=(points:Point[],color:string,key:string,alpha=.22)=>o.polygons.push({positions:points,color,componentId:g.footing_id,alpha,inspectionKey:key});
 const rect=(x:number,y:number,z:number,color:string,key:string)=>line([p(-x,-y,z),p(x,-y,z),p(x,y,z),p(-x,y,z),p(-x,-y,z)],color,key);
 const arrow=(x:number,y:number,z0:number,z1:number,color:string,key:string)=>{line([p(x,y,z0),p(x,y,z1)],color,key);const sign=Math.sign(z1-z0),w=Math.min(B*.035,.05);line([p(x-w,y,z1-sign*.08),p(x,y,z1),p(x+w,y,z1-sign*.08)],color,key);};
 const drawBars=(layers:FoundationLayer[],width:number,length:number,colorOverride?:string)=>{
  for(const [i,layer] of layers.entries()){
   if(options.direction&&options.direction!=='both'&&options.direction!==(i===0?'EW':'NS'))continue;
   const key=i===0?'anchorage-EW':'anchorage-NS',radius=layer.bar_diameter_mm/2000,z=top-layer.effective_depth_mm/1000,span=(i===0?length:width)-2*input.cover_mm/1000-2*radius,half=(i===0?width:length)/2-input.cover_mm/1000;
   for(let j=0;j<layer.bar_count;j++){const t=-span/2+j*span/(layer.bar_count-1),start=i===0?p(-half,t,z):p(t,-half,z),end=i===0?p(half,t,z):p(t,half,z);o.bars.push({start,end,radius,color:colorOverride??(i===0?FOUNDATION_COLORS.EW:FOUNDATION_COLORS.NS),inspectionKey:key,componentId:g.footing_id});}
  }
 };
 if(mode==='loads'){
  arrow(0,0,top+.65,top,FOUNDATION_COLORS.failure,'loads');
  arrow(B/3,-L/3,top+.3,top,FOUNDATION_COLORS.moment,'loads');
  mark(`Footing weight ${data.actions.service_footing_weight_kn.toFixed(2)} kN ↓`,p(B/3,-L/3,top+.35),'loads');
  for(const x of [-B/3,0,B/3])for(const y of [-L/3,0,L/3])arrow(x,y,bottom-.3,bottom,FOUNDATION_COLORS.pressure,'loads');
  mark(`Service column ${data.actions.service_column_kn.toFixed(2)} kN ↓`,p(0,0,top+.7),'loads');
  mark(`Gross soil reaction ${data.actions.service_gross_soil_kn.toFixed(2)} kN ↑\nFactored column ${data.actions.factored_column_kn.toFixed(2)} kN (separate action)`,p(0,-L/2-.15,bottom-.4),'loads');
 }else if(mode==='soil'){
  polygon([p(-B/2,-L/2,bottom-.02),p(B/2,-L/2,bottom-.02),p(B/2,L/2,bottom-.02),p(-B/2,L/2,bottom-.02)],FOUNDATION_COLORS.pressure,'soil',.58);
  for(const x of [-B/3,0,B/3])for(const y of [-L/3,0,L/3])arrow(x,y,bottom-.27,bottom-.025,FOUNDATION_COLORS.pressure,'soil');
  // A uniform numerical result has one colour. No invented spatial FEA contour.
  const exaggerated=data.contact.delta_down_m*20;
  rect(B/2,L/2,bottom-exaggerated,FOUNDATION_COLORS.NS,'soil');
  line([p(B/2+.08,0,bottom),p(B/2+.08,0,bottom-exaggerated)],FOUNDATION_COLORS.NS,'soil');
  mark(`Uniform pressure ${(data.contact.pmax_pa/1000).toFixed(3)} kPa\nWinkler displacement ${(data.contact.delta_down_m*1000).toFixed(3)} mm ↓`,p(0,-L/2-.15,bottom-.3),'soil');
  mark('Displacement outline ×20\nRigid Winkler result · no FEA field',p(B/2+.12,0,bottom-.1),'soil');
 }else if(mode==='bending'){
  for(const [i,face] of [data.factored_bending.faces[0],data.factored_bending.faces[2]].entries()){
   if(!face)continue;if(options.direction&&options.direction!=='both'&&options.direction!==(i===0?'EW':'NS'))continue;
   const key=i===0?'bending-EW':'bending-NS',color=i===0?FOUNDATION_COLORS.EW:FOUNDATION_COLORS.NS,maximum=Math.max(...face.diagram.map(v=>v.moment_knm_per_m));
   const origin=i===0?p(c/2,-L/2-.04,top+.04):p(-B/2-.04,c/2,top+.04);
   const points=face.diagram.map(v=>i===0?p(c/2+v.distance_from_face_m,-L/2-.04,top+.04+.38*v.moment_knm_per_m/maximum):p(-B/2-.04,c/2+v.distance_from_face_m,top+.04+.38*v.moment_knm_per_m/maximum));
   line([origin,...points,points.at(-1)!],color,key);
   line(i===0?[p(c/2,-L/2,top+.01),p(c/2,L/2,top+.01)]:[p(-B/2,c/2,top+.01),p(B/2,c/2,top+.01)],color,key);
   mark(`${i===0?'EW':'NS'} factored face moment\n${face.full_cut_moment_knm.toFixed(3)} kN·m full-width`,points[0],key);
  }
 }else if(mode==='one-way'){
  for(const [i,layer] of data.rc.layers.entries()){
   if(options.direction&&options.direction!=='both'&&options.direction!==(i===0?'EW':'NS'))continue;
   const key=i===0?'one-way-EW':'one-way-NS',cut=layer.one_way_section_from_center_mm/1000,color=layer.one_way.status==='EXCEEDS_IMPLEMENTED_CHECK'?FOUNDATION_COLORS.failure:FOUNDATION_COLORS.section;
   for(const sign of [-1,1]){const x=sign*cut;
    const points=i===0?[p(x,-L/2,bottom),p(x,L/2,bottom),p(x,L/2,top+.02),p(x,-L/2,top+.02)]:[p(-B/2,x,bottom),p(B/2,x,bottom),p(B/2,x,top+.02),p(-B/2,x,top+.02)];polygon(points,color,key);line([...points,points[0]],color,key);
   }
   mark(`${i===0?'EW':'NS'} · Vᵤ ${layer.one_way_demand_kn.toFixed(3)} kN\nd=${layer.effective_depth_mm.toFixed(0)} mm · ${foundationStatus(layer.one_way)}`,i===0?p(cut,-L/2-.1,top+.14):p(-B/2-.12,cut,top+.14),key);
  }
 }else if(mode==='punching'){
  const v=data.rc.punching,x=v.perimeter_mm/8000,color=v.status==='EXCEEDS_IMPLEMENTED_CHECK'?FOUNDATION_COLORS.failure:FOUNDATION_COLORS.punching,z=top-v.effective_depth_mm/1000;
  rect(x,x,top+.025,color,'punching');rect(x,x,z,color,'punching');
  for(const [a,b] of [[-x,-x],[x,-x],[x,x],[-x,x]])line([p(a,b,z),p(a,b,top+.025)],color,'punching');
  mark(`Punching Vᵤ ${v.demand_kn.toFixed(3)} kN\nb₀ ${v.perimeter_mm.toFixed(0)} mm · d/2=${(v.effective_depth_mm/2).toFixed(1)} mm`,p(0,-x-.15,top+.15),'punching');
 }else if(mode==='reinforcement'){
  drawBars(data.rc.layers,B,L);
  const index=options.direction==='NS'?1:0,layer=data.rc.layers[index],key=index===0?'anchorage-EW':'anchorage-NS',required=layer.development.required_mm,available=layer.development.available_mm;
  const color=layer.development.status==='EXCEEDS_IMPLEMENTED_CHECK'?FOUNDATION_COLORS.failure:FOUNDATION_COLORS.pressure;
  const axis=(distance:number,z:number)=>index===0?p(distance,-L*.29,z):p(-B*.29,distance,z),z=top-layer.effective_depth_mm/1000;
  if(required!==undefined&&available!==undefined){
   const start=c/2,end=start+required/1000,actualEnd=start+available/1000;
   line([axis(start,z+.035),axis(actualEnd,z+.035)],color,key);
   // Dashed dimension extension is required reach, never a fabricated physical bar.
   for(let x=start;x<end;x+=.075)line([axis(x,z+.08),axis(Math.min(x+.045,end),z+.08)],FOUNDATION_COLORS.failure,key);
   for(const x of [start,actualEnd,end])line([axis(x,z+.01),axis(x,z+.12)],color,key);
   mark(`Straight development ${Math.round(required)} mm required\n${Math.round(available)} mm available · ${foundationStatus(layer.development)}`,axis(end,z+.15),key);
   o.fitPoints.push(axis(end,z));o.fitRange=Math.max(o.fitRange,(end+B/2)*1.8);
  }else mark('Straight development · Not supported',axis(c/2,z+.2),key);
  for(const [i,l] of data.rc.layers.entries()){
   if(options.direction&&options.direction!=='both'&&options.direction!==(i===0?'EW':'NS'))continue;
   const colour=i===0?FOUNDATION_COLORS.EW:FOUNDATION_COLORS.NS;
   line([p(-B/2-.06-i*.06,L/2,top),p(-B/2-.06-i*.06,L/2,top-l.effective_depth_mm/1000)],colour,i===0?'anchorage-EW':'anchorage-NS');
   mark(`${i===0?'EW lower':'NS upper'} ${l.bar_count} × Ø${l.bar_diameter_mm} mm\nd ${l.effective_depth_mm} · spacing ${l.spacing_mm.toFixed(1)} · cover ${input.cover_mm} mm`,p(-B/2-.08,L/2+i*.16,top+.1),i===0?'anchorage-EW':'anchorage-NS');
  }
 }else if(mode==='alternatives'&&options.alternative&&options.alternative.status!=='OUTSIDE_DOMAIN'){
  const a=options.alternative,x=a.width_m/2,z=top-a.thickness_m,key='alternatives',co=FOUNDATION_COLORS.ghost;
  rect(B/2,L/2,bottom,FOUNDATION_COLORS.reference,key);
  rect(x,x,top+.012,co,key);rect(x,x,z,co,key);
  for(const [a,b] of [[-x,-x],[x,-x],[x,x],[-x,x]])line([p(a,b,z),p(a,b,top+.012)],co,key);
  for(const points of [[p(-x,-x,z),p(x,-x,z),p(x,x,z),p(-x,x,z)],[p(-x,-x,z),p(x,-x,z),p(x,-x,top),p(-x,-x,top)],[p(x,-x,z),p(x,x,z),p(x,x,top),p(x,-x,top)],[p(x,x,z),p(-x,x,z),p(-x,x,top),p(x,x,top)],[p(-x,x,z),p(-x,-x,z),p(-x,-x,top),p(-x,x,top)]])polygon(points,co,key,.12);
  if(a.layers)drawBars(a.layers,a.width_m,a.width_m,co);
  mark(`UNSAVED · ${a.width_m.toFixed(2)} m square × ${a.thickness_m.toFixed(2)} m\nMᵤ ${a.factored_moment_knm?.toFixed(3)} kN·m · steel ${a.quantities?.steel_mass_kg.toFixed(1)} kg`,p(0,-x-.1,z-.1),key);
  o.fitRange=Math.max(B,a.width_m)*2.9;o.focus=p(0,0,top-a.thickness_m/2);
 }
 return o;
}
