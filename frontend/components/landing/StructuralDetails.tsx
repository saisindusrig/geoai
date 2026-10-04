"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { alignmentZ, bridgeGrade, roadGrade, roadZ, terrainHeight } from "./engineeringSite";

type Point = [number, number, number];
type Member = { center: Point; size: Point; rotation?: Point };
function beam(a: Point, b: Point, width: number, depth = width): Member {
  const start = new THREE.Vector3(...a), end = new THREE.Vector3(...b);
  const direction = end.clone().sub(start);
  const rotation = new THREE.Euler().setFromQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0), direction.clone().normalize()));
  return { center: start.add(end).multiplyScalar(.5).toArray() as Point, size:[width,direction.length(),depth], rotation:[rotation.x,rotation.y,rotation.z] };
}
/** Repeated structural members share geometry/material and one draw call. */
function Members({items,color,metalness=0}:{items:Member[];color:string;metalness?:number}) {
  const ref=useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(()=>{const transform=new THREE.Object3D();items.forEach((item,i)=>{transform.position.set(...item.center);transform.scale.set(...item.size);transform.rotation.set(...(item.rotation??[0,0,0]));transform.updateMatrix();ref.current?.setMatrixAt(i,transform.matrix);});if(ref.current){ref.current.instanceMatrix.needsUpdate=true;ref.current.computeBoundingSphere();}},[items]);
  return <instancedMesh ref={ref} args={[undefined,undefined,items.length]}><boxGeometry/><meshStandardMaterial color={color} metalness={metalness} roughness={metalness?.55:.9}/></instancedMesh>;
}

export function BridgeStructure() {
  const steel=useMemo(()=>{
    const items:Member[]=[];
    for(const span of [-8,-4,0,4,8]) {
      // Flanges articulate the existing longitudinal girder webs.
      for(const z of [-.36,0,.36]) for(const y of [-.14,-.34]) items.push({center:[span,bridgeGrade(span)+y,alignmentZ(span)+z],size:[3.97,.035,.15],rotation:[0,-Math.atan(.005*span),Math.atan(.02)]});
      for(const dx of [-1.7,-.85,0,.85,1.7]) {
        const x=span+dx,y=bridgeGrade(x),z=alignmentZ(x);
        items.push(beam([x,y-.15,z-.4],[x,y-.34,z+.4],.025),beam([x,y-.34,z-.4],[x,y-.15,z+.4],.025));
      }
    }
    for(let x=-9.75;x<10;x+=.5) for(const side of [-1,1]) {
      const z=alignmentZ(x)+side*.535,y=bridgeGrade(x);
      items.push({center:[x,y+.19,z],size:[.023,.25,.023]});
      items.push(beam([x,y+.30,z],[x+.5,bridgeGrade(x+.5)+.30,alignmentZ(x+.5)+side*.535],.025));
    }
    // Transverse floor beams and vertical web stiffeners give the girder system reading.
    for(let x=-9.5;x<=9.5;x+=1) {
      const y=bridgeGrade(x),z=alignmentZ(x);
      items.push(beam([x,y-.34,z-.42],[x,y-.34,z+.42],.03));
      for(const gz of [-.36,0,.36]) items.push({center:[x,y-.25,gz],size:[.02,.11,.15],rotation:[0,-Math.atan(.005*x),Math.atan(.02)]});
    }
    // Bearing pads over each pier.
    for(const px of [-6,-2,2,6]) items.push({center:[px,bridgeGrade(px)-.37,alignmentZ(px)],size:[.36,.05,.95]});
    return items;
  },[]);
  const concrete=useMemo(()=>[-6,-2,2,6].flatMap(x=>{
    const z=alignmentZ(x),y=terrainHeight(x,z);
    return [{center:[x,y+.08,z] as Point,size:[.86,.16,1.42] as Point},...[-.3,.3].map(side=>({center:[x,y+.25,z+side] as Point,size:[.3,.28,.3] as Point}))];
  }),[]);
  const lights=useMemo(()=>{
    const items:Member[]=[];
    for(let x=-8;x<=8;x+=4) {
      const z=alignmentZ(x)+.55,y=bridgeGrade(x);
      items.push({center:[x,y+.62,z],size:[.03,1.25,.03]});
      items.push(beam([x,y+1.2,z],[x,y+1.2,z-.3],.022));
      items.push({center:[x,y+1.2,z-.33],size:[.14,.045,.07]});
    }
    return items;
  },[]);
  return <group><Members items={steel} color="#8e9da0" metalness={.6}/><Members items={concrete} color="#808b81"/><Members items={lights} color="#c7cfbd" metalness={.4}/></group>;
}

