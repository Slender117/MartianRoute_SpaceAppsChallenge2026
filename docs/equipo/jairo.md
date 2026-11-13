# Jairo · Visualización 3D

**Objetivo:** OE4 · HE4: el visor.
**Hitos:** participa en H2 y H3. **Respaldo:** Tulio, que también lo apoya en 3D desde H3.

## Alcance

Que el terreno real de Jezero se vea bien y que las tres rutas, la línea base, el recorrido de
Perseverance y la zona de regreso seguro se lean de un vistazo sobre él. El terreno local es
prioridad; el globo está congelado.

## Carpetas

- `apps/web/components/scene/` (`Scene`, `RegionTerrain`, `RoutePath`, `TraverseOverlay`)
- `apps/web/components/debug/` (Leva, solo con `?debug`)
- `Globe.tsx` y `CameraRig.tsx`: solo mantenimiento

## Tareas

- [ ] Terreno desde el heightmap Float32, con malla de ~512 × 512 (H2)
- [ ] Ortofoto como textura y normal map en object space (H3)
- [ ] Las tres rutas, la línea base y el recorrido real de Perseverance visibles a la vez (H3)
- [ ] Capa del mapa de regreso seguro (H3)
- [ ] Movimiento de cámara del guion y prueba de rendimiento en la laptop de la demo (H4)
- [ ] No invertirle al globo: solo verificar que siga funcionando

## Por día

| 13 nov | 14 nov | 15 nov |
| --- | --- | --- |
| Terreno real en la escena | Rutas, capas, regreso seguro y cámara; rendimiento | Ajustes visuales |

## Recibe y entrega

- **Recibe** de Tulio: heightmap Float32, ortofoto y normal map. De Miguel: geometría de rutas, línea
  base y grilla de regreso seguro.
- **Entrega** a Tulio: la exageración vertical fija (la necesita para el normal map). A Williams:
  capturas para el deck.

## Notas técnicas

- Normal map con `THREE.ObjectSpaceNormalMap` y `colorSpace = THREE.NoColorSpace`, misma exageración
  que la malla. Si `MeshLambertMaterial` no lo aplica, usar `MeshStandardMaterial`.
- El normal map es solo visual: el ruteo usa la grilla de pendientes.
- `<Html>` de drei falla con React 19: las etiquetas van en paneles HTML fuera del `<Canvas>`.

## Fuera de alcance

- Globo: textura elaborada, más sitios, Theatre.js, bloom, postprocessing. Tampoco borrarlo
  (`CameraRig`, `SitePanel` y el store dependen de él).
- Mezclar sombreado plano low poly con normal map.
