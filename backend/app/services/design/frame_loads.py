"""Bounded explicit SI load cases for the selected saved planar frame."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False,str_strip_whitespace=True)
class VerticalNodal(Strict):
 column_id:str=Field(min_length=1,max_length=200)
 endpoint:Literal['top']
 fy_n:float=Field(ge=-1e7,le=1e7)
class Density(Strict):
 component_id:str=Field(min_length=1,max_length=200)
 density_kg_m3:float=Field(gt=0,le=30000)
 source:str=Field(min_length=5,max_length=300)
class SelfWeight(Strict):
 densities:list[Density]=Field(min_length=3,max_length=3)
 gravity_m_s2:float=Field(gt=0,le=20)
 direction:Literal['local_enu_negative_up']
 source:str=Field(min_length=5,max_length=300)
class LoadCase(Strict):
 name:str=Field(min_length=1,max_length=60,pattern=r'^[A-Za-z0-9 +_.-]+$')
 source:str=Field(min_length=5,max_length=300)
 horizontal_n:float=Field(default=0,ge=-1e7,le=1e7)
 vertical_nodal_loads:list[VerticalNodal]=Field(default_factory=list,max_length=2)
 beam_uniform_n_per_m:float=Field(default=0,ge=-1e6,le=1e6)
 self_weight:SelfWeight|None=None
 @model_validator(mode='after')
 def nonempty(self):
  if not (self.horizontal_n or any(x.fy_n for x in self.vertical_nodal_loads) or self.beam_uniform_n_per_m or self.self_weight):raise ValueError('A named case requires at least one explicitly nonzero load or complete self-weight declaration')
  return self
class Factor(Strict):
 case_name:str=Field(min_length=1,max_length=60)
 factor:float=Field(ge=-10,le=10)
class Combination(Strict):
 name:str=Field(min_length=1,max_length=60,pattern=r'^[A-Za-z0-9 +_.-]+$')
 source:str=Field(min_length=5,max_length=300)
 factors:list[Factor]=Field(min_length=1,max_length=4)
 @model_validator(mode='after')
 def nonzero(self):
  if not any(f.factor for f in self.factors):raise ValueError('Combination requires a nonzero factor')
  return self

def normalize(q,g):
 """No inferred density, load, slab tributary area or structural connection."""
 members=g['members'];columns={m['component_id']:m['node_ids'][1] for m in (members[0],members[2])};ids={m['component_id'] for m in members};cases=[]
 for case in q['load_cases']:
  loads={2:[case['horizontal_n']/2,0.,0.],3:[case['horizontal_n']/2,0.,0.]};uniform={m['component_id']:[0.,0.] for m in members};sources=[]
  nodal=case['vertical_nodal_loads']
  if len({v['column_id'] for v in nodal})!=len(nodal) or any(v['column_id'] not in columns for v in nodal):raise ValueError('Vertical loads must reference each selected column top at most once; beam/slab/unknown nodes unsupported')
  for v in nodal:loads[columns[v['column_id']]][1]+=v['fy_n']
  uniform[members[1]['component_id']][1]+=case['beam_uniform_n_per_m']
  if case['self_weight']:
   sw=case['self_weight'];densities={d['component_id']:d for d in sw['densities']}
   if len(densities)!=3 or set(densities)!=ids:raise ValueError('Self-weight requires an explicit density and source for every selected member, without duplicates')
   for m in members:
    density=densities[m['component_id']];mass_per_m=density['density_kg_m3']*m['section']['area_m2'];w=mass_per_m*sw['gravity_m_s2'];uniform[m['component_id']][1]-=w
    sources.append(dict(component_id=m['component_id'],density_kg_m3=density['density_kg_m3'],area_m2=m['section']['area_m2'],mass_per_m_kg=mass_per_m,length_m=m['length_m'],gravity_m_s2=sw['gravity_m_s2'],direction=sw['direction'],weight_n_per_m=w,source=density['source'],gravity_source=sw['source']))
  cases.append(dict(name=case['name'],source=case['source'],nodal_loads_si=loads,uniform_global_by_component_n_per_m=uniform,self_weight_evidence=sources,units='N, N/m, m, kg/m³, m/s²; +X East, +Y Up',scope='Selected members only; no automatic slab distribution'))
 names=[v['name'] for v in cases]
 if len(set(names))!=len(names):raise ValueError('Load case names must be unique')
 combo=q.get('combination')
 if combo:
  refs=[f['case_name'] for f in combo['factors']]
  if len(set(refs))!=len(refs) or any(ref not in names for ref in refs) or combo['name'] in names:raise ValueError('Combination needs unique existing case references and a distinct name')
 return cases

def combine(cases,combination):
 result=dict(name=combination['name'],source=combination['source'],nodal_loads_si={2:[0.,0.,0.],3:[0.,0.,0.]},uniform_global_by_component_n_per_m={key:[0.,0.] for key in cases[0]['uniform_global_by_component_n_per_m']},self_weight_evidence=[],factors=combination['factors'],units=cases[0]['units'],scope=cases[0]['scope'])
 for f in combination['factors']:
  c=next(c for c in cases if c['name']==f['case_name'])
  for node,load in c['nodal_loads_si'].items():result['nodal_loads_si'][node]=[x+f['factor']*y for x,y in zip(result['nodal_loads_si'][node],load)]
  for member,load in c['uniform_global_by_component_n_per_m'].items():result['uniform_global_by_component_n_per_m'][member]=[x+f['factor']*y for x,y in zip(result['uniform_global_by_component_n_per_m'][member],load)]
 return result
