"""Bounded 2D Euler-Bernoulli verification models; no code design or approval."""
import json,math,os,subprocess,hashlib
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal
from app.services.design import opensees_benchmark as solver

class Inputs(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 kind:Literal['cantilever','portal','fixed_beam']
 length_m:float=Field(gt=0,le=50)
 height_m:float=Field(gt=0,le=50)
 elastic_modulus_pa:float=Field(gt=1e6,le=1e13)
 area_m2:float=Field(gt=1e-6,le=10)
 inertia_m4:float=Field(gt=1e-10,le=10)
 load_n:float=Field(ge=0,le=1e7)
 material_source:str=Field(min_length=5,max_length=300)
 section_source:str=Field(min_length=5,max_length=300)
 load_source:str=Field(min_length=5,max_length=300)
 joints:Literal['rigid']
 restraints:Literal['fixed_base']
 purpose:Literal['VERIFICATION_ONLY']
 elements_per_member:Literal[1,2,4]
 units:Literal['SI','N-mm']

FILES=('model.tcl','nodes.tsv','forces.tsv','reactions.tsv','summary.tsv','stdout.txt','stderr.txt','manifest.json')
LIMITS=['2D small-displacement linear Euler-Bernoulli elasticity only','No shear deformation, geometric stiffness, buckling, nonlinear or dynamic analysis','Rigid joints and fixed bases are explicit verification assumptions','No actual platform-wide mapping, foundation or connection capacity analysis','IS/US design checks and engineering approval disabled']

def verify_saved_geometry(document,geo):
 if document.get('units')!='metric' or document.get('metadata',{}).get('frame')!='local_enu_meters':raise ValueError('Explicit metric local ENU geometry required')
 L,H=geo['length_m'],geo['height_m']
 expected=[([L/2,0,0],0,L,'beam')] if geo['kind']=='cantilever' else [([0,0,H/2],2,H,'column'),([L/2,0,H],0,L,'beam'),([L,0,H/2],2,H,'column')]
 components=document['components']
 if len(components)!=len(expected):raise ValueError('Only the dedicated verification members may be present')
 for c,(position,axis,length,category) in zip(components,expected):
  t=c['transform'];size=c['geometry'].get('size',[])
  if c['category']!=category or c['geometry'].get('kind')!='box' or len(size)!=3 or any(v<=0 for v in size):raise ValueError('Unsupported saved member geometry')
  if c.get('parent_id') is not None or t.get('rotation_deg')!=[0,0,0] or t.get('scale')!=[1,1,1]:raise ValueError('Only unrotated independent verification centerlines supported')
  if any(not math.isclose(a,b,abs_tol=1e-7,rel_tol=0) for a,b in zip(t['position'],position)) or not math.isclose(size[axis],length,abs_tol=1e-7,rel_tol=0):raise ValueError('Saved member endpoints do not match declared benchmark joints; update a supported model before analysis')
 return components

def mesh(q):
 n=q['elements_per_member'];L=q['length_m'];H=q['height_m']
 single=q['kind']!='portal'
 corners={1:(0,0),2:(L,0)} if single else {1:(0,0),2:(0,H),3:(L,H),4:(L,0)}
 if q.get('_assembly',{}).get('node_positions_m') is not None:
  positions=q['_assembly']['node_positions_m']
  if single or len(positions)!=4:raise ValueError('Exactly four retained nodes required for a saved portal')
  corners={i:tuple(xy) for i,xy in enumerate(positions,1)}
 members=[(1,2)] if single else [(1,2),(2,3),(4,3)]
 offsets=q.get('_verification_offsets') or (q.get('_assembly') or {}).get('beam_offsets_m')
 if q.get('_verification_offsets') is not None:corners[2]=(L-offsets[1][0],-offsets[1][1])
 nodes=dict(corners);elements=[]
 for m,(a,b) in enumerate(members):
  previous=a
  offset_pair=offsets if offsets is not None and (q['kind']=='cantilever' or m==1) else [[0,0],[0,0]]
  physical_a=np.array(corners[a])+np.array(offset_pair[0]);physical_b=np.array(corners[b])+np.array(offset_pair[1])
  for j in range(1,n+1):
   current=b if j==n else len(nodes)+1
   if j!=n:nodes[current]=tuple((physical_a+(physical_b-physical_a)*j/n).tolist())
   element=dict(id=len(elements)+1,i=previous,j=current,member=m+1)
   if offsets is not None:element.update(offset_i_m=offset_pair[0] if j==1 else [0,0],offset_j_m=offset_pair[1] if j==n else [0,0])
   if q.get('_assembly'):element.update(component_id=q['_assembly']['members'][m]['component_id'],section=q['_assembly']['members'][m]['section'])
   if q.get('_uniform_global_by_member'):element['uniform_global_n_per_m']=q['_uniform_global_by_member'].get(m+1,[0.,0.])
   elements.append(element);previous=current
 loads=q['_verification_loads'] if '_verification_loads' in q else ({2:(0,-q['load_n'],0)} if single else {2:(q['load_n']/2,0,0),3:(q['load_n']/2,0,0)})
 return nodes,elements,([1,2] if q['kind']=='fixed_beam' else [1] if single else [1,4]),loads

def uniform_local(nodes,e):
 a,b=endpoint_geometry(nodes,e);L=float(np.linalg.norm(b-a));c,s=(b-a)/L;gx,gy=e.get('uniform_global_n_per_m',[0.,0.])
 return L,c*gx+s*gy,-s*gx+c*gy

def consistent_load(nodes,e):
 L,qx,qy=uniform_local(nodes,e)
 return np.array([qx*L/2,qy*L/2,qy*L*L/12,qx*L/2,qy*L/2,-qy*L*L/12])

def endpoint_geometry(nodes,e):
 return np.array(nodes[e['i']])+np.array(e.get('offset_i_m',[0,0])),np.array(nodes[e['j']])+np.array(e.get('offset_j_m',[0,0]))

def offset_operator(e):
 B=np.eye(6)
 for k,key in ((0,'offset_i_m'),(3,'offset_j_m')):
  rx,ry=e.get(key,[0,0]);B[k,k+2]=-ry;B[k+1,k+2]=rx
 return B

def endpoint_displacement(u,r):
 return [u[0]-r[1]*u[2],u[1]+r[0]*u[2],u[2]]

def reference(q):
 # Independent SI matrix formulation; no OpenSees output or TCL used.
 nodes,els,fixed,loads=mesh(q);ids=sorted(nodes);K=np.zeros((3*len(ids),3*len(ids)));F=np.zeros(3*len(ids));operators=[]
 for tag,load in loads.items():F[3*ids.index(tag):3*ids.index(tag)+3]=load
 for e in els:
  a,b=endpoint_geometry(nodes,e);length=float(np.linalg.norm(b-a));c,s=(b-a)/length
  section=e.get("section",q);A=section['elastic_modulus_pa']*section['area_m2']/length;B=section['elastic_modulus_pa']*section['inertia_m4']
  v=12*B/length**3;w=6*B/length**2;r=4*B/length;t=2*B/length
  k=np.array([[A,0,0,-A,0,0],[0,v,w,0,-v,w],[0,w,r,0,-w,t],[-A,0,0,A,0,0],[0,-v,-w,0,v,-w],[0,w,t,0,-w,r]])
  T=np.array([[c,s,0,0,0,0],[-s,c,0,0,0,0],[0,0,1,0,0,0],[0,0,0,c,s,0],[0,0,0,-s,c,0],[0,0,0,0,0,1]])
  T=T@offset_operator(e)
  dofs=[3*ids.index(tag)+d for tag in (e['i'],e['j']) for d in range(3)];K[np.ix_(dofs,dofs)]+=T.T@k@T;fe=consistent_load(nodes,e);F[dofs]+=T.T@fe;operators.append((e,k,T,dofs,fe))
 free=[i for i in range(len(F)) if ids[i//3] not in fixed];u=np.zeros(len(F));u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]);R=K@u-F
 return dict(nodes={tag:u[3*j:3*j+3].tolist() for j,tag in enumerate(ids)},reactions={tag:R[3*ids.index(tag):3*ids.index(tag)+3].tolist() for tag in fixed},forces={e['id']:(k@T@u[dofs]-fe).tolist() for e,k,T,dofs,fe in operators},stiffness_si=K.tolist(),load_vector_si=F.tolist(),formulation='Independent 2D EA/L and EI Euler-Bernoulli 6x6 stiffness, consistent uniform loads [qxL/2,qyL/2,qyL²/12,qxL/2,qyL/2,-qyL²/12], rigid-arm transformed assembly; Kff uf=Ff, R=Ku-F, end forces=k ulocal-fe')

def model_text(q):
 nodes,els,fixed,loads=mesh(q);s=1 if q['units']=='SI' else 1000
 lines=['# GeoAI bounded elastic verification model; no design approval',f'# units {q["units"]}; X=East, Y=Up, rotation positive counterclockwise','wipe','model BasicBuilder -ndm 2 -ndf 3','geomTransf Linear 1']
 lines += [f'node {i} {x*s:.17g} {y*s:.17g}' for i,(x,y) in nodes.items()]
 lines += [f'fix {i} 1 1 1' for i in fixed]
 for e in els:
  if any(e.get('offset_i_m',[0,0])+e.get('offset_j_m',[0,0])):
   values=e.get('offset_i_m',[0,0])+e.get('offset_j_m',[0,0]);lines.append(f'geomTransf Linear {100+e["id"]} -jntOffset '+ ' '.join(f'{v*s:.17g}' for v in values))
 lines += [f'element elasticBeamColumn {e["id"]} {e["i"]} {e["j"]} {e.get("section",q)["area_m2"]*s*s:.17g} {e.get("section",q)["elastic_modulus_pa"]/(s*s):.17g} {e.get("section",q)["inertia_m4"]*s**4:.17g} {100+e["id"] if any(e.get("offset_i_m",[0,0])+e.get("offset_j_m",[0,0])) else 1}' for e in els]
 lines += ['timeSeries Linear 1','pattern Plain 1 1 {']+[f'load {i} {f[0]:.17g} {f[1]:.17g} {f[2]*s:.17g}' for i,f in loads.items()]+[f'eleLoad -ele {e["id"]} -type -beamUniform {uniform_local(nodes,e)[2]/s:.17g} {uniform_local(nodes,e)[1]/s:.17g}' for e in els if any(e.get('uniform_global_n_per_m',[0,0]))]+['}','constraints Plain','numberer Plain','system BandGeneral','test NormUnbalance 1e-8 10','algorithm Linear','integrator LoadControl 1','analysis Static','set rc [analyze 1]','set f [open summary.tsv w]','puts $f "version\t[version]"','puts $f "convergence\t$rc"','close $f','if {$rc != 0} {exit 2}','reactions','set f [open nodes.tsv w]']
 lines += [f'puts $f "{i}\t[format %.17g [nodeDisp {i} 1]]\t[format %.17g [nodeDisp {i} 2]]\t[format %.17g [nodeDisp {i} 3]]"' for i in sorted(nodes)]
 lines += ['close $f','set f [open reactions.tsv w]']+[f'puts $f "{i}\t[format %.17g [nodeReaction {i} 1]]\t[format %.17g [nodeReaction {i} 2]]\t[format %.17g [nodeReaction {i} 3]]"' for i in fixed]
 lines += ['close $f','set f [open forces.tsv w]']
 for e in els:
  lines += [f'set v [eleResponse {e["id"]} localForce]',f'puts $f "{e["id"]}\t[join [lmap x $v {{format %.17g $x}}] \t]"']
 return '\n'.join(lines+['close $f','wipe','exit 0',''])

def run(inputs, *, assembly_graph=None, verification_offsets=None, verification_loads=None, verification_uniform=None):
 q=Inputs.model_validate(inputs).model_dump()
 if q['load_n']==0 and verification_loads is None:raise ValueError('Explicit loads required; no inferred default load')
 if q['kind']=='fixed_beam' and q['elements_per_member']==1:raise ValueError('Fixed-fixed benchmark requires at least two elements: one fully restrained element has no free solver degrees of freedom')
 if assembly_graph is not None:q["_assembly"]=assembly_graph
 if verification_offsets is not None:q["_verification_offsets"]=verification_offsets
 if verification_loads is not None:q["_verification_loads"]=verification_loads
 if verification_uniform is not None:q["_uniform_global_by_member"]=verification_uniform
 ref=reference(q);nodes,els,fixed,loads=mesh(q)
 if max(math.hypot(*u[:2]) for u in ref['nodes'].values())>.05*min(q['length_m'],q['height_m']):raise ValueError('Displacements outside bounded small-displacement verification domain')
 for e in els:
  L,qx,qy=uniform_local(nodes,e);a,b=endpoint_geometry(nodes,e);axis=(b-a)/L;normal=np.array([-axis[1],axis[0]]);ui=endpoint_displacement(ref['nodes'][e['i']],e.get('offset_i_m',[0,0]));uj=endpoint_displacement(ref['nodes'][e['j']],e.get('offset_j_m',[0,0]));section=e.get('section',q);EA=section['elastic_modulus_pa']*section['area_m2'];EI=section['elastic_modulus_pa']*section['inertia_m4']
  for t in (.25,.5,.75):
   x=L*t;axial=(1-t)*np.dot(ui[:2],axis)+t*np.dot(uj[:2],axis)+qx*x*(L-x)/(2*EA);transverse=(1-3*t*t+2*t**3)*np.dot(ui[:2],normal)+L*(t-2*t*t+t**3)*ui[2]+(3*t*t-2*t**3)*np.dot(uj[:2],normal)+L*(-t*t+t**3)*uj[2]+qy*x*x*(L-x)**2/(24*EI)
   if math.hypot(axial,transverse)>.05*min(q['length_m'],q['height_m']):raise ValueError('Uniform-load interior displacement outside bounded small-displacement domain')
 if any(any(e.get('offset_i_m',[0,0])+e.get('offset_j_m',[0,0])) for e in els):
  if max(abs(u[2]) for u in ref['nodes'].values())>.05 or any(math.hypot(*endpoint_displacement(ref['nodes'][e[key]],e.get(offset,[0,0]))[:2])>.05*min(q['length_m'],q['height_m']) for e in els for key,offset in (('i','offset_i_m'),('j','offset_j_m'))):raise ValueError('Rigid-offset endpoint displacement or rotation outside validated small-displacement domain')
 folder=solver.ARTIFACTS/str(uuid4());folder.mkdir(parents=True);text=model_text(q);(folder/'model.tcl').write_text(text,encoding='utf-8',newline='\n')
 result=dict(run_id=folder.name,timestamp=datetime.now(timezone.utc).isoformat(),inputs=q,inputs_sha256=solver.digest(q),solver=solver.provenance(),canonical_input_text_sha256=hashlib.sha256(text.encode()).hexdigest(),input_file_sha256=hashlib.sha256((folder/'model.tcl').read_bytes()).hexdigest(),status='FAILED',engineering_approval='DISABLED',code_checks='DISABLED',limitations=LIMITS)
 try:
  proc=subprocess.run([result['solver']['executable'],'model.tcl'],cwd=folder,capture_output=True,text=True,timeout=20,shell=False,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
  for name in ('stdout','stderr'):(folder/f'{name}.txt').write_text(getattr(proc,name))
  result['exit_code']=proc.returncode
  if proc.returncode:raise ValueError('OpenSees nonzero exit; inspect retained stderr')
  summary=dict(line.split('\t') for line in (folder/'summary.tsv').read_text().splitlines())
  if summary['convergence']!='0':raise ValueError('OpenSees did not converge')
  def rows(filename,width):
   r=[[float(v) for v in line.split()] for line in (folder/filename).read_text().splitlines()]
   if any(len(x)!=width or any(not math.isfinite(v) for v in x) for x in r):raise ValueError('Malformed or nonfinite output')
   return {int(x[0]):x[1:] for x in r}
  disps=rows('nodes.tsv',4);reactions=rows('reactions.tsv',4);forces=rows('forces.tsv',7);s=1 if q['units']=='SI' else 1000
  if set(disps)!=set(nodes) or set(reactions)!=set(fixed) or set(forces)!={e['id'] for e in els}:raise ValueError('Unexpected solver identities')
  disps={i:[u[0]/s,u[1]/s,u[2]] for i,u in disps.items()};reactions={i:[r[0],r[1],r[2]/s] for i,r in reactions.items()};forces={i:[v/s if j in (2,5) else v for j,v in enumerate(f)] for i,f in forces.items()}
  comparisons={}
  for name,actual in [('nodes',disps),('reactions',reactions),('forces',forces)]:
   errors=[abs(v-ref[name][i][j]) for i,values in actual.items() for j,v in enumerate(values)];passed=all(math.isclose(v,ref[name][i][j],rel_tol=1e-7,abs_tol=1e-7 if name!='nodes' else 1e-10) for i,values in actual.items() for j,v in enumerate(values));comparisons[name]=dict(max_absolute_error=max(errors),passed=passed)
  residual=[sum(r[k] for r in reactions.values())+sum(f[k] for f in loads.values()) for k in (0,1)]
  residual.append(sum(r[2]+nodes[i][0]*r[1]-nodes[i][1]*r[0] for i,r in reactions.items())+sum(f[2]+nodes[i][0]*f[1]-nodes[i][1]*f[0] for i,f in loads.items()))
  for e in els:
   a,b=endpoint_geometry(nodes,e);L=float(np.linalg.norm(b-a));gx,gy=e.get('uniform_global_n_per_m',[0,0]);center=(a+b)/2
   residual[0]+=gx*L;residual[1]+=gy*L;residual[2]+=(center[0]*gy-center[1]*gx)*L
  if q['kind']=='cantilever' and verification_offsets is None and verification_uniform is None and verification_loads is None:
   expected=-q['load_n']*q['length_m']**3/(3*q['elastic_modulus_pa']*q['inertia_m4']);comparisons['closed_form_tip']=dict(computed=disps[2][1],reference=expected,passed=math.isclose(disps[2][1],expected,rel_tol=1e-8));ref['closed_form']={'tip_displacement':'-P L^3 / (3 E I)','tip_rotation':'-P L^2 / (2 E I)','base_shear':'P','base_moment':'P L','tip_displacement_m':expected}
  joint_balance={i:np.zeros(3) for i in nodes};transfers=[]
  for e in els:
   a,b=endpoint_geometry(nodes,e);direction=b-a;c,ss=direction/np.linalg.norm(direction);f=forces[e['id']]
   for tag,k,key in ((e['i'],0,'offset_i_m'),(e['j'],3,'offset_j_m')):
    fx,fy=c*f[k]-ss*f[k+1],ss*f[k]+c*f[k+1];rx,ry=e.get(key,[0,0]);couple=rx*fy-ry*fx;joint_balance[tag]+=np.array([fx,fy,f[k+2]+couple])
    if rx or ry:transfers.append(dict(element_id=e['id'],component_id=e.get('component_id'),node=tag,offset_m=[rx,ry],physical_end_global_force_si=[float(fx),float(fy),f[k+2]],offset_moment_nm=float(couple),retained_node_global_force_si=[float(fx),float(fy),float(f[k+2]+couple)],physical_end_displacement_si=endpoint_displacement(disps[tag],[rx,ry])))
  for tag in nodes:
   joint_balance[tag]-=np.array(loads.get(tag,(0,0,0)))
   joint_balance[tag]-=np.array(reactions.get(tag,(0,0,0)))
  joint_error=float(max(abs(v) for values in joint_balance.values() for v in values))
  comparisons['joint_equilibrium']=dict(max_absolute_error=joint_error,passed=joint_error<=1e-4)
  if not all(c['passed'] for c in comparisons.values()) or max(abs(v) for v in residual)>1e-4:raise ValueError('Independent nodal/force/reaction/equilibrium verification failed')
  # Hermite interpolation uses actual solver rotations/displacements; diagrams use actual local end forces.
  curves=[]
  for e in els:
   a,b=endpoint_geometry(nodes,e);length=float(np.linalg.norm(b-a));axis=(b-a)/length;normal=np.array([-axis[1],axis[0]]);ui=endpoint_displacement(disps[e['i']],e.get('offset_i_m',[0,0]));uj=endpoint_displacement(disps[e['j']],e.get('offset_j_m',[0,0]));vi=np.dot(ui[:2],normal);vj=np.dot(uj[:2],normal);ai=np.dot(ui[:2],axis);aj=np.dot(uj[:2],axis);f=forces[e['id']];samples=[];_,qx,qy=uniform_local(nodes,e);section=e.get('section',q);EA=section['elastic_modulus_pa']*section['area_m2'];EI=section['elastic_modulus_pa']*section['inertia_m4']
   for t in np.linspace(0,1,17):
    xy=a+t*(b-a);du=((1-t)*ai+t*aj)*axis+((1-3*t*t+2*t**3)*vi+length*(t-2*t*t+t**3)*ui[2]+(3*t*t-2*t**3)*vj+length*(-t*t+t**3)*uj[2])*normal
    x=length*t;du+=qx*x*(length-x)/(2*EA)*axis+qy*x*x*(length-x)**2/(24*EI)*normal
    samples.append(dict(position_m=xy.tolist(),displacement_m=du.tolist(),moment_nm=float(-f[2]+f[1]*x+qy*x*x/2),shear_n=float(f[1]+qy*x),axial_n=float(-f[0]-qx*x)))
   curves.append({**e,'local_end_forces_si':f,'samples':samples})
  result.update(status='VERIFIED',verified=True,solver_version=summary['version'],convergence_code=0,nodes=[dict(id=i,position_m=list(nodes[i]),displacement_m=disps[i]) for i in sorted(nodes)],elements=curves,reactions=[dict(node=i,fx_n=r[0],fy_n=r[1],moment_nm=r[2]) for i,r in reactions.items()],rigid_offset_transfers=transfers,joint_equilibrium_residuals_si={i:v.tolist() for i,v in joint_balance.items()},equilibrium_residual_si=residual,comparisons=comparisons,independent_reference=ref)
 except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:
  result['error']=str(error)
  for name in ('stdout','stderr'):
   path=folder/f'{name}.txt'
   if not path.exists():
    captured=getattr(error,name,None) or ''
    if isinstance(captured,bytes):captured=captured.decode(errors='replace')
    path.write_text(captured)
 result['artifact_sha256']={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in FILES[:-1] if (folder/name).exists()};(folder/'manifest.json').write_text(json.dumps(result,indent=2));return result

def fixture(kind):
 return dict(kind=kind,length_m=3 if kind=='cantilever' else 4,height_m=3,elastic_modulus_pa=200e9,area_m2=.01 if kind=='cantilever' else .02,inertia_m4=8e-6 if kind=='cantilever' else 8e-5,load_n=1000 if kind=='cantilever' else 20000,material_source='Explicit synthetic elastic verification material',section_source='Explicit synthetic A and Iz; not actual project sections',load_source='Synthetic tip load downward' if kind=='cantilever' else 'Synthetic equal horizontal top-joint loads',joints='rigid',restraints='fixed_base',purpose='VERIFICATION_ONLY',elements_per_member=2,units='SI')

def suite(kind):
 # Beam MUST pass before any portal verification.
 cases=[run({**fixture('cantilever'), 'elements_per_member':n}) for n in (1,2,4)]
 if any(r['status']!='VERIFIED' for r in cases):raise ValueError('Beam prerequisite failed; portal disabled')
 if kind=='portal':cases += [run({**fixture('portal'),'elements_per_member':n}) for n in (1,2,4)]
 cases += [run({**fixture(kind),'units':'N-mm'}),run({**fixture(kind),'load_n':fixture(kind)['load_n']*.5})]
 return dict(status='VERIFIED' if all(r['status']=='VERIFIED' for r in cases) else 'FAILED',cases=cases)

