"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { generateHeroSiteLayout, LANDING_PALETTE as P } from "./landingSceneUtils";
import {
  AsphaltRoad,
  CivilBuilding,
  DrapedGrid,
  FuturisticContourOverlay,
  FuturisticDataNodes,
  GroundShadowPlane,
  RealisticTerrain,
  SceneLighting,
  VegetationPatch,
  WaterBody,
} from "./landingSceneShared";
import { SkyClouds } from "./landingCloudModel";
import { SatelliteModel } from "./landingSatelliteModel";

function ScanRing() {
  const ref = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = (clock.elapsedTime * 0.28) % 1;
    const scale = 1.2 + t * 2.2;
    ref.current.scale.set(scale, scale, scale);
    const material = ref.current.material as THREE.MeshBasicMaterial;
    material.opacity = 0.18 * (1 - t);
  });

  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.04, 0]}>
      <ringGeometry args={[0.9, 1, 64]} />
      <meshBasicMaterial color={P.terrainHighlight} transparent opacity={0.2} side={THREE.DoubleSide} />
    </mesh>
  );
}

function SceneContent() {
  const rig = useRef<THREE.Group>(null);

  const site = useMemo(() => generateHeroSiteLayout(), []);

  const trees = useMemo<[number, number][]>(
    () => [
      [-2.1, 0.8],
      [-1.4, 1.6],
      [-0.5, 2.0],
      [0.3, 1.8],
      [-2.5, -0.5],
      [0.8, -1.8],
      [-0.2, -2.2],
      [1.2, 1.4],
      [-1.8, -1.2],
      [2.6, 0.2],
      [-2.8, -0.9],
      [1.8, -1.5],
    ],
    [],
  );

  const dataNodes = useMemo<[number, number][]>(
    () => [
      [-0.8, 0.2],
      [0.6, -0.4],
      [1.4, 0.8],
      [-1.5, 1.0],
      [0.2, 1.2],
      [2.4, -0.6],
      [-2.2, -1.4],
    ],
    [],
  );

  useFrame((_, delta) => {
    if (rig.current) rig.current.rotation.y += delta * 0.055;
  });

  return (
    <>
      <SceneLighting shadow={false} />
      <SkyClouds />
      <fog attach="fog" args={["#1a2830", 20, 38]} />

      <group ref={rig}>
        <RealisticTerrain size={9} segments={112} highQuality={false} />
        <GroundShadowPlane />
        <DrapedGrid />
        <FuturisticContourOverlay />
        <WaterBody cx={-1.6} cz={1.2} rx={0.9} rz={0.65} />
        <AsphaltRoad points={site.mainRoad} width={0.2} marking />
        {site.branchRoads.map((points, i) => (
          <AsphaltRoad key={`branch-${i}`} points={points} width={0.14} />
        ))}
        {site.buildings.map((b) => (
          <CivilBuilding key={`${b.x}-${b.z}-${b.rotation ?? 0}`} spec={b} />
        ))}
        <VegetationPatch positions={trees} />
        <FuturisticDataNodes points={dataNodes} />
        <ScanRing />
      </group>

      <SatelliteModel />
    </>
  );
}

export default function HeroEarthScene() {
  return (
    <Canvas
      camera={{ position: [5.4, 4.6, 5.8], fov: 52, near: 0.1, far: 100 }}
      dpr={[1, 1.35]}
      gl={{
        alpha: true,
        antialias: false,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1.45,
        powerPreference: "high-performance",
      }}
      style={{ background: "transparent", width: "100%", height: "100%" }}
      className="!h-full !w-full"
    >
      <SceneContent />
    </Canvas>
  );
}
