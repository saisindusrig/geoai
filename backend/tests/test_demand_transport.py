import pytest
from app.services.design import demand_transport as d

def test_independent_benchmarks():assert d.benchmarks()['status']=='VERIFIED'
@pytest.mark.parametrize('F,M,O,P', [([10,20,30],[3,4,5],[2,-3,4],[-2,1,-1]),([-10,0,-20],[0,-50,0],[0,0,0],[0,0,-.45]),([0,10,0],[0,0,5],[2,0,0],[0,0,0])])
def test_equilibrium_reverse_sequential_and_scaling(F,M,O,P):
 r=d.transport(F,M,O,P);assert max(map(abs,r['equilibrium_residual_nm']))<1e-7
 assert d.transport(F,r['moment_enu_nm'],P,O)['moment_enu_nm']==pytest.approx(M)
 mid=[(a+b)/2 for a,b in zip(O,P)];step=d.transport(F,M,O,mid);assert d.transport(F,step['moment_enu_nm'],mid,P)['moment_enu_nm']==pytest.approx(r['moment_enu_nm'])
 assert d.transport([v/2 for v in F],[v/2 for v in M],O,P)['moment_enu_nm']==pytest.approx([v/2 for v in r['moment_enu_nm']])
@pytest.mark.parametrize('bad',[float('nan'),float('inf')])
def test_nonfinite_rejected(bad):
 with pytest.raises(ValueError):d.transport([bad,0,0],[0,0,0],[0,0,0],[0,0,0])
def test_mm_unit_hand_conversion():
 r=d.transport([10000,0,-30000],[0,10000,0],[0,0,0],[0,0,-.45]);assert r['moment_enu_nm'][1]*1000==10000000+450*10000
