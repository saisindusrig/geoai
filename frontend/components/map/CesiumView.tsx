"use client";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

import {
  applyGlobeTranslucency,
  cesiumDevLog,
  corridorRing,
  sampleTerrainHeightM,
  createFlatTerrain,
  buildDesignModelMatrix,
  resetGlobeTranslucency,
  resetImageryAlpha,
  estimateBuildingHeight,
  objectInfoFromFeature,
  roadWidthM,
  type Scene3DLayerKey,
} from "@/lib/cesium-scene";
import {
  createPhotorealisticTileState,
  destroyPhotorealisticTiles,
  setPhotorealisticTilesVisible,
  syncPhotorealisticTiles,
  type PhotorealisticTileState,
} from "@/lib/cesium-photorealistic-tiles";
import { lineLengthM } from "@/lib/geo";
import {
  fetchMapRuntimeConfig,
  loadCesiumBasemapProvider,
  type MapBasemap,
} from "@/lib/map-imagery";
import { MAP_COLORS } from "@/lib/map-colors";
import { designModelAnchor, alignmentBearing, modelLayerVisibility } from "@/lib/project-workflow";
import { applyDesignMeshVisibilityWhenReady } from "@/lib/design-mesh-layers";
import type { EditableModelDocument, GeoJSONFeature, GeoJSONGeometry } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buildSandboxMapPrimitives } from "@/lib/sandbox-cesium";
import { measurementValues, measurementClassification, type MeasurementPoint } from "@/lib/engineering-measurement";
import type { AnalysisClip } from "@/lib/editor-clipping";
import { installCesiumTransform } from "@/lib/cesium-transform";
import EngineeringEvidencePanel from "@/components/map/EngineeringEvidencePanel";
import SunStudyControls from "@/components/map/SunStudyControls";
import { resolveAutomaticTerrain } from "@/lib/automatic-terrain";
import { modelDisplayElevation, globalBuildingsVisible } from "@/lib/model-display-elevation";
import { api } from "@/lib/api";
import { useWorkspaceMap } from "@/components/layout/WorkspaceMapContext";

interface CesiumViewProps {
  localSandbox?: boolean;
  projectId?: number;
  center: [number, number];
  boundary?: GeoJSONGeometry | null;
  alignment?: GeoJSONGeometry | null;
  modelUrl?: string | null;
  excavationUrl?: string | null;
  useModelLayers?: boolean;
  roadFeatures?: GeoJSONFeature[];
  buildingFeatures?: GeoJSONFeature[];
  waterFeatures?: GeoJSONFeature[];
  surveyGcpFeatures?: GeoJSONFeature[];
  surveyMode?: boolean;
  disableVendor3DTiles?: boolean;
  basemap?: MapBasemap;
  modelOpacity?: number;
  terrainExaggeration?: number;
  editor?: EditableModelEditor;
  editableModel?: EditableModelDocument | null;
  modelRevisionId?: number;
  selectedComponentIds?: string[];
  onSelectComponent?: (id: string | null, additive?: boolean) => void;
  fitRequest?: number;
}

const LAYER_DS: Scene3DLayerKey[] = [
  "roads",
  "buildings",
  "water",
  "trees",
  "pipeline",
  "construction",
  "labels",
];

type CesiumInputHandler = {
  isDestroyed?: () => boolean;
  destroy: () => void;
};

function destroyInputHandler(handler: CesiumInputHandler | null | undefined) {
  if (!handler) return;
  try {
    if (handler.isDestroyed?.()) return;
    handler.destroy();
  } catch {
    /* handler or viewer already torn down */
  }
}

