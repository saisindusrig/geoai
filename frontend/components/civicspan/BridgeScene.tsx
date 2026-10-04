"use client";

import { Canvas } from "@react-three/fiber";
import type { BridgeSpec } from "@/lib/civicspan";

type Props = { spec: BridgeSpec; stage: BridgeSpec["stages"][number] };
function Part({
  children,
  visible,
}: {
  children: React.ReactNode;
  visible: boolean;
}) {
  return visible ? <>{children}</> : null;
}

function Bridge({ spec, stage }: Props) {
  const show = (part: BridgeSpec["stages"][number]) =>
    spec.stages.indexOf(part) <= spec.stages.indexOf(stage);
  const span = 26;
  const pierPositions = Array.from(
    { length: spec.supports },
    (_, index) => -span / 2 + ((index + 1) * span) / (spec.supports + 1),
  );
  const trussPosts = Array.from(
    { length: 7 },
    (_, index) => -span / 2 + (index * span) / 6,
  );
  return (
    <group rotation={[0, -0.5, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[70, 70]} />
        <meshStandardMaterial color="#1d3a35" roughness={0.95} />
      </mesh>
      <Part visible={show("foundation")}>
        {[-span / 2 + 1, span / 2 - 1, ...pierPositions].map((x) => (
          <mesh key={`foundation-${x}`} position={[x, 0.25, 0]} castShadow>
            <boxGeometry args={[2.8, 0.5, spec.width_m + 1.2]} />
            <meshStandardMaterial color="#64748b" />
          </mesh>
        ))}
      </Part>
      <Part visible={show("supports")}>
        {pierPositions.map((x) => (
          <mesh
            key={`pier-${x}`}
            position={[x, spec.deck_elevation_m / 2, 0]}
            castShadow
          >
            <cylinderGeometry args={[0.72, 0.95, spec.deck_elevation_m, 18]} />
            <meshStandardMaterial color="#94a3b8" />
          </mesh>
        ))}
      </Part>
      <Part visible={show("steel")}>
        {spec.structure_type === "steel_truss" ? (
          <>
            {[-spec.width_m / 2 + 0.35, spec.width_m / 2 - 0.35].map((z) => (
              <group key={z}>
                {trussPosts.map((x, index) => (
                  <mesh
                    key={x}
                    position={[x, spec.deck_elevation_m + 2.15, z]}
                    rotation={[0, 0, index % 2 ? -0.62 : 0.62]}
                    castShadow
                  >
                    <boxGeometry args={[4.7, 0.18, 0.22]} />
                    <meshStandardMaterial
                      color="#38bdf8"
                      metalness={0.75}
                      roughness={0.3}
                    />
                  </mesh>
                ))}
                <mesh position={[0, spec.deck_elevation_m + 0.4, z]}>
                  <boxGeometry args={[span, 0.32, 0.28]} />
                  <meshStandardMaterial color="#0f766e" metalness={0.8} />
                </mesh>
                <mesh position={[0, spec.deck_elevation_m + 4, z]}>
                  <boxGeometry args={[span, 0.25, 0.25]} />
                  <meshStandardMaterial color="#0f766e" metalness={0.8} />
                </mesh>
              </group>
            ))}
          </>
        ) : (
          [-spec.width_m / 2 + 0.55, spec.width_m / 2 - 0.55].map((z) => (
            <mesh
              key={z}
              position={[0, spec.deck_elevation_m + 0.35, z]}
              castShadow
            >
              <boxGeometry args={[span, 0.75, 0.55]} />
              <meshStandardMaterial
                color="#0f766e"
                metalness={0.75}
                roughness={0.32}
              />
            </mesh>
          ))
        )}
      </Part>
      <Part visible={show("deck")}>
        <mesh position={[0, spec.deck_elevation_m + 0.75, 0]} castShadow>
          <boxGeometry args={[span + 2, 0.65, spec.width_m]} />
          <meshStandardMaterial color="#d4d4d8" roughness={0.72} />
        </mesh>
        {spec.railings &&
          [-spec.width_m / 2 + 0.08, spec.width_m / 2 - 0.08].map((z) => (
            <group key={z}>
              <mesh position={[0, spec.deck_elevation_m + 1.65, z]}>
                <boxGeometry args={[span + 2, 0.09, 0.08]} />
                <meshStandardMaterial color="#e2e8f0" metalness={0.65} />
              </mesh>
              {Array.from({ length: 12 }, (_, i) => (
                <mesh
                  key={i}
                  position={[
                    -span / 2 - 0.5 + i * 2.45,
                    spec.deck_elevation_m + 1.25,
                    z,
                  ]}
                >
                  <boxGeometry args={[0.08, 1.1, 0.08]} />
                  <meshStandardMaterial color="#e2e8f0" metalness={0.65} />
                </mesh>
              ))}
            </group>
          ))}
      </Part>
      <Part visible={stage === "finished"}>
        <mesh position={[0, spec.deck_elevation_m + 1.09, 0]}>
          <boxGeometry args={[span + 1.7, 0.06, spec.width_m - 0.25]} />
          <meshStandardMaterial color="#475569" roughness={0.9} />
        </mesh>
      </Part>
    </group>
  );
}

export default function BridgeScene({ spec, stage }: Props) {
  return (
    <Canvas shadows camera={{ position: [30, 22, 32], fov: 42 }} dpr={[1, 1.5]}>
      <color attach="background" args={["#0e100f"]} />
      <fog attach="fog" args={["#0e100f", 24, 72]} />
      <ambientLight intensity={1.25} />
      <directionalLight position={[16, 24, 12]} intensity={2.2} castShadow />
      <Bridge spec={spec} stage={stage} />
    </Canvas>
  );
}
