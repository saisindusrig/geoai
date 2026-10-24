"""One saved rectangular slab, two declared beam supports, two isolated planar frames.

Load allocation only: this module never creates a slab stiffness or capacity model.
"""
import math
from typing import Literal
from pydantic import Field
from app.services.design import physical_frame as frame, elastic_frame as elastic, gravity_frame as gravity
from app.services.design.frame_loads import Strict
from app.services.design import cad_frame

LIMITS = ['One-way symmetric tributary allocation, not plate/shell slab FEA or slab capacity.',
 'Only two independent East-Up three-member frames; transverse beams, braces, stairs and foundations excluded.',
 'Uniform pressure only, no openings, rotated slabs, two-way sharing or asymmetric support/edge overhangs.',
 'Declared massless rigid joints and fixed bases are analytical assumptions, not connection or foundation adequacy.',
 'No self-weight unless separately supplied; this workflow uses only explicit synthetic slab pressure.',
 'No code checks, reinforcement design, safety approval or whole-building analysis.']

class Selection(Strict):
 slab_id: str
 beam_ids: list[str] = Field(min_length=2,max_length=2)
 excluded_context_component_ids: list[str] = Field(default_factory=list,max_length=200)

class Loading(Selection):
 context_exclusion_source: str|None = Field(default=None,min_length=10,max_length=400)
 context_exclusion_approved: bool = False
 tributary_widths_m: list[float]|None = Field(default=None,min_length=2,max_length=2)
 tributary_width_source: str|None = Field(default=None,min_length=10,max_length=400)
 intensity_kn_m2: float = Field(gt=0,le=100)
 source: str = Field(min_length=5,max_length=400)
 direction: Literal['local_enu_negative_up']
 method: Literal['one_way_symmetric_tributary_area']
 support_assumption: str = Field(min_length=10,max_length=600)
 excluded_beam_ids: list[str] = Field(max_length=10)
 excluded_attachment_ids: list[str] = Field(max_length=100)
 no_openings_confirmed: Literal[True]
 symmetric_edge_overhang_approved: Literal[True]
 one_way_idealization_approved: Literal[True]
 purpose: Literal['SYNTHETIC_VERIFICATION_ONLY']

class FrameDeclaration(Strict):
 component_ids: list[str] = Field(min_length=3,max_length=3)
 sections: list[frame.Section] = Field(min_length=3,max_length=3)
 connections: list[frame.Joint] = Field(min_length=2,max_length=2)
 supports: Literal['both_column_bases_fixed']
 support_source: str = Field(min_length=5,max_length=300)
 elements_per_member: Literal[1,2,4]
 units: Literal['SI','N-mm']

class Inputs(Loading):
 frames: list[FrameDeclaration] = Field(min_length=2,max_length=2)

def box(c,category):
 if c.get('category')!=category or c.get('parent_id') or c.get('geometry',{}).get('kind')!='box':raise ValueError('Independent saved box '+category+' required')
 t=c.get('transform',{});size=c['geometry'].get('size',[]);p=t.get('position',[])
 if len(size)!=3 or len(p)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in size+p) or min(size)<=0:raise ValueError('Incomplete or non-positive saved geometry')
 if t.get('rotation_deg')!=[0,0,0] or t.get('scale')!=[1,1,1]:raise ValueError('Rotated/scaled geometry unsupported')
 return size,p

