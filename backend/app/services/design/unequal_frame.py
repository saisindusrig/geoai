"""Independent energy-integration reference for nonsymmetric saved three-member geometry.

No elastic_frame mesh/stiffness helpers, symmetric-frame reduction or solver output
is used to construct this reference. All twelve retained DOFs are assembled; six
independent column-head DOFs remain after the explicit fixed-base restraints.
"""
import math
import numpy as np

VERSION='cad-planar-unequal/1'
def declared_loads(q,ids,case_name=None):
 # Independent normalization from explicit source inputs, not frame_loads helpers.
 def one(case):
  F=np.zeros(12);F[3]=F[6]=case.get('horizontal_n',0)/2;uniform={id:np.zeros(2) for id in ids}
  for row in case.get('vertical_nodal_loads',[]):
   if row['column_id'] not in [ids[0],ids[2]] or row['endpoint']!='top':raise ValueError('Reference requires a declared selected column top')
   F[{ids[0]:4,ids[2]:7}[row['column_id']]]+=row['fy_n']
  uniform[ids[1]][1]+=case.get('beam_uniform_n_per_m',0)
  weight=case.get('self_weight')
  if weight:
   sections={s['component_id']:s for s in q['sections']}
   for row in weight['densities']:uniform[row['component_id']][1]-=row['density_kg_m3']*sections[row['component_id']]['area_m2']*weight['gravity_m_s2']
  return F,uniform
 if not q.get('load_cases'):
  F=np.zeros(12);F[3]=F[6]=q['load_n']/2;return F,{id:np.zeros(2) for id in ids}
 cases={c['name']:c for c in q['load_cases']}
 if case_name in cases:return one(cases[case_name])
 combination=q.get('combination')
 if not combination or case_name!=combination['name']:raise ValueError('Independent reference requires an exact declared load-case identity')
 F=np.zeros(12);uniform={id:np.zeros(2) for id in ids}
 for term in combination['factors']:
  f,u=one(cases[term['case_name']]);F+=term['factor']*f
  for id in ids:uniform[id]+=term['factor']*u[id]
 return F,uniform

def member_integrals(L,EA,EI,qx,qy):
 k=np.zeros((6,6));fe=np.zeros(6);axial=np.array([-1/L,0,0,1/L,0,0])
 for t,w in [(.5*(1-math.sqrt(3/5)),5/18),(.5,4/9),(.5*(1+math.sqrt(3/5)),5/18)]:
  curvature=np.array([0,(-6+12*t)/L**2,(-4+6*t)/L,0,(6-12*t)/L**2,(-2+6*t)/L])
  k+=L*w*(EA*np.outer(axial,axial)+EI*np.outer(curvature,curvature))
  na=np.array([1-t,0,0,t,0,0]);nt=np.array([0,1-3*t*t+2*t**3,L*(t-2*t*t+t**3),0,3*t*t-2*t**3,L*(-t*t+t**3)])
  fe+=L*w*(qx*na+qy*nt)
 return k,fe

def reference(document,q,case_name=None):
 lookup={c['id']:c for c in document['components']};cs=[lookup[id] for id in q['component_ids']]
 columns=sorted([c for c in cs if c['category']=='column'],key=lambda c:c['transform']['position'][0]);beam=next(c for c in cs if c['category']=='beam')
 physical=[]
 for c in [columns[0],beam,columns[1]]:
  p=c['transform']['position'];size=c['geometry']['size'];axis=2 if c['category']=='column' else 0
  physical.append([[p[i]+(sign*size[i]/2 if i==axis else 0) for i in [0,2]] for sign in [-1,1]])
 origin=physical[0][0];positions={1:[0.,0.],2:[physical[0][1][i]-origin[i] for i in [0,1]],3:[physical[2][1][i]-origin[i] for i in [0,1]],4:[physical[2][0][i]-origin[i] for i in [0,1]]}
 sections={s['component_id']:s for s in q['sections']};K=np.zeros((12,12));F,uniform=declared_loads(q,[columns[0]['id'],beam['id'],columns[1]['id']],case_name);operators=[];sample_operators={}
 for c,endpoints,(ni,nj) in zip([columns[0],beam,columns[1]],physical,[(1,2),(2,3),(4,3)]):
  a=np.array(endpoints[0])-np.array(origin);b=np.array(endpoints[1])-np.array(origin);delta=b-a;L=float(np.linalg.norm(delta));cx,sy=delta/L;s=sections[c['id']]
  EA=s['elastic_modulus_pa']*s['area_m2'];EI=s['elastic_modulus_pa']*s['inertia_m4'];qx,qy=np.array([[cx,sy],[-sy,cx]])@uniform[c['id']];k,fe=member_integrals(L,EA,EI,qx,qy)
  # Physical end displacement from independently measured retained-node offsets.
  T=np.zeros((6,6));offsets=[]
  for start,node,point in [(0,ni,a),(3,nj,b)]:
   rx,ry=point-np.array(positions[node]);offsets.append([float(rx),float(ry)])
   B=np.array([[1.,0.,-ry],[0.,1.,rx],[0.,0.,1.]])
   R=np.array([[cx,sy,0],[-sy,cx,0],[0,0,1.]])
   T[start:start+3,start:start+3]=R@B
  dofs=[(node-1)*3+d for node in [ni,nj] for d in range(3)];K[np.ix_(dofs,dofs)]+=T.T@k@T
  F[dofs]+=T.T@fe
  operators.append((c['id'],ni,nj,k,T,dofs,offsets,L));sample_operators[c['id']]=dict(a=a.tolist(),cx=float(cx),sy=float(sy),L=L,EA=EA,EI=EI,qx=float(qx),qy=float(qy),fe=fe.tolist(),T=T.tolist(),dofs=dofs)
 free=[3,4,5,6,7,8];u=np.zeros(12);u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free]);reactions=K@u-F
 forces={id:(k@T@u[dofs]-np.array(sample_operators[id]['fe'])).tolist() for id,_,_,k,T,dofs,_,_ in operators}
 for id,op in sample_operators.items():op['local_displacement_si']=(np.array(op.pop('T'))@u[op.pop('dofs')]).tolist()
 return dict(version='cad-planar-unequal-gravity/1' if q.get('load_cases') else VERSION,case_name=case_name,sample_operators=sample_operators,uniform_global_n_per_m={id:v.tolist() for id,v in uniform.items()},formulation='Full 12-DOF retained-node assembly, six independent free head DOFs. Independently integrate EA axial strain and EI Hermite curvature energy using exact Gauss quadrature. Measured physical endpoint transforms include uphysical=uretained+[-ry theta,rx theta]. Consistent uniform loads independently integrated against axial/Hermite shape functions; f=k ulocal-fe. Kff uf=Ff; R=Ku-F. Interior axial/quartic particular solutions verified. Nonsymmetric geometry; no symmetry reduction.',nodes={i:u[(i-1)*3:i*3].tolist() for i in [1,2,3,4]},node_positions_m=positions,reactions={i:reactions[(i-1)*3:i*3].tolist() for i in [1,4]},member_end_forces_si=forces,member_offsets_m={id:r for id,_,_,_,_,_,r,_ in operators},member_lengths_m={id:L for id,_,_,_,_,_,_,L in operators},stiffness_si=K.tolist(),free_stiffness_si=K[np.ix_(free,free)].tolist(),load_vector_si=F.tolist(),free_dofs=free,free_equation_residual_si=(K@u-F)[free].tolist(),geometry_response_symmetry_assumed=False,stiffness_symmetry_error=float(np.max(np.abs(K-K.T))),free_matrix_condition_number=float(np.linalg.cond(K[np.ix_(free,free)])))
