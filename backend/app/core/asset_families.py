"""Semantic catalogue overlay. Legacy generator routing and catalogue IDs stay unchanged."""
from dataclasses import dataclass
from app.core.project_catalog import ASSET_DEFINITIONS


@dataclass(frozen=True)
class AssetFamily:
    id: str
    display_name: str
    component_kinds: tuple[str, ...]
    selection_kinds: tuple[str, ...] = ()


COMPONENT_KINDS = {name: name.replace("_", " ").title() for name in (
    "ALIGNMENT", "CARRIAGEWAY", "LANE", "SHOULDER", "MEDIAN", "VERGE", "SURFACE", "ROADWAY", "FLOOR", "ROOM", "WALL", "OPENING", "SLAB", "BEAM", "COLUMN", "FOUNDATION",
    "DECK", "PIER", "ABUTMENT", "PIPE", "CHANNEL", "DRAIN", "CULVERT", "SHAFT", "RETAINING_WALL", "EXCAVATION",
    "EMBANKMENT", "EARTHWORK", "UTILITY_ROUTE")}
FAMILIES: dict[str, AssetFamily] = {}


def register_component(kind: str, display_name: str):
    if kind in COMPONENT_KINDS:
        raise ValueError("COMPONENT_ALREADY_REGISTERED")
    COMPONENT_KINDS[kind] = display_name


def register_family(family: AssetFamily):
    if family.id in FAMILIES or any(k not in COMPONENT_KINDS for k in family.component_kinds):
        raise ValueError("INVALID_FAMILY_REGISTRATION")
    FAMILIES[family.id] = family


for name, components, selections in (
    ("BUILDING", "FLOOR ROOM WALL OPENING SLAB BEAM COLUMN FOUNDATION", "AREA"),
    ("ROAD", "ALIGNMENT ROADWAY CARRIAGEWAY LANE SHOULDER MEDIAN VERGE SURFACE DRAIN EARTHWORK", "ROUTE ENDPOINTS"),
    ("BRIDGE", "ALIGNMENT DECK PIER ABUTMENT FOUNDATION", "CROSSING ENDPOINTS"),
    ("RAIL", "ALIGNMENT SURFACE EARTHWORK", "ROUTE ENDPOINTS"),
    ("TUNNEL", "ALIGNMENT SHAFT SURFACE DRAIN", "ROUTE ENDPOINTS"),
    ("RETAINING", "RETAINING_WALL FOUNDATION DRAIN", "ROUTE"),
    ("EARTHWORK", "SURFACE EXCAVATION EMBANKMENT EARTHWORK", "AREA"),
    ("DRAINAGE", "ALIGNMENT CHANNEL DRAIN PIPE", "AREA ROUTE POINT"),
    ("CULVERT", "CULVERT PIPE CHANNEL FOUNDATION", "CROSSING"),
    ("PIPELINE", "ALIGNMENT PIPE", "ROUTE ENDPOINTS"),
    ("WATER", "SURFACE CHANNEL PIPE FOUNDATION", "AREA ROUTE POINT"),
    ("DAM", "SURFACE FOUNDATION EMBANKMENT CHANNEL", "AREA ROUTE"),
    ("MARINE", "DECK PIER FOUNDATION SURFACE", "AREA ROUTE"),
    ("UTILITY", "UTILITY_ROUTE PIPE FOUNDATION", "ROUTE POINT"),
    ("ENERGY", "SURFACE FOUNDATION UTILITY_ROUTE", "AREA"),
    ("SITE", "ALIGNMENT SURFACE EARTHWORK", "AREA"),
    ("CUSTOM", "", "AREA ROUTE CROSSING POINT ENDPOINTS"),
):
    register_family(AssetFamily(name, name.title(), tuple(components.split()), tuple(selections.split())))

