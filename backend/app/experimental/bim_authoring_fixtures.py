"""Finite offline data demonstrations, not asset-specific execution adapters."""
from copy import deepcopy
from app.domain.bim_authoring import AuthoringBundle
from app.experimental.cad_contract import digest


def _resources():
    def section(id,profile,**values):
        return dict(id=id,profile=profile,parameters=[dict(id=k,value=v,unit="m") for k,v in values.items()])
    return [dict(id="concrete",name="Concept concrete",category="CONCRETE"),dict(id="steel",name="Concept steel",category="STEEL")],[
        section("circle","CIRCLE",radius=.2),section("i-section","I",width=.3,depth=.5,web=.02,flange=.03),
        section("rectangle","RECTANGLE",width=.25,depth=.4),section("bearing-section","RECTANGLE",width=.35,depth=.35)]


def _structure(prefix,asset_type,bridge=False,offset=0):
    assemblies,expansions,connections=[],[],[]
    asset=prefix+"-asset"
    def assembly(name,parent=None):
        id=prefix+"-"+name
        assemblies.append(dict(id=id,asset_id=asset,parent_id=parent,role=name.upper(),groups=[],placement=dict(origin=[offset if parent is None else 0,0,0])))
        expansions.append(dict(assembly_id=id,components=[]))
        return id
    def add(assembly,id,kind,role,operation,parameters,origin,section=None,horizontal=False,heading=0):
        id=prefix+"-"+id
        group=id+"-group"
        next(a for a in assemblies if a["id"] == assembly)["groups"].append(dict(id=group,role=role,component_type=kind,count=1))
        next(e for e in expansions if e["assembly_id"] == assembly)["components"].append(dict(id=id,group_id=group,role=role,component_type=kind,
            material_id="concrete" if kind in {"COLUMN","PIER","SLAB","DECK"} else "steel",
            parameters=[dict(id=k,value=float(v),unit="m") for k,v in parameters.items()],placement=dict(origin=origin,heading_deg=heading),
            cross_section_id=section,recipe=dict(component_id=id,operation=operation,orientation="HORIZONTAL" if horizontal else "VERTICAL")))
        return id
    def connect(source,target=None,kind="SUPPORTED_BY"):
        id=prefix+"-connection-"+str(len(connections))
        connections.append(dict(id=id,from_component_id=source,to_component_id=target,
            external_support="UNKNOWN_FOUNDATION" if target is None else None,kind=kind,
            explanation="Conceptual connection intent only; support, loading and connection detail require engineering review."))
    columns=assembly("pier-assemblies" if bridge else "column-assemblies")
    frame=assembly("superstructure" if bridge else "framing",columns)
    topping=assembly("deck-assembly" if bridge else "slab-assembly",frame)
    length=6 if bridge else 5
    piers=[add(columns,f"column-{i}","PIER" if bridge else "COLUMN","SUBSTRUCTURE_SUPPORT","CIRCULAR_COLUMN",dict(length=3),origin,"circle")
        for i,origin in enumerate([(0,0,0),(length,0,0),(0,3,0),(length,3,0)])]
    for p in piers:connect(p)
    supports=piers
    if bridge:
        bearings=assembly("bearing-representations",columns)
        supports=[add(bearings,f"bearing-{i}","BEARING","CONCEPTUAL_BEARING_BLOCK","PROFILE_EXTRUSION",dict(length=.1),origin,"bearing-section")
            for i,origin in enumerate([(0,0,3),(length,0,3),(0,3,3),(length,3,3)])]
        for bearing,pier in zip(supports,piers):connect(bearing,pier)
    primary=[add(frame,f"primary-{i}","GIRDER" if bridge else "BEAM","LONGITUDINAL_GIRDER" if bridge else "PRIMARY_BEAM","PROFILE_EXTRUSION",dict(length=length),(0,y,3.4),"i-section",True) for i,y in enumerate([0,3])]
    for i,p in enumerate(primary):
        for support in supports[i*2:i*2+2]:connect(p,support)
    transverse=assembly("diaphragms",frame) if bridge else frame
    for i in range(2):
        second=add(transverse,f"secondary-{i}","BEAM","DIAPHRAGM" if bridge else "SECONDARY_BEAM","PROFILE_EXTRUSION",
            dict(length=3 if bridge else length),((i+1)*2,0,3.4) if bridge else (0,i+1,3.4),"rectangle",True,90 if bridge else 0)
        for p in primary:connect(second,p)
    slab=add(topping,"deck" if bridge else "platform","DECK" if bridge else "SLAB","OPENING_DECK" if bridge else "ACCESS_SLAB",
        "RECTANGULAR_OPENING",dict(width=length,depth=3,thickness=.2,hole_width=.8,hole_depth=.6),(length/2,1.5,3.7))
    for p in primary:connect(slab,p)
    if not bridge:
        plate=add(topping,"plate","PLATE","CONNECTION_PLATE","CIRCULAR_HOLE",dict(width=.4,depth=.4,thickness=.02,hole_radius=.04),(0,0,3.72))
        connect(plate,primary[0],"CONNECTS_TO")
        for i in range(2):
            brace=add(frame,f"brace-{i}","BRACING","PLANAR_TIE_REPRESENTATION","PROFILE_EXTRUSION",dict(length=2), (i*2,0,3.4),"rectangle",True,45)
            connect(brace,primary[0],"CONNECTS_TO")
    all_ids=[c["id"] for e in expansions for c in e["components"]]
    return dict(asset=dict(id=asset,system_request_id=prefix+"-system",asset_type=asset_type,name=prefix+" concept"),
        system=dict(id=prefix+"-system",asset_type=asset_type,purpose="Offline conceptual shared-component assembly",compatible_selection_kinds=["AREA"]),
        assemblies=assemblies,expansions=expansions,connections=connections,
        clearances=[dict(id=prefix+"-clearance",component_ids=all_ids,explanation="Member/support/deck clearances have no validated rule set.")],
        dependencies=[dict(id=prefix+"-length-copy",source_component_id=primary[0],source_parameter_id="length",target_component_id=primary[1],target_parameter_id="length",operation="COPY")])