def verify(document,q,result):
 if result['status']!='VERIFIED':raise ValueError('No verified local solver output available')
 r=reference(document,q,result.get('case_name'));checks=[]
 if {e['component_id'] for e in result['elements']}!=set(r['member_end_forces_si']) or any(not e.get('samples') for e in result['elements']):raise ValueError('Incomplete saved member result mapping')
 if {n['node'] for n in result['reactions']}!={1,4} or not {1,2,3,4}.issubset({n['id'] for n in result['nodes']}):raise ValueError('Incomplete retained node or support results')
 for n in result['nodes']:
  if n['id'] in r['nodes']:
   for a,b in zip(n['displacement_m'],r['nodes'][n['id']]):checks.append(('retained_displacement',a,b,1e-10))
 for n in result['reactions']:
  for a,b in zip([n[k] for k in ['fx_n','fy_n','moment_nm']],r['reactions'][n['node']]):checks.append(('base_reaction',a,b,1e-6))
 for id,expected in r['member_end_forces_si'].items():
  elements=[e for e in result['elements'] if e['component_id']==id];actual=elements[0]['local_end_forces_si'][:3]+elements[-1]['local_end_forces_si'][3:]
  for a,b in zip(actual,expected):checks.append(('physical_member_end_force',a,b,1e-6))
 for e in result['elements']:
  op=r['sample_operators'][e['component_id']];L=op['L'];u=op['local_displacement_si'];cx=op['cx'];sy=op['sy'];qx=op['qx'];qy=op['qy'];f=r['member_end_forces_si'][e['component_id']]
  for sample in e['samples']:
   x=float(np.dot(np.array(sample['position_m'])-op['a'],[cx,sy]));t=x/L
   axial=(1-t)*u[0]+t*u[3]+qx*x*(L-x)/(2*op['EA'])
   transverse=(1-3*t*t+2*t**3)*u[1]+L*(t-2*t*t+t**3)*u[2]+(3*t*t-2*t**3)*u[4]+L*(-t*t+t**3)*u[5]+qy*x*x*(L-x)**2/(24*op['EI'])
   for a,b in zip(sample['displacement_m'],[cx*axial-sy*transverse,sy*axial+cx*transverse]):checks.append(('interior_displacement',a,b,1e-10))
   for key,b in [('axial_n',-f[0]-qx*x),('shear_n',f[1]+qy*x),('moment_nm',-f[2]+f[1]*x+qy*x*x/2)]:checks.append((key,sample[key],b,1e-6))
 return dict(passed=all(math.isclose(a,b,rel_tol=1e-7,abs_tol=tol) for _,a,b,tol in checks) and max(map(abs,r['free_equation_residual_si']))<1e-5,checks=len(checks),max_absolute_errors={name:max(abs(a-b) for label,a,b,_ in checks if label==name) for name in {label for label,_,_,_ in checks}},reference=r,note='Elastic stiffness is reciprocal/symmetric; the retained six-DOF geometry and resulting response are nonsymmetric. No symmetric-frame hand formulas applied.')
