"""One bounded physical-to-analytical mapping: vertical solid rectangular column."""
from copy import deepcopy
import math
from app.services.design import opensees_benchmark as solver

CORE_COLUMNS = {f'industrial-platform-5x3:column-{name}' for name in ('ne','nw','se','sw')}


def geometry(document, component_id):
    if document.get('units') != 'metric' or document.get('metadata', {}).get('frame') != 'local_enu_meters':
        raise ValueError('Saved metric geometry in local ENU metres is required.')
    matches = [c for c in document.get('components', []) if c.get('id') == component_id]
    if len(matches) != 1 or component_id not in CORE_COLUMNS:
        raise ValueError('Select exactly one existing maintenance-platform column.')
    c = matches[0]
    if c.get('category') != 'column' or c.get('geometry', {}).get('kind') != 'box':
        raise ValueError('Only uniform box column geometry is supported.')
    t = c.get('transform', {})
    size, position, rotation, scale = [c.get('geometry', {}).get('size'), t.get('position'), t.get('rotation_deg'), t.get('scale')]
    if any(not isinstance(v, list) or len(v) != 3 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in v) for v in (size,position,rotation,scale)):
        raise ValueError('Finite explicit saved dimensions and transforms are required.')
    if any(x <= 0 for x in size) or any(abs(x-1)>1e-8 for x in scale):
        raise ValueError('Positive box dimensions and unit scales are required.')
    if any(abs(x)>1e-8 for x in rotation[:2]):
        raise ValueError('Tilted columns are unsupported; the saved column must be vertical.')
    if c.get('parent_id') is not None:
        raise ValueError('Nested component transforms are unsupported.')
    return {'component_id':component_id,'name':c.get('name', component_id),
        'length_m':size[2],'width_m':size[0],'depth_m':size[1],
        'base_enu_m':[position[0],position[1],position[2]-size[2]/2],
        'head_enu_m':[position[0],position[1],position[2]+size[2]/2],
        'axis_enu':[0,0,1],'rotation_deg':rotation,'component_sha256':solver.digest(c),
        'validation':'Saved geometry and transform consistency only; engineering status remains unverified',
        'excluded_component_ids':[other['id'] for other in document.get('components',[]) if other['id'] != component_id]}


def parameters(physical, inputs):
    if not math.isclose(inputs['section_width_m'],physical['width_m'],abs_tol=1e-6,rel_tol=0) or not math.isclose(inputs['section_depth_m'],physical['depth_m'],abs_tol=1e-6,rel_tol=0):
        raise ValueError('Declared solid rectangular section dimensions must match the saved column. Hollow/rolled sections are unsupported.')
    q = {'length_m':physical['length_m'],'area_m2':inputs['section_width_m']*inputs['section_depth_m'],
        'elastic_modulus_pa':inputs['elastic_modulus_pa'], 'support_stiffness_n_per_m':inputs['support_stiffness_n_per_m'],
        'compression_n':inputs['compression_n']}
    solver.axial_values(q)
    delta = q['compression_n']*q['length_m']/(q['elastic_modulus_pa']*q['area_m2']) + q['compression_n']/q['support_stiffness_n_per_m']
    if delta > .01*q['length_m']:
        raise ValueError('Predicted displacement exceeds the supported small-displacement limit (1% of length). This is a model-validity limit, not a safety check.')
    return q


def independent_reference(q):
    # Separate two-DOF stiffness-equilibrium calculation, not solver output.
    kb = q['elastic_modulus_pa']*q['area_m2']/q['length_m']
    k, p = q['support_stiffness_n_per_m'], q['compression_n']
    a, b, c, d = kb+k, -kb, -kb, kb
    det = a*d-b*c
    if not math.isfinite(det) or det <= 0: raise ValueError('Reference system is singular or outside numeric range.')
    base, head = -b*p/det, a*p/det
    return {'base_displacement_m':base,'head_displacement_m':head,
        'shortening_m':head-base,'reaction_n':k*base,'compression_stress_pa':p/q['area_m2'],
        'formulas':{'shortening':'P L / (E A)','support_translation':'P / k','head_translation':'P L / (E A) + P / k','stress':'P / A','reaction':'P'},
        'matrix':[[a,b],[c,d]],'load_vector_n':[0,p]}


def run(physical, inputs):
    q = parameters(physical,inputs)
    result = solver.run_case(elements=inputs['elements'],units=inputs['solver_units'],axial_parameters=q)
    result.update(physical_component=deepcopy(physical),engineering_inputs=deepcopy(inputs),
        scope='Selected saved physical column, isolated linear axial response only',
        limitations=['Connections, base plates, anchors and foundations excluded from the analytical model',
                    'No bending, buckling, self-weight, lateral loading or frame load redistribution',
                    'Prescribed linear axial spring is an explicit support idealization, not soil/foundation design',
                    'Solid rectangular cross-section declaration required; hollow/rolled sections unsupported',
                    'No structural safety approval or design-code checks'])
    reference = independent_reference(q)
    result['independent_reference'] = reference
    if result['status'] == 'VERIFIED':
        values = result['values_si']
        comparisons = {'column_shortening_m':reference['shortening_m'], 'spring_settlement_m':reference['base_displacement_m'],
            'total_displacement_m':reference['head_displacement_m'],'reaction_n':reference['reaction_n'],
            'compression_stress_pa':reference['compression_stress_pa']}
        if not all(math.isclose(values[key],value,rel_tol=1e-6,abs_tol=1e-12) for key,value in comparisons.items()):
            result.update(status='FAILED',verified=False,error='Independent stiffness reference failed.')
        result['analytical_mapping'] = [{'node_id':n['id'],'component_id':physical['component_id'],
            'position_enu_m':[physical['base_enu_m'][0],physical['base_enu_m'][1],physical['base_enu_m'][2]+n['z_m']],
            'displacement_enu_m':[0,0,n['displacement_m']]} for n in result['nodes']]
    return result
