"use client";

import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Group } from "three";

import { bboxCenter, latLonToSphere } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

/**
 * Globo de Marte con los sitios disponibles (los nombres están en SitePanel).
 * TODO(3D): textura de color + mapa de relieve MOLA (Mars Trek) en lugar del color plano.
 */
export function Globe() {
  const regions = useMapStore((s) => s.regions);
  const view = useMapStore((s) => s.view);
  const selectRegion = useMapStore((s) => s.selectRegion);
  const group = useRef<Group>(null);

  useFrame((_, dt) => {
    if (group.current && view === "globe") group.current.rotation.y += dt * 0.05;
  });

  return (
    <group ref={group}>
      <mesh>
        <sphereGeometry args={[1, 128, 128]} />
        <meshStandardMaterial color="#b4532f" roughness={0.95} />
      </mesh>

      {regions.map((r) => (
        <mesh
          key={r.id}
          position={latLonToSphere(bboxCenter(r.bbox), 1.01)}
          onClick={() => selectRegion(r.id)}
        >
          <sphereGeometry args={[0.02, 16, 16]} />
          <meshBasicMaterial color="#ffd27a" toneMapped={false} />
        </mesh>
      ))}
    </group>
  );
}
