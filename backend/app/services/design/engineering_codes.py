"""Versioned design-method registry, independent of FEA and contact demand solvers."""
from decimal import Decimal as D
import hashlib,json
from pathlib import Path
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict
ACI_SOURCE='https://www.ocf.berkeley.edu/~chiep/wp-content/uploads/2024/01/CE-123-ACI-318-19.pdf'
VERSION='US/ACI318-19-INLB/anchor-steel-nominal-tension@1'
REGISTRY=[dict(id=VERSION,country='US',standard='ACI 318',edition='2019 IN-LB',method_version='1.0.0',clause='17.6.1.2',status='BENCHMARK_VERIFIED_NOMINAL_TERM_ONLY',source=ACI_SOURCE,formula='Nsa = Ase,N × min(fu, 1.9 fy, 125000 psi)',units='SI input/output; original IN-LB edition strength cap converted exactly',benchmark_id='anchor-steel-tension-known-answer/v1',excluded=['Strength reduction factor phi and factored demand check','Concrete breakout, pullout, side-face blowout, bond, shear and interaction','Anchor assembly, plate bending, welds, footing/soil and full ACI compliance']),dict(id='IN/IS800-2007/anchor-steel-tension@planned',country='IN',standard='IS 800',edition='2007; amendment/adoption review required',method_version=None,status='NOT_IMPLEMENTED',source='https://www.bis.gov.in/Know-Your-Standard/',reason='Independent Indian clause, applicability, amendments, material/partial-factor and benchmark review required; US formulas never substituted'),dict(id='US/AISC360-22/anchor-design@planned',country='US',standard='AISC 360',edition='2022; errata/adoption review required',method_version=None,status='NOT_IMPLEMENTED',source='https://www.aisc.org/aisc/publications/current-standards/aisc-360',reason='Separate AISC adapter and benchmark required; no automatic equivalence with ACI')]
def manifest():
 return dict(method_id=VERSION,descriptor_sha256=hashlib.sha256(json.dumps(REGISTRY[0],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
class Inputs(Strict):
 method_id:str
 country:Literal['IN','US']
 jurisdiction:str=Field(min_length=5,max_length=200)
 code_edition:str=Field(min_length=3,max_length=120)
 input_classification:Literal['REAL_PROJECT','SYNTHETIC_VERIFICATION','UNVERIFIED']
 anchor_reference:str=Field(min_length=3,max_length=160)
 linked_drawing_reference_id:int|None=Field(default=None,gt=0)
 linked_drawing_entity_id:str|None=None
 effective_tensile_area_mm2:float=Field(gt=0,le=10000)
 yield_strength_mpa:float=Field(gt=0,le=2000)
 ultimate_strength_mpa:float=Field(gt=0,le=2000)
 area_source:str=Field(min_length=10,max_length=800)
 material_source:str=Field(min_length=10,max_length=800)
 code_source_reference:str=Field(min_length=10,max_length=800)
 applicability_source:str=Field(min_length=10,max_length=800)
 input_reviewed_by:str=Field(min_length=3,max_length=120)
 pure_axial_single_steel_element:Literal[True]
 nominal_term_only_no_design_approval:Literal[True]

def calculate(inputs):
 q=Inputs.model_validate(inputs).model_dump()
 if q['method_id']!=VERSION or q['country']!='US' or q['code_edition']!='ACI 318-19 IN-LB':raise ValueError('Code/method/edition unsupported; Indian and AISC adapters are NOT IMPLEMENTED; no fallback calculation')
 if q['input_classification']=='UNVERIFIED':raise ValueError('Unverified inputs cannot produce a strength result; supply explicit sourced real data or a labeled synthetic benchmark')
 if q['input_classification']=='REAL_PROJECT' and any('SYNTHETIC' in q[k].upper() or 'TEST ONLY' in q[k].upper() for k in ['area_source','material_source','anchor_reference']):raise ValueError('Explicit synthetic source values cannot be promoted to REAL PROJECT')
 if q['ultimate_strength_mpa']<q['yield_strength_mpa']:raise ValueError('Ultimate strength cannot be below yield strength')
 A=q['effective_tensile_area_mm2'];fy=q['yield_strength_mpa'];fu=q['ultimate_strength_mpa'];psi_pa=6894.757293168361;cap=125000*psi_pa/1e6;used=min(fu,1.9*fy,cap);N=A*used
 # Independent IN-LB computation with Decimal, separate area and stress conversion.
 area_in2=D(str(A))/D('25.4')**2;psi=D(str(used))*D('1000000')/D(str(psi_pa));hand=area_in2*psi*D('4.4482216152605')
 if abs(float(hand)-N)>1e-7*max(1,N):raise ValueError('Independent IN-LB/SI nominal steel calculation disagrees')
 return dict(status='VERIFIED_NOMINAL_STEEL_TERM_ONLY',inputs=q,method=REGISTRY[0],nominal_strength_n=N,nominal_strength_kn=N/1000,effective_area_m2=A/1e6,fy_pa=fy*1e6,reported_fu_mpa=fu,used_fu_mpa=used,edition_cap_mpa=cap,governing_strength_limit='reported fu' if used==fu else '1.9 fy' if used==1.9*fy else '125000 psi',formula='Nsa [N] = Ase,N [mm²] × futa_used [N/mm²]',substitution=f'{A} mm² × {used} MPa = {N} N',independent_inlb=dict(area_in2=str(area_in2),used_fu_psi=str(psi),nominal_strength_n=str(hand),error_n=float(hand)-N),design_strength_phi_n=None,demand_capacity_status='NOT_EVALUATED',physical_connection_capacity='NOT_VERIFIED',engineering_approval='DISABLED',evidence_status='USER_SUPPLIED_SOURCE_DECLARATIONS_NOT_AUTHENTICATED',limitations=REGISTRY[0]['excluded'])
def fixture():
 return dict(method_id=VERSION,country='US',jurisdiction='Synthetic verification only; no actual code adoption claimed',code_edition='ACI 318-19 IN-LB',input_classification='SYNTHETIC_VERIFICATION',anchor_reference='Synthetic single steel anchor tensile section; not actual project bolt',linked_drawing_reference_id=None,linked_drawing_entity_id=None,effective_tensile_area_mm2=245,yield_strength_mpa=400,ultimate_strength_mpa=600,area_source='Explicit synthetic tensile area 245 mm2, not derived from nominal circle or diameter',material_source='Explicit synthetic fy 400 MPa / fu 600 MPa; no actual manufacturer certificate',code_source_reference=ACI_SOURCE+' ; section 17.6.1.2, IN-LB edition',applicability_source='Synthetic single steel tensile section, pure axial nominal term only; no phi, concrete or connection capacity claims',input_reviewed_by='Synthetic benchmark reviewer',pure_axial_single_steel_element=True,nominal_term_only_no_design_approval=True)
def benchmark():
 q=fixture();r=calculate(q);hand=D('245')*D('600');assert r['nominal_strength_n']==float(hand)
 return dict(status='VERIFIED',benchmark_id='anchor-steel-tension-known-answer/v1',hand=dict(formula='245 mm² × 600 N/mm²',expected_n=str(hand),expected_kn=str(hand/1000)),computed_n=r['nominal_strength_n'],independent_inlb=r['independent_inlb'],classification='SYNTHETIC_VERIFICATION')
