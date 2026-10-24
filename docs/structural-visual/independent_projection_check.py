"""Independent read-only equilibrium and unit checks on saved display fixtures."""
from pathlib import Path
import json,math
OUT=Path(__file__).parent;checks=[]
for pid in [793,794]:
 raw=json.loads((OUT/f'project-{pid}.json').read_text());result=raw['rows'][0]['result']
 frames=[f['result'] for f in result['frames']] if 'frames' in result else [result]
 for frame in frames:
  g=frame['physical_to_analytical_graph']
  for case in [frame]+frame.get('load_case_results',[]):
   loads=case.get('applied_loads',{});fx=fy=moment=0.
   for reaction in case['reactions']:
    x,y=g['node_positions_m'][reaction['node']-1];fx+=reaction['fx_n'];fy+=reaction['fy_n'];moment+=reaction['moment_nm']+x*reaction['fy_n']-y*reaction['fx_n']
   for node,load in loads.get('nodal_loads_si',{}).items():
    x,y=g['node_positions_m'][int(node)-1];fx+=load[0];fy+=load[1];moment+=load[2]+x*load[1]-y*load[0]
   for member in g['members']:
    q=loads.get('uniform_global_by_component_n_per_m',{}).get(member['component_id'],[0.,0.]);a,b=member['centerline_endpoints_m'];length=math.dist(a,b);x,y=[(a[i]+b[i])/2 for i in [0,1]];fx+=q[0]*length;fy+=q[1]*length;moment+=length*(x*q[1]-y*q[0])
   assert max(abs(fx),abs(fy),abs(moment))<.001,(pid,case.get('case_name'),fx,fy,moment)
   samples=[s for e in case['elements'] for s in e['samples']]
   checks.append(dict(project_id=pid,case=case.get('case_name'),frame_origin_enu_m=g['origin_enu_m'],independent_residual_n_n_nm=[fx,fy,moment],max_displacement_mm=1000*max(math.hypot(*s['displacement_m']) for s in samples),max_absolute_moment_knm=max(abs(s['moment_nm']) for s in samples)/1000,samples=len(samples)))
 if 'transfer' in result:
  t=result['transfer'];assert abs(sum(s['transferred_kn'] for s in t['strips'])-t['applied_kn'])<1e-9
(OUT/'independent-projection-checks.json').write_text(json.dumps(dict(checked_cases=len(checks),equilibrium_tolerance_n_n_nm=.001,checks=checks,note='Independent summation of saved applied nodal/distributed loads and support reactions. No new solver response, design combination or capacity calculation.'),indent=2))
print('Independent saved-load equilibrium and display-unit checks passed:',len(checks))
