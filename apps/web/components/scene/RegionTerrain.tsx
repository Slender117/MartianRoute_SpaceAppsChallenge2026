"use client";

import { useTexture } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import { useMemo } from "react";

import { assetUrl } from "@/lib/api";
import { regionFrame, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";

const SEGMENTS = 192; // baja resolución a propósito: estética low poly

/** Terreno de la región desplazado con el heightmap, con las capas activas encima. */
export function RegionTerrain({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const activeLayers = useMapStore((s) => s.activeLayers);
  const pickPoint = useMapStore((s) => s.pickPoint);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);

  const heightmap = useTexture(assetUrl(manifest.id, "heightmap.png"));
  const layerTextures = useTexture(
    Object.fromEntries(manifest.layers.concat("slope").map((l) => [l, assetUrl(manifest.id, `textures/${l}.png`)])),
  );

  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    pickPoint(frame.fromScene(e.point));
  };

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <mesh onClick={onClick}>
        <planeGeometry args={[TERRAIN_SIZE, TERRAIN_SIZE, SEGMENTS, SEGMENTS]} />
        <meshStandardMaterial
          color="#c1643c"
          roughness={1}
          flatShading
          displacementMap={heightmap}
          displacementScale={frame.heightScale}
        />
      </mesh>

      {activeLayers.map((layer, i) => (
        <mesh key={layer} renderOrder={i + 1}>
          <planeGeometry args={[TERRAIN_SIZE, TERRAIN_SIZE, SEGMENTS, SEGMENTS]} />
          {/* Lambert y no Basic: MeshBasicMaterial no soporta displacementMap */}
          <meshLambertMaterial
            map={layerTextures[layer]}
            transparent
            depthWrite={false}
            polygonOffset
            polygonOffsetFactor={-1 - i}
            displacementMap={heightmap}
            displacementScale={frame.heightScale}
          />
        </mesh>
      ))}
    </group>
  );
}