def geometry(doc,selection):
 q=Selection.model_validate(selection).model_dump()
 if doc.get('units')!='metric' or doc.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Saved geometry must be metric local ENU')
 cs=doc.get('components',[]);ids=[c['id'] for c in cs]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate saved identities')
 exclusions=q['excluded_context_component_ids']
 if exclusions:
  legacy={c['id'] for c in cs if not c['id'].startswith('drawing-cad:')}
  if not doc.get('metadata',{}).get('cad_slab_path_review') or len(set(exclusions))!=len(exclusions) or set(exclusions)!=legacy:raise ValueError('Only an explicitly reviewed complete non-CAD context exclusion is supported in the dedicated CAD load-path scope; CAD supports cannot be hidden')
  cs=[c for c in cs if c['id'] not in exclusions]
 by={c['id']:c for c in cs}
 if len(set([q['slab_id']]+q['beam_ids']))!=3 or any(i not in by for i in [q['slab_id']]+q['beam_ids']):raise ValueError('Three distinct saved slab/beam identities required')
 slab=by[q['slab_id']];s,p=box(slab,'slab');L,W,T=s
 if doc.get('metadata',{}).get('cad_slab_path_review'):
  for id in [q['slab_id']]+q['beam_ids']:cad_frame.identity(by[id])
 if T>=min(L,W)/2 or L>50 or W>50:raise ValueError('Unsupported slab proportions or extent')
 if any(slab.get('geometry',{}).get(k) or slab.get('metadata',{}).get(k) for k in ('openings','holes','cutouts')):raise ValueError('Slab openings unsupported')
 attachments=[c for c in cs if c.get('parent_id')==slab['id']]
 if any(c.get('category') in ('opening','void') for c in cs) or any(c.get('category')!='stairs' or c.get('metadata',{}).get('attachment_kind')!='stairs' for c in attachments):raise ValueError('Attached slab geometry / opening components unsupported; review complete geometry')
 bs=sorted([by[i] for i in q['beam_ids']],key=lambda b:b['transform']['position'][1]);centers=[]
 for b in bs:
  sz,pos=box(b,'beam')
  if sz[0]<=max(sz[1:]) or not math.isclose(sz[0],L,abs_tol=1e-8) or abs(pos[0]-p[0])>1e-8 or abs(pos[2]+sz[2]/2-(p[2]-T/2))>1e-8:raise ValueError('Full-length parallel East beams at slab underside required; no projection or automatic connection')
  if abs(pos[1]-p[1])+sz[1]/2>W/2+1e-8:raise ValueError('Support footprint outside slab')
  centers.append(pos[1])
 span=centers[1]-centers[0];edges=[centers[0]-(p[1]-W/2),p[1]+W/2-centers[1]]
 if span<=0 or min(edges)<-1e-8 or abs(edges[0]-edges[1])>1e-8 or max(edges)>.1*span:raise ValueError('Only symmetric support lines with short equal edge overhangs supported')
 excluded=[]
 for c in cs:
  if c.get('category')!='beam' or c['id'] in q['beam_ids']:continue
  sz,pos=box(c,'beam')
  overlaps=abs(pos[0]-p[0])<=(L+sz[0])/2+1e-8 and abs(pos[1]-p[1])<=(W+sz[1])/2+1e-8 and abs(pos[2]+sz[2]/2-(p[2]-T/2))<1e-8
  if overlaps:
   if sz[1]<=max(sz[0],sz[2]) or abs(abs(pos[0]-p[0])+sz[0]/2-L/2)>1e-8:raise ValueError('Additional interior/parallel support geometry makes this two-support idealization ambiguous')
   excluded.append(c['id'])
 mid=sum(centers)/2;strips=[]
 for b,lo,hi in [(bs[0],p[1]-W/2,mid),(bs[1],mid,p[1]+W/2)]:
  width=hi-lo;strips.append(dict(beam_id=b['id'],beam_name=b['name'],width_m=width,area_m2=L*width,length_m=L,polygon_enu_m=[[p[0]-L/2,lo,p[2]+T/2],[p[0]+L/2,lo,p[2]+T/2],[p[0]+L/2,hi,p[2]+T/2],[p[0]-L/2,hi,p[2]+T/2]]))
 return dict(slab_id=slab['id'],slab_name=slab['name'],excluded_context_component_ids=exclusions,slab_source=cad_frame.identity(slab) if slab['id'].startswith('drawing-cad:') else None,size_m=s,position_enu_m=p,area_m2=L*W,support_spacing_m=span,edge_overhangs_m=edges,required_excluded_beam_ids=sorted(excluded),required_excluded_attachment_ids=sorted(c['id'] for c in attachments),strips=strips,limitations=LIMITS)