GROUPS = {
    "ROAD": "road highway expressway urban_street rural_road service_road access_road approach_road construction_access_road farm_road roundabout airport_runway taxiway apron pedestrian_walkway cycleway",
    "BRIDGE": "flyover interchange interchange_transport trumpet_interchange cloverleaf_interchange bridge highway_bridge railway_bridge pedestrian_bridge cycle_bridge beam_bridge box_girder_bridge arch_bridge truss_bridge cable_stayed_bridge suspension_bridge",
    "RAIL": "railway metro_light_rail monorail rail_yard rail_station_platform",
    "TUNNEL": "tunnel road_tunnel rail_tunnel underpass",
    "BUILDING": "airport_terminal_massing bus_terminal truck_terminal parking_structure building residential_building commercial_building office_building institutional_building hospital school_campus_building hotel warehouse industrial_building high_rise_tower observation_tower canopy_shelter warehouse_complex greenhouse_layout data_center_massing foundation raft_foundation pile_foundation footing_layout",
    "RETAINING": "retaining_wall gravity_retaining_wall cantilever_retaining_wall reinforced_earth_wall flood_wall noise_barrier boundary_wall",
    "DAM": "dam gravity_dam arch_dam embankment_dam rockfill_dam spillway weir_barrage",
    "CULVERT": "culvert box_culvert pipe_culvert cross_drain",
    "DRAINAGE": "drainage stormwater_drain open_drain underground_drain drainage_canal sewer_network stormwater_basin agricultural_drainage detention_pond retention_pond",
    "PIPELINE": "pipeline sewer_pipeline stormwater_pipeline oil_pipeline gas_pipeline fuel_pipeline district_heating_cooling_pipeline water_supply_pipeline",
    "EARTHWORK": "site_grading earthwork_platform cut_fill_area excavation embankment slope_stabilization levee_dike material_stockpile",
    "UTILITY": "utility_crossing utility_corridor underground_cable_route electrical_distribution_line transmission_line transmission_tower substation transformer_yard telecom_duct fiber_optic_corridor telecom_tower cell_tower communication_mast fiber_route conveyor_corridor",
}
CATEGORY_FAMILY = {"transport":"SITE","structures":"BUILDING","water":"WATER","utilities":"UTILITY","energy":"ENERGY",
    "marine":"MARINE","civil":"SITE","industrial":"SITE","environmental":"SITE","agriculture":"SITE","telecom":"UTILITY","other":"CUSTOM"}
OVERRIDES = {asset:family for family,assets in GROUPS.items() for asset in assets.split()}
OVERRIDES.update(parking="SITE",water_tank="WATER",canal="WATER",irrigation_network="WATER",farm_reservoir="WATER",solar_agriculture_layout="ENERGY",cofferdam="CUSTOM")


def asset_definition(asset_type: str):
    key=asset_type.strip().lower().replace(" ","_").replace("-","_")
    catalogue=ASSET_DEFINITIONS.get(key)
    family=OVERRIDES.get(key) or (CATEGORY_FAMILY.get(catalogue["category"],"CUSTOM") if catalogue else "CUSTOM")
    entry=FAMILIES[family]
    return {"assetType":catalogue["id"] if catalogue else asset_type,"family":family,
        "displayName":(catalogue.get("label") or catalogue.get("name") or key.replace("_"," ").title()) if catalogue else asset_type.replace("_"," ").title(),
        "componentKinds":list(entry.component_kinds),"catalogueId":catalogue["id"] if catalogue else None,
        "mappingSource":"EXPLICIT" if key in OVERRIDES else "CATEGORY" if catalogue else "CUSTOM",
        "specialistModule":None,"generationStatus":"UNSUPPORTED"}


def catalogue_coverage():
    mapped=[asset_definition(key) for key in ASSET_DEFINITIONS]
    return {"total":len(mapped),"explicit":sum(a["mappingSource"]=="EXPLICIT" for a in mapped),
        "category":sum(a["mappingSource"]=="CATEGORY" for a in mapped),"custom":sum(a["family"]=="CUSTOM" for a in mapped),"assets":mapped}
