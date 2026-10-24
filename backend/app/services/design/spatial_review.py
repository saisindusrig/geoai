"""Deterministic parametric CAD review fixtures, not inferred building models."""
import numpy as np
from app.services.design import spatial_frame as solver

def fixture(storeys=1):
 if storeys not in (1,2):raise ValueError('Only independently benchmarked one/two-storey review fixtures')
 nodes=[];members=[];slabs=[];components=[];index={}
 for floor in range(storeys+1):
  for y in range(2):
   for x in range(3):
    tag=len(nodes)+1;index[floor,x,y]=tag;nodes.append(dict(id=tag,position=[4*x,4*y,3*floor],fixed=floor==0))
 def component(id,kind,pos,size):
  return dict(id=id,parent_id=None,name=id,category=kind,visible=True,locked=False,geometry=dict(kind='box',size=size),transform=dict(position=pos,rotation_deg=[0,0,0],scale=[1,1,1]),material=dict(name='Synthetic elastic review',color='#8fb4cc' if kind=='column' else '#b5c4d3' if kind=='beam' else '#637b8e',roughness=.75,metalness=0),quantity=dict(included=False))
 def member(kind,floor,a,b):
  id=f'{kind}-F{floor}-N{a}-{b}';p=np.array([nodes[a-1]['position'],nodes[b-1]['position']]);delta=p[1]-p[0];axis=int(np.argmax(abs(delta)));size=[.3,.3,.3];size[axis]=float(np.linalg.norm(delta));v=[0,1,0] if kind=='column' else [0,0,1];L,R=solver.basis(*p,v);sy=float(np.dot(abs(R[1]),size));sz=float(np.dot(abs(R[2]),size))
  members.append(dict(id=id,nodes=[a,b],floor=floor,kind=kind,vecxz=v,E=30e9,G=12.5e9,A=sy*sz,Iy=sy*sz**3/12,Iz=sz*sy**3/12,J=.001))
  components.append(component(id,kind,p.mean(axis=0).tolist(),size));return id
 for f in range(1,storeys+1):
  for y in range(2):
   for x in range(3):member('column',f,index[f-1,x,y],index[f,x,y])
  supports={}
  for y in range(2):
   for x in range(2):supports[x,y]=member('beam',f,index[f,x,y],index[f,x+1,y])
  for x in range(3):member('beam',f,index[f,x,0],index[f,x,1])
  for x in range(2):
   id=f'slab-F{f}-B{x+1}';slabs.append(dict(id=id,floor=f,beams=[supports[x,0],supports[x,1]],width_m=4,pressure_pa=5000));components.append(component(id,'slab',[x*4+2,2,f*3],[4,4,.16]))
 lateral={n['id']:[1000*(1+n['position'][1]/8),600,0,0,0,0] for n in nodes if not n['fixed']}
 cases=[dict(name='Gravity · 5 kPa one-way slabs',nodal={},slab_factor=1),dict(name='Lateral · E + N nodal actions',nodal=lateral,slab_factor=0),dict(name='Linear gravity + lateral',nodal=lateral,slab_factor=1)]
 q=dict(nodes=nodes,members=members,slabs=slabs,cases=cases,connection_review='rigid_coincident_joints_reviewed',section_source='Synthetic uncracked E=30 GPa, G=12.5 GPa; 300 mm square A/I bound to CAD; prescribed J=0.001 m4 (not physical RC torsion design). Slab 5 kPa includes declared total gravity; member self-weight excluded.',purpose='SYNTHETIC_VERIFICATION_ONLY')
 doc=dict(schema_version=1,project_id=0,scenario_id=0,project_type='unclassified',units='metric',origin=dict(lng=77.5946,lat=12.9716,elevation_m=0,heading_deg=0),generator_parameters={},components=components,metadata=dict(frame='local_enu_meters',source='reviewed_parametric_spatial_fixture',spatial_frame_review=dict(storeys=storeys,bays=[2,1],input=q)))
 solver.validate(q,doc);return doc,q

def cantilever(axis=0):
 p=[0,0,0];p[axis]=3
 m=dict(id='cantilever',nodes=[1,2],floor=1,kind='beam',vecxz=[0,1,0] if axis==2 else [0,0,1],E=200e9,G=80e9,A=.02,Iy=8e-5,Iz=4e-5,J=1e-4)
 return dict(nodes=[dict(id=1,position=[0,0,0],fixed=True),dict(id=2,position=p,fixed=False)],members=[m],slabs=[],cases=[dict(name='six DOF',nodal={2:[1000,2000,3000,400,500,600]},slab_factor=0)],connection_review='rigid_coincident_joints_reviewed',section_source='Synthetic explicit independent six DOF cantilever benchmark',purpose='SYNTHETIC_VERIFICATION_ONLY')

def benchmarks():
 evidence=[]
 for axis in (0,1,2):
  q=cantilever(axis);m=q['members'][0];L,R=solver.basis(q['nodes'][0]['position'],q['nodes'][1]['position'],m['vecxz']);f=R@np.array(q['cases'][0]['nodal'][2][:3]);moment=R@np.array(q['cases'][0]['nodal'][2][3:])
  expected=np.array([f[0]*L/(m['E']*m['A']),f[1]*L**3/(3*m['E']*m['Iz'])+moment[2]*L**2/(2*m['E']*m['Iz']),f[2]*L**3/(3*m['E']*m['Iy'])-moment[1]*L**2/(2*m['E']*m['Iy']),moment[0]*L/(m['G']*m['J']),-f[2]*L**2/(2*m['E']*m['Iy'])+moment[1]*L/(m['E']*m['Iy']),f[1]*L**2/(2*m['E']*m['Iz'])+moment[2]*L/(m['E']*m['Iz'])])
  for units in ('SI','N-mm'):
   result=solver.solve(q,q['cases'][0],units);actual=np.array(result['nodes'][1]['displacement']);local=np.r_[R@actual[:3],R@actual[3:]];error=float(np.max(abs(local-expected)))
   if result['status']!='VERIFIED' or error>1e-10:raise ValueError('3D analytical cantilever prerequisite failed')
   evidence.append(dict(axis=axis,units=units,run_id=result['run_id'],expected_local=expected.tolist(),actual_local=local.tolist(),max_abs_error=error))
 return dict(status='VERIFIED',checks=evidence,scope='6DOF axial, two bending planes, torsion, three orientations, SI/N-mm; independent closed forms + assembled stiffness')

