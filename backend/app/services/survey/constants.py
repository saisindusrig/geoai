"""Survey mode constants and tier ordering."""

ACCURACY_TIERS = ("visual", "gis_grade", "survey_grade", "engineering_ready")

TIER_RANK = {t: i for i, t in enumerate(ACCURACY_TIERS)}

ENGINEERING_LAYER_TYPES = (
    "road_centerline",
    "road_edge",
    "parcel",
    "drain",
    "bridge",
    "retaining_wall",
    "utility",
    "construction_zone",
    "mask_source",
)

DATASET_KINDS = ("orthomosaic", "dem", "lidar", "cad", "vector", "osm_context")

GCP_SOURCES = ("RTK", "DGPS", "CORS", "manual")

# Survey-grade cut/fill requires DEM resolution <= this (meters)
SURVEY_DEM_MAX_PIXEL_M = 0.5

GCP_MIN_FOR_SURVEY = 3

SURVEY_RMSE_H_MAX_M = 0.05
SURVEY_RMSE_V_MAX_M = 0.10

VISUAL_BASEMAP_WARNING = (
    "Public satellite/3D map data is for visualization and planning only. "
    "Final construction quantities and dimensions require licensed survey/LiDAR/RTK data."
)
