"""Isolated research benchmarks; never enable/change a saved project formulation.

Rigid-diaphragm kinematics: independent three-DOF condensation.
Plate: thin simply supported square, uniform pressure, independent Navier series.
Passing these isolated tests does NOT validate coupling to the existing frame.
"""
import sys,json,math,subprocess
from pathlib import Path
from uuid import uuid4
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.services.design import opensees_benchmark as common
OUT=Path(__file__).parent/'mechanics-evidence'

def execute(lines):
 folder=OUT/str(uuid4());folder.mkdir(parents=True,exist_ok=False);(folder/'model.tcl').write_text('\n'.join(lines))
 completed=subprocess.run([str(common.executable().resolve()),'model.tcl'],cwd=folder,capture_output=True,text=True,timeout=40,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 (folder/'stdout.txt').write_text(completed.stdout);(folder/'stderr.txt').write_text(completed.stderr)
 if completed.returncode:raise RuntimeError(str(folder)+' '+completed.stderr)
 return folder

def diaphragm():
 coordinates=[(2,0),(-2,0),(0,2)];K=np.zeros((3,3));lines=['wipe','model BasicBuilder -ndm 3 -ndf 6','node 1 0 0 3','fix 1 0 0 1 1 1 0','uniaxialMaterial Elastic 1 1000000','uniaxialMaterial Elastic 2 2000000']
 for i,(x,y) in enumerate(coordinates,2):
  B=np.array([[1,0,-y],[0,1,x]]);K+=B.T@np.diag([1000000,2000000])@B
  lines.extend([f'node {i} {x} {y} 3',f'node {i+10} {x} {y} 3',f'fix {i} 0 0 1 1 1 0',f'fix {i+10} 1 1 1 1 1 1',f'element zeroLength {i} {i+10} {i} -mat 1 2 -dir 1 2'])
 lines+=['rigidDiaphragm 3 1 2 3 4','timeSeries Linear 1','pattern Plain 1 1 {load 1 1000 500 0 0 0 300}','constraints Transformation','numberer RCM','system BandGeneral','algorithm Linear','integrator LoadControl 1','analysis Static','if {[analyze 1] != 0} {exit 2}','reactions','set f [open nodes.tsv w]']
 for i in range(1,5):lines.append(f'puts $f "{i} [nodeDisp {i}]"')
 lines+=['close $f','exit 0'];folder=execute(lines);actual=np.array([[float(v) for v in l.split()[1:]] for l in (folder/'nodes.tsv').read_text().splitlines()]);q=np.linalg.solve(K,[1000,500,300]);expected=np.array([q]+[[q[0]-y*q[2],q[1]+x*q[2],q[2]] for x,y in coordinates]);selected=actual[:,[0,1,5]];error=float(np.max(abs(selected-expected)))
 return dict(status='BENCHMARK_VERIFIED' if error<1e-10 else 'FAILED',run_folder=str(folder.relative_to(ROOT)),condensed_stiffness=K.tolist(),expected=expected.tolist(),actual=selected.tolist(),max_abs_error=error,production_enabled=False,scope='Small-rotation rigid-plane kinematics with prescribed linear springs; not actual slab rigidity/capacity.')

def navier(terms=101):
 # a=4m, t=.04m (a/t=100), nu=.3, E=30GPa, q=-100Pa.
 a=4;t=.04;nu=.3;E=30e9;pressure=-100;D=E*t**3/(12*(1-nu**2))
 series=sum((-1)**((m-1)//2+(n-1)//2)/(m*n*((m/a)**2+(n/a)**2)**2) for m in range(1,terms+1,2) for n in range(1,terms+1,2))
 return 16*pressure*series/(math.pi**6*D)

def plate(mesh):
 a=4;t=.04;nu=.3;E=30e9;pressure=-100;dx=a/mesh;tag=lambda x,y:y*(mesh+1)+x+1
 lines=['wipe','model BasicBuilder -ndm 3 -ndf 6',f'section ElasticMembranePlateSection 1 {E} {nu} {t} 0'];loads={}
 for y in range(mesh+1):
  for x in range(mesh+1):
   i=tag(x,y);edge=x in (0,mesh) or y in (0,mesh)
   lines += [f'node {i} {x*dx} {y*dx} 0',f'fix {i} 1 1 {1 if edge else 0} 0 0 1']
 for y in range(mesh):
  for x in range(mesh):
   ids=[tag(x,y),tag(x+1,y),tag(x+1,y+1),tag(x,y+1)];lines.append(f'element ShellMITC4 {y*mesh+x+1} '+ ' '.join(map(str,ids))+' 1')
   for i in ids:loads[i]=loads.get(i,0)+pressure*dx*dx/4
 lines+=['timeSeries Linear 1','pattern Plain 1 1 {']+[f'load {i} 0 0 {p} 0 0 0' for i,p in loads.items()]+['}','constraints Plain','numberer RCM','system BandGeneral','algorithm Linear','integrator LoadControl 1','analysis Static','if {[analyze 1] != 0} {exit 2}','reactions','set f [open values.tsv w]',f'puts $f [nodeDisp {tag(mesh//2,mesh//2)} 3]']
 for i in loads:lines.append(f'puts $f [nodeReaction {i} 3]')
 lines+=['close $f','exit 0'];folder=execute(lines);values=[float(v) for v in (folder/'values.tsv').read_text().splitlines()];expected=navier();error=abs(values[0]/expected-1)
 return dict(mesh=mesh,run_folder=str(folder.relative_to(ROOT)),center_displacement_m=values[0],navier_center_m=expected,relative_error=error,total_reaction_n=sum(values[1:]),expected_reaction_n=-pressure*a*a,production_enabled=False)

def run():
 rigid=diaphragm();plates=[plate(m) for m in (4,8,16)];converged=plates[-1]['relative_error']<.02 and plates[-1]['relative_error']<plates[0]['relative_error'] and all(abs(p['total_reaction_n']-p['expected_reaction_n'])<1e-5 for p in plates)
 result=dict(diaphragm=rigid,plate=dict(status='BENCHMARK_VERIFIED' if converged else 'NOT_VALIDATED',meshes=plates,navier_series_101_vs_201_m=abs(navier(101)-navier(201)),scope='Linear pure bending only; all in-plane/drilling DOFs restrained. No membrane verification, beam-shell coupling, real floor boundary or connection validation.',production_enabled=False),solver=common.provenance(),integration_status='DISABLED',blockers=['Saved frame inputs contain LOAD-ONLY slabs without reviewed shell mesh, slab material/section properties or edge restraints.','No reviewed rigid-diaphragm assumption or master/slave DOF mapping in saved source.','Beam-shell compatibility, joint offsets, reaction/stiffness coupling, irregular floors/openings and mesh sensitivity remain unvalidated.'],references=['https://opensees.github.io/OpenSeesDocumentation/user/manual/model/mp_constraint/rigidDiaphragm.html','https://opensees.berkeley.edu/OpenSees/manuals/usermanual/231.htm','https://opensees.berkeley.edu/OpenSees/manuals/ExamplesManual/HTML/876.htm','https://ntrs.nasa.gov/api/citations/19880019811/downloads/19880019811.pdf'])
 (Path(__file__).parent/'mechanics-investigation.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':print(json.dumps(run(),indent=2))