export function RoadStructure() {
  const details=useMemo(()=>{
    const rails:Member[]=[],drains:Member[]=[],markers:Member[]=[];
    for(let x=-16;x<16;x+=.65) for(const side of [-1,1]) {
      const z=roadZ(x)+side*.48,y=roadGrade(x),fill=y-terrainHeight(x,z);
      if(fill>.25){rails.push({center:[x,y+.07,z],size:[.025,.2,.025]});rails.push(beam([x,y+.15,z],[x+.65,roadGrade(x+.65)+.15,roadZ(x+.65)+side*.48],.045,.025));}
      else {drains.push({center:[x,y-.018,z],size:[.6,.03,.06],rotation:[0,-Math.atan(.005*x),0]});}
      if(Math.round((x+16)/.65)%4===0)markers.push({center:[x,y+.08,z+side*.10],size:[.025,.16,.025]});
    }
    return {rails,drains,markers};
  },[]);
  const lights=useMemo(()=>{
    const items:Member[]=[];
    for(let x=-15;x<=15;x+=5) {
      const z=roadZ(x)+.55,y=roadGrade(x);
      items.push({center:[x,y+.6,z],size:[.03,1.2,.03]});
      items.push(beam([x,y+1.15,z],[x,y+1.15,z-.32],.02));
      items.push({center:[x,y+1.15,z-.35],size:[.13,.04,.07]});
    }
    return items;
  },[]);
  return <group><Members items={details.rails} color="#a5ada9" metalness={.65}/><Members items={details.drains} color="#6c7977"/><Members items={details.markers} color="#e0ddc4"/><Members items={lights} color="#c7cfbd" metalness={.4}/></group>;
}

export function PipelineStructure() {
  const supports=useMemo(()=>{
    const items:Member[]=[];
    for(let x=-16;x<=16;x+=1){const z=alignmentZ(x),y=terrainHeight(x,z);items.push({center:[x,y+.025,z],size:[.20,.10,.28]},{center:[x,y+.09,z],size:[.09,.07,.15]});}
    // Intermediate cradles double the support rhythm between main supports.
    for(let x=-15.5;x<16;x+=1){const z=alignmentZ(x),y=terrainHeight(x,z);items.push({center:[x,y+.02,z],size:[.14,.06,.2]});}
    for(const x of [-10,-5,0,5,10]){const z=alignmentZ(x),y=terrainHeight(x,z);items.push({center:[x,y+.02,z],size:[.62,.08,.55]},{center:[x,y+.23,z+.22],size:[.12,.35,.10]});}
    // Anchor blocks terminate the line at each end.
    items.push({center:[-16.3,terrainHeight(-16.3,alignmentZ(-16.3))+.08,alignmentZ(-16.3)],size:[.5,.32,.7]},{center:[16.3,terrainHeight(16.3,alignmentZ(16.3))+.08,alignmentZ(16.3)],size:[.5,.32,.7]});
    return items;
  },[]);
  return <group><Members items={supports} color="#828d83"/>{Array.from({length:33},(_,i)=>i-16).map(x=>{
    const z=alignmentZ(x),y=terrainHeight(x,z)+.16;
    const tangent=new THREE.Vector3(.02,terrainHeight(x+.01,alignmentZ(x+.01))-terrainHeight(x-.01,alignmentZ(x-.01)),alignmentZ(x+.01)-alignmentZ(x-.01)).normalize();
    const quaternion=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),tangent);
    return <group key={x} position={[x,y,z]} quaternion={quaternion}><mesh><torusGeometry args={[.052,.012,6,12]}/><meshStandardMaterial color="#6d8184" metalness={.65} roughness={.5}/></mesh></group>;
  })}</group>;
}

export function DamStructure() {
  const details=useMemo(()=>{
    const concrete:Member[]=[],metal:Member[]=[],chutes:Member[]=[];
    // Chutes lie on the downstream batter, rather than protruding above it.
    for(const x of [-1.2,-.4,.4,1.2]){
      chutes.push(beam([x,2.36,-.24],[x,.14,-1.8],.64,.045));
      for(const side of [-.35,.35])concrete.push(beam([x+side,2.38,-.25],[x+side,.16,-1.85],.07,.13));
      concrete.push({center:[x,.1,-2.1],size:[.8,.16,.65]});
      metal.push({center:[x,2.65,-.12],size:[.04,.5,.04]},{center:[x,2.88,-.12],size:[.72,.06,.08]});
    }
    for(let x=-7.5;x<=7.5;x+=.5) for(const z of [-.19,.19])metal.push({center:[x,2.55,z],size:[.02,.23,.02]});
    for(const x of [-6,-4,-2,2,4,6]){concrete.push(beam([x,2.32,-.3],[x,.13,-1.9],.10,.16));}
    concrete.push({center:[-3,2.65,0],size:[.7,.42,.38]});
    // Crest handrail and gate frames read the control deck.
    for(let x=-7;x<=7;x+=.7)metal.push({center:[x,2.68,0],size:[.03,.28,.03]});
    metal.push(beam([-7.2,2.98,0],[7.2,2.98,0],.03));
    for(const x of [-3,0,3]){metal.push({center:[x,3.15,0],size:[.07,1.15,.07]});metal.push(beam([x,3.7,0],[x,3.7,-.9],.045));}
    return {concrete,metal,chutes};
  },[]);
  return <group><Members items={details.concrete} color="#bbc0b2"/><Members items={details.metal} color="#687c7d" metalness={.7}/><Members items={details.chutes} color="#718c90" metalness={.35}/></group>;
}
