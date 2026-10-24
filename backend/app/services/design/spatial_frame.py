"""Bounded linear spatial-frame verification. ENU, N, m, rad; no design approval.

OpenSees elasticBeamColumn is checked against a separately assembled 12-DOF
Euler-Bernoulli stiffness system. Slabs are reviewed one-way load allocators,
never plate elements or diaphragms. No geometry is inferred from proximity.
"""
import json
import math
import subprocess
from pathlib import Path
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from app.services.design import opensees_benchmark as common

ARTIFACTS = (common.ARTIFACT_ROOT / 'spatial-frame') if common.ARTIFACT_ROOT else common.ROOT / 'backend/storage/spatial-frame'
LIMITS = ['Linear small-displacement elastic 3D frame only; no safety or code approval.',
 'Rigid coincident centreline joints are explicit idealizations; connection capacity unverified.',
 'No releases, rigid offsets, cracked stiffness, P-delta, buckling, dynamics or nonlinear materials.',
 'Slabs: one-way uniform tributary loading only; no plate stress, slab stiffness or diaphragm.',
 'Fixed bases are prescribed restraints; foundation flexibility and soil transfer not verified.',
 'Declared synthetic section torsion J is an input, not a rectangular-section design calculation.']
REFERENCES = ['https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/elasticBeamColumn.html',
 'https://opensees.github.io/OpenSeesDocumentation/user/manual/model/geomTransf/Linear.html']

class Strict(BaseModel):
 model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class Node(Strict):
 id:int=Field(gt=0,le=1000)
 position:tuple[float,float,float]
 fixed:bool=False
class Member(Strict):
 id:str=Field(min_length=1,max_length=100)
 nodes:tuple[int,int]
 floor:int=Field(ge=1,le=3)
 kind:Literal['beam','column']
 vecxz:tuple[float,float,float]
 E:float=Field(gt=1e6,le=1e12)
 G:float=Field(gt=1e6,le=1e12)
 A:float=Field(gt=1e-5,le=10)
 Iy:float=Field(gt=1e-9,le=10)
 Iz:float=Field(gt=1e-9,le=10)
 J:float=Field(gt=1e-9,le=10)
class Slab(Strict):
 id:str
 floor:int=Field(ge=1,le=3)
 beams:tuple[str,str]
 width_m:float=Field(gt=0,le=20)
 pressure_pa:float=Field(ge=0,le=20000)
class Case(Strict):
 name:str=Field(min_length=1,max_length=60)
 nodal:dict[int,tuple[float,float,float,float,float,float]]=Field(default_factory=dict)
 slab_factor:float=Field(ge=0,le=2)
class Inputs(Strict):
 nodes:list[Node]=Field(min_length=2,max_length=80)
 members:list[Member]=Field(min_length=1,max_length=150)
 slabs:list[Slab]=Field(default_factory=list,max_length=12)
 cases:list[Case]=Field(min_length=1,max_length=4)
 connection_review:Literal['rigid_coincident_joints_reviewed']
 section_source:str=Field(min_length=20,max_length=1000)
 purpose:Literal['SYNTHETIC_VERIFICATION_ONLY']

def basis(a,b,v):
 x=np.array(b,dtype=float)-a;L=float(np.linalg.norm(x))
 if not 0.1<=L<=30:raise ValueError('Member length outside 0.1–30 m')
 x/=L;y=np.cross(v,x);n=np.linalg.norm(y)
 if n<1e-8:raise ValueError('Local orientation parallel to member')
 y/=n;return L,np.array([x,y,np.cross(x,y)])