def authoring_case(name):
    """A-D share exactly the same contracts/mappings, irrespective of asset label."""
    require_names={"bridge","platform","mixed","unregistered","unsupported"}
    if name not in require_names:raise ValueError("UNKNOWN_OFFLINE_FIXTURE")
    parts=[_structure("bridge","BRIDGE",True)] if name in {"bridge","unsupported"} else [_structure("platform","INDUSTRIAL_PLATFORM")]
    if name == "mixed":parts=[_structure("bridge","BRIDGE",True),_structure("platform","INDUSTRIAL_PLATFORM",offset=20)]
    if name == "unregistered":parts=[_structure("custom","UNREGISTERED_OBSERVATION_STRUCTURE")]
    materials,sections=_resources()
    intent=dict(requested_structure=name+" detailed conceptual assembly",systems=[p["system"] for p in parts],
        requested_features=["I_SECTION","SLAB_OPENING"],assumptions=["All member dimensions are explicit preview assumptions, not structural sizing."])
    if name == "unsupported":intent["requested_features"].append("REINFORCEMENT_CAGE")
    from app.domain.bim_authoring import AuthoringIntent, AssemblyPlan
    intent=AuthoringIntent.model_validate(intent)
    plan=AssemblyPlan.model_validate(dict(intent_hash=digest(intent),assets=[p["asset"] for p in parts],assemblies=[a for p in parts for a in p["assemblies"]],materials=materials,cross_sections=sections))
    expansions=[dict(**deepcopy(e),plan_hash=digest(plan)) for p in parts for e in p["expansions"]]
    relationships=dict(plan_hash=digest(plan),connections=[c for p in parts for c in p["connections"]],clearances=[c for p in parts for c in p["clearances"]],dependencies=[c for p in parts for c in p["dependencies"]])
    return AuthoringBundle(intent=intent,plan=plan,expansions=expansions,relationships=relationships)
