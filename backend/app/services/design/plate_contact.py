"""Uniaxial nominal rigid-plate contact feasibility, not material capacity or contact FEA."""
import math
from decimal import Decimal

def assess(n_n,m_nm,b_m,l_m):
 if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (n_n,m_nm,b_m,l_m)) or n_n<=0 or b_m<=0 or l_m<=0:raise ValueError('Positive finite compression and plate dimensions, finite signed moment required')
 if b_m>50 or l_m>50:raise ValueError('Unsupported plate extent')
 e=m_nm/n_n;area=b_m*l_m;kern=b_m/6;half=b_m/2;I=l_m*b_m**3/12;tol=1e-12*max(b_m,1)
 # Applied +moment about -North requires upward contact centroid toward -East.
 # The scalar e=M/N is measured toward -East; plotted East centroid is -e.
 r=dict(compression_n=n_n,moment_about_negative_north_nm=m_nm,width_east_m=b_m,length_north_m=l_m,area_m2=area,eccentricity_m=e,eccentricity_east_m=-e,kern_limit_m=kern,footprint_half_width_m=half,mean_pressure_kpa=n_n/area/1000,pressure_min_kpa=None,pressure_max_kpa=None,pressure_at_minus_east_edge_kpa=None,pressure_at_plus_east_edge_kpa=None,verification='VERIFIED_FEASIBILITY_CLASSIFICATION_ONLY',full_connection_status='NOT_YET_VERIFIED',shear_transfer='NOT_YET_VERIFIED',partial_contact='NOT_IMPLEMENTED_NOT_VERIFIED',anchor_resistance='NOT_ASSUMED',capacity_check='NOT_YET_VERIFIED',reference='N and M at saved column-base reference plane. No horizontal-shear translation to plate underside.',formulas=['e = M/N [m]','kern = B/6 [m]; footprint limit = B/2 [m]','Full nominal contact only: p(x)=N/(BL)−Mx/I (x positive East); I=LB³/12 [m⁴]','p(−B/2)=N/(BL)×(1+6e/B); p(+B/2)=N/(BL)×(1−6e/B) [Pa]','∫p dA=N; ∫East x p dA=−M; applied M + contact moment = 0'],scope='Uniaxial nominal gross rectangular rigid plate; compression-only. No holes/contact loss, biaxial moments, anchors, shear, plate flexibility or material strength verification.')
 if abs(e)>half+tol:
  r.update(contact_state='RESULTANT_OUTSIDE_FOOTPRINT',compression_only_equilibrium='IMPOSSIBLE',message='Compression-only contact cannot equilibrate the full N/M demand: resultant lies outside the physical plate footprint.',contact_loss_detected=True)
  return r
 if abs(e)>kern+tol:
  r.update(contact_state='CONTACT_LOSS_PARTIAL_UNSUPPORTED',compression_only_equilibrium='NOT_CALCULATED_PARTIAL_CONTACT_UNSUPPORTED',message='Resultant outside middle third; full-contact linear law would require tension. Partial-contact pressure calculations are not implemented or verified.',contact_loss_detected=True)
  return r
 p0=n_n/area;minus=p0+m_nm*b_m/(2*I);plus=p0-m_nm*b_m/(2*I)
 if min(minus,plus)<-1e-6:raise ValueError('Full-contact classification produced tensile pressure')
 # Independent dimensional conversion: N/mm² plus M[Nmm]/S[mm³].
 N=Decimal(str(n_n));M=Decimal(str(m_nm))*1000;B=Decimal(str(b_m))*1000;L=Decimal(str(l_m))*1000;section_modulus=L*B*B/6
 dminus=float(N/(B*L)+M/section_modulus);dplus=float(N/(B*L)-M/section_modulus)
 # Two-point Gauss integrates the linear force and quadratic first moment exactly.
 x=b_m/(2*math.sqrt(3));points=[-x,x];weight=b_m*l_m/2;force=sum((p0-m_nm*t/I)*weight for t in points);moment=sum(t*(p0-m_nm*t/I)*weight for t in points)
 if not(math.isclose(minus/1e6,dminus,rel_tol=1e-10,abs_tol=1e-10) and math.isclose(plus/1e6,dplus,rel_tol=1e-10,abs_tol=1e-10) and math.isclose(force,n_n,rel_tol=1e-10,abs_tol=1e-7) and math.isclose(moment,-m_nm,rel_tol=1e-10,abs_tol=1e-7)):raise ValueError('Full-contact pressure units or N/M equilibrium verification failed')
 r.update(contact_state='KERN_BOUNDARY_ZERO_EDGE_PRESSURE' if math.isclose(abs(e),kern,abs_tol=tol,rel_tol=0) else 'FULL_CONTACT_LINEAR',compression_only_equilibrium='VERIFIED_N_M_EQUILIBRIUM',message='Nominal linear compression pressure verified for N/M only; shear and physical capacity remain unverified.',contact_loss_detected=False,pressure_min_kpa=max(0,min(minus,plus))/1000,pressure_max_kpa=max(minus,plus)/1000,pressure_at_minus_east_edge_kpa=max(0,minus)/1000,pressure_at_plus_east_edge_kpa=max(0,plus)/1000,verification='VERIFIED_LINEAR_PRESSURE_UNITS_AND_N_M_EQUILIBRIUM',independent_n_mm2_at_edges=[dminus,dplus],integrated_force_n=force,integrated_moment_nm=moment,force_residual_n=force-n_n,moment_residual_nm=moment+m_nm)
 return r

def benchmarks():
 cases=[]
 # Hand: N=100kN, B=.6,L=.5,A=.3; M=5kNm,e=.05,kern=.1.
 for n,m,expected in [(100000,0,[1000/3,1000/3]),(100000,5000,[500,500/3]),(100000,-5000,[500/3,500]),(100000,10000,[2000/3,0]),(50000,2500,[250,250/3])]:
  r=assess(n,m,.6,.5)
  if not all(math.isclose(v,w,abs_tol=1e-8) for v,w in zip([r['pressure_at_minus_east_edge_kpa'],r['pressure_at_plus_east_edge_kpa']],expected)):raise ValueError('Independent linear pressure known-answer benchmark failed')
  cases.append(dict(result=r,hand_edge_pressures_kpa=expected))
 for m,state in [(15000,'CONTACT_LOSS_PARTIAL_UNSUPPORTED'),(30001,'RESULTANT_OUTSIDE_FOOTPRINT')]:
  r=assess(100000,m,.6,.5)
  if r['contact_state']!=state or r['pressure_min_kpa'] is not None:raise ValueError('Contact loss/footprint benchmark failed')
  cases.append(dict(result=r,hand_contact_state=state))
 return dict(status='VERIFIED',reference='Independent worked N=100kN, B=600mm,L=500mm: A=300000mm²,S=30000000mm³; M=±5kNm gives edges 0.166666667/0.5 N/mm². Kern e=100mm, footprint half-width=300mm. Zero moment, kern boundary, reversed moment, proportional half load and unsupported contact states verified.',cases=cases)
