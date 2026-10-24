"""DXF plan reference extraction, without inferred structural semantics or elevations."""
import hashlib, io, math
from collections import Counter
from typing import Literal
from pydantic import Field
from app.services.design.frame_loads import Strict
from app.services.survey.import_pipeline import ezdxf

Classification=Literal['REAL_PROJECT','SYNTHETIC_VERIFICATION','UNVERIFIED']
MISSING=['Reviewed member elevations, section orientation and physical-to-analytical mapping','Explicit elastic material properties and structural section A/I (nominal drawing boxes are not designed sections)','Engineer-supplied load cases and load reference planes','Declared supports and joint behavior; touching plan outlines do not establish connections','Reinforcement, weld/anchor details and foundation behavior','Geotechnical data and surveyed datum','Jurisdiction, adopted code edition and authenticated engineering source evidence']
def extract(content:bytes,filename:str,classification:str):
 if not filename.lower().endswith('.dxf'):raise ValueError('Only text DXF reference import is supported; IFC/DWG/PDF structural extraction is unavailable')
 if not content or len(content)>2_000_000:raise ValueError('DXF reference must be nonempty and at most 2 MB')
 if ezdxf is None:raise ValueError('Existing ezdxf runtime unavailable; no automatic installation')
 try:d=ezdxf.read(io.StringIO(content.decode('utf-8-sig')))
 except Exception as e:raise ValueError('Invalid or unsupported text DXF') from e
 unit=d.header.get('$INSUNITS');scale={4:.001,6:1}.get(unit)
 if scale is None:raise ValueError('Explicit DXF INSUNITS of millimetres (4) or metres (6) required; unitless and other units unsupported')
 sha=hashlib.sha256(content).hexdigest();items=[];counts=Counter();unsupported=[]
 for e in d.modelspace():
  kind=e.dxftype();counts[kind]+=1;item=dict(id=f'dxf:{sha[:16]}:{e.dxf.handle}',handle=e.dxf.handle,layer=e.dxf.layer,kind=kind,material=None,engineering_status='UNVERIFIED',source_geometry=True)
  if e.dxf.hasattr('extrusion') and tuple(e.dxf.extrusion)!=(0,0,1):unsupported.append(dict(handle=e.dxf.handle,kind=kind,reason='Transformed entity coordinate plane unsupported'));continue
  if kind=='LINE':item.update(points_native=[list(e.dxf.start),list(e.dxf.end)],closed=False)
  elif kind in ['LWPOLYLINE','POLYLINE']:
   if kind=='LWPOLYLINE':
    if any(abs(p[4])>1e-12 for p in e.get_points('xyseb')):unsupported.append(dict(handle=e.dxf.handle,kind=kind,reason='Curved bulge polyline unsupported'));continue
    points=[[float(p[0]),float(p[1]),float(e.dxf.elevation)] for p in e.get_points('xy')]
   else:
    if any(abs(v.dxf.get('bulge',0))>1e-12 for v in e.vertices):unsupported.append(dict(handle=e.dxf.handle,kind=kind,reason='Curved polyline unsupported'));continue
    points=[list(v.dxf.location) for v in e.vertices]
   item.update(points_native=points,closed=bool(e.is_closed))
  elif kind=='CIRCLE':item.update(center_native=list(e.dxf.center),radius_native=float(e.dxf.radius),interpretation='REFERENCE_CIRCLE_ONLY_NOT_PHYSICAL_ANCHOR')
  elif kind in ['TEXT','MTEXT']:item.update(text=e.dxf.text if kind=='TEXT' else e.plain_text(),position_native=list(e.dxf.insert))
  else:unsupported.append(dict(handle=e.dxf.handle,kind=kind,reason='Entity retained in original DXF but not extracted'));continue
  coordinates=item.get('points_native',[])+([item['center_native']] if 'center_native' in item else [])+([item['position_native']] if 'position_native' in item else [])
  if any(len(p)!=3 or not all(math.isfinite(float(v)) and abs(v)*scale<10000 for v in p) or abs(p[2])*scale>1e-9 for p in coordinates):raise ValueError('Only finite planar 2D local DXF references are supported; out-of-plane geometry rejected')
  if kind=='CIRCLE' and (not math.isfinite(item['radius_native']) or item['radius_native']<=0):raise ValueError('Invalid reference circle radius')
  if 'points_native' in item:
   item['points_m']=[[float(v)*scale for v in p] for p in item['points_native']]
   xs=[p[0] for p in item['points_m']];ys=[p[1] for p in item['points_m']]
   if len(xs)<2:raise ValueError('Degenerate DXF linework')
   item['plan_bounds_m']=[min(xs),min(ys),max(xs),max(ys)];item['plan_dimensions_m']=[max(xs)-min(xs),max(ys)-min(ys)]
  items.append(item)
  if len(items)>2000:raise ValueError('Reference import limited to 2000 extracted entities')
 notes=[v['text'] for v in items if 'text' in v];synthetic=any('SYNTHETIC' in n.upper() or 'TRAINING GEOMETRY' in n.upper() for n in notes)
 if synthetic and classification=='REAL_PROJECT':raise ValueError('Source explicitly identifies synthetic geometry; cannot classify as REAL PROJECT')
 if classification not in ['REAL_PROJECT','SYNTHETIC_VERIFICATION','UNVERIFIED']:raise ValueError('Explicit source classification required')
 if synthetic:classification='SYNTHETIC_VERIFICATION'
 if not any('points_m' in v for v in items):raise ValueError('No supported plan linework found')
 return dict(filename=filename,source_sha256=sha,dxf_version=d.dxfversion,unit_code=unit,source_units='mm' if unit==4 else 'm',scale_to_m=scale,classification=classification,entities=items,entity_counts=dict(counts),unsupported_entities=unsupported,notes=notes,frame='LOCAL_XY_REFERENCE_NOT_GEOREFERENCED; displayed Z=0 is drawing plane, not a structural elevation',engineering_approval='DISABLED',analytical_model_status='BLOCKED',missing_engineering_inputs=MISSING)

