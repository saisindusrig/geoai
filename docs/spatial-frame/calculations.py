"""Compact reproducible numerical evidence extracted from immutable review runs."""
import json,math
from pathlib import Path
OUT=Path(__file__).parent
reviews=json.loads((OUT/'demo.json').read_text())
result={'actions':'Declared unfactored synthetic gravity/lateral; linear sum factors 1.0; no code load combinations','benchmarks':reviews[1]['analysis']['result']['benchmark_gate'],'independent_formulas':{
 'cantilever_local_axial':'u=P L/(E A)',
 'cantilever_local_y':'v=Fy L^3/(3 E Iz)+Mz L^2/(2 E Iz)',
 'cantilever_local_z':'w=Fz L^3/(3 E Iy)-My L^2/(2 E Iy)',
 'cantilever_torsion':'theta_x=T L/(G J)',
 'fixed_beam_uniform':'delta_mid=q L^4/(384 E I); |M_end|=|q| L^2/12; |M_mid|=|q| L^2/24',
 'reference_system':'Independent 12-DOF local Euler-Bernoulli matrices; K_global=T^T K_local T; consistent uniform loads; constrained Kff u=P; reaction=K u-P',
 'one_way_slab':'Area 4x4=16 m2, pressure 5 kPa ->80 kN/slab; q=5*4/2=10 kN/m on each of two 4 m beams; two slabs/floor ->160 kN/floor'},'fixed_beam_closed_form':dict(L_m=4,q_n_m=-10000,E_pa=30e9,I_m4=.3**4/12,mid_deflection_mm=-10000*4**4/(384*30e9*(.3**4/12))*1000,end_moment_abs_knm=10000*4**2/12/1000,mid_moment_abs_knm=10000*4**2/24/1000),'reviews':[]}
for review in reviews:
 q=review['fixture']['inputs'];r=review['analysis']['result'];rows=[]
 for c in r['cases']:
  rows.append(dict(name=c['case']['name'],reaction_sum_enu_n=[sum(n['reaction'][i] for n in c['nodes']) for i in range(3)],max_node_translation_mm=max(math.hypot(*n['displacement'][:3])*1000 for n in c['nodes']),max_member_sample_translation_mm=max(math.hypot(*s['displacement'])*1000 for m in c['members'] for s in m['samples']),native_vs_independent=c['comparisons'],run_id=c['run_id']))
 result['reviews'].append(dict(project=review['fixture']['project_id'],revision=review['fixture']['model_revision_id'],analysis=review['analysis']['id'],nodes=len(q['nodes']),members=len(q['members']),slabs=len(q['slabs']),document_sha256=r['model_document_sha256'],input_sha256=r['input_sha256'],evidence_sha256=r['evidence_sha256'],cases=rows))
(OUT/'independent-calculations.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result['reviews'],indent=2))
