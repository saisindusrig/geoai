"""Evidence gate for real four-anchor inputs. No defaults for physical properties."""
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict
from app.services.design import anchor_contact_3d as mechanics

Category = Literal['measured', 'manufacturer_data', 'engineer_declared_assumption', 'synthetic_verification']

class Evidence(Strict):
 category: Category | None = None
 reference: str = Field(default='', max_length=800)
 method: str = Field(default='', max_length=800)
 applicability: str = Field(default='', max_length=800)
 reviewed_by: str = Field(default='', max_length=120)

class Quantity(Strict):
 value: float | None = Field(default=None, gt=0)
 evidence: Evidence = Field(default_factory=Evidence)

class Anchor(Strict):
 id: str = Field(min_length=1, max_length=80)
 material: str = Field(default='', max_length=160)
 geometry_and_material_evidence: Evidence = Field(default_factory=Evidence)
 diameter_m: Quantity = Field(default_factory=Quantity)
 effective_embedment_m: Quantity = Field(default_factory=Quantity)
 tensile_area_m2: Quantity = Field(default_factory=Quantity)
 steel_modulus_pa: Quantity = Field(default_factory=Quantity)
 axial_stiffness_n_m: Quantity = Field(default_factory=Quantity)
 max_valid_tension_n: Quantity = Field(default_factory=Quantity)
 max_valid_opening_m: Quantity = Field(default_factory=Quantity)
 tension_load_path: str = Field(default='', max_length=1200)

class Inputs(Strict):
 anchors: list[Anchor] = Field(min_length=4, max_length=4)
 saved_geometry_evidence: Evidence = Field(default_factory=Evidence)
 contact_stiffness_n_m3: Quantity = Field(default_factory=Quantity)
 max_valid_pressure_pa: Quantity = Field(default_factory=Quantity)
 max_valid_contact_displacement_m: Quantity = Field(default_factory=Quantity)
 concrete_material: str = Field(default='', max_length=160)
 contact_model_justification: str = Field(default='', max_length=1200)
 reference_plane_assumption: str = Field(default='', max_length=1200)
 mechanical_evidence: Evidence = Field(default_factory=Evidence)
 rigid_plate: bool = False
 homogeneous_contact: bool = False
 fixed_anchor_ground: bool = False
 zero_pretension: bool = False
 shear_excluded: bool = False
 engineer_input_review: bool = False

ANCHOR_FIELDS = {
 'diameter_m': ('Anchor diameter [m]', 'Physical anchor dimensions must be sourced; prior 20 mm is synthetic.'),
 'effective_embedment_m': ('Effective embedment [m]', 'Identify the effective tension path into concrete; prior 300 mm is synthetic, not resistance.'),
 'tensile_area_m2': ('Tensile area [m²]', 'Threaded tensile area cannot be inferred from nominal diameter.'),
 'steel_modulus_pa': ('Steel elastic modulus [Pa]', 'Material evidence is required; modulus alone does not define the effective connection stiffness.'),
 'axial_stiffness_n_m': ('Effective axial stiffness [N/m]', 'Each tension-only spring needs its own justified effective stiffness, including the declared load path.'),
 'max_valid_tension_n': ('Stiffness applicability: tension limit [N]', 'This is a model applicability bound, not a strength or breakout capacity.'),
 'max_valid_opening_m': ('Stiffness applicability: opening limit [m]', 'The linear spring law may only be used within its justified displacement range.'),
}
CONTACT_FIELDS = {
 'contact_stiffness_n_m3': ('Contact stiffness [N/m³]', 'An effective compression bed requires calibration or an explicitly reviewed assumption; concrete strength or soil modulus is not a substitute.'),
 'max_valid_pressure_pa': ('Contact-law applicability: pressure limit [Pa]', 'Bound the linear compression law; this does not establish concrete bearing capacity.'),
 'max_valid_contact_displacement_m': ('Contact-law applicability: displacement limit [m]', 'Bound the compression law and state effects excluded by the model.'),
}
FLAGS = {
 'rigid_plate': 'Review a massless, rigid plate; plate bending and prying excluded.',
 'homogeneous_contact': 'Review a uniform rectangular compression-only linear bed; no holes/layer variations.',
 'fixed_anchor_ground': 'Review fixed anchor spring ground; footing deformation and soil settlement excluded.',
 'zero_pretension': 'Declare zero initial anchor pretension and no gap/preload effects.',
 'shear_excluded': 'Exclude the separate shear demand; no shear-induced moment transport or resistance calculation.',
 'engineer_input_review': 'Review all supplied evidence and signed lever arms; this is not engineering safety approval.',
}

