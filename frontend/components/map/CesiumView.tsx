"use client";
import {outcome,type WorkspaceCommand} from "@/lib/workspace-assistant";
import { bindWorkspaceGraphics, type GraphicsQuality, type GraphicsContextState } from "@/lib/workspace-graphics";
import { useProtectedFile } from "@/hooks/useProtectedFile";
import {structuralFitRange,layoutEngineeringLabels,engineeringLabelText} from "@/lib/structural-display";
import {deformationPhase} from "@/lib/deformation-animation";
import type {FoundationOverlay} from "@/lib/foundation-visual";
import "cesium/Build/Cesium/Widgets/widgets.css";
import {frameEntities} from "@/lib/visual-framing";
import {modelFitRange} from "@/lib/model-framing";
import WorkspaceMouseControls from "./WorkspaceMouseControls";
import SupervisedPrimitiveControls from '../model-editor/SupervisedPrimitiveControls';
import { componentDisplayName } from "@/lib/component-presentation";
import MeasurementResult from "./MeasurementResult";
import { loadCadMeshes } from "@/lib/cad-mesh";
import { loadCesiumRuntime } from "@/lib/cesium-runtime";
import { cameraLease, cylinderFrame } from "@/lib/editor-transform";
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
import { corridorFromLine, geometryToVertices, rectangleFromCorners, verticesToLine, verticesToPolygon, verticesToSmoothLine } from "@/lib/map-draw";
import { boundaryError } from "@/lib/boundary-validation";
import {
  fetchMapRuntimeConfig,
  loadCesiumBasemapProvider,
  type MapBasemap,
} from "@/lib/map-imagery";
import { MAP_COLORS } from "@/lib/map-colors";
import { designModelAnchor, alignmentBearing, modelLayerVisibility } from "@/lib/project-workflow";
import { applyDesignMeshVisibilityWhenReady } from "@/lib/design-mesh-layers";
import type { EditableModelComponent, EditableModelDocument, GeoJSONFeature, GeoJSONGeometry } from "@/lib/types";
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
  modelUrl: modelSourceUrl,
  excavationUrl: excavationSourceUrl,
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
  const modelUrl = useProtectedFile(editableModel || editor ? null : modelSourceUrl);
  const excavationUrl = useProtectedFile(excavationSourceUrl);
  const { creditsContainer } = useWorkspaceMap();
  const drawingTool = useProjectStore(state => state.activeTool);
  const onSelectComponentRef = useRef(onSelectComponent);
  useEffect(() => { onSelectComponentRef.current = onSelectComponent; }, [onSelectComponent]);
  const containerRef = useRef<HTMLDivElement>(null);
  const [runtimeRetry, setRuntimeRetry] = useState(0);
  const graphicsEditor = Boolean(editor);
  const [graphicsQuality, setGraphicsQuality] = useState<GraphicsQuality>("auto");
  const qualityRef = useRef<GraphicsQuality>(graphicsQuality);
  qualityRef.current = graphicsQuality;
  const [graphicsContext, setGraphicsContext] = useState<GraphicsContextState>("ready");
  const graphicsRef = useRef<ReturnType<typeof bindWorkspaceGraphics> | null>(null);
  useEffect(() => { graphicsRef.current?.update(); }, [graphicsQuality]);
  // Presentation only: inspect the unchanged model independently of site terrain.
  const [modelView, setModelView] = useState(Boolean(editor));
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("geoai:presentation-view", { detail: modelView ? "model" : "site" }));
  }, [modelView]);
  const [hoveredName, setHoveredName] = useState<string | null>(null);
  const modelViewRef = useRef(modelView);
  modelViewRef.current = modelView;
  const connectionInspectionRef=useRef(false);
  const [dimensionsVisible,setDimensionsVisible]=useState(false);
  const dimensionsVisibleRef=useRef(false);
  const [componentPreview,setComponentPreview]=useState<EditableModelComponent|null>(null);
  useEffect(()=>{
    const preview=(event:Event)=>setComponentPreview((event as CustomEvent<EditableModelComponent|null>).detail);
    window.addEventListener("geoai:component-preview",preview);
    return()=>window.removeEventListener("geoai:component-preview",preview);
  },[]);
  useEffect(()=>{
    dimensionsVisibleRef.current=dimensionsVisible;
    for(const entity of dataSourcesRef.current.get("editable-model")?.entities.values??[])if(entity.id.startsWith("platform-dimension:"))entity.show=dimensionsVisible&&!connectionInspectionRef.current;
    viewerRef.current?.scene.requestRender();
  },[dimensionsVisible]);
  const [elasticState,setElasticResults]=useState<{sourceScope?:string;assistantCommand?:WorkspaceCommand;paths:number[][][];label:string;mode:string;overlayThroughSolids?:boolean;fit?:boolean;componentIds?:string[];colors?:string[];focus?:number[];fitRange?:number;fitPitch?:number;fitHeadingOffset?:number;focusComponentIds?:string[];fitPoints?:number[][];nodeMarkers?:{name:string;position:number[];componentId?:string;inspectionKey?:string}[];polygons?:{positions:number[][];basePositions?:number[][];color:string;componentId:string;alpha?:number;inspectionKey?:string}[];arrowIndices?:number[];bars?:FoundationOverlay['bars'];visualMode?:string;hideModel?:boolean;displayOpacity?:Record<string,number>;pathStyles?:string[];selectedComponentId?:string;inspectionKeys?:string[];floorSystem?:boolean;animation?:{basePaths:number[][][];periodSeconds:number}}|null>(null);
  const overlayScope=`${editableModel?.project_id}:${modelRevisionId}`;
  const elasticResults=editor?.platformPreview?.proposal ? null : elasticState?.sourceScope===overlayScope ? elasticState : null;
  const structuralOpacityKey=JSON.stringify(elasticResults?.displayOpacity??{});
  const solverDiagram = !!elasticResults && ["deformation", "axial", "shear", "moment", "reactions", "loads"].includes(elasticResults.mode);
  const analysisFocusKey=(elasticResults?.focusComponentIds ?? (solverDiagram ? elasticResults?.componentIds : undefined))?.join('\n')??'';
  useEffect(()=>{const update=(event:Event)=>{const detail=(event as CustomEvent).detail as (NonNullable<typeof elasticResults>&{clearMode?:string})|null;setElasticResults(current=>{if(detail?.clearMode)return current?.mode===detail.clearMode ? null:current;if(detail===null&&['finite-bearing-schematic','footing-flexure-demand','rc-flexure-layout','foundation-integrated','structural-visual'].includes(current?.mode??''))return current;return detail ? {...detail,sourceScope:overlayScope}:null;});};window.addEventListener('geoai:elastic-results',update);return()=>window.removeEventListener('geoai:elastic-results',update);},[overlayScope]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const cesiumRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dataSourcesRef = useRef<Map<string, any>>(new Map());
  const photorealisticTilesRef = useRef<PhotorealisticTileState>(createPhotorealisticTileState());
  const [acceptedPlacement, setAcceptedPlacement] = useState<{ longitude: number; latitude: number; elevation: number | null; offset: number; heading: number; status: string;vertical_reference?:{type?:string};terrain_version_id?:number|null } | null>(null);
  const [terrainStatus, setTerrainStatus] = useState("WORLD TERRAIN · CHECKING");
  const [terrainDetail, setTerrainDetail] = useState("Selecting terrain automatically…");
  const [terrainRetry, setTerrainRetry] = useState(0);
  const [buildingStatus, setBuildingStatus] = useState<string | null>(null);
  const [projectTerrain, setProjectTerrain] = useState<{ id: number; state: string; ion_asset_id: number; coverage: GeoJSONGeometry } | null>(null);
  const measurePointsRef = useRef<[number, number, number][]>([]);
  const measurementSamples = useRef<MeasurementPoint[]>([]);
  const measurementRequest = useRef(0);
  const measurementQueue = useRef<Promise<void>>(Promise.resolve());
  const handlerRef = useRef<CesiumInputHandler | null>(null);
  const sitePickRef = useRef<((event:{position:{x:number;y:number}})=>void) | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const modelsRef = useRef<{ main: any; excav: any }>({ main: null, excav: null });
  const basemapRef = useRef(basemap);
  const mapRuntimeRef = useRef<{ cesium_ion_token: string | null; google_maps_api_key: string | null }>({
    cesium_ion_token: null,
    google_maps_api_key: null,
  });

  const [error, setError] = useState("");
  const foundationMarkersRef=useRef<{position:import('cesium').Cartesian3;key:string;name:string;box?:{x:number;y:number;width:number;height:number}}[]>([]);
  const [foundationAppearance,setFoundationAppearance]=useState<Record<string,number>>({});
  useEffect(()=>{const update=(event:Event)=>{setFoundationAppearance((event as CustomEvent<Record<string,number>>).detail??{});};window.addEventListener('geoai:foundation-appearance',update);return()=>window.removeEventListener('geoai:foundation-appearance',update);},[]);
  const [analysisClip, setAnalysisClip] = useState<AnalysisClip>({ mode: "off", value: 0, size: 50 });
  const [transformPointer, setTransformPointer] = useState<{x:number;y:number}|null>(null);
  const [transformReadout, setTransformReadout] = useState<string | null>(null);
  const [cameraOutside,setCameraOutside]=useState(false);
  const [cadMeshError, setCadMeshError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  useEffect(()=>{
    const viewer=viewerRef.current,C=cesiumRef.current;if(!loaded||!viewer||!C)return;
    let pressed=false;
    const capture=(event:Event)=>{
      const e=event as MouseEvent;if(e.button!==0||useProjectStore.getState().scene3dMeasureTool!=='none')return;
      const box=viewer.canvas.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top;
      const marker=foundationMarkersRef.current.find(m=>{const p=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,m.position);if(m.box)return x>=m.box.x&&x<=m.box.x+m.box.width&&y>=m.box.y&&y<=m.box.y+m.box.height;if(!p)return false;const lines=m.name.split('\n');return Math.abs(x-p.x-12)<=Math.max(...lines.map(l=>l.length))*3.4+8&&Math.abs(y-p.y-14)<=lines.length*6.5+5;});
      const surfaceKey=!marker&&viewer.canvas.getAttribute('data-floor-system')==='true'?viewer.scene.drillPick(new C.Cartesian2(x,y),20).map((hit:{id?:import('cesium').Entity})=>hit.id?.properties?.getValue?.(viewer.clock.currentTime)).filter((p:{engineeringPickPriority?:number}|undefined)=>p&&!!p.engineeringPickPriority).sort((a:{engineeringPickPriority:number},b:{engineeringPickPriority:number})=>b.engineeringPickPriority-a.engineeringPickPriority).map((p:{foundationCheckKey?:string})=>p.foundationCheckKey).find(Boolean):undefined;
      const key=marker?.key??surfaceKey;
      if(!key&&!pressed)return;
      e.preventDefault();e.stopImmediatePropagation();
      if(key&&(e.type==='pointerdown'||e.type==='click'&&!pressed)){pressed=true;viewer.canvas.setAttribute('data-foundation-last-inspected',key);window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key}}));}
      if(e.type==='click')pressed=false;
    };
    const events=['pointerdown','mousedown','pointerup','mouseup','click'];for(const type of events)viewer.canvas.addEventListener(type,capture,true);
    return()=>{for(const type of events)viewer.canvas.removeEventListener(type,capture,true);};
  },[loaded]);
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
  const analysisOverlayActive = useRef(false);
  const foundationInspectionRef = useRef(false);
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
  useEffect(()=>{
    const locate=(event:Event)=>{
      const viewer=viewerRef.current,C=cesiumRef.current;
      if(!viewer || !C || viewer.isDestroyed())return;
      const id=(event as CustomEvent<string>).detail;
      const entity=dataSourcesRef.current.get("editable-model")?.entities.getById(`editable:${id}`);
      const position=entity?.position?.getValue(C.JulianDate.now());
      if(position) {
        const radius=Number(entity?.properties?.getValue(C.JulianDate.now())?.previewRadiusM) || 15;
        viewer.camera.flyToBoundingSphere(new C.BoundingSphere(position,radius),{duration:0.7,offset:new C.HeadingPitchRange(viewer.camera.heading,C.Math.toRadians(-58),modelFitRange(radius, Number((viewer.camera.frustum as {fovy?:number}).fovy ?? Math.PI/3), viewer.canvas.clientWidth/Math.max(1,viewer.canvas.clientHeight)))});
      }
    };
    const frameAssembly=()=>{
      const viewer=viewerRef.current,C=cesiumRef.current;
      if(!viewer || !C || viewer.isDestroyed())return;
      const now=C.JulianDate.now();
      const entities: import("cesium").Entity[]=dataSourcesRef.current.get("editable-model")?.entities.values ?? [];
      const spheres=entities.filter(e=>e.id.startsWith("editable:industrial-platform-5x3:") || e.id.startsWith("editable:platform-addon:")).flatMap(e=>{
        const point=e.position?.getValue(now);return point?[new C.BoundingSphere(point,Number(e.properties?.getValue(now)?.previewRadiusM)||1)]:[];
      });
      if(spheres.length){const bounds=C.BoundingSphere.fromBoundingSpheres(spheres);viewer.camera.cancelFlight();viewer.camera.lookAt(bounds.center,new C.HeadingPitchRange(C.Math.toRadians(-25),C.Math.toRadians(-25),modelFitRange(bounds.radius, Number((viewer.camera.frustum as {fovy?:number}).fovy ?? Math.PI/3), viewer.canvas.clientWidth/Math.max(1,viewer.canvas.clientHeight))));viewer.camera.lookAtTransform(C.Matrix4.IDENTITY);}
    };
    window.addEventListener("geoai:locate-component",locate);
    window.addEventListener("geoai:frame-platform-assembly",frameAssembly);
    return()=>{window.removeEventListener("geoai:locate-component",locate);window.removeEventListener("geoai:frame-platform-assembly",frameAssembly);};
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
      if(position)ds.entities.add({position,point:{pixelSize:10,color:C.Color.fromCssColorString("#60a5fa"),disableDepthTestDistance:Infinity}});
      viewer.scene.requestRender();
    };
    window.addEventListener("geoai:analysis-location",highlight);
    return ()=>window.removeEventListener("geoai:analysis-location",highlight);
  },[loaded,editableModel,acceptedPlacement,displayElevation]);
  useEffect(()=>{
    const viewer=viewerRef.current,C=cesiumRef.current;
    if(!loaded||!viewer||!C||!editableModel)return;
    let connectionOverlay: import('cesium').Primitive | null=null;
    let barOverlay: import('cesium').Primitive | null=null;
    let removeLabelProjection:(()=>void)|undefined;
    let removeAnimationRender:(()=>void)|undefined;
    const draw=(event:Event)=>{
      if(connectionOverlay){viewer.scene.primitives.remove(connectionOverlay);connectionOverlay=null;}
      const data=(event as CustomEvent<{assistantCommand?:WorkspaceCommand;paths:number[][][];label:string;mode:string;overlayThroughSolids?:boolean;fit?:boolean;componentIds?:string[];colors?:string[];focus?:number[];fitRange?:number;fitPitch?:number;fitHeadingOffset?:number;focusComponentIds?:string[];fitPoints?:number[][];nodeMarkers?:{name:string;position:number[];componentId?:string;inspectionKey?:string}[];polygons?:{positions:number[][];basePositions?:number[][];color:string;componentId:string;alpha?:number;inspectionKey?:string}[];arrowIndices?:number[];bars?:FoundationOverlay['bars'];visualMode?:string;hideModel?:boolean;displayOpacity?:Record<string,number>;pathStyles?:string[];selectedComponentId?:string;inspectionKeys?:string[];floorSystem?:boolean;animation?:{basePaths:number[][][];periodSeconds:number}}|null>).detail;
      analysisOverlayActive.current=!!data;foundationMarkersRef.current=[];viewer.scene.canvas.setAttribute("data-floor-system",String(!!data?.floorSystem));if(!data?.floorSystem){viewer.scene.canvas.removeAttribute("data-floor-surface-points");viewer.scene.canvas.removeAttribute("data-engineering-load-points");}
      foundationInspectionRef.current=['foundation-interface','drawing-cad','foundation-integrated','structural-visual'].includes(data?.mode??'');
      connectionInspectionRef.current=!!data;
      for(const entity of dataSourcesRef.current.get('editable-model')?.entities.values??[])if(entity.id.startsWith('platform-dimension:')||entity.id.startsWith('selected-label:'))entity.show=dimensionsVisibleRef.current&&!connectionInspectionRef.current;
      for(const entity of dataSourcesRef.current.get('editable-model')?.entities.values??[])if(entity.id.startsWith('editable:')&&entity.label)entity.label.show=new C.ConstantProperty(!['foundation-interface','drawing-cad','foundation-integrated','structural-visual'].includes(data?.mode??''));
      const ds=getDs(viewer,C,'elastic-results');ds.entities.removeAll();
      if(!data){viewer.scene.canvas.removeAttribute('data-deformation-animation');viewer.scene.canvas.removeAttribute('data-deformation-phase');viewer.scene.canvas.removeAttribute('data-structural-transition');viewer.scene.canvas.removeAttribute('data-engineering-label-boxes');viewer.scene.canvas.removeAttribute('data-structural-mode');viewer.scene.canvas.removeAttribute('data-foundation-mode');viewer.scene.canvas.removeAttribute('data-foundation-label-points');viewer.scene.canvas.removeAttribute('data-foundation-bars');viewer.scene.canvas.removeAttribute('data-elastic-diagram');viewer.scene.canvas.removeAttribute('data-analysis-label');viewer.scene.canvas.removeAttribute('data-analysis-pick-points');viewer.scene.requestRender();return;}
      const frame=C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(acceptedPlacement?.longitude??editableModel.origin.lng,acceptedPlacement?.latitude??editableModel.origin.lat,displayElevation));
      const heading=(acceptedPlacement?.heading??editableModel.origin.heading_deg)*Math.PI/180;
      const world=([x,y,z]:number[])=>C.Matrix4.multiplyByPoint(frame,new C.Cartesian3(x*Math.cos(heading)-y*Math.sin(heading),x*Math.sin(heading)+y*Math.cos(heading),z),new C.Cartesian3());
      const paths=data.paths.map(path=>path.map(world));
      const basePaths=data.animation?.basePaths.map(path=>path.map(world)),animationStart=performance.now(),animated=new Set(paths.map((p,i)=>i).filter(i=>basePaths?.[i]?.length===paths[i].length&&paths[i].some((p,j)=>C.Cartesian3.distance(p,basePaths[i][j])>1e-9)));
      viewer.scene.canvas.setAttribute("data-deformation-animation",data.animation?"playing":"paused");
      const animatedPositions=(index:number)=>{const cached=paths[index].map(()=>new C.Cartesian3());return new C.CallbackProperty(()=>{const phase=deformationPhase((performance.now()-animationStart)/1000,data.animation?.periodSeconds);if(index===animated.values().next().value)viewer.scene.canvas.setAttribute("data-deformation-phase",phase.toFixed(3));for(let i=0;i<cached.length;i++)C.Cartesian3.lerp(basePaths![index][i],paths[index][i],phase,cached[i]);return cached;},false);};
      if(data.animation){const request=()=>{if(!document.hidden)viewer.scene.requestRender();};removeAnimationRender=viewer.scene.postRender.addEventListener(request);}
      for(const area of data.polygons??[]){
        const target=area.positions.map(world),base=data.animation&&area.basePositions?.length===target.length?area.basePositions.map(world):undefined,cached=target.map(()=>new C.Cartesian3()),hierarchy=new C.PolygonHierarchy(cached);
        const animatedHierarchy=base?new C.CallbackProperty(()=>{const phase=deformationPhase((performance.now()-animationStart)/1000,data.animation?.periodSeconds);for(let i=0;i<cached.length;i++)C.Cartesian3.lerp(base[i],target[i],phase,cached[i]);return hierarchy;},false):new C.PolygonHierarchy(target);
        ds.entities.add({properties:{editableComponentId:area.componentId,foundationCheckKey:area.inspectionKey,engineeringPickPriority:data.floorSystem?10:0},polygon:{hierarchy:animatedHierarchy,perPositionHeight:true,material:C.Color.fromCssColorString(area.color).withAlpha(area.alpha??.42),outline:!(data.mode==='structural-visual'&&data.visualMode==='forces'),outlineColor:C.Color.WHITE}});
      }
      const pathMaterial=(index:number)=>{const color=C.Color.fromCssColorString(data.colors?.[index]??(data.mode==='deformation'?'#60a5fa':data.mode==='moment'?'#ff8b5c':'#53cfff'));return ['reference','diagram-dashed'].includes(data.pathStyles?.[index]??'')?new C.PolylineDashMaterialProperty({color,dashLength:data.pathStyles?.[index]==='reference'?12:20}):color;};
      for(const [index,positions] of paths.entries())ds.entities.add({properties:{editableComponentId:data.componentIds?.[index],foundationCheckKey:data.inspectionKeys?.[index],engineeringPickPriority:data.floorSystem?20:0},polyline:{positions:animated.has(index)?animatedPositions(index):positions,arcType:C.ArcType.NONE,width:data.pathStyles?.[index]==='reference'?2:data.pathStyles?.[index]==='ordinate'?1.5:data.mode==='structural-visual'?5:6,material:(data.mode==='loads'||data.arrowIndices?.includes(index))?new C.PolylineArrowMaterialProperty(C.Color.fromCssColorString(data.floorSystem?(data.colors?.[index]??'#ffe18a'):'#ffe18a')):pathMaterial(index),depthFailMaterial:pathMaterial(index)}});
      if(data.mode==='connections'||data.mode==='foundation-interface'||data.mode==='drawing-cad'||data.overlayThroughSolids||['deformation','axial','shear','moment','reactions','loads'].includes(data.mode)){
        const instances=paths.map((positions,index)=>({positions,index})).filter(({positions,index})=>!animated.has(index)&&!['reference','ordinate','diagram-dashed'].includes(data.pathStyles?.[index]??'')&&positions.length>1&&positions.some((p,i)=>i>0&&C.Cartesian3.distance(p,positions[i-1])>1e-9)).map(({positions,index})=>new C.GeometryInstance({geometry:new C.PolylineGeometry({positions,width:5,arcType:C.ArcType.NONE,vertexFormat:C.PolylineColorAppearance.VERTEX_FORMAT}),attributes:{color:C.ColorGeometryInstanceAttribute.fromColor(C.Color.fromCssColorString(data.colors?.[index]??(data.mode==='deformation'?'#60a5fa':data.mode==='moment'?'#ff8b5c':data.mode==='loads'?'#ffe18a':'#53cfff')))},id:{properties:new C.PropertyBag({editableComponentId:data.componentIds?.[index],foundationCheckKey:data.inspectionKeys?.[index],engineeringPickPriority:data.floorSystem?20:0})}}));
        connectionOverlay=viewer.scene.primitives.add(new C.Primitive({geometryInstances:instances,appearance:new C.PolylineColorAppearance({translucent:['rc-flexure-layout','foundation-integrated'].includes(data.mode),renderState:{depthTest:{enabled:false},depthMask:false}}),asynchronous:false}));
      }
      if(data.bars?.length){
        const instances=data.bars.map(bar=>{
          const start=world(bar.start),end=world(bar.end),direction=C.Cartesian3.normalize(C.Cartesian3.subtract(end,start,new C.Cartesian3()),new C.Cartesian3()),length=C.Cartesian3.distance(start,end);
          const dot=Math.max(-1,Math.min(1,C.Cartesian3.dot(C.Cartesian3.UNIT_Z,direction))),axis=C.Cartesian3.cross(C.Cartesian3.UNIT_Z,direction,new C.Cartesian3());
          const rotation=C.Cartesian3.magnitude(axis)>1e-9?C.Quaternion.fromAxisAngle(C.Cartesian3.normalize(axis,axis),Math.acos(dot)):dot<0?C.Quaternion.fromAxisAngle(C.Cartesian3.UNIT_X,Math.PI):C.Quaternion.IDENTITY;
          return new C.GeometryInstance({geometry:new C.CylinderGeometry({length,topRadius:bar.radius,bottomRadius:bar.radius,slices:12,vertexFormat:C.PerInstanceColorAppearance.VERTEX_FORMAT}),modelMatrix:C.Matrix4.fromRotationTranslation(C.Matrix3.fromQuaternion(rotation),C.Cartesian3.midpoint(start,end,new C.Cartesian3())),attributes:{color:C.ColorGeometryInstanceAttribute.fromColor(C.Color.fromCssColorString(bar.color))},id:{properties:new C.PropertyBag({editableComponentId:bar.componentId,foundationCheckKey:bar.inspectionKey})}});
        });
        barOverlay=viewer.scene.primitives.add(new C.Primitive({geometryInstances:instances,appearance:new C.PerInstanceColorAppearance({closed:true,translucent:true,renderState:{depthTest:{enabled:false},depthMask:false}}),asynchronous:false}));
      }
      const markerEntities=(data.nodeMarkers??[]).map(marker=>ds.entities.add({position:world(marker.position),properties:{editableComponentId:marker.componentId,foundationCheckKey:marker.inspectionKey,engineeringPickPriority:data.floorSystem?30:0},point:{pixelSize:8,color:C.Color.YELLOW,outlineColor:C.Color.BLACK,outlineWidth:1,disableDepthTestDistance:Infinity},label:{text:marker.name,font:'11px sans-serif',showBackground:true,pixelOffset:new C.Cartesian2(12,marker.name.startsWith('Beam')?-28:14),disableDepthTestDistance:Infinity}}));
      if(paths[0]?.length&& !data.nodeMarkers)ds.entities.add({position:paths[0][paths[0].length-1],label:{text:data.label,font:'13px sans-serif',showBackground:true,pixelOffset:new C.Cartesian2(0,-65),disableDepthTestDistance:Infinity}});
      const all=[...paths.flat(),...(data.fitPoints??[]).map(world),...(data.mode==='structural-visual'?(data.polygons??[]).flatMap(p=>p.positions.map(world)):[])];if(all.length&&(data.fit!==false||data.assistantCommand)){const bounds=C.BoundingSphere.fromPoints(all);++sandboxFlightGeneration.current;viewer.camera.cancelFlight();sandboxCameraReady.current=true;const target=data.focus?world(data.focus):bounds.center;
        if(data.mode==='structural-visual'||data.mode==='foundation-integrated'){
          const range=data.mode==='foundation-integrated'?(data.fitRange??Math.max(bounds.radius*3.4,12)):data.fitRange?data.fitRange*.88:structuralFitRange(bounds.radius,viewer.scene.canvas.clientWidth/viewer.scene.canvas.clientHeight,viewer.camera.frustum.fovy??Math.PI/3);
          viewer.scene.canvas.setAttribute('data-structural-transition','framing');
          const ready=()=>{if(!viewer.isDestroyed()){viewer.scene.canvas.setAttribute('data-structural-transition','ready');viewer.scene.requestRender();}};
          viewer.camera.flyToBoundingSphere(new C.BoundingSphere(target,bounds.radius),{duration:.5,complete:ready,cancel:ready,offset:new C.HeadingPitchRange(heading+(data.fitHeadingOffset??Math.PI),C.Math.toRadians(data.fitPitch??-18),range)});
        }else{viewer.camera.lookAt(data.focus?world(data.focus):bounds.center,new C.HeadingPitchRange(heading+(data.fitHeadingOffset??Math.PI),C.Math.toRadians(data.fitPitch??(data.mode==='connections'?-20:data.mode==='slab-transfer'?-32:data.mode==='foundation-interface'?-32:-18)),data.fitRange??Math.max(bounds.radius*3.4,12)));viewer.camera.lookAtTransform(C.Matrix4.IDENTITY);}
      }
      if(data.mode==='structural-visual')viewer.scene.canvas.setAttribute('data-structural-mode',data.visualMode??'');else viewer.scene.canvas.removeAttribute('data-structural-mode');
      if(data.visualMode){
        foundationMarkersRef.current=(data.nodeMarkers??[]).filter(marker=>marker.inspectionKey).map(marker=>({position:world(marker.position),name:marker.name,key:marker.inspectionKey!}));
        const projectLabels=()=>{const points=foundationMarkersRef.current.map(marker=>{const point=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,marker.position);return point?{key:marker.key,x:point.x+12,y:point.y+14}:null;});const json=JSON.stringify(points);if(viewer.scene.canvas.getAttribute('data-foundation-label-points')!==json)viewer.scene.canvas.setAttribute('data-foundation-label-points',json);};
        let lastLayout='';
        const labelMeasure=window.document.createElement('canvas').getContext('2d');if(labelMeasure)labelMeasure.font='12px sans-serif';
        const projectStructuralLabels=()=>{
          if(viewer.scene.canvas.getAttribute('data-structural-transition')==='framing'){for(const entity of markerEntities)if(entity.label)entity.label.show=new C.ConstantProperty(false);foundationMarkersRef.current=[];lastLayout='';viewer.scene.canvas.setAttribute('data-engineering-label-boxes','[]');viewer.scene.canvas.setAttribute('data-foundation-label-points','[]');return;}
                    if(data.floorSystem){
            const surfaces=(data.polygons??[]).filter((p,i,all)=>p.inspectionKey&&p.positions.length===4&&all.findIndex(q=>q.inspectionKey===p.inspectionKey)===i).flatMap(p=>{const point=p.positions[0].map((_,i)=>p.positions[0][i]*.49+p.positions[1][i]*.21+p.positions[2][i]*.09+p.positions[3][i]*.21),screen=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,world(point));return screen?[{key:p.inspectionKey,x:screen.x,y:screen.y}]:[];});viewer.scene.canvas.setAttribute('data-floor-surface-points',JSON.stringify(surfaces));
            const loads=paths.flatMap((path,i)=>data.inspectionKeys?.[i]?.startsWith('load:')?(()=>{const point=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,C.Cartesian3.midpoint(path[0],path.at(-1)!,new C.Cartesian3()));return point?[{key:data.inspectionKeys[i],x:point.x,y:point.y}]:[];})():[]);viewer.scene.canvas.setAttribute('data-engineering-load-points',JSON.stringify(loads));
          }
          const markers=data.nodeMarkers??[],screen=markers.map((marker,index)=>{const point=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,world(marker.position));const text=engineeringLabelText(marker.name,marker.componentId===data.selectedComponentId);return point?{key:String(index),x:Math.round(point.x),y:Math.round(point.y),width:Math.ceil(Math.max(...text.split('\n').map(t=>labelMeasure?.measureText(t).width??t.length*7)))+20,height:text.split('\n').length*18+16,priority:marker.componentId===data.selectedComponentId,text,marker}:null;}).filter((p):p is NonNullable<typeof p>=>!!p);
          const obstacles=data.visualMode==='forces'?paths.flatMap((path,index)=>data.pathStyles?.[index]?.startsWith('diagram')?path.slice(1).flatMap((end,i)=>{const a=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,path[i]),b=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,end);return a&&b?[{x:Math.min(a.x,b.x)-10,y:Math.min(a.y,b.y)-10,width:Math.abs(a.x-b.x)+20,height:Math.abs(a.y-b.y)+20}]:[];}):[]):[];
          const layout=layoutEngineeringLabels(screen,viewer.scene.canvas.clientWidth,viewer.scene.canvas.clientHeight,obstacles),signature=JSON.stringify(layout);if(signature===lastLayout)return;lastLayout=signature;
          for(const [index,entity]of markerEntities.entries()){const item=layout.find(l=>l.key===String(index)),base=screen.find(l=>l.key===String(index));if(!entity.label)continue;entity.label.show=new C.ConstantProperty(!!item);if(item&&base){entity.label.text=new C.ConstantProperty(base.text);entity.label.font=new C.ConstantProperty('12px sans-serif');entity.label.horizontalOrigin=new C.ConstantProperty(C.HorizontalOrigin.LEFT);entity.label.verticalOrigin=new C.ConstantProperty(C.VerticalOrigin.TOP);entity.label.pixelOffset=new C.ConstantProperty(new C.Cartesian2(item.x-base.x,item.y-base.y));}}
          foundationMarkersRef.current=screen.map(p=>{const b=layout.find(l=>l.key===p.key);return {position:world(p.marker.position),name:p.marker.name,key:p.marker.inspectionKey??'',box:b?{x:b.x,y:b.y,width:b.width,height:b.height}:{x:p.x-5,y:p.y-5,width:10,height:10}};});
          viewer.scene.canvas.setAttribute('data-engineering-label-boxes',JSON.stringify(layout.map(l=>({x:l.x,y:l.y,width:l.width,height:l.height}))));
          viewer.scene.canvas.setAttribute('data-foundation-label-points',JSON.stringify(layout.map(l=>({key:markers[Number(l.key)].inspectionKey,x:l.x+l.width/2,y:l.y+l.height/2}))));viewer.scene.requestRender();
        };
        const project=data.mode==='structural-visual'?projectStructuralLabels:projectLabels;project();removeLabelProjection=viewer.scene.postRender.addEventListener(project);
        viewer.scene.canvas.setAttribute('data-foundation-mode',data.visualMode);viewer.scene.canvas.setAttribute('data-foundation-bars',String(data.bars?.length??0));
      }

      viewer.scene.canvas.setAttribute('data-analysis-pick-points',JSON.stringify(paths.map((path,index)=>{const point=C.SceneTransforms.worldToWindowCoordinates(viewer.scene,data.mode==='drawing-cad'?C.Cartesian3.midpoint(path[0],path.at(-1)!,new C.Cartesian3()):path[Math.floor(path.length/4)]);return point?{componentId:data.componentIds?.[index],x:point.x,y:point.y}:null;})));viewer.scene.canvas.setAttribute('data-elastic-diagram',data.mode);viewer.scene.canvas.setAttribute('data-analysis-label',data.label);viewer.scene.requestRender();
      if(data.assistantCommand){const command=data.assistantCommand;
        if(command.projectId!==editableModel.project_id||command.revisionId!==modelRevisionId||!((data.paths?.length??0)+(data.polygons?.length??0)+(data.nodeMarkers?.length??0))){outcome(command,false,'This saved mode has no supported visual geometry. No completion is claimed.');return;}
        const remove=viewer.scene.postRender.addEventListener(()=>{if(connectionOverlay&&!connectionOverlay.ready)return;remove();clearTimeout(timer);viewer.canvas.dataset.assistantResult=JSON.stringify({projectId:command.projectId,revisionId:command.revisionId,resultId:command.resultIdentity?.id,method:command.resultIdentity?.method,loadCase:command.loadCase,mode:command.mode});outcome(command,true,`Displayed saved result #${command.resultIdentity?.id} · ${command.resultIdentity?.method} · ${command.loadCase} · ${command.mode}. No calculation was run.`);});
        const timer=window.setTimeout(()=>{remove();outcome(command,false,'The result renderer did not confirm this display.');},7000);
      }
    };
    draw(new CustomEvent('geoai:elastic-results',{detail:elasticResults}));
    return()=>{removeAnimationRender?.();removeLabelProjection?.();foundationMarkersRef.current=[];if(!viewer.isDestroyed()){getDs(viewer,C,'elastic-results').entities.removeAll();if(connectionOverlay)viewer.scene.primitives.remove(connectionOverlay);if(barOverlay)viewer.scene.primitives.remove(barOverlay);}};
  },[loaded,editableModel,acceptedPlacement,displayElevation,elasticResults,modelRevisionId]);
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
    const unresolvedPreview = acceptedPlacement?.status === "REVIEW_REQUIRED" && acceptedPlacement.elevation === null;
    if (!loaded || !viewer || !Cesium || !terrainReady || localSandbox || (acceptedPlacement && !unresolvedPreview) || (editableModel?.origin.elevation_m ?? 0) !== 0) return;
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

  const isBuildingModel = editableModel?.project_type === "building";
  const fitProject = useCallback((mode: "structure" | "all" = "structure") => {
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
    let sphere = sandboxBounds.current ?? (points.length
      ? Cesium.BoundingSphere.fromPoints(points)
      : mainSphere ?? excavSphere ?? (alignmentPoints.length ? Cesium.BoundingSphere.fromPoints(alignmentPoints) : null));
    // Legacy models and centerlines can be at ellipsoid height zero, beneath terrain.
    // Frame them from the terrain surface so the camera never flies underground.
    if (sphere && !modelView && !localSandbox && !undergroundView) {
      const location = Cesium.Cartographic.fromCartesian(sphere.center);
      if (location) {
        const ground = viewer.scene.globe.getHeight(location);
        if (Number.isFinite(ground) && location.height < ground) {
          sphere = new Cesium.BoundingSphere(Cesium.Cartesian3.fromRadians(location.longitude, location.latitude, ground), sphere.radius);
        }
      } else sphere = null;
    }
    if (sphere) {
      const flight = ++sandboxFlightGeneration.current;
      if (localSandbox) {
        sandboxCameraReady.current = false;
        delete viewer.scene.canvas.dataset.sandboxReady;
      }
      const heading=alignmentBearing(alignment ?? null)+0.45,pitch=Cesium.Math.toRadians(-28);
      const framed=(modelView||localSandbox) ? frameEntities(Cesium,editable,sphere,heading,pitch,Number((viewer.camera.frustum as {fovy?:number}).fovy ?? Math.PI/3),viewer.canvas.clientWidth/Math.max(1,viewer.canvas.clientHeight),mode==='structure' ? entity=>!!entity.properties?.getValue(now)?.structuralPresentation : undefined) : null;
      viewer.camera.flyToBoundingSphere(framed?.sphere ?? sphere, {
        offset: new Cesium.HeadingPitchRange(alignmentBearing(alignment ?? null) + 0.45, Cesium.Math.toRadians(-28), framed ? framed.range : Math.max(sphere.radius*3.4,isBuildingModel ? 12 : 280)),
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
  }, [alignment, centerLat, centerLng, loaded, localSandbox, isBuildingModel, undergroundView, modelView]);

  useEffect(() => {
    const viewer = viewerRef.current, C = cesiumRef.current;
    if (!loaded || !viewer || !C || viewer.isDestroyed()) return;
    viewer.scene.globe.show = !modelView;
    if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = !modelView;
    if (viewer.scene.skyBox) viewer.scene.skyBox.show = !modelView;
    viewer.scene.backgroundColor = C.Color.fromCssColorString("#18232e");
    if (viewer.scene.sun) viewer.scene.sun.show = !modelView;
    if (viewer.scene.moon) viewer.scene.moon.show = !modelView;
    viewer.scene.screenSpaceCameraController.enableCollisionDetection = !modelView && !undergroundView;
    viewer.shadows = modelView;
    viewer.shadowMap.softShadows = true;
    for (const [key, source] of dataSourcesRef.current) {
      if (["roads", "buildings", "water", "pipeline", "construction", "project", "labels"].includes(key)) source.show = !modelView;
    }
    viewer.scene.requestRender();
    if (sandboxBounds.current) fitProject();
  }, [loaded, modelView, undergroundView, fitProject]);

  useEffect(() => {
    const onFit = () => fitProject();
    const presentation = (event: Event) => { setModelView((event as CustomEvent<string>).detail === "model"); fitProject(); };
    window.addEventListener("geoai:fit-project", onFit);
    window.addEventListener("geoai:presentation", presentation);
    return () => { window.removeEventListener("geoai:fit-project", onFit); window.removeEventListener("geoai:presentation", presentation); };
  }, [fitProject]);

  useEffect(()=>{
    const viewer=viewerRef.current;
    if(!loaded||!viewer)return;
    const camera=(event:Event)=>{
      const command=(event as CustomEvent<WorkspaceCommand>).detail;
      if(command.operation!=='switch_workspace_view')return;
      if(command.projectId!==editableModel?.project_id||command.revisionId!==modelRevisionId||!['model','site'].includes(command.view||'')){outcome(command,false,'Viewer source does not match.');return;}
      const desired=command.view==='model';setModelView(desired);fitProject();
      const remove=viewer.scene.postRender.addEventListener(()=>{if(modelViewRef.current===desired){remove();clearTimeout(timer);outcome(command,true,`Switched to ${command.view} view.`);}});
      const timer=window.setTimeout(()=>{remove();outcome(command,false,'The viewer did not confirm the presentation.');},7000);viewer.scene.requestRender();
    };
    window.addEventListener('geoai:workspace-camera',camera);
    const removeError=viewer.scene.renderError.addEventListener((_scene:unknown,failure:unknown)=>setError(`3D rendering failed: ${failure instanceof Error?failure.message:'graphics context unavailable'}`));
    return()=>{window.removeEventListener('geoai:workspace-camera',camera);removeError();};
  },[loaded,editableModel?.project_id,modelRevisionId,fitProject]);
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
    viewer.canvas.dataset.sandboxReady="false";
    if (!editableModel) return;
    let cancelled = false;
    let sandboxCollection: import("cesium").PrimitiveCollection | null = null;
    let removePostRender: (() => void) | null = null;
    let pickCandidates: import("cesium").Entity[] | null = null;
    const removePickInvalidation = ds.entities.collectionChanged.addEventListener(() => { pickCandidates = null; });
    const removePickPoints = viewer.scene.postRender.addEventListener(() => {
      const points: Record<string, {x:number;y:number}> = {};
      // Edge entities have no position. Cache only projected component anchors.
      const candidates: import("cesium").Entity[] = pickCandidates ?? ds.entities.values.filter((entity: import("cesium").Entity) => Boolean(entity.position && entity.properties?.editableComponentId));
      pickCandidates = candidates;
      for (const entity of candidates) {
        const id = entity.properties?.getValue(viewer.clock.currentTime)?.editableComponentId;
        const position = entity.position?.getValue(viewer.clock.currentTime);
        const point = position && Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene, position);
        if (id && point) points[id] = {x:point.x,y:point.y};
      }
      viewer.canvas.dataset.componentPickPoints = JSON.stringify(points);
      if(viewer.canvas.dataset.sandboxReady==='true'&&sandboxCameraReady.current&&!analysisOverlayActive.current){
        const hasVisible=ds.entities.values.some((entity:import("cesium").Entity)=>entity.show&&entity.properties?.getValue(viewer.clock.currentTime)?.editableComponentId);
        const inView=Object.values(points).some(p=>p.x>=0&&p.y>=0&&p.x<=viewer.canvas.clientWidth&&p.y<=viewer.canvas.clientHeight);
        setCameraOutside(hasVisible&&!inView);
      }

    });
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
      if (localSandbox || editor || editableModel.components.some(c => c.geometry.kind === "cad_mesh")) {
        const baseDisplayDocument = editor?.platformPreview?.document ?? editableModel;
        const displayDocument = componentPreview ? {...baseDisplayDocument,components:baseDisplayDocument.components.map(c=>c.id===componentPreview.id ? componentPreview:c)} : baseDisplayDocument;
        const renderedDocument = editor?.comparison?.current ?? (localSandbox ? displayDocument : { ...displayDocument, origin: { lng, lat, elevation_m: elevation, heading_deg: documentHeading } });
        await loadCadMeshes(renderedDocument);
        if (editor?.comparison) await loadCadMeshes(editor.comparison.previous);
        if (cancelled) return;
        setCadMeshError(null);
        const primitiveProposal=editor?.platformPreview?.proposal;
        const visualDocument=primitiveProposal?renderedDocument:elasticResults?.hideModel ? {...renderedDocument,components:[]} : analysisFocusKey ? {...renderedDocument,components:renderedDocument.components.filter(c=>analysisFocusKey.split('\n').includes(c.id))} : renderedDocument;
        const preview = buildSandboxMapPrimitives(Cesium, ds.entities, visualDocument, selectedComponentIds, ground, analysisClip, false, {...foundationAppearance,...JSON.parse(structuralOpacityKey),...(primitiveProposal?.candidate?{[primitiveProposal.candidate.id]:.55}:{})});
        for(const entity of ds.entities.values)if(entity.id.startsWith('platform-dimension:')||entity.id.startsWith('selected-label:'))entity.show=dimensionsVisibleRef.current&&!connectionInspectionRef.current;
        for(const entity of ds.entities.values)if(entity.id.startsWith('editable:')&&entity.label)entity.label.show=new Cesium.ConstantProperty(foundationInspectionRef.current===false);
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
        if (editor && !editor.comparison && !editor.platformPreview && !componentPreview) disposeTransform = installCesiumTransform(Cesium, viewer, renderedDocument, selectedComponentIds, {
          mode: editor.tool, coordinates: editor.coordinateMode, pivot: editor.pivotMode,
          translationSnap: editor.snapMeters, rotationSnap: editor.rotationSnap, scaleSnap: editor.scaleSnap,
        }, preview.collection, editor.commitTransforms, setTransformReadout, alignment, ds.entities.values, setTransformPointer);
        viewer.scene.requestRender();
        const originKey = JSON.stringify([renderedDocument.project_id,renderedDocument.origin,primitiveProposal?.actionId]);
        if (!analysisOverlayActive.current && (localSandbox || modelViewRef.current) && preview.bounds && (!sandboxWasFitted.current || sandboxLastOrigin.current !== originKey)) {
          sandboxWasFitted.current = true;
          sandboxLastOrigin.current = originKey;
          sandboxCameraReady.current = false;
          const flight = ++sandboxFlightGeneration.current;
          const assistantLeft=document.querySelector('[aria-label="StruvoCivil Assistant"]')?.getBoundingClientRect().left;
          const availableWidth=assistantLeft===undefined?viewer.canvas.clientWidth:Math.max(300,Math.min(viewer.canvas.clientWidth,assistantLeft-viewer.canvas.getBoundingClientRect().left));
          const fovy=Number((viewer.camera.frustum as {fovy?:number}).fovy ?? Math.PI/3);
          const framed=frameEntities(Cesium,ds.entities.values,preview.bounds,.45,Cesium.Math.toRadians(-28),fovy,availableWidth/Math.max(1,viewer.canvas.clientHeight),entity=>!!entity.properties?.getValue(Cesium.JulianDate.now())?.structuralPresentation);
          viewer.camera.flyToBoundingSphere(framed.sphere, { offset: new Cesium.HeadingPitchRange(0.45, Cesium.Math.toRadians(-28), framed.range), duration: 0.9, complete: () => { if (flight === sandboxFlightGeneration.current) {viewer.camera.moveRight(framed.range*Math.tan(fovy/2)*(viewer.canvas.clientWidth-availableWidth)/Math.max(1,viewer.canvas.clientHeight));sandboxCameraReady.current = true;viewer.scene.requestRender();} }, cancel: () => { if (flight === sandboxFlightGeneration.current) sandboxCameraReady.current = false; } });
        }
        removePostRender = viewer.scene.postRender.addEventListener(() => {
          if (cancelled || (preview.bounds && !analysisOverlayActive.current && !sandboxCameraReady.current)) return;
          for (let i = 0; i < preview.collection.length; i++) if (!preview.collection.get(i).ready) return;
          if(primitiveProposal?.candidate){const position=ds.entities.getById(`editable:${primitiveProposal.candidate.id}`)?.position?.getValue(viewer.clock.currentTime),point=position&&Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene,position),right=document.querySelector('[aria-label="StruvoCivil Assistant"]')?.getBoundingClientRect().left??viewer.canvas.clientWidth;if(!point||point.x<90||point.x>right||point.y<0||point.y>viewer.canvas.clientHeight)return;}
          viewer.scene.canvas.dataset.sandboxReady = "true";
          viewer.scene.canvas.dataset.modelProject=String(editableModel.project_id);
          viewer.scene.canvas.dataset.modelRevision=String(modelRevisionId);
          if(primitiveProposal){viewer.scene.canvas.dataset.primitivePreview=primitiveProposal.actionId;outcome(primitiveProposal,true,`Temporary ${primitiveProposal.candidate?.category} preview rendered. This receipt records a preview only; current approval status is shown in the editor.`);}
          else delete viewer.scene.canvas.dataset.primitivePreview;
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
          const frame = cylinderFrame(component);
          if (!Number.isFinite(frame.length) || frame.length < .001) continue;
          const localMid = frame.center.toArray() as [number, number, number];
          const worldStart = toWorld(frame.start.toArray() as [number, number, number]);
          const worldEnd = toWorld(frame.end.toArray() as [number, number, number]);
          const direction = Cesium.Cartesian3.normalize(Cesium.Cartesian3.subtract(worldEnd, worldStart, new Cesium.Cartesian3()), new Cesium.Cartesian3());
          const axis = Cesium.Cartesian3.cross(Cesium.Cartesian3.UNIT_Z, direction, new Cesium.Cartesian3());
          const dot = Math.max(-1, Math.min(1, direction.z));
          const cylinderOrientation = Cesium.Cartesian3.magnitude(axis) > 1e-8
            ? Cesium.Quaternion.fromAxisAngle(Cesium.Cartesian3.normalize(axis, axis), Math.acos(dot))
            : Cesium.Quaternion.fromAxisAngle(Cesium.Cartesian3.UNIT_X, dot < 0 ? Math.PI : 0);
          const length = Math.max(0.02, frame.length);
          const radius = Math.max(0.01, frame.radius);
          ds.entities.add({
            id: `editable:${component.id}`,
            name: component.name,
            position: toWorld(localMid),
            orientation: cylinderOrientation,
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
    })().catch((failure: unknown) => { if (!cancelled) setCadMeshError(failure instanceof Error ? failure.message : "CAD geometry could not load."); });
    return () => {
      cancelled = true;
      removePickPoints(); removePickInvalidation(); if (!viewer.isDestroyed?.()) delete viewer.canvas.dataset.componentPickPoints;
      disposeTransform?.();
      if(!viewer.isDestroyed?.()){if(ghostCollection)viewer.scene.primitives.remove(ghostCollection);if(ghostDataSource)viewer.dataSources.remove(ghostDataSource,true);}
      removePostRender?.();
      if (localSandbox && !viewer.isDestroyed?.()) delete viewer.scene.canvas.dataset.sandboxReady;
      if (sandboxCollection && !viewer.isDestroyed?.()) viewer.scene.primitives.remove(sandboxCollection);
    };
  // Only scene-relevant editor fields participate; the editor object changes on
  // saving/error/panel updates, which must not interrupt a scene transaction.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded, editableModel, componentPreview, analysisFocusKey, elasticResults?.hideModel, structuralOpacityKey, selectedComponentIds, terrainEpoch, localSandbox, acceptedPlacement, displayElevation, alignment, analysisClip, foundationAppearance, editor?.comparison, editor?.platformPreview, editor?.tool, editor?.coordinateMode, editor?.pivotMode, editor?.snapMeters, editor?.rotationSnap, editor?.scaleSnap, editor?.commitTransforms]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function getDs(viewer: any, Cesium: any, key: string) {
    const map = dataSourcesRef.current;
    if (map.has(key)) return map.get(key)!;
    const ds = new Cesium.CustomDataSource(key);
    if (["roads", "buildings", "water", "pipeline", "construction", "project", "labels"].includes(key)) ds.show = !modelViewRef.current;
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
        const Cesium = await loadCesiumRuntime();
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
          selectionIndicator: false,
          terrain: createFlatTerrain(Cesium),
        });
        viewer.scene.requestRenderMode = graphicsEditor;
        viewer.scene.maximumRenderTimeChange = Infinity;
        viewer.scene.globe.depthTestAgainstTerrain = true;
        viewer.scene.globe.enableLighting = false;
        viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#28332c");
        // Selection is owned by the workspace; Cesium's default click selection
        // otherwise competes with drawing and noneditable-context filtering.
        viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
        viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
        viewerRef.current = viewer;
        if (graphicsEditor) graphicsRef.current = bindWorkspaceGraphics(viewer, () => qualityRef.current, setGraphicsContext, () => { setLoaded(false); setRuntimeRetry(value => value + 1); });
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
      graphicsRef.current?.dispose(); graphicsRef.current = null;
      dataSources.clear();
      viewerRef.current?.destroy?.();
      viewerRef.current = null;
    };
  }, [localSandbox, runtimeRetry, graphicsEditor]);

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
    viewer.scene.screenSpaceCameraController.enableCollisionDetection = !transparentOn && !modelViewRef.current;
    cesiumDevLog(
      "transparent",
      transparentOn ? "Transparent ON (globe translucency)" : "Transparent OFF (opaque globe)",
    );

    if (transparentOn) {
      applyGlobeTranslucency(viewer, Cesium);
      // Unknown-elevation models can be below terrain: its back face must not
      // become an opaque ceiling when framing the saved reference plane.
      viewer.scene.globe.translucency.backFaceAlpha = 0;
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
          material: Cesium.Color.fromCssColorString("#38bdf8").withAlpha(0.12),
          // Cesium does not support polygon outlines when terrain-clamped.
          // The fill remains visible without producing a renderer warning.
          outline: false,
          height: 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        properties: { layer: "construction", objectType: "Construction zone" },
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(ring.flat()),
          width: 4,
          material: new Cesium.PolylineGlowMaterialProperty({ color: Cesium.Color.fromCssColorString("#38bdf8"), glowPower: 0.12 }),
          clampToGround: true,
        },
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
    if ((localSandbox || modelViewRef.current || analysisOverlayActive.current) && sandboxFitRequest.current === fitRequest) return;
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

  // Draw and edit project geometry directly on the Cesium globe.
  useEffect(() => {
    if (!loaded || !drawingTool.startsWith("draw-") && !drawingTool.startsWith("edit-")) return;
    const viewer = viewerRef.current, C = cesiumRef.current;
    if (!viewer || !C) return;
    const editing = drawingTool.startsWith("edit-");
    let points: [number, number][] = editing ? geometryToVertices(drawingTool === "edit-boundary" ? boundary : alignment) : [];
    const source = new C.CustomDataSource("project-drawing");
    viewer.dataSources.add(source);
    const handler = new C.ScreenSpaceEventHandler(viewer.canvas);
    let dragging: number | null = null;
    let releaseDrawingCamera: (()=>void) | null = null;
    let originalDragPoints: [number,number][] | null = null;
    let cursor: [number, number] | null = null;
    let closeReady = false;
    const accent = C.Color.fromCssColorString("#38bdf8");
    const nearStart = (position: { x: number; y: number }) => {
      if (drawingTool !== "draw-polygon" || points.length < 3) return false;
      const start = C.SceneTransforms.worldToWindowCoordinates(viewer.scene, C.Cartesian3.fromDegrees(...points[0]));
      return !!start && Math.hypot(position.x - start.x, position.y - start.y) <= 18;
    };
    let lastClick: { x: number; y: number; at: number } | null = null;
    const pick = (position: { x: number; y: number }): [number, number] | null => {
      const ray = viewer.camera.getPickRay(position);
      const world = ray && viewer.scene.globe.pick(ray, viewer.scene) || viewer.camera.pickEllipsoid(position, C.Ellipsoid.WGS84);
      if (!world) return null;
      const cartographic = C.Cartographic.fromCartesian(world);
      return [C.Math.toDegrees(cartographic.longitude), C.Math.toDegrees(cartographic.latitude)];
    };
    const redraw = () => {
      source.entities.removeAll();
      points.forEach((point, index) => source.entities.add({
        id: `draw-handle-${index}`, position: C.Cartesian3.fromDegrees(...point),
        point: { pixelSize: index === 0 && closeReady ? 18 : 12, color: index === 0 ? accent : C.Color.WHITE, outlineColor: accent, outlineWidth: 2, heightReference: C.HeightReference.CLAMP_TO_GROUND, disableDepthTestDistance: Number.POSITIVE_INFINITY },
        ...(index === 0 && drawingTool === "draw-polygon" && points.length >= 3 ? { label: {
          text: closeReady ? "Click to close boundary" : "Start · click to close", font: "12px sans-serif",
          fillColor: C.Color.WHITE, showBackground: true, backgroundColor: C.Color.fromCssColorString("#0f172a").withAlpha(0.92),
          backgroundPadding: new C.Cartesian2(10, 7), pixelOffset: new C.Cartesian2(0, -30),
          heightReference: C.HeightReference.CLAMP_TO_GROUND, disableDepthTestDistance: Number.POSITIVE_INFINITY,
        } } : {}),
      }));
      const smooth = drawingTool === "draw-line" && useProjectStore.getState().smoothAlignment;
      const rectangle = drawingTool === "draw-rectangle" && points.length && cursor ? geometryToVertices(rectangleFromCorners(points[0], cursor)) : null;
      const preview = rectangle ? [...rectangle, rectangle[0]] : smooth ? geometryToVertices(verticesToSmoothLine(points)) : editing && drawingTool === "edit-boundary" && points.length > 2 ? [...points, points[0]] : points;
      if (preview.length > 1) source.entities.add({ polyline: { positions: C.Cartesian3.fromDegreesArray(preview.flat()), width: 2.5, material: accent, clampToGround: true } });
      // One dashed segment marks the prospective edge; never a second cursor-to-start line.
      if (!editing && !rectangle && cursor && points.length) source.entities.add({ id: "draw-live-edge", polyline: { positions: C.Cartesian3.fromDegreesArray([points.at(-1)!, closeReady ? points[0] : cursor].flat()), width: 2, material: new C.PolylineDashMaterialProperty({ color: accent.withAlpha(0.8), dashLength: 12 }), clampToGround: true } });
      const areaPoints = rectangle || (drawingTool === "draw-polygon" || drawingTool === "edit-boundary" ? points : []);
      if (areaPoints.length >= 3 && !boundaryError(verticesToPolygon(areaPoints))) source.entities.add({ polygon: { hierarchy: C.Cartesian3.fromDegreesArray(areaPoints.flat()), material: accent.withAlpha(0.10), heightReference: C.HeightReference.CLAMP_TO_GROUND } });
      viewer.canvas.dataset.boundaryCloseReady = String(closeReady);
      useProjectStore.getState().setDrawVertices(points);
      viewer.scene.requestRender();
    };
    const finish = () => {
      points = points.filter((point, index) => index === 0 || point[0] !== points[index - 1][0] || point[1] !== points[index - 1][1]);
      const polygon = drawingTool === "draw-polygon" || drawingTool === "edit-boundary";
      let geometry: GeoJSONGeometry | null = null;
      if (polygon && points.length >= 3) geometry = verticesToPolygon(points);
      else if (drawingTool === "draw-rectangle" && points.length >= 2) geometry = rectangleFromCorners(points[0], points.at(-1)!);
      else if (drawingTool === "draw-corridor" && points.length >= 2) geometry = corridorFromLine(points, useProjectStore.getState().corridorWidthM);
      else if (points.length >= 2 && !polygon) geometry = drawingTool === "draw-line" && useProjectStore.getState().smoothAlignment ? verticesToSmoothLine(points) : verticesToLine(points);
      if (!geometry) { useProjectStore.setState({drawingError: polygon ? "Place at least three distinct vertices before finishing." : "Place at least two points before finishing."}); return; }
      const kind = polygon || drawingTool === "draw-rectangle" || drawingTool === "draw-corridor" ? "boundary" : "alignment";
      const error = kind === "boundary" ? boundaryError(geometry) : null;
      useProjectStore.setState({ drawingError: error });
      if (error) return;
      useProjectStore.getState().finishDrawing({ kind, geometry });
    };
    redraw();
    handler.setInputAction((click: { position: { x: number; y: number } }) => {
      if (editing) return;
      if (nearStart(click.position)) { finish(); return; }
      // Cesium dispatches both clicks before a double-click. Ignore the second
      // within the same pixel neighbourhood, rather than relying on geographic equality.
      const now = performance.now();
      if (lastClick && now-lastClick.at < 400 && Math.hypot(click.position.x-lastClick.x,click.position.y-lastClick.y) < 5) return;
      lastClick = { ...click.position, at: now };
      const point = pick(click.position);
      if (point) { points = [...points, point]; useProjectStore.setState({ drawingError: null }); redraw(); if (drawingTool === "draw-rectangle" && points.length === 2) finish(); }
    }, C.ScreenSpaceEventType.LEFT_CLICK);
    handler.setInputAction(finish, C.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
    handler.setInputAction((click: { position: { x: number; y: number } }) => {
      if (!editing) return;
      const entity = viewer.scene.pick(click.position)?.id;
      let index = entity?.id?.startsWith("draw-handle-") ? Number(entity.id.slice(12)) : -1;
      // Request-render scenes can receive pointer input before the new handle
      // primitives reach the GPU pick buffer. Use the displayed vertex position
      // as a bounded fallback so a drag never turns into an accidental orbit.
      if (index < 0) {
        let nearest = 14;
        points.forEach((point, candidate) => {
          const position = C.SceneTransforms.worldToWindowCoordinates(viewer.scene, C.Cartesian3.fromDegrees(...point));
          if (!position) return;
          const distance = Math.hypot(position.x - click.position.x, position.y - click.position.y);
          if (distance < nearest) { nearest = distance; index = candidate; }
        });
      }
      if (index >= 0 && index < points.length && !viewer.canvas.dataset.mouseOwner) { dragging = index; originalDragPoints=points.map(p=>[...p] as [number,number]); releaseDrawingCamera=cameraLease(viewer.scene.screenSpaceCameraController); viewer.canvas.dataset.mouseOwner="drawing"; }
    }, C.ScreenSpaceEventType.LEFT_DOWN);
    handler.setInputAction((motion: { endPosition: { x: number; y: number } }) => {
      const point = pick(motion.endPosition);
      if (!point) return;
      if (dragging !== null) { points = points.map((p,i) => i === dragging ? point : p); useProjectStore.setState({ drawingError: null }); }
      else if (!editing) {
        cursor = point;
        const wasCloseReady = closeReady;
        closeReady = nearStart(motion.endPosition);
        // Preserve committed edges while the cursor moves. Recreating every
        // terrain-clamped entity on each motion makes the perimeter flicker.
        const liveEdge = source.entities.getById("draw-live-edge");
        if (drawingTool !== "draw-rectangle" && wasCloseReady === closeReady && liveEdge?.polyline) {
          liveEdge.polyline.positions = new C.ConstantProperty(C.Cartesian3.fromDegreesArray([points.at(-1)!, closeReady ? points[0] : cursor].flat()));
          viewer.scene.requestRender();
        } else redraw();
        return;
      }
      else return;
      redraw();
    }, C.ScreenSpaceEventType.MOUSE_MOVE);
    const releaseDrag = () => { if(dragging===null)return; dragging = null; originalDragPoints=null; releaseDrawingCamera?.(); releaseDrawingCamera=null; if (!viewer.isDestroyed()) delete viewer.canvas.dataset.mouseOwner; };
    const cancelDrag = () => { if(originalDragPoints){points=originalDragPoints;redraw();} releaseDrag(); };
    handler.setInputAction(releaseDrag, C.ScreenSpaceEventType.LEFT_UP);
    window.addEventListener("pointerup", releaseDrag);
    window.addEventListener("blur", cancelDrag);
    viewer.canvas.addEventListener("pointercancel",cancelDrag);
    const keyboard = (event: KeyboardEvent) => { if(document.activeElement!==viewer.canvas)return; if(event.key === "Escape")cancelDrag(); if (event.target instanceof HTMLElement && event.target.closest("input,textarea,select")) return; if (event.key === "Enter") finish(); if (event.key === "Backspace" && !editing) { event.preventDefault(); useProjectStore.getState().popDrawVertex(); } };
    window.addEventListener("keydown", keyboard);
    window.addEventListener("geoai:finish-drawing", finish);
    const removeHandles = viewer.scene.postRender.addEventListener(() => {
      viewer.canvas.dataset.boundaryHandles = JSON.stringify(points.map(p => C.SceneTransforms.worldToWindowCoordinates(viewer.scene, C.Cartesian3.fromDegrees(...p))).map(p => p ? { x:p.x,y:p.y } : null));
    });
    const unsubscribe = useProjectStore.subscribe((state, previous) => {
      if (state.drawVertices.length < previous.drawVertices.length && state.activeTool === drawingTool) points = state.drawVertices;
      if (state.activeTool === drawingTool && (state.drawVertices.length < previous.drawVertices.length || state.smoothAlignment !== previous.smoothAlignment)) redraw();
    });
    return () => { releaseDrag(); viewer.canvas.removeEventListener("pointercancel",cancelDrag); window.removeEventListener("pointerup", releaseDrag); window.removeEventListener("blur", cancelDrag); removeHandles(); if (!viewer.isDestroyed()) { delete viewer.canvas.dataset.boundaryHandles; delete viewer.canvas.dataset.boundaryCloseReady; } unsubscribe(); window.removeEventListener("keydown", keyboard); window.removeEventListener("geoai:finish-drawing", finish); destroyInputHandler(handler); if (!viewer.isDestroyed()) { viewer.dataSources.remove(source, true); } };
  }, [loaded, drawingTool, boundary, alignment]);

  // Pick + measure
  useEffect(() => {
    const viewer = viewerRef.current;
    const Cesium = cesiumRef.current;
    if (!viewer || !Cesium || !loaded) return;

    destroyInputHandler(handlerRef.current);
    handlerRef.current = null;

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    const pickSelection = (position: {x:number;y:number}) => {
      const first = viewer.scene.pick(position);
      if (String(first?.id?.id ?? "").startsWith("transform:")) return first;
      return viewer.scene.drillPick(position, 12).find((hit: { id?: import("cesium").Entity }) => {
        const id = hit.id?.properties?.getValue?.(Cesium.JulianDate.now())?.editableComponentId;
        return editableModel?.components.some(c => c.id === id && c.visible);
      }) ?? first;
    };
    const handleSelection = (click: { position: { x: number; y: number } }) => {
      if(scene3dMeasureTool==='none'){
        const label=foundationMarkersRef.current.find(marker=>{
          const point=Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene,marker.position);if(marker.box)return click.position.x>=marker.box.x&&click.position.x<=marker.box.x+marker.box.width&&click.position.y>=marker.box.y&&click.position.y<=marker.box.y+marker.box.height;if(!point)return false;
          const lines=marker.name.split('\n'),halfWidth=Math.max(...lines.map(line=>line.length))*3.4+8,halfHeight=lines.length*6.5+5;
          return Math.abs(click.position.x-point.x-12)<=halfWidth&&Math.abs(click.position.y-point.y-14)<=halfHeight;
        });
        const check=label?.key??viewer.scene.drillPick(click.position,20).map((hit:{id?:import('cesium').Entity})=>hit.id?.properties?.getValue?.(viewer.clock.currentTime)).filter(Boolean).sort((a:{engineeringPickPriority?:number},b:{engineeringPickPriority?:number})=>(b.engineeringPickPriority??0)-(a.engineeringPickPriority??0)).map((p:{foundationCheckKey?:string})=>p.foundationCheckKey).find(Boolean);
        if(check){viewer.canvas.setAttribute('data-foundation-last-inspected',String(check));window.dispatchEvent(new CustomEvent('geoai:foundation-inspect',{detail:{key:String(check)}}));return;}
      }

      const picked = scene3dMeasureTool !== "none" ? viewer.scene.pick(click.position) : pickSelection(click.position);
      if (String(picked?.id?.id ?? "").startsWith("transform:")) return;
      const store = useProjectStore.getState();
      if (store.activeTool.startsWith("draw-") || store.activeTool.startsWith("edit-") || store.pendingSave) return;

      if (scene3dMeasureTool !== "none") {
        const measurementSequence = measurementRequest.current;
        const props = picked?.id?.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
        const design = !!props.editableComponentId;
        const ray = viewer.camera.getPickRay(click.position);
        let depthPoint = null;
        try { if (viewer.scene.pickPositionSupported) depthPoint = viewer.scene.pickPosition(click.position); } catch { /* Fall back to terrain ray picking. */ }
        const point = depthPoint
          ?? (ray ? viewer.scene.globe.pick(ray, viewer.scene) : null)
          ?? viewer.camera.pickEllipsoid(click.position, Cesium.Ellipsoid.WGS84);
        if (!point) { store.setScene3dMeasureReadout("UNKNOWN · Surface could not be picked."); return; }
        viewer.entities.add({ id: `measurement-point-${Date.now()}-${Math.random()}`, position: point, point: { pixelSize: 9, color: Cesium.Color.YELLOW, outlineColor: Cesium.Color.BLACK, outlineWidth: 2, disableDepthTestDistance: Number.POSITIVE_INFINITY } });
        viewer.scene.requestRender();
        const carto = Cesium.Cartographic.fromCartesian(point);
        const longitude = Cesium.Math.toDegrees(carto.longitude), latitude = Cesium.Math.toDegrees(carto.latitude);
        measurementQueue.current = measurementQueue.current.catch(() => {}).then(async () => {
          if (measurementSequence !== measurementRequest.current || viewer.isDestroyed()) return;
          const designResolved=acceptedPlacement?.elevation!=null && acceptedPlacement?.status==="VALID" && acceptedPlacement.vertical_reference?.type==="ELLIPSOIDAL";
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
        }).catch(() => { if (measurementSequence === measurementRequest.current) store.setScene3dMeasureReadout("Could not measure this surface. Try another point."); });
        return;
      }
      if (!picked?.id && selectedComponentIds.length && boundary?.type === "Polygon" && scene3dLayers.construction) {
        // Terrain-clamped context can be absent from the GPU pick buffer at
        // close zoom. Keep object selection when the ground click is in the site.
        const ray = viewer.camera.getPickRay(click.position);
        const ground = ray ? viewer.scene.globe.pick(ray, viewer.scene) : undefined;
        if (ground) {
          const carto = Cesium.Cartographic.fromCartesian(ground);
          const x = Cesium.Math.toDegrees(carto.longitude), y = Cesium.Math.toDegrees(carto.latitude);
          const ring = (boundary.coordinates as number[][][])[0];
          let inside = false;
          for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            const [xi, yi] = ring[i], [xj, yj] = ring[j];
            if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
          }
          if (inside) return;
        }
      }
      if (!picked?.id) {
        viewer.selectedEntity = undefined;
        onSelectComponentRef.current?.(null);
        store.setSelectedObject3d(null);
        return;
      }

      const entity = picked.id;
      const props = entity.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
      if (props.editableComponentId) {
        if (!editableModel?.components.some(c => c.id === props.editableComponentId && c.visible)) return;
        store.setSelectedObject3d(null);
        onSelectComponentRef.current?.(String(props.editableComponentId));
        viewer.selectedEntity = entity;
        return;
      }
      if (selectedComponentIds.length) return;
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
    };
    handler.setInputAction(handleSelection, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    sitePickRef.current = handleSelection;

    const additivePick = (click: { position: { x: number; y: number } }) => {
      const store = useProjectStore.getState();
      if (store.activeTool !== "select" || store.pendingSave || scene3dMeasureTool !== "none") return;
      const entity = pickSelection(click.position)?.id;
      const props = entity?.properties?.getValue?.(Cesium.JulianDate.now()) ?? {};
      if (props.editableComponentId && editableModel?.components.some(c => c.id === props.editableComponentId && c.visible)) { store.setSelectedObject3d(null); onSelectComponentRef.current?.(String(props.editableComponentId), true); }
    };
    handler.setInputAction(additivePick, Cesium.ScreenSpaceEventType.LEFT_CLICK, Cesium.KeyboardEventModifier.SHIFT);
    handler.setInputAction(additivePick, Cesium.ScreenSpaceEventType.LEFT_CLICK, Cesium.KeyboardEventModifier.CTRL);

    let hover: { primitive: import("cesium").Primitive; entity: import("cesium").Entity; color: Uint8Array } | null = null;
    const clearHover = () => {
      if (hover && !hover.primitive.isDestroyed()) {
        try { hover.primitive.getGeometryInstanceAttributes(hover.entity).color = hover.color; } catch { /* disposed with model rebuild */ }
      }
      hover = null;
    };
    const hoverCanvas = viewer.canvas;
    const leaveHover = () => {
      clearHover(); setHoveredName(null); hoverCanvas.style.cursor = "default";
      if (!viewer.isDestroyed()) viewer.scene.requestRender();
    };
    hoverCanvas.addEventListener("pointerleave", leaveHover);
    handler.setInputAction((move: { endPosition: { x: number; y: number } }) => {
      const store = useProjectStore.getState();
      if (viewer.canvas.dataset.mouseOwner || viewer.canvas.dataset.navigationMode && viewer.canvas.dataset.navigationMode !== "select") { clearHover(); setHoveredName(null); return; }
      if (store.activeTool !== "select" || scene3dMeasureTool !== "none" || editor?.tool !== "select") return;
      const picked = pickSelection(move.endPosition);
      const id = picked?.id?.properties?.getValue?.(Cesium.JulianDate.now())?.editableComponentId;
      if (hover?.entity === picked?.id) return;
      clearHover();
      const component = editableModel?.components.find(c => c.id === id);
      setHoveredName(component ? componentDisplayName(component) : null);
      viewer.canvas.style.cursor = component ? "pointer" : "default";
      if (component && picked.primitive?.getGeometryInstanceAttributes) {
        try {
          const attrs = picked.primitive.getGeometryInstanceAttributes(picked.id);
          hover = { primitive: picked.primitive, entity: picked.id, color: new Uint8Array(attrs.color) };
          attrs.color = Cesium.ColorGeometryInstanceAttribute.toValue(Cesium.Color.lerp(Cesium.Color.fromBytes(hover.color[0],hover.color[1],hover.color[2],hover.color[3]),Cesium.Color.fromCssColorString("#93b5c5"),0.12,new Cesium.Color()));
        } catch { /* overlays use entity highlighting instead */ }
      }
      viewer.scene.requestRender();
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    handlerRef.current = handler;
    return () => {
      hoverCanvas.removeEventListener("pointerleave", leaveHover);
      clearHover(); if (!viewer.isDestroyed()) viewer.canvas.style.cursor = "default";
      if (handlerRef.current === handler) { handlerRef.current = null; sitePickRef.current = null; }
      // This is a request generation counter, not a captured DOM reference.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      measurementRequest.current++;
      destroyInputHandler(handler);
    };
  }, [loaded, scene3dMeasureTool, measureUnit, alignment, boundary, scene3dLayers.construction, projectTerrain, projectId, terrainEpoch, editableModel, acceptedPlacement, selectedComponentIds, editor?.tool]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (viewer && !viewer.isDestroyed()) viewer.entities.values.filter((entity: import("cesium").Entity) => entity.id.startsWith("measurement-point-")).forEach((entity: import("cesium").Entity) => viewer.entities.remove(entity));
    measurePointsRef.current = [];
    measurementSamples.current = [];
    measurementRequest.current++;
    useProjectStore.getState().setScene3dMeasureReadout(null);
  }, [scene3dMeasureTool, terrainEpoch, editableModel, acceptedPlacement]);

  if (error) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-6 text-center text-sm">
        <p className="font-semibold">3D view unavailable</p><p>WebGL may be unavailable or disabled. Check browser graphics support; software rendering depends on the browser.</p><p className="text-muted-foreground">{error}</p>
        <button className="rounded border border-border px-4 py-2 text-primary" onClick={() => { setError(""); setLoaded(false); setRuntimeRetry(value => value + 1); }}>Retry 3D view</button>
      </div>
    );
  }
  return <>{editor&&<SupervisedPrimitiveControls editor={editor}/ >}{graphicsEditor&&loaded&&<div className="absolute right-14 top-36 z-30 rounded border border-border bg-background/95 px-3 py-2 text-xs"><label className="flex items-center gap-2">Graphics<select aria-label="Graphics quality" value={graphicsQuality} onChange={event=>setGraphicsQuality(event.target.value as GraphicsQuality)} className="rounded border border-border bg-background px-2 py-1"><option value="auto">Auto</option><option value="high">High quality</option><option value="balanced">Balanced</option><option value="performance">Performance</option></select></label><p className="mt-1 text-[10px] text-muted-foreground">WebGL · browser-managed acceleration</p></div>}{graphicsEditor&&graphicsContext!=="ready"&&<div role="status" className="absolute left-24 top-32 z-50 rounded bg-background p-3 text-sm">{graphicsContext==="lost"?"Graphics context lost. Waiting for browser recovery.":"Restoring the 3D view…"}<button className="ml-2 underline" onClick={()=>{setLoaded(false);setRuntimeRetry(value=>value+1);}}>Retry graphics</button></div>}{loaded&&cameraOutside&&!elasticResults&&<div role="status" className="absolute left-24 top-32 z-40 rounded bg-background p-3 text-sm">Model geometry is outside the camera view.<button className="ml-2 underline" onClick={()=>fitProject('all')}>Fit saved model</button></div>}{editor?.loadError&&<div role="alert" className="absolute left-24 top-20 z-50 max-w-md rounded bg-background p-3 text-sm">Saved model could not load: {editor.loadError}<button className="ml-2 underline" onClick={editor.retryModelLoad}>Retry saved model</button></div>}{(!loaded||editor?.loading)&&<p role="status" className="absolute left-24 top-20 z-40 rounded bg-background p-3 text-sm">Loading the 3D workspace…</p>}{loaded&&!editor?.loading&&editableModel&&editableModel.components.length===0&&<p role="status" className="absolute left-24 top-20 z-40 rounded bg-background p-3 text-sm">This saved model contains no components. Open Create / Import to review inputs.</p>}{loaded&&editableModel&&editableModel.components.length>0&&!editableModel.components.some(c=>c.visible)&&<p role="status" className="absolute left-24 top-20 z-40 rounded bg-background p-3 text-sm">All model components are hidden. Review visibility in Layers; the saved model is not empty.</p>}{loaded&&elasticResults&&(elasticResults.hideModel||analysisFocusKey)&&<div role="status" className="absolute left-24 top-20 z-40 rounded bg-background p-3 text-xs">Saved-result isolation is active. Other geometry is preserved.<button className="ml-2 underline" onClick={()=>{setElasticResults(null);window.dispatchEvent(new Event('geoai:guided-restore-model'));fitProject();}}>Restore full model</button></div>}{loaded && editor && <WorkspaceMouseControls viewer={viewerRef.current} C={cesiumRef.current} editor={editor} modelView={modelView} underground={undergroundView} entities={() => dataSourcesRef.current.get("editable-model")?.entities.values ?? []} bounds={() => sandboxBounds.current} fit={fitProject} onSitePick={point=>sitePickRef.current?.({position:point})} />}{hoveredName && <p className="pointer-events-none absolute bottom-32 right-4 z-20 rounded border border-white/15 bg-background/95 px-3 py-2 text-xs">{hoveredName} · click to select</p>}{editor && <div className="absolute bottom-3 left-3 z-30 max-w-[calc(100%-24px)] rounded-lg border border-white/15 bg-background/95 px-3 py-2 text-xs" aria-label="Viewport presentation">
      <div className="flex flex-wrap items-center gap-2"><button aria-pressed={modelView} className={modelView ? "font-semibold text-primary" : "text-muted-foreground"} onClick={()=>setModelView(true)}>Model view</button><span>/</span><button aria-pressed={!modelView} className={!modelView ? "font-semibold text-primary" : "text-muted-foreground"} onClick={()=>setModelView(false)}>Site view</button><span className="text-[10px] text-muted-foreground">{modelView ? "Illustrative finishes · not material evidence" : "Site context · check elevation evidence"}</span></div>
      <div className="mt-2 flex flex-wrap items-center gap-3"><details className="relative"><summary className="cursor-pointer text-primary">Standard views</summary><div className="absolute bottom-full left-0 mb-2 w-36 rounded border border-border bg-background p-1">{[["Isometric",25,-30],["Top",0,-90],["Front",180,-5],["Side",270,-5]].map(([name,heading,pitch])=><button key={name} className="block w-full rounded p-2 text-left hover:bg-white/10" onClick={event=>{window.dispatchEvent(new CustomEvent("geoai:orient-view",{detail:{heading,pitch}}));event.currentTarget.closest("details")?.removeAttribute("open");}}>{name}</button>)}</div></details><button className="text-primary" title="Camera only: focus structural members; other geometry stays visible" onClick={()=>fitProject("structure")}>Focus Structure</button><button className="text-primary" title="Camera only: fit all currently visible saved geometry" onClick={()=>fitProject("all")}>Fit All</button><button className="text-primary disabled:text-muted-foreground" disabled={!selectedComponentIds.length} onClick={()=>window.dispatchEvent(new Event("geoai:fit-selection"))}>Fit selection</button><button aria-pressed={dimensionsVisible} onClick={()=>setDimensionsVisible(v=>!v)}>Dimensions {dimensionsVisible ? "on":"off"}</button><details className="relative"><summary className="cursor-pointer text-muted-foreground">Display legend</summary><div className="absolute bottom-full right-0 mb-2 w-64 rounded border border-border bg-background p-3 leading-relaxed"><p className="font-semibold">Illustrative geometry finishes</p><p>Blue steel-style members · silver stairs/connections · warm concrete-style slabs/footings.</p><p className="mt-2">Finishes are not material evidence or stress results. Geometry may be conceptual. Review sourced properties in Inspect; computed diagrams retain their analysis evidence and status.</p><p className="mt-2">Focus Structure and Fit All change only the camera. No objects are hidden.</p></div></details></div>
    </div>}{componentPreview && <p role="status" className="absolute left-24 bottom-56 z-30 rounded border border-sky-300/30 bg-background/95 p-2 text-xs">Edit preview · not applied · use Apply or Cancel in Inspect</p>}{editor?.platformPreview && !editor.platformPreview.proposal && <div role="status" className="absolute left-20 top-3 z-30 rounded border border-primary/40 bg-background/95 px-3 py-2 text-xs">{editor.platformPreview.label ?? "Platform preview"} · conceptual / unverified <button className="ml-3 text-primary" onClick={()=>editor.setPlatformPreview(null)}>Cancel preview</button></div>}{acceptedPlacement?.status === "REVIEW_REQUIRED" && acceptedPlacement.elevation === null && previewHeight !== null && <p role="status" className="pointer-events-none absolute bottom-12 right-3 z-20 rounded border border-white/10 bg-background/90 px-2 py-1 text-[10px] text-muted-foreground">Context-ground preview · elevation unvalidated</p>}{cadMeshError && <p role="alert" className="absolute left-16 top-20 z-30 rounded border border-red-400 bg-background p-3 text-xs">{cadMeshError}</p>}{measurementReadout && <MeasurementResult readout={measurementReadout} mode={scene3dMeasureTool} onClear={() => useProjectStore.getState().setScene3dMeasureReadout(null)} />}{transformReadout && <p role="status" style={transformPointer ? {left:Math.min(transformPointer.x,viewerRef.current?.canvas.clientWidth-330),top:Math.min(transformPointer.y,viewerRef.current?.canvas.clientHeight-60)} : {bottom:64,left:64}} className="pointer-events-none absolute z-40 rounded-sm border border-white/10 bg-background/95 px-3 py-2 font-mono text-xs">{transformReadout}</p>}{loaded && !layers.terrain && layers.tiles3d && <div role="status" className="absolute left-16 top-14 z-20 rounded-lg border border-white/15 bg-background/95 px-3 py-2 text-xs"><span>Global buildings paused on flat ground.</span><button className="ml-3 text-primary underline" onClick={() => useProjectStore.getState().setLayers({ terrain: true })}>Restore terrain & buildings</button></div>}{loaded && <SunStudyControls key={placementProjectId ?? "local"} viewer={viewerRef.current} Cesium={cesiumRef.current} longitude={centerLng} latitude={centerLat} projectId={localSandbox ? undefined : placementProjectId} buildingsAvailable={photorealisticTilesOn && buildingStatus === "READY" || scene3dLayers.buildings && buildingFeatures.length > 0} terrainAvailable={layers.terrain && (terrainStatus.includes("VISUAL REFERENCE") || terrainStatus.startsWith("PROJECT TERRAIN"))} />}<div ref={containerRef} style={{ position: "absolute", inset: 0 }} />{!localSandbox && editableModel && <EngineeringEvidencePanel key={`${editableModel.project_id}:${modelRevisionId ?? "unsaved"}`} projectId={editableModel.project_id} revisionId={modelRevisionId} origin={editableModel.origin} onPlacement={setAcceptedPlacement} />}{buildingStatus && photorealisticTilesOn && buildingStatus !== "READY" && <p role="alert" className="absolute left-16 top-24 rounded-xl border border-white/15 bg-background/90 px-3 py-2 text-[10px] text-muted-foreground shadow-lg backdrop-blur-xl">Context buildings unavailable: {buildingStatus === "MISSING_TOKEN" ? "configure world data" : "provider could not load"}</p>}{localSandbox && loaded && layers.terrain && <details className="workspace-terrain-status absolute left-16 top-14 z-20 max-w-[330px] rounded-xl border border-white/15 bg-background/95 text-[10px] shadow-lg"><summary role="status" className="cursor-pointer px-3 py-2 text-muted-foreground">{terrainStatus}</summary><div className="space-y-2 border-t border-white/10 px-3 py-3 text-xs leading-relaxed text-muted-foreground"><p>{terrainDetail}</p><p>Elevation scale: {terrainExaggeration}× · source resolution: not reported</p><button className="text-primary underline" onClick={() => setTerrainRetry((n) => n + 1)}>Reload elevation</button><a href="/settings/api-keys" className="block text-primary underline">World data connection</a></div></details>}{localSandbox && loaded && <p className="pointer-events-none absolute left-3 top-3 rounded-sm border border-white/10 bg-background/90 px-3 py-2 text-[10px] text-muted-foreground">Origin {centerLat.toFixed(6)}, {centerLng.toFixed(6)}{!sandboxHasImagery && " · Loading map imagery…"}</p>}{imageryError && <p role="alert" className="absolute left-3 top-12 rounded-sm border border-amber-400/30 bg-background/95 px-3 py-2 text-xs text-amber-200">{imageryError}</p>}</>;
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
