def validate(q,doc=None):
 q=Inputs.model_validate(q).model_dump()
 nodes={n['id']:n for n in q['nodes']};members={m['id']:m for m in q['members']}
 if len(nodes)!=len(q['nodes']) or len(members)!=len(q['members']):raise ValueError('Duplicate identity')
 if any(max(map(abs,n['position']))>1000 for n in nodes.values()):raise ValueError('Local review coordinates must be within 1000 m')
 if len({tuple(n['position']) for n in nodes.values()})!=len(nodes):raise ValueError('Coincident duplicate nodes require explicit consolidation')
 if not any(n['fixed'] for n in nodes.values()):raise ValueError('Fixed base required')
 connected={i:set() for i in nodes};edges=set()
 for m in members.values():
  i,j=m['nodes']
  if i not in nodes or j not in nodes or i==j:raise ValueError('Invalid connectivity')
  edge=tuple(sorted((i,j)))
  if max(map(abs,m['vecxz']))>1000:raise ValueError('Orientation vector outside supported numeric range')
  if edge in edges:raise ValueError('Duplicate member connectivity')
  edges.add(edge);connected[i].add(j);connected[j].add(i)
  basis(nodes[i]['position'],nodes[j]['position'],m['vecxz'])
 reached={next(iter(nodes))};pending=list(reached)
 while pending:
  for i in connected[pending.pop()]-reached:reached.add(i);pending.append(i)
 if reached!=set(nodes):raise ValueError('Disconnected structural graph')
 if len({c['name'] for c in q['cases']})!=len(q['cases']):raise ValueError('Duplicate case name')
 for c in q['cases']:
  if any(i not in nodes or max(map(abs,f))>1e7 for i,f in c['nodal'].items()):raise ValueError('Unknown load node or excessive action')
 for s in q['slabs']:
  if len(set(s['beams']))!=2 or any(i not in members for i in s['beams']):raise ValueError('Slab needs two distinct supported beams')
  a,b=[members[i] for i in s['beams']]
  pa,pb=[np.array([nodes[i]['position'] for i in m['nodes']]) for m in (a,b)]
  da,db=pa[1]-pa[0],pb[1]-pb[0]
  if a['kind']!='beam' or b['kind']!='beam' or a['floor']!=s['floor'] or b['floor']!=s['floor'] or abs(da[2])+abs(db[2])+abs(pa[0,2]-pb[0,2])>1e-8 or not np.allclose(da,db):raise ValueError('Only parallel equal-span horizontal one-way support beams')
  offset=pb[0]-pa[0]
  if abs(np.dot(offset,da))>1e-8 or not math.isclose(float(np.linalg.norm(offset)),s['width_m'],abs_tol=1e-8):raise ValueError('Slab width or support alignment mismatch')
 if len({s['id'] for s in q['slabs']})!=len(q['slabs']):raise ValueError('Duplicate slab identity')
 if set(members)&{s['id'] for s in q['slabs']}:raise ValueError('Slab and member source identities must be distinct')
 if doc is not None:
  if doc.get('units')!='metric' or doc.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Saved metric ENU geometry required')
  components={c['id']:c for c in doc['components']}
  for m in members.values():
   c=components.get(m['id']);p=np.array([nodes[i]['position'] for i in m['nodes']]);axis=np.argmax(abs(p[1]-p[0]))
   if not c or c.get('parent_id') is not None or c['category']!=m['kind'] or c['geometry']['kind']!='box' or not np.allclose(c['transform']['position'],p.mean(axis=0)) or not np.allclose(c['transform']['rotation_deg'],[0,0,0]) or not np.allclose(c['transform']['scale'],[1,1,1]):raise ValueError('Saved geometry/source binding changed')
   size=c['geometry']['size'];length=np.linalg.norm(p[1]-p[0])
   if not math.isclose(size[axis],length,abs_tol=1e-8) or sum(abs(p[1]-p[0])>1e-8)!=1:raise ValueError('Only saved orthogonal centreline boxes supported')
   # Area/inertias are bound to the actual local section; J remains explicitly declared.
   _,R=basis(*p,m['vecxz'])
   if not np.allclose(abs(R),np.round(abs(R)),atol=1e-8):raise ValueError('Rolled local section axes do not match unrotated CAD boxes')
   sy=float(np.dot(abs(R[1]),size));sz=float(np.dot(abs(R[2]),size))
   if not all(math.isclose(a,b,rel_tol=1e-8) for a,b in [(m['A'],sy*sz),(m['Iy'],sy*sz**3/12),(m['Iz'],sz*sy**3/12)]):raise ValueError('Section area/inertia does not match saved geometry')
  for s in q['slabs']:
   c=components.get(s['id']);a,b=[members[i] for i in s['beams']];p=np.array([nodes[i]['position'] for m in (a,b) for i in m['nodes']]);size=np.ptp(p,axis=0)
   if not c or c.get('parent_id') is not None or c['category']!='slab' or c['geometry']['kind']!='box' or not np.allclose(c['transform']['position'][:2],p.mean(axis=0)[:2]) or not np.allclose(c['geometry']['size'][:2],size[:2]) or not math.isclose(c['transform']['position'][2],p[0,2],abs_tol=1e-8) or not np.allclose(c['transform']['rotation_deg'],[0,0,0]) or not np.allclose(c['transform']['scale'],[1,1,1]):raise ValueError('Saved slab geometry binding changed')
 return q

