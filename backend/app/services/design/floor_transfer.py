"""Read-only equilibrium/tributary evidence from an existing spatial solver run.

No new stiffness, force redistribution, diaphragm or slab response is calculated.
Member local end actions belong to the complete saved case, never a traced load.
"""
import math
import numpy as np

LIMITATIONS=['LOAD-ONLY floors: no plate stiffness, plate stresses, slab deformation or diaphragm.',
 'Routes show explicit analytical connectivity, not per-load force attribution.',
 'Member end actions and base reactions belong to the entire saved load case.',
 'Rigid joints/fixed bases are prescribed idealizations; joint, base-plate, foundation and soil capacity NOT VERIFIED.']

def evidence(case):
 if case.get('status')!='VERIFIED':raise ValueError('Current verified spatial result required')
 nodes={n['id']:n for n in case['nodes']};members={m['id']:m for m in case['members']}
 for n in nodes.values():
  if len(n['position'])!=3 or len(n['reaction'])!=6 or not np.all(np.isfinite(n['position']+n['reaction'])):raise ValueError('Nonfinite or incomplete saved node evidence')
 for tag,load in case['case']['nodal'].items():
  if int(tag) not in nodes or len(load)!=6 or not np.all(np.isfinite(load)):raise ValueError('Invalid saved nodal action')
 if not math.isfinite(case['case']['slab_factor']):raise ValueError('Nonfinite slab load factor')
 sums={i:np.zeros(6) for i in nodes};expected={i:np.zeros(3) for i in members};slabs=[]
 for m in members.values():
  R=np.array(m['axes']);forces=np.array(m['end_forces'])
  if R.shape!=(3,3) or forces.shape!=(12,) or not np.all(np.isfinite(forces)) or not np.allclose(R@R.T,np.eye(3),atol=1e-9) or len(m['uniform_global_n_m'])!=3 or not np.all(np.isfinite(m['uniform_global_n_m'])):raise ValueError('Invalid saved local axes/end actions')
  for end,tag in enumerate(m['nodes']):
   if tag not in nodes:raise ValueError('Missing saved analytical node')
   f=forces[end*6:end*6+6];sums[tag]+=np.r_[R.T@f[:3],R.T@f[3:]]
 for s in case['slabs']:
  a,b=[members[i] for i in s['beams']];pa=np.array([nodes[i]['position'] for i in a['nodes']]);pb=np.array([nodes[i]['position'] for i in b['nodes']]);mid=(pa+pb)/2
  if not all(math.isfinite(v) for v in [s['pressure_pa'],s['width_m'],a['length_m'],b['length_m']]) or not math.isclose(np.linalg.norm(pa[1]-pa[0]),a['length_m'],abs_tol=1e-8) or not math.isclose(np.linalg.norm(pb[1]-pb[0]),b['length_m'],abs_tol=1e-8):raise ValueError('Invalid saved slab dimensions/actions')
  if not np.allclose(pa[1]-pa[0],pb[1]-pb[0]) or not math.isclose(np.linalg.norm(pb[0]-pa[0]),s['width_m'],abs_tol=1e-8):raise ValueError('Saved slab support geometry inconsistent')
  pressure=s['pressure_pa']*case['case']['slab_factor'];L=a['length_m'];area=L*s['width_m'];q=pressure*s['width_m']/2
  strips=[]
  for beam,p,other in [(a,pa,mid),(b,mid,pb)]:
   expected[beam['id']][2]-=q
   strips.append(dict(beam_id=beam['id'],area_m2=area/2,line_load_n_m=q,downward_force_n=q*L,polygon=[p[0].tolist(),p[1].tolist(),other[1].tolist(),other[0].tolist()]))
  slabs.append(dict(id=s['id'],floor=s['floor'],status='LOAD_ONLY',pressure_pa=pressure,area_m2=area,applied_downward_n=pressure*area,strips=strips,allocation_residual_n=pressure*area-sum(t['downward_force_n'] for t in strips)))
 balances=[]
 for tag,node in nodes.items():
  nodal=np.array(case['case']['nodal'].get(str(tag),case['case']['nodal'].get(tag,[0]*6)));reaction=np.array(node['reaction']);residual=sums[tag]-nodal-reaction
  balances.append(dict(node_id=tag,fixed=node['fixed'],member_end_action_sum_enu=sums[tag].tolist(),applied_nodal_enu=nodal.tolist(),support_reaction_enu=reaction.tolist(),residual_enu=residual.tolist()))
 uniform_error=max([float(np.max(abs(expected[i]-m['uniform_global_n_m']))) for i,m in members.items()]+[0])
 force_error=max([max(abs(v) for v in n['residual_enu'][:3]) for n in balances]+[0]);moment_error=max([max(abs(v) for v in n['residual_enu'][3:]) for n in balances]+[0])
 verified=max(uniform_error,force_error,moment_error)<1e-5
 return dict(status='VERIFIED' if verified else 'VERIFICATION_FAILED',method='saved-spatial-floor-transfer/1',case_name=case['case']['name'],run_id=case['run_id'],slabs=slabs,node_balances=balances,comparisons=dict(uniform_load_max_error_n_m=uniform_error,joint_force_max_residual_n=force_error,joint_moment_max_residual_nm=moment_error),capabilities=dict(load_only_floor=True,diaphragm=False,slab_structural_analysis=False,connection_capacity=False,per_load_force_attribution=False),limitations=LIMITATIONS)