class Correction(Strict):
 entity_id:str
 label:str=Field(default='',max_length=120)
 role:Literal['UNVERIFIED','COLUMN','BEAM','SLAB','BASE_PLATE','FOUNDATION','ANCHOR_REFERENCE']='UNVERIFIED'
 reviewed_dimensions_mm:list[float]|None=Field(default=None,min_length=2,max_length=2)
 material:str=Field(default='',max_length=200)
 property_classification:Classification='UNVERIFIED'
 source_reference:str=Field(default='',max_length=600)
 correction_reason:str=Field(default='',max_length=600)
 matched_saved_component_id:str|None=None
class Review(Strict):
 corrections:list[Correction]=Field(max_length=2000)
 reviewed_by:str=Field(min_length=3,max_length=120)
 acknowledge_missing_engineering_inputs:Literal[True]

def review(source,inputs,document):
 q=Review.model_validate(inputs).model_dump();by={e['id']:e for e in source['entities']};ids=set();saved={c['id'] for c in document['components']}
 for c in q['corrections']:
  if c['entity_id'] not in by or c['entity_id'] in ids:raise ValueError('Corrections must retain distinct known source entity identities')
  ids.add(c['entity_id'])
  if c['role']=='ANCHOR_REFERENCE' and by[c['entity_id']]['kind']!='CIRCLE':raise ValueError('Anchor reference role requires a source reference circle; not a physical bolt')
  if c['role'] not in ['UNVERIFIED','ANCHOR_REFERENCE'] and by[c['entity_id']]['kind'] not in ['LINE','POLYLINE','LWPOLYLINE']:raise ValueError('Structural candidate role requires supported source linework; annotations are not structural members')
  if c['matched_saved_component_id'] is not None and c['matched_saved_component_id'] not in saved:raise ValueError('Mapping must identify an actual saved component; no inferred mapping')
  if source['classification']=='SYNTHETIC_VERIFICATION' and c['property_classification']=='REAL_PROJECT':raise ValueError('Synthetic drawing review cannot promote data to REAL PROJECT')
  if c['reviewed_dimensions_mm'] and any(v<=0 or v>1e7 for v in c['reviewed_dimensions_mm']):raise ValueError('Reviewed plan dimensions must be finite positive millimetres')
  if (c['material'] or c['reviewed_dimensions_mm'] or c['role']!='UNVERIFIED' or c['matched_saved_component_id']) and min(len(c['source_reference'].strip()),len(c['correction_reason'].strip()))<10:raise ValueError('Source reference and correction/review reason required for each declared property or mapping')
 return dict(inputs=q,classification=source['classification'],source_sha256=source['source_sha256'],analytical_model=dict(status='BLOCKED_MISSING_SUPPORTED_3D_ENGINEERING_INPUTS',nodes=[],members=[],reviewed_source_candidates=[dict(source_entity_id=c['entity_id'],declared_role=c['role'],matched_saved_component_id=c['matched_saved_component_id']) for c in q['corrections']],missing=MISSING,reason='Plan reference and nominal boxes do not supply a complete analytical graph. No invented elevations, materials, loads or joint connections.'),engineering_approval='DISABLED')