def template(audit):
 return Inputs(anchors=[Anchor(id=a['id']) for a in audit['actual_anchor_local_positions']]).model_dump()

def assess(inputs, audit):
 q = Inputs.model_validate(inputs).model_dump()
 missing = []
 def issue(path, why): missing.append(dict(path=path, reason=why))
 def evidence(e, path):
  if e['category'] is None: issue(path, 'Select measured, manufacturer data or engineer-declared assumption provenance.')
  elif e['category'] == 'synthetic_verification': issue(path, 'Synthetic verification values cannot authorize actual-project analysis.')
  for k in ['reference','method','applicability','reviewed_by']:
   if len(e[k].strip()) < (3 if k=='reviewed_by' else 10): issue(path+'.'+k, 'Supply source identification, derivation/measurement method, applicability limits and a reviewer; text is declared evidence, not authenticated laboratory verification.')
 def quantity(v, path, why):
  if v['value'] is None: issue(path+'.value', why)
  evidence(v['evidence'],path+'.evidence')
 ids = [a['id'] for a in q['anchors']]
 expected = [a['id'] for a in audit['actual_anchor_local_positions']]
 if len(set(ids))!=4 or set(ids)!=set(expected): raise ValueError('Exactly the four declared source anchor identities required; new or duplicate anchors are unsupported')
 evidence(q['saved_geometry_evidence'],'saved_geometry_evidence')
 evidence(q['mechanical_evidence'],'mechanical_evidence')
 for field,(_,why) in CONTACT_FIELDS.items(): quantity(q[field],field,why)
 for key in ['concrete_material','contact_model_justification','reference_plane_assumption']:
  if len(q[key].strip())<10: issue(key,'Describe concrete identity, justified homogeneous linear contact model, and the column-base N/M reference-plane assumption; shear transport to the plate underside remains excluded.')
 for key,why in FLAGS.items():
  if not q[key]: issue(key,why)
 for a in q['anchors']:
  path='anchors.'+a['id']
  if len(a['material'].strip())<3: issue(path+'.material','Supply actual anchor material designation; no default steel grade.')
  if len(a['tension_load_path'].strip())<30: issue(path+'.tension_load_path','Describe the effective stiffness model, free/effective length, embedment and fixed-ground load path, with exclusions; an embedment length is not evidence of capacity.')
  evidence(a['geometry_and_material_evidence'],path+'.geometry_and_material_evidence')
  for field,(_,why) in ANCHOR_FIELDS.items(): quantity(a[field],path+'.'+field,why)
  if a['diameter_m']['value'] and a['tensile_area_m2']['value']:
   import math
   if a['tensile_area_m2']['value'] > math.pi*a['diameter_m']['value']**2/4*(1+1e-9): issue(path+'.tensile_area_m2','Tensile area exceeds the gross circular section; inconsistent geometry.')
  plate=audit['geometry']['objects'][1];footing=audit['geometry']['objects'][2]
  position=next(v['position_east_north_m'] for v in audit['actual_anchor_local_positions'] if v['id']==a['id'])
  if a['effective_embedment_m']['value'] and a['effective_embedment_m']['value']>footing['size_m'][2]: issue(path+'.effective_embedment_m','Effective embedment exceeds saved footing thickness; unsupported physical geometry.')
  if a['diameter_m']['value'] and any(abs(position[i])+a['diameter_m']['value']/2>=plate['size_m'][i]/2 for i in [0,1]): issue(path+'.diameter_m','Anchor section lies outside saved plate footprint; no edge-capacity inference is made.')
 if not missing:
  numerical(q,audit) # bounded numerical domain and exact lever-arm validation
 return dict(status='BLOCKED_MISSING_ENGINEERING_INPUTS' if missing else 'READY_FOR_EXPLICIT_AUTHORIZATION',missing=missing,inputs=q,engineering_approval='DISABLED',evidence_status='USER_SUPPLIED_DECLARATIONS_NOT_INDEPENDENTLY_AUTHENTICATED',shear_transfer='UNSUPPORTED',categories=['measured','manufacturer_data','engineer_declared_assumption','synthetic_verification'])

