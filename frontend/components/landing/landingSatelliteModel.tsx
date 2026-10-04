"use client";

import { Suspense, useMemo, useRef } from "react";
import { useFrame, useLoader } from "@react-three/fiber";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export const SATELLITE_GLB_URL = "/models/simple_satellite_low_poly_free.glb";

const TARGET_SIZE = 0.55;

function SatelliteGlbInner() {
  const gltf = useLoader(GLTFLoader, SATELLITE_GLB_URL);
  const rig = useRef<THREE.Group>(null);

  const model = useMemo(() => {
    const root = gltf.scene.clone(true);
    root.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        for (const mat of mats) {
          if (mat instanceof THREE.MeshStandardMaterial || mat instanceof THREE.MeshPhysicalMaterial) {
            mat.roughness = Math.min(mat.roughness, 0.65);
            mat.metalness = Math.max(mat.metalness, 0.25);
            if (mat.map) mat.map.anisotropy = 8;
          }
        }
      }
    });

    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    root.scale.setScalar(TARGET_SIZE / maxDim);
    box.setFromObject(root);
    root.position.sub(box.getCenter(new THREE.Vector3()));
    return root;
  }, [gltf]);

  useFrame(({ clock }) => {
    if (!rig.current) return;
    const t = clock.elapsedTime * 0.28;
    rig.current.position.set(Math.cos(t) * 4.4, 2.6 + Math.sin(t * 1.1) * 0.22, Math.sin(t) * 4.4);
    rig.current.rotation.y = t * 1.2;
    rig.current.rotation.x = Math.sin(t * 0.7) * 0.12;
  });

  return (
    <group ref={rig}>
      <primitive object={model} />
    </group>
  );
}

function SatelliteFallback() {
  const ref = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.elapsedTime * 0.28;
    ref.current.position.set(Math.cos(t) * 4.4, 2.6 + Math.sin(t * 1.1) * 0.22, Math.sin(t) * 4.4);
    ref.current.rotation.y = t * 1.2;
  });

  return (
    <group ref={ref}>
      <mesh castShadow>
        <boxGeometry args={[0.22, 0.14, 0.14]} />
        <meshStandardMaterial color="#c0c5cc" roughness={0.35} metalness={0.5} />
      </mesh>
      <mesh position={[0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <boxGeometry args={[0.5, 0.02, 0.18]} />
        <meshStandardMaterial color="#1a3d5c" roughness={0.2} metalness={0.65} />
      </mesh>
      <mesh position={[-0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <boxGeometry args={[0.5, 0.02, 0.18]} />
        <meshStandardMaterial color="#1a3d5c" roughness={0.2} metalness={0.65} />
      </mesh>
    </group>
  );
}

export function SatelliteModel() {
  return (
    <Suspense fallback={<SatelliteFallback />}>
      <SatelliteGlbInner />
    </Suspense>
  );
}

useLoader.preload(GLTFLoader, SATELLITE_GLB_URL);
