"""Traceable saved CAD geometry audit; never snaps geometry or supplies engineering values."""
from app.services.design import drawing_cad as cad,physical_frame as frame

MISSING=['Explicit E in Pa, A in m² and in-plane I in m⁴ for each selected solid rectangular member, with material/section sources','Explicit load magnitude/direction/source; no automatic slab or member self-weight','Explicit supported fixed-base restraints and source; no footing participation','Two independently reviewed analytical joints and exact rigid-offset vectors; geometric CAD attachments are not analytical joints']
def identity(c):
 m=c.get('metadata',{}).get('drawing_cad',{})
 if m.get('generator')!=cad.TAG or m.get('classification')!='SYNTHETIC_VERIFICATION' or c['id']!='drawing-cad:'+str(m.get('source_entity_id','')).removeprefix('dxf:') or m.get('component_sha256')!=cad.component_hash(c):raise ValueError('CAD component identity/geometry provenance mismatch; reviewed geometry authorization required')
 return dict(source_entity_id=m['source_entity_id'],source_sha256=m['source_sha256'],generator=m['generator'],component_sha256=cad.component_hash(c),classification=m['classification'],input_evidence=m['input'])
def audit(doc,ids):
 lookup={c['id']:c for c in doc['components']};members=[]
 if len(ids)!=3 or len(set(ids))!=3:raise ValueError('Select exactly three distinct CAD-derived member identities')
 for id in ids:
  c=lookup.get(id)
  if not c or not cad.is_generated(c) or c['category'] not in ['column','beam']:raise ValueError('Only actual saved CAD columns and beam supported; slab/footing participation excluded')
  provenance=identity(c);p=c['transform']['position'];s=c['geometry'].get('size',[])
  if c['geometry']['kind']!='box' or len(s)!=3:raise ValueError('Supported reviewed rectangular envelopes required')
  axis=2 if c['category']=='column' else 0
  members.append(dict(component_id=id,name=c['name'],category=c['category'],size_m=s,position_enu_m=p,axis='Up' if axis==2 else 'East',centerline_enu_m=[[p[i]+(sign*s[i]/2 if i==axis else 0) for i in range(3)] for sign in [-1,1]],source=provenance))
 columns=sorted([m for m in members if m['category']=='column'],key=lambda m:m['position_enu_m'][0]);beams=[m for m in members if m['category']=='beam']
 if len(columns)!=2 or len(beams)!=1:raise ValueError('Select two CAD columns and one CAD beam')
 offsets=[]
 for c,end in zip(columns,beams[0]['centerline_enu_m']):
  top=c['centerline_enu_m'][1];offset=[end[i]-top[i] for i in range(3)]
  offsets.append(dict(column_id=c['component_id'],beam_id=beams[0]['component_id'],column_top_enu_m=top,beam_end_enu_m=end,offset_enu_m=offset))
 try:g=frame.geometry(doc,ids,allow_rigid_offsets=True);blockers=[]
 except ValueError as e:g=None;blockers=[str(e)]
 return dict(status='BLOCKED_SAVED_GEOMETRY_OUTSIDE_SOLVER_DOMAIN' if blockers else 'GEOMETRY_CANDIDATE_EXPLICIT_INPUTS_REQUIRED',members=members,observed_connections=offsets,column_top_difference_m=columns[0]['centerline_enu_m'][1][2]-columns[1]['centerline_enu_m'][1][2],geometry_blockers=blockers,missing_inputs=MISSING,candidate_graph=g,engineering_approval='DISABLED',code_checks='DISABLED',limitations=frame.LIMITS,notice='Original unequal heights retained. Explicit vertical nodal, beam uniform and sourced member self-weight cases are supported only after individual rigid-joint review, section/material/support declarations and exact authorization. No slab distribution or foundation behavior.' if doc.get('metadata',{}).get('unequal_gravity_review') else 'Original unequal CAD heights are retained in this dedicated scope. Four actual retained nodes and two separately reviewed short rigid offsets are required; no automatic alignment or connection. Horizontal nodal verification only; no slab/footing participation.' if doc.get('metadata',{}).get('unequal_frame_review') else 'Geometry facts only. Unequal heights remain blocked by the existing solver. An engineer may explicitly edit a review copy through CAD preview/authorization, or retain the blocker. No automatic alignment, touching-object connection, slab or footing participation.')
