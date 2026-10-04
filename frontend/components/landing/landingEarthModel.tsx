"use client";

import { Suspense, useMemo, useRef } from "react";
import { useFrame, useLoader } from "@react-three/fiber";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { LANDING_PALETTE as P, createEarthTexture } from "./landingSceneUtils";

export const EARTH_GLB_URL = "/models/earth_16k.glb";

const TARGET_DIAMETER = 2.2;

function EarthGlobeProcedural() {
  const ref = useRef<THREE.Mesh>(null);
  const texture = useMemo(() => createEarthTexture(1024), []);

  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.08;
  });

  return (
    <mesh ref={ref} castShadow>
      <sphereGeometry args={[TARGET_DIAMETER / 2, 96, 96]} />
      <meshStandardMaterial map={texture} roughness={0.85} metalness={0.03} />
    </mesh>
  );
}

function EarthOrbitRing() {
  return (
    <>
      <mesh>
        <sphereGeometry args={[TARGET_DIAMETER / 2 + 0.04, 48, 48]} />
        <meshBasicMaterial color={P.wire} transparent opacity={0.06} wireframe />
      </mesh>
      <mesh rotation={[1.1, 0.3, 0.5]}>
        <torusGeometry args={[1.45, 0.01, 8, 128]} />
        <meshStandardMaterial color={P.wire} transparent opacity={0.35} metalness={0.4} roughness={0.3} />
      </mesh>
    </>
  );
}

function EarthGlobeGlbInner() {
  const gltf = useLoader(GLTFLoader, EARTH_GLB_URL);
  const rig = useRef<THREE.Group>(null);

  const earth = useMemo(() => {
    const root = gltf.scene.clone(true);
    root.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        for (const mat of mats) {
          if (mat instanceof THREE.MeshStandardMaterial || mat instanceof THREE.MeshPhysicalMaterial) {
            mat.roughness = Math.min(mat.roughness, 0.92);
            mat.metalness = Math.max(mat.metalness, 0.02);
            if (mat.map) mat.map.anisotropy = 16;
          }
        }
      }
    });

    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    root.scale.setScalar(TARGET_DIAMETER / maxDim);
    box.setFromObject(root);
    root.position.sub(box.getCenter(new THREE.Vector3()));
    return root;
  }, [gltf]);

  useFrame((_, delta) => {
    if (rig.current) rig.current.rotation.y += delta * 0.08;
  });

  return (
    <group ref={rig}>
      <primitive object={earth} />
    </group>
  );
}

function EarthGlobeContent() {
  return (
    <>
      <EarthGlobeGlbInner />
      <EarthOrbitRing />
    </>
  );
}

function EarthGlobeFallbackContent() {
  return (
    <>
      <EarthGlobeProcedural />
      <EarthOrbitRing />
    </>
  );
}

export function EarthGlobe() {
  return (
    <group position={[0, 3.4, -2.2]} scale={1.35}>
      <Suspense fallback={<EarthGlobeFallbackContent />}>
        <EarthGlobeContent />
      </Suspense>
    </group>
  );
}

useLoader.preload(GLTFLoader, EARTH_GLB_URL);