def numerical(q,a):
 plate=a['geometry']['objects'][1]; positions={v['id']:v['position_east_north_m'] for v in a['actual_anchor_local_positions']}
 return mechanics.validate(dict(scope='SEPARATE_SYNTHETIC_3D_BENCHMARK_NOT_ACTUAL_PROJECT',case_name='Reviewed source column-base N/M',width_east_m=plate['size_m'][0],length_north_m=plate['size_m'][1],compression_n=a['demand']['compression_n'],moments_east_north_nm=a['demand']['demand_on_interface_enu_moment_nm'][:2],load_source='Immutable saved OpenSees column-base reactions; shear excluded, reference plane explicitly reviewed',contact_stiffness_n_m3=q['contact_stiffness_n_m3']['value'],contact_stiffness_source=q['contact_stiffness_n_m3']['evidence']['reference'][:400],anchors=[dict(id=v['id'],position_east_north_m=positions[v['id']],effective_lever_arms_m=positions[v['id']],axial_stiffness_n_m=v['axial_stiffness_n_m']['value'],source=v['axial_stiffness_n_m']['evidence']['reference'][:400]) for v in q['anchors']],mechanical_assumption='THREE_DOF_MASSLESS_RIGID_PLATE_LINEAR_COMPRESSION_BED_AND_INDIVIDUAL_TENSION_SPRINGS',mechanical_source=q['mechanical_evidence']['reference'][:600],fixed_anchor_ground_assumption=True,horizontal_shear_excluded=True,no_pretension=True,engineer_idealization_reviewed=True))

def solve(inputs,audit):
 review=assess(inputs,audit)
 if review['missing']: raise ValueError('Actual-project analysis BLOCKED: complete non-synthetic evidence and reviewed mechanical assumptions required')
 q=review['inputs'];model=numerical(q,audit)
 # Reuse precisely the benchmarked kernel; replace its synthetic provenance with actual adapter provenance.
 result=mechanics.run(model)
 max_compression=max(s['pressure_pa']/model['contact_stiffness_n_m3'] for s in result['pressure_samples'])
 if result['pressure_max_kpa']*1000>q['max_valid_pressure_pa']['value'] or max_compression>q['max_valid_contact_displacement_m']['value']: raise ValueError('Computed contact response exceeds declared applicability bounds; no actual result published')
 anchors={v['id']:v for v in q['anchors']}
 for v in result['anchors']:
  limit=anchors[v['id']]
  if v['tension_n']>limit['max_valid_tension_n']['value'] or v['opening_m']>limit['max_valid_opening_m']['value']: raise ValueError('Computed anchor response exceeds declared stiffness applicability bounds; no actual result published')
 result['status']='COMPUTED_N_M_ONLY_WITH_DECLARED_INPUT_EVIDENCE'
 result['inputs']={**model,'scope':'ACTUAL_SOURCE_N_M_WITH_EXPLICIT_REVIEWED_INPUT_EVIDENCE'}
 result['engineering_inputs']=q
 result['evidence_status']=review['evidence_status']
 result['limitations'][0]='Actual source N/M equilibrium under user-supplied properties and reviewed idealizations; evidence declarations are not experimentally verified by StruvoCivil.'
 result['shear_transfer']='UNSUPPORTED_SEPARATE_DEMAND'
 return result
