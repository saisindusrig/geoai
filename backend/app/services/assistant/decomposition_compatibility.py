"""Bounded semantic compatibility, never geometry generation or AI reasoning."""
import re
from collections import Counter

GROUPS={
    'BRIDGE':{'BRIDGE','PEDESTRIAN_BRIDGE','BRIDGE_ALIGNMENT','BRIDGE_DECK','BRIDGE_SUPPORT','ABUTMENT','PIER','APPROACH'},
    'WAREHOUSE':{'WAREHOUSE','WAREHOUSE_SHELL','WAREHOUSE_COLUMNS'},
    'PARKING':{'PARKING','PARKING_SURFACE','PARKING_ZONE'},
    'ROAD':{'ROAD','ACCESS_ROAD','ACCESS_PATH','ROAD_SURFACE'},
}
PARTS={'BRIDGE':{'ALIGNMENT','PATH','DECK','PIER','PIERS','ABUTMENT','ABUTMENTS','SUPPORT','SUPPORTS','COLUMN','APPROACH','APPROACHES'},
    'WAREHOUSE':{'SHELL','WALL','WALLS','COLUMN','COLUMNS','ROOF','SLAB','FOUNDATION'}}
def group(value):
    value=value.upper()
    return next((key for key,values in GROUPS.items() if value in values),value)

def compatibility(classified,design,user_text=''):
    expected={group(a['assetType']) for a in classified}
    # Reuse deterministic request parsing, never infer an extra asset from a
    # model-authored relationship. Negated/ambiguous requests remain conservative.
    if user_text and not re.search(r'\b(no|not|without|avoid|exclude|remove|delete)\b',user_text,re.I):
        from app.services.assistant.decomposition import decompose
        expected.update(group(a['assetType']) for a in decompose(user_text) if a['assetType']!='UNREGISTERED_CIVIL_ASSET')
    systems=design.get('systems',[]); covered=set();issues=[]; assignments={}
    by_id={s['id']:s for s in systems}
    object_system={o['objectId']:o['systemId'] for o in design.get('objects',[])}
    for system in systems:
        family=group(system.get('assetType',''));role=system.get('role','').upper();semantic=system.get('semanticType','').upper()
        if family not in expected:
            parents=[key for key in expected if family in PARTS.get(key,set()) or (system.get('assetType','').upper() in PARTS.get(key,set()))]
            if len(parents)>1:
                related=set()
                for relation in design.get('relationships',[]):
                    if relation.get('kind') not in {'CONTAINS','SUPPORTED_BY','CONNECTS_TO'}:continue
                    ends=[object_system.get(relation.get(key),relation.get(key)) for key in ('fromId','toId')]
                    if system['id'] in ends:
                        related.update(group(by_id[id]['assetType']) for id in ends if id!=system['id'] and id in by_id)
                parents=[key for key in parents if key in related]
            family=parents[0] if len(parents)==1 else family
        recognized_assets=set().union(*GROUPS.values())|{'DAM','AIRPORT','PIPELINE','DRAINAGE','WATER_TANK'}
        if family not in expected or any(group(value)!=family and value in recognized_assets and value not in PARTS.get(family,set()) for value in (role,semantic)):
            issues.append({'code':'UNEXPECTED_SYSTEM','systemId':system.get('id'),'assetType':system.get('assetType')});continue
        covered.add(family);assignments[system['id']]=family
    for missing in sorted(expected-covered):issues.append({'code':'MISSING_REQUIRED_SYSTEM','assetType':missing})
    required_parts={'BRIDGE_ALIGNMENT':{'ALIGNMENT','PATH'},'BRIDGE_DECK':{'DECK'},'BRIDGE_SUPPORT':{'SUPPORT','SUPPORTS','PIER','PIERS','COLUMN','COLUMNS','ABUTMENT','ABUTMENTS'}}
    roles={s.get(k,'').upper() for s in systems for k in ('role','semanticType')}
    roles.update(o.get(k,'').upper() for o in design.get('objects',[]) for k in ('role','semanticType'))
    for asset in classified:
        part=asset['assetType'].upper()
        if part in required_parts and not roles.intersection(required_parts[part]):issues.append({'code':'MISSING_REQUIRED_SYSTEM','assetType':part})
    words={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
    quantity_checked=set()
    for number,noun in re.findall(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(warehouses?|bridges?|parking(?:\s+areas?)?|roads?)\b',user_text.lower()):
        family=group({'warehouses':'WAREHOUSE','warehouse':'WAREHOUSE','bridges':'BRIDGE','bridge':'BRIDGE','roads':'ROAD','road':'ROAD'}.get(noun,'PARKING'))
        count=int(number) if number.isdigit() else words[number]
        quantity_checked.add(family)
        roots=[s for s in systems if assignments.get(s['id'])==family and s.get('role','').upper() in {family,'PEDESTRIAN_BRIDGE','WAREHOUSE_SHELL','SHELL'}]
        # Quantity requires identifiable asset instances; incidental columns/paths
        # cannot silently count as another warehouse/bridge.
        if len(roots)!=count:issues.append({'code':'QUANTITY_MISMATCH','assetType':family,'expected':count,'actual':len(roots)})
    if user_text and not re.search(r'\b(no|not|without|avoid|exclude|remove|delete)\b',user_text,re.I):
        counts=Counter(group(a['assetType']) for a in decompose(user_text))
        for family,count in counts.items():
            if count<=1 or family in quantity_checked:continue
            roots=[s for s in systems if assignments.get(s['id'])==family and s.get('role','').upper() in {family,'PEDESTRIAN_BRIDGE','WAREHOUSE_SHELL','SHELL'}]
            if len(roots)!=count:issues.append({'code':'QUANTITY_MISMATCH','assetType':family,'expected':count,'actual':len(roots)})
    return {'status':'DECOMPOSITION_COMPATIBLE' if not issues else issues[0]['code'],'issues':issues,'systemAssignments':assignments}

def require_compatible(classified,arguments,user_text):
    from app.services.ai.provider import AssistantProviderError
    generic=[a for a in arguments.get('assets',[]) if a.get('ai3dDesign')]
    if len(generic)==1 and len(arguments['assets'])==1 and generic[0].get('assetType')=='AI3D_DESIGN':
        result=compatibility(classified,generic[0]['ai3dDesign'],user_text)
        if result['issues']:raise AssistantProviderError(result['status'],result)
        return result
    if Counter(a['assetType'].upper() for a in classified)!=Counter(a.get('assetType','').upper() for a in arguments.get('assets',[])):
        raise AssistantProviderError('ASSET_DECOMPOSITION_MISMATCH')
