"""Deterministic selection capabilities and server-projected local bounds."""
from shapely.geometry import shape

CONSTRAINTS={'AREA':['WITHIN_AREA','AVOID_AREA'],'ROUTE':['FOLLOW_ROUTE','START_AT','END_AT','AVOID_AREA'],
    'CROSSING':['FOLLOW_ROUTE','START_AT','END_AT','AVOID_AREA'],'ENDPOINTS':['START_AT','END_AT','AVOID_AREA'],'POINT':['AVOID_AREA']}

def selection_capabilities(kind):
    return {'selectionType':kind,'supportedConstraints':CONSTRAINTS.get(kind,[]),
        'placementBehavior':'Place relative to the saved local point; footprint and elevation remain unverified.' if kind=='POINT' else 'Use the saved LOCAL_ENU geometry; preview Z is not measured elevation.'}

def local_selection(summary):
    geometry=shape(summary['localGeometry'])
    usable=geometry.intersection(shape(summary['projectBoundaryLocal'])) if summary['selectionKind']=='AREA' and summary.get('projectBoundaryLocal') else geometry
    if usable.is_empty:
        from app.services.ai.provider import AssistantProviderError
        raise AssistantProviderError('NO_USABLE_SELECTION')
    x0,y0,x1,y1=usable.bounds
    result={'coordinateFrame':'LOCAL_ENU','selectionType':summary['selectionKind'],'geometry':summary['localGeometry'],
        'boundingBox':{'minX':x0,'minY':y0,'maxX':x1,'maxY':y1},'widthM':x1-x0,'heightM':y1-y0,
        'centroid':[usable.centroid.x,usable.centroid.y],'usableCoordinateRange':{'x':[x0,x1],'y':[y0,y1],'z':'UNKNOWN; preview only'},
        'orientationDeg':summary['origin']['heading_deg'] if summary['frameSource']=='SAVED_MODEL_PLACEMENT' else None,
        'capabilities':selection_capabilities(summary['selectionKind'])}
    if summary['selectionKind']=='AREA':result.update(localPolygon=summary['localGeometry'],usablePolygon=usable.__geo_interface__)
    return result