def transfer(doc,inputs):
 q=Loading.model_validate({k:v for k,v in inputs.items() if k!='frames'}).model_dump();g=geometry(doc,{k:q[k] for k in ('slab_id','beam_ids','excluded_context_component_ids')})
 if q['excluded_context_component_ids'] and (not q['context_exclusion_approved'] or not q['context_exclusion_source']):raise ValueError('Complete context exclusion requires a source/reason and explicit separate-system review')
 if doc.get('metadata',{}).get('cad_slab_path_review'):
  widths=q['tributary_widths_m']
  if not widths or not q['tributary_width_source'] or any(not math.isfinite(v) or v<=0 or not math.isclose(v,s['width_m'],abs_tol=1e-8,rel_tol=0) for v,s in zip(widths,g['strips'])):raise ValueError('Explicit sourced tributary widths must match actual saved support geometry')
 if sorted(q['excluded_beam_ids'])!=g['required_excluded_beam_ids'] or len(q['excluded_beam_ids'])!=len(set(q['excluded_beam_ids'])):raise ValueError('Explicitly exclude every observed transverse edge beam; no inferred two-way sharing')
 if sorted(q['excluded_attachment_ids'])!=g['required_excluded_attachment_ids'] or len(q['excluded_attachment_ids'])!=len(set(q['excluded_attachment_ids'])):raise ValueError('Explicitly exclude all observed stair attachments and their transmitted loads; stairs are not slab openings')
 pressure=q['intensity_kn_m2'];strips=[{**s,'line_load_kn_m':pressure*s['width_m'],'transferred_kn':pressure*s['area_m2']} for s in g['strips']]
 applied=pressure*g['area_m2'];total=sum(s['line_load_kn_m']*s['length_m'] for s in strips)
 if not math.isclose(applied,total,rel_tol=1e-12,abs_tol=1e-10):raise ValueError('Slab load conservation failed')
 return {**g,'strips':strips,'loading':q,'applied_kn':applied,'transferred_kn':total,'conservation_error_kn':total-applied,'formulas':['A = L × W (m²)','b = support spacing/2 + equal edge overhang = W/2 (m)','q = p × b (kN/m)','P = p × A = Σ(q × L) (kN)'],'engineering_approval':'DISABLED','code_checks':'DISABLED','idealization':'Symmetric uniform one-way strips with two simple vertical support lines and equal free edge overhangs. Vertical load allocation only: no transferred slab support moment/torsion; no slab stiffness or capacity model.'}

def graphs(doc,inputs):
 q=Inputs.model_validate(inputs).model_dump();t=transfer(doc,q);outputs=[];used=[]
 for s in t['strips']:
  matches=[f for f in q['frames'] if s['beam_id'] in f['component_ids']]
  if len(matches)!=1:raise ValueError('Exactly one explicit three-member frame per support beam required')
  f=matches[0];payload={**f,'purpose':'VERIFICATION_ONLY','load_cases':[dict(name='Slab tributary',source=q['source'],beam_uniform_n_per_m=-s['line_load_kn_m']*1000)]}
  if not all(j['idealization_approved'] for j in f['connections']):raise ValueError('Explicit approval of every declared analytical joint required')
  g=frame.graph(doc,payload)
  if g['members'][1]['component_id']!=s['beam_id']:raise ValueError('Selected support must be the actual frame beam')
  used.extend(g['component_ids']);outputs.append(dict(beam_id=s['beam_id'],inputs=payload,graph=g))
 if len(used)!=len(set(used)):raise ValueError('Frames must be separate; shared columns or whole-assembly analysis unsupported')
 return t,outputs

def beam_reference(payload,section,L,wy):
 """Real fixed-fixed beam under the transferred UDL, independently checked closed form."""
 b=section
 q={**elastic.fixture('cantilever'),'kind':'fixed_beam','length_m':L,'elastic_modulus_pa':b['elastic_modulus_pa'],'area_m2':b['area_m2'],'inertia_m4':b['inertia_m4'],'material_source':b['material_source'],'section_source':b['section_source'],'load_n':0,'load_source':payload['load_cases'][0]['source'],'elements_per_member':2,'units':payload['units']}
 r=elastic.run(q,verification_loads={},verification_uniform={1:[0,wy]});h=gravity.fixed_beam_hand(q,wy)
 if r['status']!='VERIFIED':raise ValueError('Transferred-load beam reference failed')
 samples=[s for e in r['elements'] for s in e['samples']];EI=q['elastic_modulus_pa']*q['inertia_m4'];errors=[]
 for s in samples:
  x=s['position_m'][0];expect=[wy*x*x*(L-x)**2/(24*EI),-wy*L/2+wy*x,wy*L*L/12-wy*L*x/2+wy*x*x/2];actual=[s['displacement_m'][1],s['shear_n'],s['moment_nm']]
  if not all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-6) for a,b in zip(actual,expect)):raise ValueError('Transferred-load beam hand check failed')
  errors.extend(abs(a-b) for a,b in zip(actual,expect))
 for a in r['reactions']:
  if not math.isclose(a['fy_n'],h['reaction_y_n'],abs_tol=1e-6):raise ValueError('Reference reaction check failed')
 return dict(status='VERIFIED',hand=h,solver=r,max_sample_error_m_n_nm=max(errors),scope='Independent fixed-fixed beam verification with the same L, E, I and transferred pressure; not the portal boundary condition')

