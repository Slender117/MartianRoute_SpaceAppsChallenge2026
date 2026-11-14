"use client";

import { useTexture } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { BufferAttribute, PlaneGeometry, SRGBColorSpace, type Texture } from "three";

import { assetUrl } from "@/lib/api";
import { regionFrame, TERRAIN_SIZE } from "@/lib/geo";
import { useMapStore } from "@/lib/store";
import type { RegionManifest } from "@/lib/types";

import { useRegionExtras, useRegionHeights } from "./regionAssets";

// Color de la ortofoto en escala de grises: la tiñe del tono del suelo marciano (solo visual).
const SOIL_TINT = "#e3a27a";
const SOIL_COLOR = "#c1643c";

/**
 * Terreno de la región con sus capas fusionadas encima, como en las vistas de unidades geológicas:
 * malla con el relieve real (heightmap.bin), ortofoto como textura y cada capa activa como un
 * velo semitransparente sobre la misma geometría. Las regiones viejas sin heightmap.bin usan el
 * heightmap.png como displacementMap.
 */
export function RegionTerrain({ exaggeration }: { exaggeration: number }) {
  const manifest = useMapStore((s) => s.manifest)!;
  const extras = useRegionExtras(manifest.id);
  const heights = useRegionHeights(manifest, extras);

  if (!extras) return null;
  if (!extras.assets?.heightmap) return <DisplacedTerrain manifest={manifest} exaggeration={exaggeration} />;
  if (!heights) return null;
  return (
    <MeshTerrain
      manifest={manifest}
      heights={heights}
      exaggeration={exaggeration}
      orthoPath={extras.assets.ortho?.path}
    />
  );
}

function useLayerTextures(manifest: RegionManifest, orthoPath?: string): Record<string, Texture> {
  const urls = useMemo(() => {
    const entries = manifest.layers.concat("slope").map((l) => [l, assetUrl(manifest.id, `textures/${l}.png`)]);
    if (orthoPath) entries.push(["__ortho", assetUrl(manifest.id, orthoPath)]);
    return Object.fromEntries(entries) as Record<string, string>;
  }, [manifest, orthoPath]);
  const textures = useTexture(urls) as Record<string, Texture>;
  // Los colores de las capas están en sRGB: sin esto se ven lavados y no coinciden con la leyenda.
  useMemo(() => {
    for (const t of Object.values(textures)) {
      t.colorSpace = SRGBColorSpace;
      t.anisotropy = 8;
      t.needsUpdate = true;
    }
  }, [textures]);
  return textures;
}

function MeshTerrain({
  manifest,
  heights,
  exaggeration,
  orthoPath,
}: {
  manifest: RegionManifest;
  heights: Float32Array;
  exaggeration: number;
  orthoPath?: string;
}) {
  const activeLayers = useMapStore((s) => s.activeLayers);
  const pickPoint = useMapStore((s) => s.pickPoint);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const textures = useLayerTextures(manifest, orthoPath);

  // Un vértice por celda de la grilla; la misma geometría la comparten el suelo y los velos.
  const geometry = useMemo(() => {
    const [h, w] = manifest.shape;
    const [zMin, zMax] = manifest.elevation_range;
    const g = new PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, w - 1, h - 1);
    const pos = g.attributes.position as BufferAttribute;
    const k = frame.heightScale / Math.max(zMax - zMin, 1e-6);
    for (let i = 0; i < heights.length; i++) pos.setZ(i, (heights[i] - zMin) * k);
    pos.needsUpdate = true;
    g.computeVertexNormals();
    g.computeBoundingBox();
    g.computeBoundingSphere();
    return g;
  }, [manifest, heights, frame]);
  useEffect(() => () => geometry.dispose(), [geometry]);

  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    pickPoint(frame.fromScene(e.point));
  };

  const ortho = textures.__ortho;
  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <mesh geometry={geometry} onClick={onClick}>
        <meshStandardMaterial map={ortho ?? null} color={ortho ? SOIL_TINT : SOIL_COLOR} roughness={1} metalness={0} />
      </mesh>

      {activeLayers.map((layer, i) => (
        <mesh key={layer} geometry={geometry} renderOrder={i + 1}>
          <meshLambertMaterial
            map={textures[layer]}
            transparent
            depthWrite={false}
            polygonOffset
            polygonOffsetFactor={-1 - i}
          />
        </mesh>
      ))}
    </group>
  );
}

const LEGACY_SEGMENTS = 192;

/** Regiones publicadas antes del heightmap.bin: el PNG de 16 bits desplaza un plano. */
function DisplacedTerrain({ manifest, exaggeration }: { manifest: RegionManifest; exaggeration: number }) {
  const activeLayers = useMapStore((s) => s.activeLayers);
  const pickPoint = useMapStore((s) => s.pickPoint);
  const frame = useMemo(() => regionFrame(manifest, exaggeration), [manifest, exaggeration]);
  const heightmap = useTexture(assetUrl(manifest.id, "heightmap.png"));
  const textures = useLayerTextures(manifest);

  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    pickPoint(frame.fromScene(e.point));
  };

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <mesh onClick={onClick}>
        <planeGeometry args={[TERRAIN_SIZE, TERRAIN_SIZE, LEGACY_SEGMENTS, LEGACY_SEGMENTS]} />
        <meshStandardMaterial
          color={SOIL_COLOR}
          roughness={1}
          flatShading
          displacementMap={heightmap}
          displacementScale={frame.heightScale}
        />
      </mesh>

      {activeLayers.map((layer, i) => (
        <mesh key={layer} renderOrder={i + 1}>
          <planeGeometry args={[TERRAIN_SIZE, TERRAIN_SIZE, LEGACY_SEGMENTS, LEGACY_SEGMENTS]} />
          {/* Lambert y no Basic: MeshBasicMaterial no soporta displacementMap */}
          <meshLambertMaterial
            map={textures[layer]}
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
