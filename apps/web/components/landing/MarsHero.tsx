"use client";

import { Stars } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import { CanvasTexture, SRGBColorSpace, type Mesh } from "three";

// Pseudoaleatorio con semilla: el planeta se ve igual en cada visita.
function rng(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Textura procedural (manchas, cráteres y casquetes). Es decorativa, no es un mapa real de Marte. */
function marsTexture(): CanvasTexture {
  const w = 1024;
  const h = 512;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const rand = rng(7);

  ctx.fillStyle = "#b4532f";
  ctx.fillRect(0, 0, w, h);

  // Regiones claras y oscuras grandes, luego detalle fino.
  const blobs: [number, number, number, string][] = [
    [40, 60, 160, "rgba(90, 38, 22, 0.18)"],
    [60, 30, 120, "rgba(214, 120, 74, 0.16)"],
    [1600, 6, 30, "rgba(70, 30, 18, 0.10)"],
    [1600, 4, 22, "rgba(230, 150, 100, 0.08)"],
  ];
  for (const [count, minR, maxR, color] of blobs) {
    ctx.fillStyle = color;
    for (let i = 0; i < count; i++) {
      const x = rand() * w;
      const y = h * 0.12 + rand() * h * 0.76;
      const r = minR + rand() * (maxR - minR);
      ctx.beginPath();
      ctx.ellipse(x, y, r * (1 + rand()), r, rand() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Cráteres: borde claro y fondo oscuro.
  for (let i = 0; i < 420; i++) {
    const x = rand() * w;
    const y = h * 0.1 + rand() * h * 0.8;
    const r = 1 + rand() ** 4 * 7;
    ctx.fillStyle = "rgba(60, 24, 14, 0.22)";
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "rgba(240, 170, 120, 0.14)";
    ctx.lineWidth = Math.max(1, r * 0.25);
    ctx.stroke();
  }

  // Casquetes polares.
  for (const [y0, y1] of [
    [0, h * 0.07],
    [h, h * 0.94],
  ]) {
    const g = ctx.createLinearGradient(0, y0, 0, y1);
    g.addColorStop(0, "rgba(250, 240, 232, 0.95)");
    g.addColorStop(1, "rgba(250, 240, 232, 0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, Math.min(y0, y1), w, Math.abs(y1 - y0));
  }

  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  return tex;
}

function Planet({ spin }: { spin: boolean }) {
  const planet = useRef<Mesh>(null);
  const map = useMemo(marsTexture, []);
  // En pantallas anchas el planeta va a la derecha para no tapar el título.
  const wide = useThree((s) => s.viewport.aspect > 1.2);

  useFrame((_, dt) => {
    if (spin && planet.current) planet.current.rotation.y += dt * 0.12;
  });

  return (
    <group
      position={[wide ? 0.75 : 0, wide ? 0 : 0.55, 0]}
      scale={wide ? 1 : 0.6}
      rotation={[0.1, 0, 0.44]}
    >
      <mesh ref={planet}>
        <sphereGeometry args={[1, 96, 96]} />
        <meshStandardMaterial map={map} bumpMap={map} bumpScale={0.6} roughness={0.95} />
      </mesh>
    </group>
  );
}

/** Marte girando para la portada. Respeta "reducir movimiento" del sistema. */
export default function MarsHero() {
  const spin = useMemo(
    () => typeof window === "undefined" || !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  return (
    <Canvas camera={{ position: [0, 0, 3.1], fov: 45 }} dpr={[1, 2]} aria-hidden>
      <ambientLight intensity={0.12} />
      <directionalLight position={[5, 2, 4]} intensity={2.6} />
      <Stars radius={60} depth={30} count={2500} factor={3} fade speed={spin ? 0.5 : 0} />
      <Planet spin={spin} />
    </Canvas>
  );
}
