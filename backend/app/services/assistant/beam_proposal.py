"""Adapt explicit endpoints to the editor's existing box and XYZ Euler transform.

Pure conceptual geometry; no numerical/analytical member or connectivity is created.
"""
from math import isfinite
import numpy as np
from trimesh.transformations import euler_from_matrix

CONVENTION='Local X runs A to B; section depth follows projected ENU Up. Near-vertical beams use North as reference. No connection declaration.'

def beam_box(endpoints,width,depth,units):
    factor={'m':1.,'cm':.01,'mm':.001}[units]
    p=np.asarray(endpoints,dtype=float)*factor
    section=[width*factor,depth*factor]
    if p.shape!=(2,3) or not np.isfinite(p).all() or np.max(np.abs(p))>10000:
        raise ValueError('Two explicit finite ENU endpoints within ±10,000 m are required.')
    if any(not isfinite(v) or not .01<=v<=100 for v in section):
        raise ValueError('Explicit beam width and depth must be 0.01–100 m.')
    delta=p[1]-p[0];length=float(np.linalg.norm(delta))
    if not .01<=length<=100:raise ValueError('Beam length must be 0.01–100 m; identical or near-identical endpoints are rejected.')
    direction=delta/length
    reference=np.array([0.,1.,0.]) if abs(direction[2])>1-1e-8 else np.array([0.,0.,1.])
    transverse=np.cross(reference,direction);transverse/=np.linalg.norm(transverse)
    matrix=np.eye(4);matrix[:3,:3]=np.column_stack([direction,transverse,np.cross(direction,transverse)])
    rotation=np.degrees(euler_from_matrix(matrix,axes='rxyz')).tolist()
    return dict(size=[length,*section],position=p.mean(axis=0).tolist(),rotation_deg=rotation,
                endpoints_enu_m=p.tolist(),length_m=length,direction_enu=direction.tolist(),orientation_convention=CONVENTION)
