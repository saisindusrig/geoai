"""Synthetic shell/frame research gate. Never upgrades an existing LOAD-ONLY floor.

Shell nodal resisting forces are recovered in global ENU and transferred, with
opposite sign, to a separately assembled frame. This is a substructure check,
not an independent shell solution. Plate accuracy requires separate benchmarks
and coupled mesh convergence. No stresses or connection capacities are inferred.
"""
import json
import subprocess
import hashlib
from uuid import uuid4
import numpy as np
from app.services.design import spatial_frame as frame, opensees_benchmark as common

ARTIFACTS = (common.ARTIFACT_ROOT / 'coupled-floor') if common.ARTIFACT_ROOT else common.ROOT / 'docs/coupled-floor/solver-evidence'
LIMITATIONS = [
 'Synthetic linear elastic, small-displacement research; no safety/code approval.',
 'Shell midsurface and beam centrelines coincide: zero offsets, full shared six-DOF compatibility.',
 'Uncracked isotropic elastic slab; no reinforcement, cracking, connection or punching capacity.',
 'Fixed column bases are mathematical restraints; no foundation/soil capacity.',
 'Gravity shell loading only; no tributary beam loads, self-weight or lateral load added.',
 'Independent frame check is conditional on native shell interface forces, not an independent coupled shell solution.',
 'Rigid diaphragm integration and two-storey extension remain disabled until separate gates pass.'
]

def model(mesh=4):
 """One 4×4 m panel, four 3 m columns and four subdivided edge beams.

 CCW shell quads, 160 mm plate; no duplicate coincident nodes or MPCs.
 Every shell edge node is an actual beam node. Columns meet the four corners.
 """
 if mesh not in (2,4,8,12,16): raise ValueError('Reviewed meshes only: 2, 4, 8, 12, 16')
 E=30e9;nu=.2;G=E/(2*(1+nu));section=dict(E=E,G=G,A=.3**2,Iy=.3**4/12,Iz=.3**4/12,J=.001)
 tag=lambda x,y:y*(mesh+1)+x+1
 nodes=[dict(id=tag(x,y),position=[4*x/mesh,4*y/mesh,3.],fixed=False) for y in range(mesh+1) for x in range(mesh+1)]
 boundary=[n for n in nodes if n['position'][0] in (0,4) or n['position'][1] in (0,4)]
 members=[]
 for side in range(4):
  ids=([tag(x,0) for x in range(mesh+1)] if side==0 else [tag(mesh,y) for y in range(mesh+1)] if side==1 else [tag(x,mesh) for x in range(mesh,-1,-1)] if side==2 else [tag(0,y) for y in range(mesh,-1,-1)])
  for i in range(mesh):members.append(dict(id=f'edge-{side}-{i}',nodes=ids[i:i+2],floor=1,kind='beam',vecxz=[0,0,1],**section))
 for i,(x,y) in enumerate([(0,0),(mesh,0),(mesh,mesh),(0,mesh)]):
  top=tag(x,y);base=900+i;n=dict(id=base,position=[4*x/mesh,4*y/mesh,0.],fixed=True);nodes.append(n);boundary.append(n)
  members.append(dict(id=f'column-{i}',nodes=[base,top],floor=1,kind='column',vecxz=[0,1,0],**section))
 quads=[dict(id=1000+y*mesh+x,nodes=[tag(x,y),tag(x+1,y),tag(x+1,y+1),tag(x,y+1)]) for y in range(mesh) for x in range(mesh)]
 q=frame.validate(dict(nodes=boundary,members=members,slabs=[],cases=[dict(name='Shell gravity only',nodal={},slab_factor=0)],connection_review='rigid_coincident_joints_reviewed',section_source='Synthetic 300 mm square uncracked frame; prescribed J=.001 m4; zero offsets.',purpose='SYNTHETIC_VERIFICATION_ONLY'))
 return dict(mesh=mesh,nodes=nodes,quads=quads,frame=q,E=E,nu=nu,thickness_m=.16,pressure_pa=-5000.,offset_m=0.,diaphragm=False,load_source='SHELL_CONSISTENT_NODAL_ONLY')