export default function CesiumView({
  localSandbox = false,
  projectId,
  center,
  boundary,
  alignment,
  modelUrl,
  excavationUrl,
  useModelLayers = false,
  roadFeatures = [],
  buildingFeatures = [],
  waterFeatures = [],
  surveyGcpFeatures = [],
  surveyMode = false,
  disableVendor3DTiles = false,
  basemap = "satellite",
  modelOpacity = 1,
  terrainExaggeration = 1,
  editor,
  editableModel,
  modelRevisionId,
  selectedComponentIds = [],
  onSelectComponent,
  fitRequest = 0,
}: CesiumViewProps) {
  const { creditsContainer } = useWorkspaceMap();
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const cesiumRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dataSourcesRef = useRef<Map<string, any>>(new Map());
  const photorealisticTilesRef = useRef<PhotorealisticTileState>(createPhotorealisticTileState());
  const [acceptedPlacement, setAcceptedPlacement] = useState<{ longitude: number; latitude: number; elevation: number; offset: number; heading: number; status: string;vertical_reference?:{type?:string};terrain_version_id?:number|null } | null>(null);
  const [terrainStatus, setTerrainStatus] = useState("WORLD TERRAIN · CHECKING");
  const [terrainDetail, setTerrainDetail] = useState("Selecting terrain automatically…");
  const [terrainRetry, setTerrainRetry] = useState(0);
  const [buildingStatus, setBuildingStatus] = useState<string | null>(null);
  const [projectTerrain, setProjectTerrain] = useState<{ id: number; state: string; ion_asset_id: number; coverage: GeoJSONGeometry } | null>(null);
  const measurePointsRef = useRef<[number, number, number][]>([]);
  const measurementSamples = useRef<MeasurementPoint[]>([]);
  const measurementRequest = useRef(0);
  const handlerRef = useRef<CesiumInputHandler | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const modelsRef = useRef<{ main: any; excav: any }>({ main: null, excav: null });
  const basemapRef = useRef(basemap);
  const mapRuntimeRef = useRef<{ cesium_ion_token: string | null; google_maps_api_key: string | null }>({
    cesium_ion_token: null,
    google_maps_api_key: null,
  });

  const [error, setError] = useState("");
  const [analysisClip, setAnalysisClip] = useState<AnalysisClip>({ mode: "off", value: 0, size: 50 });
  const [transformReadout, setTransformReadout] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  /** Bumped after terrain provider switches so clamped entities re-bind to the globe. */
  const [terrainEpoch, setTerrainEpoch] = useState(0);
  const layers = useProjectStore((s) => s.layers);
  const surveyLayers = useProjectStore((s) => s.surveyLayers);
  const modelLayers = useProjectStore((s) => s.modelLayers);
  const cesiumTool = useProjectStore((s) => s.cesiumTool);
  const scene3dLayers = useProjectStore((s) => s.scene3dLayers);
  const undergroundView = useProjectStore((s) => s.undergroundView);
  const scene3dMeasureTool = useProjectStore((s) => s.scene3dMeasureTool);
  const measurementReadout = useProjectStore((s) => s.scene3dMeasureReadout);
  const measureUnit = useProjectStore((s) => s.measureUnit);
  const designMeshCatalog = useProjectStore((s) => s.designMeshCatalog);
  const designMeshVisibility = useProjectStore((s) => s.designMeshVisibility);

  const centerLng = center[0];
  const centerLat = center[1];
  const sandboxBounds = useRef<import("cesium").BoundingSphere | null>(null);
  const sandboxWasFitted = useRef(false);
  const sandboxCameraReady = useRef(false);
  const sandboxFlightGeneration = useRef(0);
  const sandboxFitRequest = useRef(fitRequest);
  const sandboxLastOrigin = useRef<string | null>(null);
  const [sandboxHasImagery, setSandboxHasImagery] = useState(false);
  const [imageryError, setImageryError] = useState<string | null>(null);
  const placementProjectId = editableModel?.project_id ?? projectId;
  const previewLng = editableModel?.origin.lng ?? centerLng;
  const previewLat = editableModel?.origin.lat ?? centerLat;
  const [contextGround, setContextGround] = useState<{ lng: number; lat: number; epoch: number; height: number | null } | null>(null);
  const terrainReady = layers.terrain && (terrainStatus.includes("VISUAL REFERENCE") || terrainStatus.startsWith("PROJECT TERRAIN"));
  const previewHeight = !localSandbox && terrainReady && contextGround?.lng === previewLng && contextGround?.lat === previewLat && contextGround?.epoch === terrainEpoch ? contextGround.height : null;
  useEffect(()=>{window.dispatchEvent(new CustomEvent("geoai:terrain-changed",{detail:{version:projectTerrain?.id ?? null}}));},[terrainEpoch,projectTerrain?.id]);
  const displayElevation = modelDisplayElevation(editableModel?.origin.elevation_m ?? 0, acceptedPlacement, previewHeight);
  const visualGroundPreview = !acceptedPlacement && (editableModel?.origin.elevation_m ?? 0) === 0 && previewHeight !== null;
  useEffect(()=>{
    const locate=(event:Event)=>{
      const viewer=viewerRef.current,C=cesiumRef.current;
      if(!viewer || !C || viewer.isDestroyed())return;
      const id=(event as CustomEvent<string>).detail;
      const entity=dataSourcesRef.current.get("editable-model")?.entities.getById(`editable:${id}`);
      const position=entity?.position?.getValue(C.JulianDate.now());
      if(position)viewer.camera.flyToBoundingSphere(new C.BoundingSphere(position,15),{duration:0.7});
    };
    window.addEventListener("geoai:locate-component",locate);
    return()=>window.removeEventListener("geoai:locate-component",locate);
  },[]);
  useEffect(() => {
    const update = (event: Event) => setAnalysisClip((event as CustomEvent<AnalysisClip>).detail);
    window.addEventListener("geoai:analysis-clip",update);
    return () => window.removeEventListener("geoai:analysis-clip",update);
  }, []);
  useEffect(() => {
    const viewer=viewerRef.current, C=cesiumRef.current;
    if(!viewer || !C || !loaded) return;
    const highlight=(event:Event)=>{
      const point=(event as CustomEvent<{longitude?:number;latitude?:number;elevation?:number;local?:[number,number,number]}>).detail;
      const ds=getDs(viewer,C,"analysis-location"); ds.entities.removeAll();
      if(!point) {viewer.scene.requestRender();return;}
      let position;
      if(point.local && editableModel){
        const frame=C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(acceptedPlacement?.longitude ?? editableModel.origin.lng,acceptedPlacement?.latitude ?? editableModel.origin.lat,displayElevation));
        const heading=(acceptedPlacement?.heading ?? editableModel.origin.heading_deg)*Math.PI/180;
        const [x,y,z]=point.local;
        position=C.Matrix4.multiplyByPoint(frame,new C.Cartesian3(x*Math.cos(heading)-y*Math.sin(heading),x*Math.sin(heading)+y*Math.cos(heading),z),new C.Cartesian3());
      }else if(point.longitude != null && point.latitude != null && point.elevation != null) position=C.Cartesian3.fromDegrees(point.longitude,point.latitude,point.elevation);
      if(position)ds.entities.add({position,point:{pixelSize:10,color:C.Color.fromCssColorString("#c8ff32"),disableDepthTestDistance:Infinity}});
      viewer.scene.requestRender();
    };
    window.addEventListener("geoai:analysis-location",highlight);
    return ()=>window.removeEventListener("geoai:analysis-location",highlight);
  },[loaded,editableModel,acceptedPlacement,displayElevation]);
  useEffect(()=>{
    const viewer=viewerRef.current,C=cesiumRef.current;
    if(!loaded || !viewer || !C || !editableModel) return;
    if(analysisClip.mode !== "terrain") return;
    const previous=viewer.scene.globe.clippingPlanes;
    const clipping=new C.ClippingPlaneCollection({modelMatrix:C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(editableModel.origin.lng,editableModel.origin.lat,displayElevation)),planes:[new C.ClippingPlane(new C.Cartesian3(1,0,0),-analysisClip.value)],edgeWidth:1});
    viewer.scene.globe.clippingPlanes=clipping;
    viewer.scene.requestRender();
    return ()=>{if(!viewer.isDestroyed()){viewer.scene.globe.clippingPlanes=previous;viewer.scene.requestRender();}};
  },[loaded,analysisClip,editableModel,displayElevation]);


  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!loaded || !viewer || !Cesium || !terrainReady || localSandbox || acceptedPlacement || (editableModel?.origin.elevation_m ?? 0) !== 0) return;
    let cancelled = false;
    void sampleTerrainHeightM(Cesium, viewer.terrainProvider, previewLng, previewLat).then((height) => {
      if (!cancelled && !viewer.isDestroyed()) setContextGround({ lng: previewLng, lat: previewLat, epoch: terrainEpoch, height });
    });
    return () => { cancelled = true; };
  }, [loaded, terrainReady, terrainEpoch, previewLng, previewLat, localSandbox, acceptedPlacement, editableModel?.origin.elevation_m]);

  useEffect(() => {
    if (localSandbox || !placementProjectId) return;
    let cancelled = false;
    api.get<{ active_version_id: number | null; versions: { id: number; state: string; ion_asset_id: number; coverage: GeoJSONGeometry }[] }>(`/api/projects/${placementProjectId}/engineering/terrain-datasets`).then((result) => {
      if (!cancelled) setProjectTerrain(result.versions.find((v) => v.id === result.active_version_id) ?? null);
    }).catch(() => { if (!cancelled) setProjectTerrain(null); });
    return () => { cancelled = true; };
  }, [placementProjectId, localSandbox, terrainRetry]);
  useEffect(() => {
    if (localSandbox || !placementProjectId || !modelRevisionId) return;
    let cancelled = false;
    api.get<{ placement: typeof acceptedPlacement }>(`/api/projects/${placementProjectId}/engineering/placements/${modelRevisionId}`).then((result) => {
      if (!cancelled) setAcceptedPlacement(result.placement);
    }).catch(() => { if (!cancelled) setAcceptedPlacement(null); });
    return () => { cancelled = true; };
  }, [placementProjectId, modelRevisionId, localSandbox]);

  const fitProject = useCallback(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;
    const now = Cesium.JulianDate.now();
    const editable = dataSourcesRef.current.get("editable-model")?.entities.values ?? [];
    const points = editable
      .filter((entity: { id?: string; position?: { getValue?: (date: unknown) => unknown } }) => String(entity.id ?? "").startsWith("editable:"))
      .map((entity: { position?: { getValue?: (date: unknown) => unknown } }) => entity.position?.getValue?.(now))
      .filter(Boolean);
    const mainSphere = modelsRef.current.main?.boundingSphere;
    const excavSphere = modelsRef.current.excav?.boundingSphere;
    const alignmentPoints = alignment?.type === "LineString"
      ? Cesium.Cartesian3.fromDegreesArray((alignment.coordinates as [number, number][]).flat())
      : [];
    const sphere = localSandbox && sandboxBounds.current ? sandboxBounds.current : points.length
      ? Cesium.BoundingSphere.fromPoints(points)
      : mainSphere ?? excavSphere ?? (alignmentPoints.length ? Cesium.BoundingSphere.fromPoints(alignmentPoints) : null);
    if (sphere) {
      const flight = ++sandboxFlightGeneration.current;
      if (localSandbox) {
        sandboxCameraReady.current = false;
        delete viewer.scene.canvas.dataset.sandboxReady;
      }
      viewer.camera.flyToBoundingSphere(sphere, {
        offset: new Cesium.HeadingPitchRange(alignmentBearing(alignment ?? null), Cesium.Math.toRadians(-58), Math.max(sphere.radius * 3.2, localSandbox ? 30 : 280)),
        duration: 0.9,
        complete: () => {
          if (flight !== sandboxFlightGeneration.current || viewer.isDestroyed?.()) return;
          sandboxCameraReady.current = true;
          if (localSandbox) viewer.scene.canvas.dataset.sandboxReady = "true";
        },
        cancel: () => {
          if (flight === sandboxFlightGeneration.current) sandboxCameraReady.current = false;
        },
      });
      return;
    }
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(centerLng, centerLat - 0.0035, 1250),
      orientation: { heading: alignmentBearing(alignment ?? null), pitch: Cesium.Math.toRadians(-58) },
      duration: 0.9,
    });
  }, [alignment, centerLat, centerLng, loaded, localSandbox]);

  useEffect(() => {
    basemapRef.current = basemap;
  }, [basemap]);

  const visibility = useMemo(
    () =>
      useModelLayers
        ? modelLayerVisibility(modelLayers)
        : { showProjectModel: layers.projectModel, showExcavation: layers.excavation },
    [useModelLayers, modelLayers, layers.projectModel, layers.excavation],
  );

  // Semantic editable components are rendered as individual Cesium entities so
  // picking, visibility, materials, and engineering transforms stay deterministic.
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;
    const ds = getDs(viewer, Cesium, "editable-model");
    ds.entities.removeAll();
    if (!editableModel) return;
    let cancelled = false;
    let sandboxCollection: import("cesium").PrimitiveCollection | null = null;
    let removePostRender: (() => void) | null = null;
    let disposeTransform: (() => void) | undefined;
    let ghostCollection: import("cesium").PrimitiveCollection | undefined;
    let ghostDataSource: import("cesium").CustomDataSource | undefined;
    void (async () => {
      const lng = acceptedPlacement?.longitude ?? editableModel.origin.lng;
      const lat = acceptedPlacement?.latitude ?? editableModel.origin.lat;
      const elevation = displayElevation;
      const documentHeading = acceptedPlacement?.heading ?? editableModel.origin.heading_deg;
      // Only an unplaced zero-origin model uses a temporary context-ground preview.
      // Accepted engineering coordinates and the document are never modified.
      const ground = 0;
      if (cancelled) return;
      if (localSandbox || editor) {
        const renderedDocument = editor?.comparison?.current ?? (localSandbox ? editableModel : { ...editableModel, origin: { lng, lat, elevation_m: elevation, heading_deg: documentHeading } });
        const preview = buildSandboxMapPrimitives(Cesium, ds.entities, renderedDocument, selectedComponentIds, ground, analysisClip);
        sandboxCollection = preview.collection;
        sandboxBounds.current = preview.bounds;
        viewer.scene.primitives.add(sandboxCollection);
        if(editor?.comparison){
          preview.collection.show=editor.comparison.mode !== "previous";
          if(editor.comparison.mode !== "current"){
            ghostDataSource=new Cesium.CustomDataSource("revision-ghost");
            void viewer.dataSources.add(ghostDataSource);
            ghostCollection=buildSandboxMapPrimitives(Cesium,ghostDataSource!.entities,editor.comparison.previous,[],0,undefined,true).collection;
            viewer.scene.primitives.add(ghostCollection);
          }
        }
        if (editor && !editor.comparison) disposeTransform = installCesiumTransform(Cesium, viewer, renderedDocument, selectedComponentIds, {
          mode: editor.tool, coordinates: editor.coordinateMode, pivot: editor.pivotMode,
          translationSnap: editor.snapMeters, rotationSnap: editor.rotationSnap, scaleSnap: editor.scaleSnap,
        }, preview.collection, editor.commitTransforms, setTransformReadout, alignment);
        viewer.scene.requestRender();
        const originKey = JSON.stringify(editableModel.origin);
        if (localSandbox && preview.bounds && (!sandboxWasFitted.current || sandboxLastOrigin.current !== originKey)) {
          sandboxWasFitted.current = true;
          sandboxLastOrigin.current = originKey;
          sandboxCameraReady.current = false;
          const flight = ++sandboxFlightGeneration.current;
          viewer.camera.flyToBoundingSphere(preview.bounds, { offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-58), Math.max(preview.bounds.radius * 3.2, 80)), duration: 0.9, complete: () => { if (flight === sandboxFlightGeneration.current) sandboxCameraReady.current = true; }, cancel: () => { if (flight === sandboxFlightGeneration.current) sandboxCameraReady.current = false; } });
        }
        removePostRender = viewer.scene.postRender.addEventListener(() => {
          if (cancelled || (preview.bounds && !sandboxCameraReady.current)) return;
          for (let i = 0; i < preview.collection.length; i++) if (!preview.collection.get(i).ready) return;
          viewer.scene.canvas.dataset.sandboxReady = "true";
          removePostRender?.(); removePostRender = null;
        });
        return;
      }
      const origin = Cesium.Cartesian3.fromDegrees(lng, lat, ground + elevation);
      const enu = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
      const headingRad = Cesium.Math.toRadians(documentHeading || 0);
      const toWorld = (point: [number, number, number]) => {
        const east = point[0] * Math.cos(headingRad) - point[1] * Math.sin(headingRad);
        const north = point[0] * Math.sin(headingRad) + point[1] * Math.cos(headingRad);
        return Cesium.Matrix4.multiplyByPoint(enu, new Cesium.Cartesian3(east, north, point[2]), new Cesium.Cartesian3());
      };
      for (const component of editableModel.components) {
        if (!component.visible) continue;
        const selected = selectedComponentIds.includes(component.id);
        const color = Cesium.Color.fromCssColorString(component.material.color || "#94A3B8").withAlpha(selected ? 0.96 : 0.84);
        const properties = { editableComponentId: component.id, layer: component.category, objectType: component.geometry.kind, material: component.material.name };
        const position = toWorld(component.transform.position);
        const rotation = component.transform.rotation_deg;
        const orientation = Cesium.Transforms.headingPitchRollQuaternion(
          position,
          new Cesium.HeadingPitchRoll(
            headingRad + Cesium.Math.toRadians(rotation[2]),
            Cesium.Math.toRadians(rotation[1]),
            Cesium.Math.toRadians(rotation[0]),
          ),
        );
        if (component.geometry.kind === "box" || component.geometry.kind === "extrusion") {
          const size = component.geometry.size.map((value, index) => Math.max(0.02, value * component.transform.scale[index]));
          ds.entities.add({
            id: `editable:${component.id}`,
            name: component.name,
            position,
            orientation,
            properties,
            box: {
              shadows: Cesium.ShadowMode.ENABLED,
              dimensions: new Cesium.Cartesian3(size[0], size[1], size[2]),
              material: color,
              // Selection uses the label and transform axes below. Entity outlines
              // can trigger unsupported terrain-outline paths in Cesium.
              outline: false,
            },
          });
        } else if (component.geometry.kind === "cylinder" || component.geometry.kind === "sweep") {
          const start = component.geometry.start;
          const end = component.geometry.end;
          const localMid: [number, number, number] = [
            component.transform.position[0] + (start[0] + end[0]) * 0.5,
            component.transform.position[1] + (start[1] + end[1]) * 0.5,
            component.transform.position[2] + (start[2] + end[2]) * 0.5,
          ];
          const length = Math.max(0.02, Math.hypot(end[0] - start[0], end[1] - start[1], end[2] - start[2]) * component.transform.scale[2]);
          const radius = Math.max(0.01, component.geometry.radius_m * Math.max(component.transform.scale[0], component.transform.scale[1]));
          ds.entities.add({
            id: `editable:${component.id}`,
            name: component.name,
            position: toWorld(localMid),
            orientation,
            properties,
            cylinder: {
              shadows: Cesium.ShadowMode.ENABLED,
              length,
              topRadius: radius,
              bottomRadius: radius,
              material: color,
              outline: false,
            },
          });
        }
        if (selected) {
          ds.entities.add({
            id: `selected-label:${component.id}`,
            position,
            label: {
              text: component.name.toUpperCase(),
              font: "600 12px sans-serif",
              fillColor: Cesium.Color.fromCssColorString(MAP_COLORS.primary),
              showBackground: true,
              backgroundColor: Cesium.Color.BLACK.withAlpha(0.72),
              pixelOffset: new Cesium.Cartesian2(0, -22),
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
          });
          const p = component.transform.position;
          const axisLength = 8;
          ([
            ["x", [p[0] + axisLength, p[1], p[2]], Cesium.Color.RED],
            ["y", [p[0], p[1] + axisLength, p[2]], Cesium.Color.LIME],
            ["z", [p[0], p[1], p[2] + axisLength], Cesium.Color.DODGERBLUE],
          ] as const).forEach(([axis, endpoint, axisColor]) => ds.entities.add({
            id: `gizmo:${component.id}:${axis}`,
            polyline: { positions: [position, toWorld(endpoint as [number, number, number])], width: 4, material: axisColor },
          }));
        }
      }
      viewer.scene.requestRender();
    })();
    return () => {
      cancelled = true;
      disposeTransform?.();
      if(!viewer.isDestroyed?.()){if(ghostCollection)viewer.scene.primitives.remove(ghostCollection);if(ghostDataSource)viewer.dataSources.remove(ghostDataSource,true);}
      removePostRender?.();
      if (localSandbox && !viewer.isDestroyed?.()) delete viewer.scene.canvas.dataset.sandboxReady;
      if (sandboxCollection && !viewer.isDestroyed?.()) viewer.scene.primitives.remove(sandboxCollection);
    };
  // Only scene-relevant editor fields participate; the editor object changes on
  // saving/error/panel updates, which must not interrupt a scene transaction.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded, editableModel, selectedComponentIds, terrainEpoch, localSandbox, acceptedPlacement, displayElevation, alignment, analysisClip, editor?.comparison, editor?.tool, editor?.coordinateMode, editor?.pivotMode, editor?.snapMeters, editor?.rotationSnap, editor?.scaleSnap, editor?.commitTransforms]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function getDs(viewer: any, Cesium: any, key: string) {
    const map = dataSourcesRef.current;
    if (map.has(key)) return map.get(key)!;
    const ds = new Cesium.CustomDataSource(key);
    viewer.dataSources.add(ds);
    map.set(key, ds);
    return ds;
  }

  const clearDs = (key: string) => {
    dataSourcesRef.current.get(key)?.entities.removeAll();
  };

  /** Photorealistic Ion/Google 3D tiles — gated by the "3D city tiles" layer. */
  const photorealisticTilesOn = globalBuildingsVisible(layers.tiles3d, layers.terrain, terrainReady, disableVendor3DTiles);

  // Init viewer
  useEffect(() => {
    const dataSources = dataSourcesRef.current;
    let cancelled = false;
    (async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).CESIUM_BASE_URL = "/cesium";
        if (!document.getElementById("cesium-widgets-css")) {
          const link = document.createElement("link");
          link.id = "cesium-widgets-css";
          link.rel = "stylesheet";
          link.href = "/cesium/Widgets/widgets.css";
          document.head.appendChild(link);
        }
        const Cesium = await import("cesium");
        if (cancelled || !containerRef.current || viewerRef.current) return;
        cesiumRef.current = Cesium;

        const runtime = await fetchMapRuntimeConfig().catch(() => ({ cesium_ion_token: null, google_maps_api_key: null }));
        mapRuntimeRef.current = runtime;
        if (!runtime.cesium_ion_token) setTerrainStatus("WORLD TERRAIN · TOKEN REQUIRED");

        const token = runtime.cesium_ion_token ?? undefined;
        if (token) Cesium.Ion.defaultAccessToken = token;
        if (cancelled || !containerRef.current || viewerRef.current) return;

        const viewer = new Cesium.Viewer(containerRef.current, {
          baseLayer: false,
          baseLayerPicker: false,
          geocoder: false,
          timeline: false,
          animation: false,
          sceneModePicker: false,
          homeButton: false,
          navigationHelpButton: false,
          infoBox: false,
          selectionIndicator: true,
          terrain: createFlatTerrain(Cesium),
        });
        viewer.scene.requestRenderMode = false;
        viewer.scene.maximumRenderTimeChange = Infinity;
        viewer.scene.globe.depthTestAgainstTerrain = true;
        viewer.scene.globe.enableLighting = false;
        viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#28332c");
        viewerRef.current = viewer;
        setLoaded(true);
      } catch (e) {
        setError(`Cesium failed to load: ${e instanceof Error ? e.message : e}`);
      }
    })();
    return () => {
      cancelled = true;
      destroyInputHandler(handlerRef.current);
      handlerRef.current = null;
      const viewer = viewerRef.current;
      if (viewer) {
        photorealisticTilesRef.current = destroyPhotorealisticTiles(
          viewer,
          photorealisticTilesRef.current,
          "viewer destroyed",
        );
      }
      dataSources.clear();
      viewerRef.current?.destroy?.();
      viewerRef.current = null;
    };
  }, [localSandbox]);

  // Keep provider credits visible in the Engineering dock instead of over the scene.
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!loaded || !creditsContainer || !viewer || viewer.isDestroyed()) return;
    const credits = viewer.bottomContainer as HTMLElement;
    const originalParent = credits.parentNode;
    creditsContainer.appendChild(credits);
    return () => {
      if (viewer.isDestroyed()) credits.remove();
      else originalParent?.appendChild(credits);
    };
  }, [loaded, creditsContainer]);

  // Swap basemap imagery in 3D
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    let cancelled = false;
    void (async () => {
      try {
        const token = mapRuntimeRef.current.cesium_ion_token;
        const provider = await loadCesiumBasemapProvider(Cesium, basemap, token);
        if (cancelled || viewer.isDestroyed?.()) return;
        // Resolve the replacement before removing the currently visible basemap.
        viewer.imageryLayers.removeAll();
        viewer.imageryLayers.addImageryProvider(provider);
        setSandboxHasImagery(true);
        setImageryError(null);
        resetImageryAlpha(viewer);
        cesiumDevLog("basemap", `Basemap switched to ${basemap}`);
        viewer.scene.requestRender();
      } catch {
        if (!cancelled && !viewer.isDestroyed?.()) setImageryError("Map imagery could not load. Check the map connection and reload.");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [basemap, loaded]);

  // Terrain is independent from buildings: hiding OSM buildings must never
  // flatten the project site or invalidate terrain-ground measurements.
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    let cancelled = false;
    void (async () => {
      setTerrainStatus(layers.terrain ? "WORLD TERRAIN · CHECKING" : "TERRAIN · OFF");
      const token = mapRuntimeRef.current.cesium_ion_token;
      if (!layers.terrain || !token) {
        viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
        setTerrainStatus(layers.terrain ? "WORLD TERRAIN · TOKEN REQUIRED" : "TERRAIN · OFF");
        setTerrainDetail(layers.terrain ? "Connect world terrain in provider settings to load real elevation automatically." : "Flat reference globe. Real elevations are not loaded.");
        setTerrainEpoch((n) => n + 1);
        viewer.scene.requestRender();
        return;
      }
      try {
        const result = await resolveAutomaticTerrain({
          project: projectTerrain,
          longitude: previewLng,
          latitude: previewLat,
          load: (assetId) => Cesium.CesiumTerrainProvider.fromIonAssetId(assetId, { accessToken: token, requestVertexNormals: true }),
        });
        if (cancelled || viewer.isDestroyed()) return;
        viewer.terrainProvider = result.provider;
        setTerrainStatus(result.source === "project" ? `PROJECT TERRAIN v${result.version} · Check survey evidence` : "WORLD TERRAIN · VISUAL REFERENCE");
        setTerrainDetail(result.source === "project"
          ? "Active project terrain covering this location. Check its survey evidence before using elevations for earthwork."
          : `${result.fallback ?? "Cesium World Terrain selected automatically."} Local resolution and vertical accuracy are not verified. Earthwork quantities require validated ground data.`);
        setTerrainEpoch((n) => n + 1);
        viewer.scene.requestRender();
      } catch {
        if (cancelled || viewer.isDestroyed()) return;
        viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
        setTerrainStatus("WORLD TERRAIN · ACCESS FAILED");
        setTerrainDetail("Elevation data could not load. The flat reference globe is not a measured ground surface. Retry or check the world-data connection.");
        setTerrainEpoch((n) => n + 1);
        viewer.scene.requestRender();
      }
    })();
    return () => { cancelled = true; };
  }, [loaded, projectTerrain, layers.terrain, previewLng, previewLat, terrainRetry]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!loaded || !viewer || viewer.isDestroyed()) return;
    viewer.scene.verticalExaggeration = Number.isFinite(terrainExaggeration) ? Math.min(3, Math.max(1, terrainExaggeration)) : 1;
    viewer.scene.verticalExaggerationRelativeHeight = 0;
    viewer.scene.requestRender();
  }, [loaded, terrainExaggeration]);

  // Transparent / underground — globe translucency only (not pipeline/drainage).
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    const transparentOn = undergroundView;
    viewer.scene.globe.depthTestAgainstTerrain = !transparentOn;
    cesiumDevLog(
      "transparent",
      transparentOn ? "Transparent ON (globe translucency)" : "Transparent OFF (opaque globe)",
    );

    if (transparentOn) {
      applyGlobeTranslucency(viewer, Cesium);
    } else {
      resetGlobeTranslucency(viewer);
      resetImageryAlpha(viewer);
    }
    viewer.scene.requestRender();
  }, [loaded, undergroundView]);

  // Buildings load independently; terrain changes must not discard them.
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    const enabled = photorealisticTilesOn;

    cesiumDevLog(
      "buildings",
      `Photorealistic 3D tiles ${enabled ? "rebuilding" : "off"}`,
    );

    let cancelled = false;

    void (async () => {
      if (!enabled) {
        photorealisticTilesRef.current = destroyPhotorealisticTiles(
          viewer,
          photorealisticTilesRef.current,
          "3D tiles disabled",
        );
        return;
      }

      const nextState = await syncPhotorealisticTiles({
        viewer,
        Cesium,
        enabled: true,
        state: photorealisticTilesRef.current,
        runtime: mapRuntimeRef.current,
        isCurrent: () => !cancelled,
        onStatus: setBuildingStatus,
      });
      if (!cancelled) photorealisticTilesRef.current = nextState;
    })();

    return () => {
      cancelled = true;
    };
  }, [loaded, photorealisticTilesOn]);
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    clearDs("roads");
    clearDs("buildings");
    clearDs("water");
    clearDs("trees");
    clearDs("pipeline");
    clearDs("construction");
    clearDs("labels");
    clearDs("project");

    const roadsDs = getDs(viewer, Cesium, "roads");
    const buildingsDs = getDs(viewer, Cesium, "buildings");
    const waterDs = getDs(viewer, Cesium, "water");
    const pipelineDs = getDs(viewer, Cesium, "pipeline");
    const constructionDs = getDs(viewer, Cesium, "construction");
    const projectDs = getDs(viewer, Cesium, "project");

    roadsDs.show = scene3dLayers.roads;
    buildingsDs.show = scene3dLayers.buildings;
    waterDs.show = scene3dLayers.water;
    pipelineDs.show = scene3dLayers.pipeline || scene3dLayers.drainage;
    constructionDs.show = scene3dLayers.construction;

    if (boundary?.type === "Polygon" && scene3dLayers.construction) {
      const ring = (boundary.coordinates as number[][][])[0];
      constructionDs.entities.add({
        id: "construction-boundary",
        name: "Construction zone",
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(ring.flat()),
          material: Cesium.Color.fromCssColorString(MAP_COLORS.valid).withAlpha(0.2),
          // Cesium does not support polygon outlines when terrain-clamped.
          // The fill remains visible without producing a renderer warning.
          outline: false,
          height: 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        properties: { layer: "construction", objectType: "Construction zone" },
      });
    }

    roadFeatures.forEach((f, i) => {
      if (f.geometry.type !== "LineString") return;
      const coords = f.geometry.coordinates as [number, number][];
      const width = roadWidthM(f.properties ?? {}) || Number(f.properties?.width_m) || 7;
      const isSurvey = surveyMode && f.properties?.tier;
      const ring = corridorRing(coords, width);
      if (ring) {
        roadsDs.entities.add({
          id: `road-${i}`,
          name: String(f.properties?.name ?? `Road ${i + 1}`),
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(ring.flat()),
            material: Cesium.Color.fromCssColorString(MAP_COLORS.road).withAlpha(
              isSurvey ? 0.95 : 0.92,
            ),
            height: 0.35,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          properties: { ...f.properties, layer: "roads", objectType: isSurvey ? "Survey road" : "Road" },
        });
      } else {
        roadsDs.entities.add({
          id: `road-line-${i}`,
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArrayHeights(
              coords.flatMap(([lng, lat]) => [lng, lat, 0.35]),
            ),
            width: Math.max(4, width / 2),
            material: Cesium.Color.fromCssColorString(MAP_COLORS.road),
            clampToGround: true,
          },
          properties: { ...f.properties, layer: "roads", objectType: isSurvey ? "Survey road" : "Road" },
        });
      }
    });

    if (surveyMode && surveyLayers.surveyGcp) {
      const gcpDs = getDs(viewer, Cesium, "labels");
      surveyGcpFeatures.forEach((f, i) => {
        if (f.geometry.type !== "Point") return;
        const [lng, lat] = f.geometry.coordinates as [number, number];
        gcpDs.entities.add({
          id: `gcp-${i}`,
          name: String(f.properties?.name ?? `GCP ${i + 1}`),
          position: Cesium.Cartesian3.fromDegrees(lng, lat, 0),
          point: {
            pixelSize: 10,
            color: Cesium.Color.fromCssColorString(MAP_COLORS.primary),
            outlineColor: Cesium.Color.fromCssColorString(MAP_COLORS.vertexStroke),
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: String(f.properties?.name ?? "GCP"),
            font: "11px sans-serif",
            fillColor: Cesium.Color.fromCssColorString(MAP_COLORS.primary),
            pixelOffset: new Cesium.Cartesian2(0, -14),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          properties: { layer: "gcp", objectType: "Ground control point" },
        });
      });
    }

    if (scene3dLayers.buildings) {
      buildingFeatures.forEach((f, i) => {
        if (f.geometry.type !== "Polygon") return;
        const ring = (f.geometry.coordinates as number[][][])[0];
        const height = estimateBuildingHeight(f.properties ?? {});
        buildingsDs.entities.add({
          id: `building-${i}`,
          name: String(f.properties?.name ?? f.properties?.["addr:street"] ?? `Building ${i + 1}`),
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(ring.flat()),
            height: 0,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            extrudedHeight: height,
            extrudedHeightReference: Cesium.HeightReference.RELATIVE_TO_GROUND,
            material: Cesium.Color.fromCssColorString(MAP_COLORS.contextBuilding),
            // Terrain-clamped geometry cannot render entity outlines reliably.
            outline: false,
          },
          properties: { ...f.properties, layer: "buildings", objectType: "Building", heightM: height, heightSource: "OSM tags or estimated height; visual context" },
        });
      });
      if (buildingFeatures.length > 0) {
        cesiumDevLog("osm", `OSM extruded buildings created (${buildingFeatures.length})`);
      }
    }

    waterFeatures.forEach((f, i) => {
      if (f.geometry.type !== "LineString" && f.geometry.type !== "Polygon") return;
      if (f.geometry.type === "Polygon") {
        const ring = (f.geometry.coordinates as number[][][])[0];
        waterDs.entities.add({
          id: `water-${i}`,
          name: "Water body",
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(ring.flat()),
            material: Cesium.Color.fromCssColorString(MAP_COLORS.water).withAlpha(0.55),
            height: 0,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          properties: { layer: "water", objectType: "Water" },
        });
      }
    });

    if (alignment?.type === "LineString" && scene3dLayers.flyover) {
      const coords = alignment.coordinates as [number, number][];
      projectDs.entities.add({
        id: "alignment-centerline",
        name: "Alignment / flyover path",
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArrayHeights(
            coords.flatMap(([lng, lat]) => [lng, lat, 2]),
          ),
          width: 3,
          material: Cesium.Color.fromCssColorString(MAP_COLORS.primary).withAlpha(0.9),
        },
        properties: { layer: "flyover", objectType: "Alignment" },
      });

      if (scene3dLayers.pipeline) {
        pipelineDs.entities.add({
          id: "pipeline-under-alignment",
          name: "Pipeline (underground)",
          polylineVolume: {
            positions: Cesium.Cartesian3.fromDegreesArrayHeights(
              coords.flatMap(([lng, lat]) => [lng, lat, -3]),
            ),
            shape: computePipeShape(Cesium, 0.6),
            material: Cesium.Color.fromCssColorString(MAP_COLORS.water).withAlpha(0.85),
          },
          properties: { layer: "pipeline", objectType: "Pipeline", material: "HDPE" },
        });
      }
    }

    projectDs.show =
      scene3dLayers.flyover || scene3dLayers.bridge || scene3dLayers.excavation;

  }, [
    loaded,
    boundary,
    alignment,
    modelUrl,
    excavationUrl,
    centerLng,
    centerLat,
    roadFeatures,
    buildingFeatures,
    waterFeatures,
    surveyMode,
    surveyGcpFeatures,
    surveyLayers.surveyGcp,
    scene3dLayers,
    cesiumTool,
    terrainEpoch,
  ]);

  // AI design GLB models (per-mesh layer visibility via node names)
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    let cancelled = false;

    const destroyModel = (model: { destroy?: () => void; isDestroyed?: () => boolean } | null) => {
      if (!model) return;
      try {
        viewer.scene.primitives.remove(model);
        if (!model.isDestroyed?.()) model.destroy?.();
      } catch {
        /* viewer shutting down */
      }
    };

    (async () => {
      destroyModel(modelsRef.current.main);
      destroyModel(modelsRef.current.excav);
      modelsRef.current = { main: null, excav: null };

      const placement = acceptedPlacement
        ? { lng: acceptedPlacement.longitude, lat: acceptedPlacement.latitude, bearingRad: Cesium.Math.toRadians(acceptedPlacement.heading) }
        : editableModel ? { lng: editableModel.origin.lng, lat: editableModel.origin.lat, bearingRad: Cesium.Math.toRadians(editableModel.origin.heading_deg) }
        : designModelAnchor(alignment ?? null, centerLng, centerLat);
      const groundHeight = displayElevation;
      const modelOpts = {
        shadows: Cesium.ShadowMode.ENABLED,
        minimumPixelSize: 0,
        silhouetteColor: Cesium.Color.fromCssColorString(MAP_COLORS.primary).withAlpha(0.4),
        silhouetteSize: 2,
      };

      if (!editableModel && modelUrl && scene3dLayers.flyover && (useModelLayers ? visibility.showProjectModel : layers.projectModel)) {
        const modelMatrix = buildDesignModelMatrix(
          Cesium,
          placement.lng,
          placement.lat,
          placement.bearingRad,
          groundHeight,
        );
        const model = await Cesium.Model.fromGltfAsync({
          url: modelUrl,
          modelMatrix,
          ...modelOpts,
        });
        if (cancelled) {
          model.destroy();
          return;
        }
        viewer.scene.primitives.add(model);
        modelsRef.current.main = model;
        model.color = Cesium.Color.WHITE.withAlpha(modelOpacity);
        model.colorBlendMode = Cesium.ColorBlendMode.MIX;
        applyDesignMeshVisibilityWhenReady(
          model,
          useProjectStore.getState().designMeshCatalog,
          useProjectStore.getState().designMeshVisibility,
        );
      }

      const showExcav = useModelLayers ? visibility.showExcavation : layers.excavation;
      if (excavationUrl && scene3dLayers.excavation && showExcav) {
        const excavHeight = groundHeight + (cesiumTool === "exploded" ? -25 : 0);
        const excavMatrix = buildDesignModelMatrix(
          Cesium,
          placement.lng,
          placement.lat,
          placement.bearingRad,
          excavHeight,
        );
        const excav = await Cesium.Model.fromGltfAsync({
          url: excavationUrl,
          modelMatrix: excavMatrix,
          ...modelOpts,
        });
        if (cancelled) {
          excav.destroy();
          return;
        }
        viewer.scene.primitives.add(excav);
        modelsRef.current.excav = excav;
        excav.color = Cesium.Color.WHITE.withAlpha(modelOpacity);
        excav.colorBlendMode = Cesium.ColorBlendMode.MIX;
        applyDesignMeshVisibilityWhenReady(
          excav,
          useProjectStore.getState().designMeshCatalog,
          useProjectStore.getState().designMeshVisibility,
        );
        if (!useProjectStore.getState().designMeshCatalog.length) {
          excav.show = useProjectStore.getState().designMeshVisibility.excavation !== false;
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    loaded,
    modelUrl,
    excavationUrl,
    centerLng,
    centerLat,
    alignment,
    scene3dLayers.flyover,
    scene3dLayers.excavation,
    cesiumTool,
    useModelLayers,
    visibility.showProjectModel,
    visibility.showExcavation,
    layers.projectModel,
    layers.excavation,
    designMeshCatalog,
    designMeshVisibility,
    terrainEpoch,
    modelOpacity,
    editor,
  editableModel,
    acceptedPlacement,
    displayElevation,
  ]);

  useEffect(() => {
    const Cesium = cesiumRef.current;
    if (!Cesium || !loaded) return;
    const alpha = Math.min(1, Math.max(0.2, modelOpacity));
    for (const model of [modelsRef.current.main, modelsRef.current.excav]) {
      if (!model) continue;
      model.color = Cesium.Color.WHITE.withAlpha(alpha);
      model.colorBlendMode = Cesium.ColorBlendMode.MIX;
    }
  }, [loaded, modelOpacity]);

  // Reuse the accepted anchor; terrain changes never relocate structures.
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    let cancelled = false;

    void (async () => {
      const placement = acceptedPlacement
        ? { lng: acceptedPlacement.longitude, lat: acceptedPlacement.latitude, bearingRad: Cesium.Math.toRadians(acceptedPlacement.heading) }
        : editableModel ? { lng: editableModel.origin.lng, lat: editableModel.origin.lat, bearingRad: Cesium.Math.toRadians(editableModel.origin.heading_deg) }
        : designModelAnchor(alignment ?? null, centerLng, centerLat);
      const groundHeight = displayElevation;
      if (cancelled) return;

      const { main, excav } = modelsRef.current;
      if (main && !main.isDestroyed?.()) {
        main.modelMatrix = buildDesignModelMatrix(
          Cesium,
          placement.lng,
          placement.lat,
          placement.bearingRad,
          groundHeight,
        );
      }
      if (excav && !excav.isDestroyed?.()) {
        excav.modelMatrix = buildDesignModelMatrix(
          Cesium,
          placement.lng,
          placement.lat,
          placement.bearingRad,
          groundHeight + (cesiumTool === "exploded" ? -25 : 0),
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    loaded,
    centerLng,
    centerLat,
    alignment,
    terrainEpoch,
    cesiumTool,
    modelUrl,
    editor,
  editableModel,
    acceptedPlacement,
    displayElevation,
  ]);

  // Layer visibility toggles without full rebuild (except buildings handled above on rebuild).
  useEffect(() => {
    if (!loaded) return;
    const map = dataSourcesRef.current;
    LAYER_DS.forEach((key) => {
      const ds = map.get(key);
      if (ds) ds.show = scene3dLayers[key];
    });
    const projectDs = map.get("project");
    if (projectDs) {
      projectDs.show = scene3dLayers.flyover || scene3dLayers.excavation;
    }

    const showVendor = photorealisticTilesOn;
    setPhotorealisticTilesVisible(photorealisticTilesRef.current, showVendor);
    viewerRef.current?.scene?.requestRender?.();

    const { main, excav } = modelsRef.current;
    if (main) {
      main.show = scene3dLayers.flyover && (useModelLayers ? visibility.showProjectModel : layers.projectModel);
      if (designMeshCatalog.length) {
        applyDesignMeshVisibilityWhenReady(main, designMeshCatalog, designMeshVisibility);
      }
    }
    if (excav) {
      const showExcav = useModelLayers ? visibility.showExcavation : layers.excavation;
      excav.show =
        scene3dLayers.excavation &&
        showExcav &&
        designMeshVisibility.excavation !== false;
      if (designMeshCatalog.length) {
        applyDesignMeshVisibilityWhenReady(excav, designMeshCatalog, designMeshVisibility);
      }
    }
  }, [loaded, scene3dLayers, visibility, layers.projectModel, layers.excavation, layers.tiles3d, useModelLayers, designMeshCatalog, designMeshVisibility, disableVendor3DTiles, photorealisticTilesOn]);

  // Camera home
  const autoFitDocument = localSandbox ? null : editableModel;
  useEffect(() => {
    if (localSandbox && sandboxFitRequest.current === fitRequest) return;
    sandboxFitRequest.current = fitRequest;
    fitProject();
  }, [fitProject, fitRequest, autoFitDocument, modelUrl, excavationUrl, localSandbox, displayElevation]);

  // Camera controls
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;
    const ctrl = viewer.scene.screenSpaceCameraController;
    ctrl.enableRotate = cesiumTool === "orbit";
    ctrl.enableTranslate = cesiumTool === "pan" || cesiumTool === "orbit";
    ctrl.enableZoom = true;
    ctrl.enableTilt = cesiumTool === "orbit";
    if (cesiumTool === "zoom") {
      ctrl.enableRotate = false;
      ctrl.enableTranslate = false;
    }
  }, [cesiumTool, loaded]);

  // Pick + measure
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    destroyInputHandler(handlerRef.current);
    handlerRef.current = null;

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    handler.setInputAction((click: { position: { x: number; y: number } }) => {
      const picked = viewer.scene.pick(click.position);
      if (String(picked?.id?.id ?? "").startsWith("transform:")) return;
      const store = useProjectStore.getState();

      if (scene3dMeasureTool !== "none") {
        const measurementSequence = ++measurementRequest.current;
        const props = picked?.id?.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
        const design = !!props.editableComponentId;
        const ray = viewer.camera.getPickRay(click.position);
        const point = design && viewer.scene.pickPositionSupported ? viewer.scene.pickPosition(click.position) : ray ? viewer.scene.globe.pick(ray,viewer.scene) : null;
        if (!point) { store.setScene3dMeasureReadout("UNKNOWN · Surface could not be picked."); return; }
        const carto = Cesium.Cartographic.fromCartesian(point);
        const longitude = Cesium.Math.toDegrees(carto.longitude), latitude = Cesium.Math.toDegrees(carto.latitude);
        void (async () => {
          const designResolved=acceptedPlacement?.status==="VALID" && acceptedPlacement.vertical_reference?.type==="ELLIPSOIDAL";
          let sample: MeasurementPoint = { longitude,latitude,elevation:design ? designResolved ? carto.height : null : !(viewer.terrainProvider instanceof Cesium.EllipsoidTerrainProvider) ? carto.height : null,
            source:design ? String(picked.id.name ?? "Design geometry") : "World Terrain", dataset:null,version:null,
            horizontalReference:"EPSG:4326",verticalReference:design && !designResolved ? "UNKNOWN":"ELLIPSOIDAL",status:design ? designResolved ? "DESIGN_GEOMETRY":"UNRESOLVED_PLACEMENT" : "VISUAL_REFERENCE",classification:design ? designResolved ? "ENGINEERING_RESULT":"UNKNOWN" : "VISUAL_REFERENCE" };
          if (!design && projectTerrain && projectId) {
            store.setScene3dMeasureReadout("Sampling active survey terrain…");
            try {
              const result = await api.post<{ status:string; elevation:number|null; terrain_dataset_id:number|null; terrain_version_id:number|null; source:string; vertical_reference:{type?:string}|null; failure_reason?:string }>(`/api/projects/${projectId}/engineering/ground-samples`,{longitude,latitude});
              sample = {...sample, elevation:result.status === "VALID" ? result.elevation : null, source:result.source ?? "Project survey",dataset:result.terrain_dataset_id,version:result.terrain_version_id,verticalReference:result.vertical_reference?.type ?? "UNKNOWN",status:result.status,classification:result.status === "VALID" ? "SURVEY_DERIVED" : "UNKNOWN"};
            } catch (error) { sample = {...sample,elevation:null,status:String(error),classification:"UNKNOWN",source:"Survey sampling failed"}; }
          }
          if (measurementSequence !== measurementRequest.current || viewer.isDestroyed()) return;
          if (sample.elevation === null) sample.classification = "UNKNOWN";
          measurementSamples.current.push(sample);
          const points = measurementSamples.current;
          const values = measurementValues(scene3dMeasureTool,points);
          const format = (value: number | null | undefined, unit: string) => value == null ? "Unknown" : `${value.toFixed(3)} ${unit}`;
          const rows = Object.entries(values).map(([key,value])=>`${key.replaceAll("_"," ")}: ${format(value,key.endsWith("percent") ? "%" : key.endsWith("deg") ? "°" : key.endsWith("m2") ? "m²" : "m")}`);
          store.setScene3dMeasureReadout(`${measurementClassification(points)} · ${rows.length ? rows.join(" · ") : "Pick the next point"}\n${points.map(item=>`${item.source} · dataset ${item.dataset ?? "unavailable"} · version ${item.version ?? "unavailable"} · ${item.horizontalReference} / ${item.verticalReference} · ${item.status}`).join("\n")}${scene3dMeasureTool === "area" ? "\nLocal tangent-plane area · click more vertices; Escape to finish/reset" : ""}`);
          if (scene3dMeasureTool === "height" || scene3dMeasureTool !== "area" && points.length >= 2) measurementSamples.current = [];
        })();
        return;
      }
      if (!picked?.id) {
        onSelectComponent?.(null);
        store.setSelectedObject3d(null);
        return;
      }

      const entity = picked.id;
      const props = entity.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
      if (props.editableComponentId) {
        onSelectComponent?.(String(props.editableComponentId));
        viewer.selectedEntity = entity;
        return;
      }
      const layer = (props.layer ?? "buildings") as Scene3DLayerKey;
      store.setSelectedObject3d(
        objectInfoFromFeature(String(entity.id), layer, undefined, {
          name: entity.name ?? String(entity.id),
          type: String(props.objectType ?? layer),
          material: props.material ? String(props.material) : undefined,
          heightM: props.heightM ? Number(props.heightM) : undefined,
          lengthM:
            alignment?.type === "LineString" && entity.id === "alignment-centerline"
              ? lineLengthM(alignment.coordinates as [number, number][])
              : undefined,
          properties: props,
        }),
      );
      viewer.selectedEntity = entity;
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    const additivePick = (click: { position: { x: number; y: number } }) => {
      const entity = viewer.scene.pick(click.position)?.id;
      const props = entity?.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
      if (props.editableComponentId) onSelectComponent?.(String(props.editableComponentId), true);
    };
    handler.setInputAction(additivePick, Cesium.ScreenSpaceEventType.LEFT_CLICK, Cesium.KeyboardEventModifier.SHIFT);
    handler.setInputAction(additivePick, Cesium.ScreenSpaceEventType.LEFT_CLICK, Cesium.KeyboardEventModifier.CTRL);

    handlerRef.current = handler;
    return () => {
      if (handlerRef.current === handler) handlerRef.current = null;
      // This is a request generation counter, not a captured DOM reference.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      measurementRequest.current++;
      destroyInputHandler(handler);
    };
  }, [loaded, scene3dMeasureTool, measureUnit, alignment, onSelectComponent, projectTerrain, projectId, terrainEpoch, editableModel, acceptedPlacement]);

  useEffect(() => {
    measurePointsRef.current = [];
    measurementSamples.current = [];
    measurementRequest.current++;
    useProjectStore.getState().setScene3dMeasureReadout(null);
  }, [scene3dMeasureTool, terrainEpoch, editableModel, acceptedPlacement]);

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center text-sm text-destructive p-6 text-center">
        {error}
      </div>
    );
  }
  return <>{measurementReadout && <div role="status" aria-label="Measurement result" className="absolute bottom-16 left-16 z-30 max-w-lg whitespace-pre-line rounded-sm border border-white/10 bg-background/95 p-3 text-[10px]">{measurementReadout}</div>}{transformReadout && <p role="status" className="pointer-events-none absolute bottom-16 left-16 z-30 rounded-sm border border-white/10 bg-background/95 px-3 py-2 font-mono text-xs">{transformReadout}</p>}{loaded && !layers.terrain && layers.tiles3d && <div role="status" className="absolute left-16 top-14 z-20 rounded-lg border border-white/15 bg-background/95 px-3 py-2 text-xs"><span>Global buildings paused on flat ground.</span><button className="ml-3 text-primary underline" onClick={() => useProjectStore.getState().setLayers({ terrain: true })}>Restore terrain & buildings</button></div>}{loaded && visualGroundPreview && <p role="status" className="pointer-events-none absolute bottom-12 left-16 z-20 rounded-lg bg-background/90 px-3 py-2 text-[10px] text-muted-foreground">Model on context ground · visual preview, not a saved survey placement</p>}{loaded && <SunStudyControls key={placementProjectId ?? "local"} viewer={viewerRef.current} Cesium={cesiumRef.current} longitude={centerLng} latitude={centerLat} projectId={localSandbox ? undefined : placementProjectId} buildingsAvailable={photorealisticTilesOn && buildingStatus === "READY" || scene3dLayers.buildings && buildingFeatures.length > 0} terrainAvailable={layers.terrain && (terrainStatus.includes("VISUAL REFERENCE") || terrainStatus.startsWith("PROJECT TERRAIN"))} />}<div ref={containerRef} style={{ position: "absolute", inset: 0 }} />{!localSandbox && editableModel && <EngineeringEvidencePanel key={`${editableModel.project_id}:${modelRevisionId ?? "unsaved"}`} projectId={editableModel.project_id} revisionId={modelRevisionId} origin={editableModel.origin} onPlacement={setAcceptedPlacement} />}{buildingStatus && photorealisticTilesOn && buildingStatus !== "READY" && <p role="alert" className="absolute left-16 top-24 rounded-xl border border-white/15 bg-background/90 px-3 py-2 text-[10px] text-muted-foreground shadow-lg backdrop-blur-xl">Context buildings unavailable: {buildingStatus === "MISSING_TOKEN" ? "configure world data" : "provider could not load"}</p>}{loaded && layers.terrain && <details className="absolute left-16 top-14 z-20 max-w-[330px] rounded-xl border border-white/15 bg-background/95 text-[10px] shadow-lg"><summary role="status" className="cursor-pointer px-3 py-2 text-muted-foreground">{terrainStatus}</summary><div className="space-y-2 border-t border-white/10 px-3 py-3 text-xs leading-relaxed text-muted-foreground"><p>{terrainDetail}</p><p>Elevation scale: {terrainExaggeration}× · source resolution: not reported</p><button className="text-primary underline" onClick={() => setTerrainRetry((n) => n + 1)}>Reload elevation</button><a href="/settings/api-keys" className="block text-primary underline">World data connection</a></div></details>}{localSandbox && loaded && <p className="pointer-events-none absolute left-3 top-3 rounded-sm border border-white/10 bg-background/90 px-3 py-2 text-[10px] text-muted-foreground">Origin {centerLat.toFixed(6)}, {centerLng.toFixed(6)}{!sandboxHasImagery && " · Loading map imagery…"}</p>}{imageryError && <p role="alert" className="absolute left-3 top-12 rounded-sm border border-amber-400/30 bg-background/95 px-3 py-2 text-xs text-amber-200">{imageryError}</p>}</>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function computePipeShape(Cesium: any, radius: number) {
  const segments = 12;
  const shape = [];
  for (let i = 0; i < segments; i++) {
    const angle = (i / segments) * Math.PI * 2;
    shape.push(new Cesium.Cartesian2(radius * Math.cos(angle), radius * Math.sin(angle)));
  }
  return shape;
}

