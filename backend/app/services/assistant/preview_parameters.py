"""Conservative review derivation; never upgrades geometry to survey facts."""
def preview_parameters(design):
    if design.get('inputSource')!='PREVIEW_ASSUMPTION':return []
    result=[]
    fields={'size','radiusM','widthM','heightM','thicknessM','depthM','spacingM','spacingXM','spacingYM','count','rows','columns','headingDeg','distanceM','startChainageM'}
    for obj in design.get('objects',[]):
        for key,value in obj.get('parameters',{}).items():
            if key in fields:
                unit='count' if key in {'count','rows','columns'} else 'deg' if key=='headingDeg' else 'm'
                result.append({'objectId':obj['objectId'],'parameter':key,'value':value,'unit':unit,'source':'PREVIEW_ASSUMPTION'})
        parameters=obj.get('parameters',{})
        for key in ('center','start','end','origin'):
            if key in parameters:
                result.append({'objectId':obj['objectId'],'parameter':key+'LocalVisualZ','value':parameters[key][2],'unit':'m','source':'PREVIEW_ASSUMPTION'})
    return result