def solve(mesh=4):
 m=model(mesh);q=m['frame'];case=q['cases'][0];_,_,elements=frame.reference(q,case)
 folder=ARTIFACTS/str(uuid4());folder.mkdir(parents=True,exist_ok=False)
 fmt=lambda v:' '.join(format(float(x),'.17g') for x in v)
 lines=['wipe','model BasicBuilder -ndm 3 -ndf 6']
 for n in m['nodes']:
  lines.append(f"node {n['id']} {fmt(n['position'])}")
  if n['fixed']:lines.append(f"fix {n['id']} 1 1 1 1 1 1")
 for i,member in enumerate(q['members'],1):
  lines += [f"geomTransf Linear {i} {fmt(member['vecxz'])}",f"element elasticBeamColumn {i} {fmt(member['nodes'])} {fmt([member[k] for k in ['A','E','G','J','Iy','Iz']])} {i}"]
 lines.append(f"section ElasticMembranePlateSection 1 {m['E']} {m['nu']} {m['thickness_m']} 0")
 loads={n['id']:np.zeros(6) for n in m['nodes']}
 for quad in m['quads']:
  lines.append(f"element ShellMITC4 {quad['id']} {' '.join(map(str,quad['nodes']))} 1")
  for n in quad['nodes']:loads[n][2]+=m['pressure_pa']*(4/mesh)**2/4
 lines+=['timeSeries Linear 1','pattern Plain 1 1 {']
 lines += [f'load {tag} {fmt(f)}' for tag,f in loads.items() if np.any(f)]
 lines+=['}','constraints Plain','numberer RCM','system BandGeneral','algorithm Linear','integrator LoadControl 1','analysis Static','if {[analyze 1] != 0} {exit 2}','reactions']
 for name,command,tags in [('nodes','nodeDisp',[n['id'] for n in m['nodes']]),('reactions','nodeReaction',[n['id'] for n in m['nodes']]),('beams','eleResponse',range(1,len(elements)+1)),('shells','eleResponse',[s['id'] for s in m['quads']])]:
  lines.append(f'set f [open {name}.tsv w]')
  for tag in tags:lines.append(f'puts $f "{tag} [{command} {tag}{" localForce" if name=="beams" else " forces" if name=="shells" else ""}]"')
  lines.append('close $f')
 lines+=['exit 0'];(folder/'model.tcl').write_text('\n'.join(lines))
 p=subprocess.run([str(common.executable().resolve()),'model.tcl'],cwd=folder,capture_output=True,text=True,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 (folder/'stdout.txt').write_text(p.stdout);(folder/'stderr.txt').write_text(p.stderr)
 if p.returncode:raise RuntimeError(f'Native solver failed; retained {folder}')
 def read(name):return {int(a[0]):np.array([float(x) for x in a[1:]]) for line in (folder/(name+'.tsv')).read_text().splitlines() if (a:=line.split())}
 u=read('nodes');r=read('reactions');beams=read('beams');shells=read('shells')
 if any(len(v)!=6 or not np.isfinite(v).all() for v in [*u.values(),*r.values()]):raise ValueError('Invalid native nodal results')
 interface={n['id']:np.zeros(6) for n in m['nodes']}
 for quad in m['quads']:
  if shells[quad['id']].size!=24:raise ValueError('Expected 24 global shell nodal resisting forces')
  for n,f in zip(quad['nodes'],shells[quad['id']].reshape(4,6)):interface[n]+=f
 frameids={n['id'] for n in q['nodes']};transferred={n:(loads[n]-interface[n]).tolist() for n in frameids}
 transfercase=dict(name='Recovered shell interface actions',nodal=transferred,slab_factor=0)
 refu,refr,refelements=frame.reference(q,transfercase)
 error_u=float(np.max(abs(np.concatenate([u[n['id']] for n in q['nodes']])-refu)))
 error_r=float(np.max(abs(np.concatenate([r[n['id']] for n in q['nodes']])-refr)))
 error_f=max(float(np.max(abs(beams[i]-(k@(T@refu[ids])-f)))) for i,(_,L,R,T,k,f,ids) in enumerate(refelements,1))
 interior=max(float(np.max(abs(loads[n]-interface[n]))) for n in loads if n not in frameids)
 equilibrium=np.zeros(6)
 for n in m['nodes']:
  f=loads[n['id']]+r[n['id']];equilibrium[:3]+=f[:3];equilibrium[3:]+=f[3:]+np.cross(n['position'],f[:3])
 checks=dict(frame_displacement_error_m_rad=error_u,frame_reaction_error_n_nm=error_r,frame_end_force_error_n_nm=error_f,shell_interior_balance_n_nm=interior,global_force_error_n=float(max(abs(equilibrium[:3]))),global_moment_error_nm=float(max(abs(equilibrium[3:]))))
 # Raw native beam forces and nodal displacements, interpolated only within each unloaded beam segment.
 members=[]
 for i,(member,L,R,T,k,f,ids) in enumerate(elements,1):
  local=T@np.concatenate([u[n] for n in member['nodes']]);F=beams[i];a=np.array(next(n['position'] for n in q['nodes'] if n['id']==member['nodes'][0]));samples=[]
  for t in np.linspace(0,1,17):
   x=L*t;h=np.array([1-3*t*t+2*t**3,L*(t-2*t*t+t**3),3*t*t-2*t**3,L*(-t*t+t**3)])
   dl=np.array([(1-t)*local[0]+t*local[6],h@local[[1,5,7,11]],h@(local[[2,4,8,10]]*[1,-1,1,-1])])
   samples.append(dict(position=(a+R[0]*x).tolist(),displacement=(R.T@dl).tolist(),N=-F[0],Vy=F[1],Vz=F[2],My=F[4]+F[2]*x,Mz=-F[5]+F[1]*x,T=-F[3]))
  members.append(dict(**member,axes=R.tolist(),length_m=L,end_forces=F.tolist(),uniform_global_n_m=[0,0,0],samples=samples))
 center=next(n['id'] for n in m['nodes'] if n['position']==[2.,2.,3.])
 verified=error_u<1e-8 and max(v for k,v in checks.items() if k!='frame_displacement_error_m_rad')<.01
 result=dict(status='SUBSTRUCTURE_VERIFIED' if verified else 'VERIFICATION_FAILED',method='synthetic-coupled-shell-frame/research-1',run_id=folder.name,case=case,mesh=mesh,center_uz_m=float(u[center][2]),nodes=[dict(**n,displacement=u[n['id']].tolist(),reaction=r[n['id']].tolist(),applied=loads[n['id']].tolist()) for n in m['nodes']],members=members,slabs=[],shells=m['quads'],shell_global_nodal_resisting_forces={str(k):v.tolist() for k,v in shells.items()},interface_actions=transferred,comparisons=checks,formulation={k:v for k,v in m.items() if k not in ['nodes','quads','frame']},limitations=LIMITATIONS,solver=common.provenance(),production_enabled=False,diaphragm_enabled=False,two_storeys_enabled=False)
 result['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
 result['evidence_sha256']=common.digest(result);(folder/'manifest.json').write_text(json.dumps(result,indent=2));return result

def validated_run():
 """Fixed synthetic scope, explicit numerical acceptance thresholds.

 Native 12→16 centre convergence <1%; independent Ritz p6→p8 <0.1%;
 native vs independent centre <1.5%; native equilibrium/substructure <0.01 N/Nm.
 These numerical tolerances are verification gates, not engineering allowables.
 """
 from app.services.design.coupled_ritz import solve as ritz
 cases=[solve(n) for n in (8,12,16)];refs=[ritz(p) for p in (6,8)]
 fine=cases[-1];ref=refs[-1]
 checks=dict(mesh_relative_center_change=abs(cases[-2]['center_uz_m']/fine['center_uz_m']-1),ritz_relative_center_change=abs(refs[0]['center_uz_m']/ref['center_uz_m']-1),independent_center_relative_error=abs(fine['center_uz_m']/ref['center_uz_m']-1))
 q=model(16)['frame'];_,_,elements=frame.reference(q,q['cases'][0]);ru=np.array(ref['frame_displacements']);native={v['id']:v for v in fine['members']}
 differences=np.array([k@(T@ru[ids])-native[member['id']]['end_forces'] for member,L,R,T,k,f,ids in elements]);actual=np.array([native[member['id']]['end_forces'] for member,L,R,T,k,f,ids in elements])
 fi=[0,1,2,6,7,8];mi=[3,4,5,9,10,11]
 checks['independent_force_peak_normalized_error']=float(np.max(abs(differences[:,fi]))/np.max(abs(actual[:,fi])))
 checks['independent_moment_peak_normalized_error']=float(np.max(abs(differences[:,mi]))/np.max(abs(actual[:,mi])))
 passed=all(c['status']=='SUBSTRUCTURE_VERIFIED' for c in cases) and checks['mesh_relative_center_change']<.01 and checks['ritz_relative_center_change']<.001 and checks['independent_center_relative_error']<.015
 passed=passed and checks['independent_force_peak_normalized_error']<.03 and checks['independent_moment_peak_normalized_error']<.05
 fine['status']='VERIFIED' if passed else 'VERIFICATION_FAILED'
 fine['validation']=dict(status=fine['status'],scope='One prescribed one-storey 4×4 m synthetic panel only',thresholds=dict(mesh=.01,ritz=.001,independent=.015),checks=checks,mesh_runs=[dict(mesh=c['mesh'],center_uz_m=c['center_uz_m'],run_id=c['run_id'],comparisons=c['comparisons']) for c in cases],independent=refs)
 fine['evidence_sha256']=common.digest({k:v for k,v in fine.items() if k!='evidence_sha256'})
 (ARTIFACTS/fine['run_id']/'validated-manifest.json').write_text(json.dumps(fine,indent=2))
 return fine

def fixture():
 """Separate reviewed CAD geometry; no existing source IDs are reused."""
 from app.services.design.spatial_review import fixture as oldfixture
 doc,_=oldfixture(1);m=model(16);byid={n['id']:n for n in m['nodes']};components=[]
 template=doc['components'][0]
 import copy
 for member in m['frame']['members']:
  a=np.array(byid[member['nodes'][0]]['position']);b=np.array(byid[member['nodes'][1]]['position']);axis=int(np.argmax(abs(b-a)));dimensions=[.3,.3,.3];dimensions[axis]=float(np.linalg.norm(b-a))
  c=copy.deepcopy(template);c.update(id=member['id'],name=member['id'],category=member['kind']);c['transform']['position']=((a+b)/2).tolist();c['geometry']={'kind':'box','size':dimensions}
  components.append(c)
 slab=copy.deepcopy(template);slab.update(id='coupled-panel',name='Synthetic ShellMITC4 · 160 mm',category='slab');slab['transform']['position']=[2,2,3];slab['geometry']={'kind':'box','size':[4,4,.16]};components.append(slab)
 doc['components']=components;doc['metadata'].pop('spatial_frame_review',None)
 doc['metadata']['coupled_floor_review']=dict(method='synthetic-coupled-shell-frame/research-1',mesh=16,pressure_pa=-5000,thickness_m=.16,offset_m=0,diaphragm=False,purpose='SYNTHETIC_VERIFICATION_ONLY',limitations=LIMITATIONS)
 return doc
