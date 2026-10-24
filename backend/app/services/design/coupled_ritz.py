"""Independent variational Mindlin plate + existing independently assembled EB frame.

Legendre tensor-product displacement/rotation fields; full Gaussian integration.
No OpenSees shell stiffness, shell forces or nodal displacements enter this solve.
Five physical plate fields u,v,w,rx,ry; drilling rotation = half in-plane curl.
This is a distinct discretization, not an exact solution or code-design check.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss,legval,legder
from app.services.design.coupled_floor import model
from app.services.design import spatial_frame as frame

def solve(order=6,mesh=16):
 m=model(mesh);q=m['frame'];n=(order+1)**2;size=5*n
 def basis(x,y):
  px=[];py=[];dx=[];dy=[]
  for i in range(order+1):
   c=np.eye(order+1)[i];px.append(legval(x/2-1,c));py.append(legval(y/2-1,c));dx.append(legval(x/2-1,legder(c))/2);dy.append(legval(y/2-1,legder(c))/2)
  return np.outer(px,py).ravel(),np.outer(dx,py).ravel(),np.outer(px,dy).ravel()
 def row(field,b):
  a=np.zeros(size);a[field*n:(field+1)*n]=b;return a
 E,nu,t=m['E'],m['nu'],m['thickness_m'];G=E/(2*(1+nu))
 C=np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
 D=E*t**3/(12*(1-nu**2))*C;A=E*t/(1-nu**2)*C
 K=np.zeros((size,size));f=np.zeros(size);points,weights=leggauss(order+2)
 for ix,x in enumerate(points):
  for iy,y in enumerate(points):
   b,dx,dy=basis(2*(x+1),2*(y+1));weight=4*weights[ix]*weights[iy]
   membrane=np.array([row(0,dx),row(1,dy),row(0,dy)+row(1,dx)])
   bending=np.array([row(4,dx),-row(3,dy),row(4,dy)-row(3,dx)])
   shear=np.array([row(2,dx)+row(4,b),row(2,dy)-row(3,b)])
   K+=weight*(membrane.T@A@membrane+bending.T@D@bending+(5/6)*G*t*(shear.T@shear))
   f+=weight*m['pressure_pa']*row(2,b)
 # Evaluate the independent beam frame at the same physical boundary points.
 P=np.zeros((6*len(q['nodes']),size))
 for i,node in enumerate(q['nodes']):
  if node['fixed']:continue
  b,dx,dy=basis(*node['position'][:2])
  P[6*i:6*i+6]=[row(0,b),row(1,b),row(2,b),row(3,b),row(4,b),.5*(row(1,dx)-row(0,dy))]
 _,_,elements=frame.reference(q,q['cases'][0])
 for member,L,R,T,k,fl,ids in elements:
  B=T@P[ids];K+=B.T@k@B
 solution=np.linalg.solve(K,f);b,_,_=basis(2,2)
 return dict(order=order,frame_mesh=mesh,center_uz_m=float(b@solution[2*n:3*n]),strain_energy_j=float(.5*solution@K@solution),relative_residual=float(np.linalg.norm(K@solution-f)/np.linalg.norm(f)),frame_displacements=(P@solution).tolist(),assumptions=['Independent linear Mindlin variational plate, shear factor 5/6.','No native shell stiffness/results used.','Drilling rotation half in-plane curl; compare discretizations, not exact equality.'])