def independent_load_path_equilibrium(doc,q,results):
 # Separate global statics from raw slab geometry and actual column-base coordinates.
 import numpy as np
 by={c['id']:c for c in doc['components']};slab=by[q['slab_id']];size=slab['geometry']['size'];center=np.array(slab['transform']['position'],dtype=float)
 P=q['intensity_kn_m2']*1000*size[0]*size[1];F=np.array([0.,0.,-P]);M=np.cross(center,F);bases=[]
 for item in results:
  r=item['result'];g=r['physical_to_analytical_graph']
  for reaction in r['reactions']:
   member=next(m for m in g['members'] if m['node_ids'][0]==reaction['node']);c=by[member['component_id']];p=np.array(c['transform']['position'],dtype=float);p[2]-=c['geometry']['size'][2]/2
   f=np.array([reaction['fx_n'],0.,reaction['fy_n']]);moment=np.array([0.,-reaction['moment_nm'],0.]);F+=f;M+=np.cross(p,f)+moment
   bases.append(dict(component_id=c['id'],position_enu_m=p.tolist(),force_enu_n=f.tolist(),moment_enu_nm=moment.tolist()))
 return dict(passed=bool(max(map(abs,F))<1e-5 and max(map(abs,M))<1e-5),force_residual_enu_n=F.tolist(),moment_residual_enu_nm=M.tolist(),bases=bases,applied_pressure_resultant_n=P,pressure_centroid_enu_m=center.tolist(),method='Independent full-slab uniform-pressure resultant pLW at the saved centroid; sum actual base forces and r cross F plus base couples in saved ENU. Analytical positive rotation is about -North. Global statics only, not 3D stiffness or slab shell analysis.')

def run(doc,inputs):
 t,gs=graphs(doc,inputs);results=[];references=[]
 for f in gs:
  q=f['inputs'];beam_id=f['beam_id'];b=next(s for s in q['sections'] if s['component_id']==beam_id)
  references.append(beam_reference(q,b,t['size_m'][0],-next(s['line_load_kn_m'] for s in t['strips'] if s['beam_id']==beam_id)*1000))
  r=frame.run(q,doc)
  if r['status']!='VERIFIED':raise ValueError('Physical supporting frame verification failed')
  results.append(dict(beam_id=beam_id,result=r))
 reaction=sum(a['fy_n'] for f in results for a in f['result']['reactions'])/1000
 if not math.isclose(reaction,t['applied_kn'],rel_tol=1e-8,abs_tol=1e-6):raise ValueError('Frame reactions do not balance slab pressure')
 equilibrium=independent_load_path_equilibrium(doc,inputs,results)
 if not equilibrium['passed']:raise ValueError('Independent complete load-path force/moment equilibrium failed')
 return dict(status='VERIFIED',load_path_equilibrium=equilibrium,method_version='cad-slab-unequal/1' if doc.get('metadata',{}).get('cad_slab_path_review') else 'slab-transfer/1',self_weight_included=False,load_accounting='Imposed slab pressure only. Member and slab self-weight excluded; do not duplicate this pressure as an additional frame load.',transfer=t,frames=results,beam_references=references,reaction_total_kn=reaction,reaction_balance_error_kn=reaction-t['applied_kn'],inputs=Inputs.model_validate(inputs).model_dump(),limitations=LIMITS,engineering_approval='DISABLED',code_checks='DISABLED')
