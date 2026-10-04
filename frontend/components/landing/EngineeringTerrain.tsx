"use client";

import { BridgeStructure, RoadStructure, PipelineStructure, DamStructure } from "./StructuralDetails";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Component, useEffect, useMemo, useRef, type ReactNode } from "react";
import * as THREE from "three";
import { terrainHeight as height, alignmentZ as route, bridgeGrade as deck, roadGrade, roadZ, smooth01 } from "./engineeringSite";

export type TerrainState = {
  stage: number;
  progress: number;
  system: number;
  topDown: boolean;
  terrain: boolean;
  structure: boolean;
  alignment: boolean;
  hydrology: boolean;
  paused: boolean;
  reduced: boolean;
  storytelling: boolean;
  structuralView: boolean;
};

function BridgeDetails() {
  return <group>
    {[-8,-4,0,4,8].map(x => <group key={x} position={[x,deck(x),route(x)]} rotation={[0,-Math.atan(.005*x),Math.atan(.02)]}>
      <mesh position={[0,-.105,0]}><boxGeometry args={[3.985,.15,1.05]}/><meshStandardMaterial color="#a9aaa3" roughness={.9}/></mesh>
      {[-.36,0,.36].map(z=><mesh key={z} position={[0,-.23,z]}><boxGeometry args={[3.98,.22,.085]}/><meshStandardMaterial color="#717d80" metalness={.45} roughness={.6}/></mesh>)}
      {[-.51,.51].map(z=><mesh key={z} position={[0,.075,z]}><boxGeometry args={[3.99,.15,.055]}/><meshStandardMaterial color="#cbcdc5" roughness={.8}/></mesh>)}
    </group>)}
    {Array.from({length:67},(_,i)=>-16.5+i*.5).map(x=><group key={x} position={[x,deck(x)+.012,route(x)]} rotation={[0,-Math.atan(.005*x),Math.atan(.02)]}>
      <mesh><boxGeometry args={[.25,.008,.014]}/><meshBasicMaterial color="#e7e5cd"/></mesh>
      {[-.45,.45].map(z=><mesh key={z} position={[0,0,z]}><boxGeometry args={[.5,.008,.012]}/><meshBasicMaterial color="#ecebdc"/></mesh>)}
      {Math.abs(x)>10&&[-.52,.52].map(z=><mesh key={z} position={[0,.07,z]}><boxGeometry args={[.035,.16,.035]}/><meshStandardMaterial color="#bcc2bd"/></mesh>)}
    </group>)}
    {[-10,10].map(x=><group key={x} position={[x,0,route(x)]}>
      <mesh position={[0,(height(x,route(x))+deck(x)-.15)/2,0]}><boxGeometry args={[.4,Math.max(.3,deck(x)-height(x,route(x))-.15),1.3]}/><meshStandardMaterial color="#959a8e"/></mesh>
      {[-.58,.58].map(z=><mesh key={z} position={[x<0?-.45:.45,deck(x)-.3,z]} rotation={[0,x<0?-.18:.18,0]}><boxGeometry args={[1.1,.65,.12]}/><meshStandardMaterial color="#959a8e"/></mesh>)}
      <mesh position={[0,deck(x)+.017,0]}><boxGeometry args={[.025,.014,1]}/><meshBasicMaterial color="#343b38"/></mesh>
    </group>)}
  </group>;
}
function ribbon(points: THREE.Vector3[], width: number) {
  const vertices: number[] = [], indices: number[] = [];
  points.forEach((p, i) => {
    const tangent = points[Math.min(i + 1, points.length - 1)].clone().sub(points[Math.max(0, i - 1)]).normalize();
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).multiplyScalar(width / 2);
    vertices.push(p.x + normal.x, p.y, p.z + normal.z, p.x - normal.x, p.y, p.z - normal.z);
    if (i < points.length - 1) { const a = i * 2; indices.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  return geometry;
}

function Landscape({ state, pointer }: { state: TerrainState; pointer: React.RefObject<{ x: number; y: number }> }) {
  const { invalidate } = useThree();
  const ground = useRef<THREE.Mesh>(null);
  const bridge = useRef<THREE.Group>(null);
  const bridgeDeck = useRef<THREE.Group>(null);
  const bridgePiers = useRef<THREE.Group>(null);
  const bridgeDetail = useRef<THREE.Group>(null);
  const riverMesh = useRef<THREE.Mesh>(null);
  const road = useRef<THREE.Group>(null);
  const pipe = useRef<THREE.Group>(null);
  const dam = useRef<THREE.Group>(null);
  const alignment = useRef<THREE.Mesh>(null);
  const alternatives = useRef<THREE.Group>(null);
  const boundary = useRef<THREE.Group>(null);
  const nodes = useRef<THREE.Group>(null);
  const settleUntil = useRef(0);
  const introStart = useRef<number | null>(null);
  const finalStart = useRef<number | null>(null);
  const lookAt = useRef(new THREE.Vector3(-3, 0, 0));
  const targetCamera = useMemo(() => new THREE.Vector3(), []);
  const targetLook = useMemo(() => new THREE.Vector3(), []);
  const resources = useMemo(() => {
    const geo = new THREE.PlaneGeometry(44, 36, 220, 180);
    geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position;
    const bridgeHeights = new Float32Array(pos.count), roadHeights = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i++) {
      const x=pos.getX(i), z=pos.getZ(i);
      const original=height(x,z);
      const blend=Math.abs(x)>10 && Math.abs(x)<17.5 ? (1-smooth01((Math.abs(z-route(x))-.56)/1.64))*(1-smooth01(Math.abs(x)-16.5)) : 0;
      const roadDistance=Math.abs(z-roadZ(x));
      const earthworkWidth=.55+Math.abs(roadGrade(x)-original)*1.5;
      const roadBlend=(1-smooth01((roadDistance-.48)/Math.max(.15,earthworkWidth-.48)))*(1-smooth01(Math.abs(x)-16.5));
      pos.setY(i,original);
      bridgeHeights[i]=THREE.MathUtils.lerp(original,deck(x)-.08,blend);
      roadHeights[i]=THREE.MathUtils.lerp(original,roadGrade(x)-.035,roadBlend);
    }
    geo.setAttribute("aBridgeY",new THREE.BufferAttribute(bridgeHeights,1));
    geo.setAttribute("aRoadY",new THREE.BufferAttribute(roadHeights,1));
    geo.computeVertexNormals();
    const points = (kind: string, offset = 0) => Array.from({ length: 180 }, (_, i) => {
      const x = -17 + i * 34 / 179, z = kind==="road"?roadZ(x):route(x, offset);
      return new THREE.Vector3(x, kind === "bridge" ? deck(x) : kind==="road"?roadGrade(x):height(x, z) + .16, z);
    });
    const river = ribbon(Array.from({ length: 180 }, (_, i) => { const z = -18 + i * 36 / 179; return new THREE.Vector3(Math.sin(z * .24) * 1.5, .18, z); }), .9);
    const bridgeRoad = ribbon(points("bridge"), .96);
    const groundRoad = ribbon(points("road"), .72);
    const roadShoulder = ribbon(points("road").map(p=>p.clone().add(new THREE.Vector3(0,-.013,0))),.94);
    const roadLine = ribbon(points("road").map(p => p.add(new THREE.Vector3(0,.009,0))), .014);
    const roadEdges=[-.35,.35].map(z=>ribbon(points("road").map(p=>p.add(new THREE.Vector3(0,.009,z))),.01));
    const bridgeEdges=[-.44,.44].map(z=>ribbon(points("bridge").map(p=>p.add(new THREE.Vector3(0,.009,z))),.012));
    const line = ribbon(points("bridge"), .012);
    const railA = ribbon(points("bridge").map(p => p.clone().add(new THREE.Vector3(0, .16, .52))), .028);
    const railB = ribbon(points("bridge").map(p => p.clone().add(new THREE.Vector3(0, .16, -.52))), .028);
    const pipeGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points("pipe")), 180, .045, 8, false);
    const alt = [ribbon(points("pipe", 2.5), .027), ribbon(points("pipe", -2.7), .027)];
    // Trapezoidal gravity-dam section: narrow crest, broad downstream toe.
    const damSection=new THREE.Shape();damSection.moveTo(-.2,0);damSection.lineTo(-.2,2.4);damSection.lineTo(.22,2.4);damSection.lineTo(1.8,0);damSection.closePath();
    const damBody=new THREE.ExtrudeGeometry(damSection,{depth:16,bevelEnabled:false,steps:1});
    damBody.rotateY(Math.PI/2);damBody.translate(-8,0,0);
    const shores=[-1,1].map(direction=>Array.from({length:140},(_,i)=>{const z=.21+i*16/139;let x=Math.sin(z*.24)*1.5;for(let step=0;step<220&&height(x,z)<1.95;step++)x+=direction*.04;return new THREE.Vector3(x,1.96,z);}));
    const waterVertices:number[]=[],waterIndices:number[]=[];
    shores[0].forEach((p,i)=>{waterVertices.push(p.x,1.95,p.z,shores[1][i].x,1.95,p.z);if(i<139){const k=i*2;waterIndices.push(k,k+2,k+1,k+1,k+2,k+3);}});
    const reservoir=new THREE.BufferGeometry();reservoir.setAttribute('position',new THREE.Float32BufferAttribute(waterVertices,3));reservoir.setIndex(waterIndices);reservoir.computeVertexNormals();
    const waterBoundary=shores.map(points=>ribbon(points,.018));
    const edgePoints: THREE.Vector3[] = [];
    const corners = [[-11, -8], [11, -8], [11, 8], [-11, 8], [-11, -8]];
    for (let c = 0; c < 4; c++) for (let n = 0; n < 40; n++) { const x = THREE.MathUtils.lerp(corners[c][0], corners[c+1][0], n/40); const z = THREE.MathUtils.lerp(corners[c][1], corners[c+1][1], n/40); edgePoints.push(new THREE.Vector3(x, height(x, z) + .045, z)); }
    edgePoints.push(edgePoints[0]);
    const edge = ribbon(edgePoints, .035);
    const mat = new THREE.ShaderMaterial({
      uniforms: { uTopo: { value: .08 }, uReveal: { value: 0 },uMap:{value:0},uRoad:{value:0},uBridge:{value:0},uData:{value:0} },
      vertexShader: `attribute float aBridgeY;attribute float aRoadY;uniform float uRoad;uniform float uBridge; varying vec3 vP; varying vec3 vN; varying float vDistance;void main(){vP=position;vP.y=mix(position.y,aBridgeY,uBridge);vP.y=mix(vP.y,aRoadY,uRoad);vN=normal;vec4 eye=modelViewMatrix*vec4(vP,1.);vDistance=length(eye.xyz);gl_Position=projectionMatrix*eye;}`,
      fragmentShader: `varying vec3 vP; varying vec3 vN; varying float vDistance;uniform float uTopo; uniform float uReveal; uniform float uMap;uniform float uData;
        float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
        float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
        void main(){
          float n=noise(vP.xz*2.)*.5+noise(vP.xz*9.)*.25+noise(vP.xz*28.)*.15;
          vec3 base=mix(vec3(.105,.135,.10),vec3(.38,.36,.27),smoothstep(1.4,4.2,vP.y));
          base*=.6+n*.8;
          vec2 parcels=floor(vP.xz*1.1);float fields=hash(parcels);
          vec3 mapColor=mix(vec3(.19,.24,.13),vec3(.34,.30,.18),fields)*(.7+n*.6);
          base=mix(base,mapColor,uMap*.75);
          float light=.4+max(0.,dot(normalize(vN),normalize(vec3(-.4,1.,.45))))*.8;
          base*=light;
          float contour=abs(fract(vP.y*3.)-.5); float width=fwidth(vP.y*3.)*1.25;
          float line=1.-smoothstep(.014,.014+width,contour);
          base=mix(base,vec3(.43,.51,.35),line*uTopo*.65);
          vec2 grid=abs(fract(vP.xz*.5-.5)-.5)/max(fwidth(vP.xz*.5),vec2(.001));
          float g=1.-min(min(grid.x,grid.y),1.);
          base=mix(base,vec3(.33,.41,.30),g*uTopo*.18);
          float fog=smoothstep(13.,25.,length(vP.xz));
          base=mix(base,vec3(.12,.16,.145),smoothstep(22.,48.,vDistance)*.30*(1.-uMap));
          base*=1.-uData*.5;
          gl_FragColor=vec4(mix(vec3(.024,.032,.025),mix(base,vec3(.024,.032,.025),fog),uReveal),1.);
        }`, side: THREE.DoubleSide,
    });
    return { geo, river, bridgeRoad, groundRoad, roadShoulder, roadEdges, bridgeEdges, roadLine, line, railA, railB, pipeGeo, alt, edge, damBody, reservoir, waterBoundary, mat };
  }, []);
  useEffect(() => { settleUntil.current = performance.now() + 2200; invalidate(); }, [state, invalidate]);
  useEffect(() => () => { Object.values(resources).forEach(item => { if (Array.isArray(item)) item.forEach(g => g.dispose()); else item.dispose(); }); }, [resources]);

  useFrame(({ camera, clock }, delta) => {
    if (introStart.current === null) introStart.current = clock.elapsedTime;
    const elapsed = clock.elapsedTime - introStart.current;
    const intro = state.reduced ? 1 : Math.min(1, elapsed / 2);
    const ease = state.reduced ? 1 : 1 - Math.exp(-Math.min(delta, .05) * 4);
    const s = state.stage;
    const poses: Record<number,number[]>={0:[12,11,17,47],1:[0,70,.1,27],2:[14,34,24,34],3:[9,18,17,42],4:[3,9,24,43],5:[12,17,20,47],6:[1,14,28,44],7:[17,19,24,43],12:[16,15,24,47]};
    // Elevated broadside views keep the full corridor visible above foreground
    // terrain. Only the dam uses the downstream (negative-Z) inspection angle.
    const inspectionPoses = [[2,24,24,45],[5,12,27,43],[3,21,26,44],[10,13,-23,44]];
    const explorerPose = state.structuralView ? inspectionPoses[state.system] : [6,23,29,45];
    const current=state.topDown?[0,70,.1,27]:s===5?explorerPose:(poses[s]??poses[7]);
    const previous=state.storytelling?(poses[Math.max(0,s-1)]??current):current;
    const transition=state.storytelling?smooth01(state.progress/.42):1;
    const [x,y,z,fov]=current.map((v,i)=>THREE.MathUtils.lerp(previous[i],v,transition));
    const drift = state.reduced || state.paused ? 0 : Math.sin(clock.elapsedTime * .1) * .16;
    targetCamera.set(x + (state.reduced ? 0 : pointer.current.x * .45) + drift, y, z + (state.reduced ? 0 : pointer.current.y * .3));
    camera.position.lerp(targetCamera, ease);
    if(s===5) {
      // Offset the model into the open right-hand area, away from the selector.
      const downstream=state.structuralView&&state.system===3;
      targetLook.set(downstream?5:-6,state.system===1?2:1,state.system===0?5:0);
    } else targetLook.set(s===7?-1:s===0||s===12?-5:-3,1,0);
    lookAt.current.lerp(targetLook, ease);
    camera.lookAt(lookAt.current);
    const perspective=camera as THREE.PerspectiveCamera;
    perspective.fov=THREE.MathUtils.lerp(perspective.fov,fov,ease);perspective.updateProjectionMatrix();
    if (ground.current) {
      const material = ground.current.material as THREE.ShaderMaterial;
      material.uniforms.uTopo.value = THREE.MathUtils.lerp(material.uniforms.uTopo.value, s===1?0:s===2?transition:s===3?.6:s===6||s===7?.35:.08, ease);
      material.uniforms.uMap.value=THREE.MathUtils.lerp(material.uniforms.uMap.value,s===1?transition:0,ease);
      material.uniforms.uData.value=THREE.MathUtils.lerp(material.uniforms.uData.value,s===6?1:0,ease);
      material.uniforms.uRoad.value=THREE.MathUtils.lerp(material.uniforms.uRoad.value,s===5&&state.system===0?1:0,ease);
      material.uniforms.uBridge.value=THREE.MathUtils.lerp(material.uniforms.uBridge.value,(s>=4&&s!==5)||(s===5&&state.system===1)?1:0,ease);
      material.uniforms.uReveal.value = intro;
      ground.current.visible = state.terrain;
      const relief=s===1?THREE.MathUtils.lerp(1,.14,transition):s===2?THREE.MathUtils.lerp(.14,1,transition):1;
      ground.current.scale.y = THREE.MathUtils.lerp(ground.current.scale.y, relief, ease);
    }
    const assembled = s < 4 ? 0 : s === 4 ? state.progress : 1;
    const type = s === 5 ? state.system : 1;
    [road, bridge, pipe, dam].forEach((ref, i) => {
      if (!ref.current) return;
      const target = (s === 5 || s >= 4 || s === 0) && state.structure && i === type ? assembled : 0;
      ref.current.scale.y = THREE.MathUtils.lerp(ref.current.scale.y, Math.max(.001, i === 1 && target > 0 ? 1 : target), ease);
      ref.current.visible = ref.current.scale.y > .008;
    });
    if (bridgePiers.current) bridgePiers.current.children.forEach((pier, i) => {
      const rise = Math.max(.001, Math.min(1, (assembled-.08) * 3.6 - i * .09));
      pier.scale.y = THREE.MathUtils.lerp(pier.scale.y, rise, ease);
    });
    if (bridgeDeck.current) {
      bridgeDeck.current.visible = assembled > .43;
      const deckReveal=smooth01((assembled-.43)/.38);
      bridgeDeck.current.children.forEach(child=>{if(child instanceof THREE.Mesh) child.geometry.setDrawRange(0,Math.floor(deckReveal*179)*6);});
    }
    if(bridgeDetail.current)bridgeDetail.current.visible=assembled>.82;
    if(s===12&&finalStart.current===null)finalStart.current=clock.elapsedTime;
    if(s!==12)finalStart.current=null;
    const finalElapsed=finalStart.current===null?0:clock.elapsedTime-finalStart.current;
    if (alignment.current) {
      const material = alignment.current.material as THREE.MeshBasicMaterial;
      material.opacity = THREE.MathUtils.lerp(material.opacity, s===0?.3:s===3?smooth01((state.progress-.3)/.4):s>=4?1:0, ease);
      const draw=s===3?smooth01((state.progress-.3)/.55):s===12&&!state.reduced?Math.min(1,finalElapsed/2):s===0&&!state.reduced?Math.min(1,Math.max(0,(elapsed-1)/2)):1;
      alignment.current.geometry.setDrawRange(0,Math.floor(draw*179)*6);
      alignment.current.visible = state.alignment && (s !== 5 || type === 1);
    }
    if (alternatives.current) {
      alternatives.current.visible = s === 3;
      alternatives.current.children.forEach((child,i)=>{const mesh=child as THREE.Mesh;const material=mesh.material as THREE.MeshBasicMaterial;material.opacity=.55*(1-smooth01((state.progress-.4-i*.1)/.4));});
    }
    if (boundary.current) {
      boundary.current.visible = s === 1 || s === 2 || (s===12 && finalElapsed<4);
      boundary.current.scale.y = ground.current?.scale.y ?? 1;
      const edgeMesh=boundary.current.children[0] as THREE.Mesh;
      edgeMesh.geometry.setDrawRange(0,Math.floor((s===1?smooth01((state.progress-.1)/.6):1)*160)*6);
    }
    if (nodes.current) {
      nodes.current.visible = (state.reduced || elapsed > 1) && state.terrain && (s!==12||finalElapsed<5);
      nodes.current.scale.y = ground.current?.scale.y ?? 1;
    }
    if(riverMesh.current)riverMesh.current.visible=state.hydrology;
    if ((!state.paused && !state.reduced) || (!state.reduced&&elapsed<5) || performance.now() < settleUntil.current) invalidate();
  });

  return <>
    <ambientLight intensity={1.2}/><directionalLight position={[-8, 15, 9]} intensity={2.7} color="#efe3bf"/>
    <mesh ref={ground} geometry={resources.geo} material={resources.mat}/>
    <mesh ref={riverMesh} geometry={resources.river}><meshStandardMaterial color="#365e61" roughness={.35} metalness={.5} side={THREE.DoubleSide}/></mesh>
    <group ref={boundary}><mesh geometry={resources.edge}><meshBasicMaterial color="#c8ff32" transparent opacity={.65} side={THREE.DoubleSide}/></mesh></group>
    <group ref={alternatives}>{resources.alt.map((g, i) => <mesh geometry={g} key={i}><meshBasicMaterial color="#c5c5ae" transparent opacity={.35} side={THREE.DoubleSide}/></mesh>)}</group>
    <group ref={road} scale={[1,.001,1]}><RoadStructure/><mesh geometry={resources.roadShoulder}><meshStandardMaterial color="#7b7d66" roughness={1} side={THREE.DoubleSide}/></mesh><mesh geometry={resources.groundRoad}><meshStandardMaterial color="#343b3c" side={THREE.DoubleSide}/></mesh><mesh geometry={resources.roadLine}><meshBasicMaterial color="#c8ff32" side={THREE.DoubleSide}/></mesh>{resources.roadEdges.map((g,i)=><mesh key={i} geometry={g}><meshBasicMaterial color="#d6d9c8" side={THREE.DoubleSide}/></mesh>)}</group>
    <group ref={bridge} scale={[1,.001,1]}>
      <group ref={bridgeDeck}>
      <mesh geometry={resources.bridgeRoad}><meshStandardMaterial color="#343b3c" roughness={.95} side={THREE.DoubleSide}/></mesh>
      <group ref={bridgeDetail}><BridgeDetails/><BridgeStructure/></group>
      {[resources.railA, resources.railB].map((geo,i) => <mesh geometry={geo} key={i}><meshBasicMaterial color="#e0e5c7" side={THREE.DoubleSide}/></mesh>)}
      {resources.bridgeEdges.map((g,i)=><mesh key={i} geometry={g}><meshBasicMaterial color="#d6d9c8" side={THREE.DoubleSide}/></mesh>)}
      </group>
      <group ref={bridgePiers}>
      {[-6,-2,2,6].map(x => { const base = height(x,route(x))-.15; const h = Math.max(.15, deck(x)-.4-base); return <group key={x} position={[x,base,route(x)]}>
        {[-.3,.3].map(z=><mesh key={z} position={[0,h/2,z]}><cylinderGeometry args={[.095,.12,h,16]}/><meshStandardMaterial color="#a9ada4" roughness={.9}/></mesh>)}
        <mesh position={[0,h,0]}><boxGeometry args={[.35,.17,1.05]}/><meshStandardMaterial color="#b7bab0"/></mesh>
        <mesh position={[0,.07,0]}><boxGeometry args={[.65,.2,1.2]}/><meshStandardMaterial color="#7b8174"/></mesh>
        {[-.36,0,.36].map(z=><mesh key={z} position={[0,h+.12,z]}><boxGeometry args={[.18,.06,.14]}/><meshStandardMaterial color="#303c3c"/></mesh>)}
      </group>; })}
      </group>
    </group>
    <group ref={pipe} scale={[1,.001,1]}><PipelineStructure/><mesh geometry={resources.pipeGeo}><meshStandardMaterial color="#a1af9e" roughness={.62} metalness={.35}/></mesh>{[-10,-5,0,5,10].map(x=><group key={x} position={[x,height(x,route(x))+.16,route(x)]}><mesh><cylinderGeometry args={[.085,.085,.12,12]}/><meshStandardMaterial color="#bac5a9"/></mesh><mesh position={[0,.13,0]} rotation={[Math.PI/2,0,0]}><torusGeometry args={[.08,.012,6,12]}/><meshStandardMaterial color="#b4c869"/></mesh></group>)}</group>
    <group ref={dam} scale={[1,.001,1]}><DamStructure/>
      <mesh geometry={resources.damBody}><meshStandardMaterial color="#a6aa9d" roughness={.92}/></mesh>
      <mesh position={[0,2.41,0]}><boxGeometry args={[16,.08,.46]}/><meshStandardMaterial color="#c4c8b7"/></mesh>
      {[-.18,.18].map(z=><mesh key={z} position={[0,2.51,z]}><boxGeometry args={[16,.14,.04]}/><meshStandardMaterial color="#9ea891"/></mesh>)}
      <mesh geometry={resources.reservoir}><meshStandardMaterial color="#3c6566" roughness={.22} metalness={.35} transparent opacity={.88} side={THREE.DoubleSide}/></mesh>
      {resources.waterBoundary.map((g,i)=><mesh key={i} geometry={g}><meshBasicMaterial color="#7daaa1" transparent opacity={.55} side={THREE.DoubleSide}/></mesh>)}
    </group>
    <mesh ref={alignment} geometry={resources.line} position={[0,.05,0]}><meshBasicMaterial color="#c8ff32" transparent opacity={0} side={THREE.DoubleSide}/></mesh>
    <group ref={nodes}>{[[-10,2],[-5,-6],[7,5],[11,-5]].map(([x,z],i)=><group key={i} position={[x,height(x,z)+.08,z]}><mesh rotation={[-Math.PI/2,0,0]}><ringGeometry args={[.15,.18,24]}/><meshBasicMaterial color="#d6dfb9" side={THREE.DoubleSide}/></mesh><mesh><sphereGeometry args={[.04,8,8]}/><meshBasicMaterial color="#c8ff32"/></mesh></group>)}</group>
  </>;
}

class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}
export default function EngineeringTerrain({ state, pointer }: { state: TerrainState; pointer: React.RefObject<{x: number; y: number}> }) {
  const fallback = <div className="geo-scene-fallback"><svg viewBox="0 0 1400 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">{Array.from({length:35},(_,i)=><path key={i} d={`M0 ${350+i*14} Q250 ${60+i*20} 490 ${300+i*12} T900 ${200+i*18} T1500 ${100+i*20}`} fill="none" stroke="#718164" strokeOpacity=".4"/>)}<path d="M0 700 Q450 600 780 470 T1400 500" fill="none" stroke="#c8ff32" strokeWidth="2"/></svg><span>Illustrative terrain · 3D view unavailable</span></div>;
  return <SceneBoundary fallback={fallback}><Canvas frameloop="demand" dpr={[1,1.5]} camera={{ position:[15,12.5,18], fov:47, near:.1, far:100 }} gl={{ antialias:true, alpha:true, powerPreference:"high-performance" }} fallback={fallback}><Landscape state={state} pointer={pointer}/></Canvas></SceneBoundary>;
}