def stiffness(m,L):
 k=np.zeros((12,12))
 for ids,C in [([0,6],m['E']*m['A']/L),([3,9],m['G']*m['J']/L)]:k[np.ix_(ids,ids)]+=C*np.array([[1,-1],[-1,1]])
 for ids,I,sign in [([1,5,7,11],m['Iz'],1),([2,4,8,10],m['Iy'],-1)]:
  B=np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])*m['E']*I/L**3
  D=np.diag([1,sign,1,sign]);k[np.ix_(ids,ids)]+=D@B@D
 return k

def uniform(q,case):
 loads={m['id']:np.zeros(3) for m in q['members']}
 for s in q['slabs']:
  for bid in s['beams']:loads[bid][2]-=s['pressure_pa']*s['width_m']/2*case['slab_factor']
 return loads

def equivalent(w,L):
 x,y,z=w
 return np.array([x*L/2,y*L/2,z*L/2,0,-z*L*L/12,y*L*L/12,x*L/2,y*L/2,z*L/2,0,z*L*L/12,-y*L*L/12])

def reference(q,case):
 nodes=q['nodes'];index={n['id']:i for i,n in enumerate(nodes)};K=np.zeros((6*len(nodes),6*len(nodes)));P=np.zeros(len(K));elements=[];loads=uniform(q,case)
 for tag,f in case['nodal'].items():P[index[int(tag)]*6:index[int(tag)]*6+6]+=f
 for m in q['members']:
  a,b=[nodes[index[i]]['position'] for i in m['nodes']];L,R=basis(a,b,m['vecxz']);T=np.kron(np.eye(4),R);k=stiffness(m,L);f=equivalent(R@loads[m['id']],L);ids=[6*index[i]+d for i in m['nodes'] for d in range(6)]
  K[np.ix_(ids,ids)]+=T.T@k@T;P[ids]+=T.T@f;elements.append((m,L,R,T,k,f,ids))
 free=[6*i+d for i,n in enumerate(nodes) if not n['fixed'] for d in range(6)];u=np.zeros(len(K));matrix=K[np.ix_(free,free)]
 if not free or np.linalg.cond(matrix)>1e12:raise ValueError('Unstable or ill-conditioned frame; no result')
 u[free]=np.linalg.solve(matrix,P[free]);return u,K@u-P,elements

def solve(q,case,units='SI'):
 q=validate(q);case=Case.model_validate(case).model_dump();u,r,elements=reference(q,case)
 if units not in ('SI','N-mm'):raise ValueError('Unsupported units')
 s=1 if units=='SI' else 1000;run_id=str(uuid4());folder=ARTIFACTS/run_id;folder.mkdir(parents=True,exist_ok=False)
 fmt=lambda xs:' '.join(format(float(x),'.17g') for x in xs)
 lines=['wipe','model BasicBuilder -ndm 3 -ndf 6']
 for n in q['nodes']:
  lines.append(f"node {n['id']} {fmt(np.array(n['position'])*s)}")
  if n['fixed']:lines.append(f"fix {n['id']} 1 1 1 1 1 1")
 loads=uniform(q,case)
 for tag,(m,L,R,T,k,f,ids) in enumerate(elements,1):
  lines += [f"geomTransf Linear {tag} {fmt(m['vecxz'])}",f"element elasticBeamColumn {tag} {m['nodes'][0]} {m['nodes'][1]} {fmt([m['A']*s*s,m['E']/s**2,m['G']/s**2,m['J']*s**4,m['Iy']*s**4,m['Iz']*s**4])} {tag}"]
 lines+=['timeSeries Linear 1','pattern Plain 1 1 {']
 for tag,f in case['nodal'].items():lines.append(f'load {tag} {fmt(np.array(f)*[1,1,1,s,s,s])}')
 for tag,(m,L,R,*_) in enumerate(elements,1):
  w=R@loads[m['id']]/s
  if np.any(w):lines.append(f'eleLoad -ele {tag} -type -beamUniform {fmt([w[1],w[2],w[0]])}')
 lines+=['}','constraints Plain','numberer RCM','system BandGeneral','algorithm Linear','integrator LoadControl 1','analysis Static','if {[analyze 1] != 0} {exit 2}','reactions']
 for name,command,tags in [('nodes','nodeDisp',[n['id'] for n in q['nodes']]),('reactions','nodeReaction',[n['id'] for n in q['nodes']]),('forces','eleResponse',list(range(1,len(elements)+1)))]:
  lines.append(f'set out [open {name}.tsv w]')
  for tag in tags:lines.append(f'puts $out "{tag} [{command} {tag}{" localForce" if name=="forces" else ""}]"')
  lines.append('close $out')
 lines.append('exit 0');(folder/'model.tcl').write_text('\n'.join(lines));provenance=common.provenance()
 completed=subprocess.run([str(common.executable().resolve()),'model.tcl'],cwd=folder,capture_output=True,text=True,timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 for name,text in [('stdout.txt',completed.stdout),('stderr.txt',completed.stderr)]: (folder/name).write_text(text)
 if completed.returncode:raise RuntimeError('OpenSees failed; raw artifacts retained: '+run_id)
 read=lambda name:np.array([[float(v) for v in line.split()[1:]] for line in (folder/(name+'.tsv')).read_text().splitlines()])
 actual=read('nodes')/np.array([s,s,s,1,1,1]);reactions=read('reactions')/np.array([1,1,1,s,s,s]);forces=read('forces')/np.array([1,1,1,s,s,s]*2)
 checks={'displacement_max_abs':float(np.max(abs(actual.ravel()-u))),'reaction_max_abs':float(np.max(abs(reactions.ravel()-r))),'member_end_force_max_abs':0.0}
 members=[]
 for tag,(m,L,R,T,k,f,ids) in enumerate(elements):
  local=T@actual.ravel()[ids];ref=k@(T@u[ids])-f;F=forces[tag];checks['member_end_force_max_abs']=max(checks['member_end_force_max_abs'],float(np.max(abs(F-ref))))
  w=R@loads[m['id']];samples=[];a=np.array(q['nodes'][ids[0]//6]['position'])
  for t in np.linspace(0,1,17):
   x=L*t;h=np.array([1-3*t*t+2*t**3,L*(t-2*t*t+t**3),3*t*t-2*t**3,L*(-t*t+t**3)])
   dl=np.array([(1-t)*local[0]+t*local[6]+w[0]*x*(L-x)/(2*m['E']*m['A']),h@local[[1,5,7,11]]+w[1]*x*x*(L-x)**2/(24*m['E']*m['Iz']),h@(local[[2,4,8,10]]*[1,-1,1,-1])+w[2]*x*x*(L-x)**2/(24*m['E']*m['Iy'])])
   samples.append(dict(position=(a+R[0]*x).tolist(),displacement=(R.T@dl).tolist(),N=-F[0]-w[0]*x,Vy=F[1]+w[1]*x,Vz=F[2]+w[2]*x,My=F[4]+F[2]*x+w[2]*x*x/2,Mz=-F[5]+F[1]*x+w[1]*x*x/2,T=-F[3]))
  members.append(dict(**m,axes=R.tolist(),length_m=L,end_forces=F.tolist(),uniform_global_n_m=loads[m['id']].tolist(),samples=samples))
 total=np.zeros(6)
 for n,react in zip(q['nodes'],reactions):
  f=np.array(case['nodal'].get(n['id'],[0]*6))+react;total[:3]+=f[:3];total[3:]+=f[3:]+np.cross(n['position'],f[:3])
 for m in q['members']:
  a,b=[next(n['position'] for n in q['nodes'] if n['id']==i) for i in m['nodes']];F=loads[m['id']]*np.linalg.norm(np.array(b)-a);total[:3]+=F;total[3:]+=np.cross((np.array(a)+b)/2,F)
 checks['equilibrium_force_n']=float(np.max(abs(total[:3])));checks['equilibrium_moment_nm']=float(np.max(abs(total[3:])))
 scale=max(1,float(np.max(abs(r))),float(np.max(abs(forces))))
 verified=checks['displacement_max_abs']<1e-8 and max(v for k,v in checks.items() if k!='displacement_max_abs')<max(.001,scale*1e-7)
 result=dict(status='VERIFIED' if verified else 'VERIFICATION_FAILED',method='spatial-elastic-frame/1',units='N m rad; ENU',run_id=run_id,case=case,nodes=[dict(**n,displacement=actual[i].tolist(),reaction=reactions[i].tolist()) for i,n in enumerate(q['nodes'])],members=members,slabs=q['slabs'],comparisons=checks,independent_reference=dict(displacements=u.tolist(),reactions=r.tolist()),solver=provenance,limitations=LIMITS,references=REFERENCES,engineering_approval='DISABLED',code_checks='DISABLED')
 result['artifact_sha256']={p.name:__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()};(folder/'manifest.json').write_text(json.dumps(result,indent=2));return result

