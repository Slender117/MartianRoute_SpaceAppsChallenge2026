# Miguel · Backend FastAPI y dirección del frontend

**Objetivo:** OE2 · HE2 y OE4 · HE4.
**Hitos:** responsable de H3. **Respaldo:** Edgar.

## Alcance

Implementar en la API el costo en kg de O₂ con seguridad como restricción, los tres modos y la línea
base sobre Jezero real, el punto de no retorno y el regreso seguro. Dirigir el frontend y la
experiencia de uso: Milton construye componentes con su guía y Miguel revisa cada PR y queda a cargo
de la interfaz final integrada.

## Carpetas

- `apps/api/` (`engine/`, `routers/`, `schemas/`, `storage/`, `tests/`)
- `packages/contracts/`
- `apps/web/lib/` y revisión de `apps/web/components/ui/`

## Tareas

- [ ] Fijar con Milton el contrato de la API en `schemas/` el primer día (regla 1)
- [ ] Integrar con Edgar su modelo de O₂ (`slope_penalty`): acordar la interfaz, decidir el cambio de
      forma de la penalización y actualizar la fórmula en `CLAUDE.md` y `docs/arquitectura.md` (H3)
- [ ] Campos nuevos en `RouteResponse` (`o2_interval_kg`, línea base, procedencia) y regenerar
      `packages/contracts` (H3)
- [ ] Línea base de mínima distancia, que necesitan HE2 y HE3 (H3)
- [ ] Punto de no retorno con el método de Apollo y reserva de 30 min (H3)
- [ ] Endpoint del mapa de regreso seguro (`find_costs` desde la base) y dosis por EVA (H3)
- [ ] Prueba automática: los tres modos difieren sobre Jezero real (HE2) (H3)
- [ ] Revisar e integrar los componentes de Milton; la interfaz final queda a cargo de Miguel (H3)
- [ ] Elegir con Edgar los puntos de demo donde la ruta corta gaste más O₂ (H4)

## Por día

| 13 nov | 14 nov | 15 nov |
| --- | --- | --- |
| Campos nuevos del contrato; integración del modelo de O₂ con Edgar | Motor sobre Jezero real e interfaz final integrada | Guardia técnica durante la presentación |

## Recibe y entrega

- **Recibe** de Tulio: grillas y manifest de Jezero. De Edgar: modelo de O₂ y parámetros con fuente.
  De Milton: componentes por PR.
- **Entrega** a Milton y a Tulio (escena 3D): contrato de la API y respuestas con procedencia. Al pitch: los
  números del caso de demo.

## Plan B a su cargo

- Si `MCP_Flexible` no avanza tras un día: costo simétrico en O₂ para el ruteo y velocidades
  asimétricas solo para el tiempo.
- Si los tres modos dan la misma ruta: cambiar los puntos de demo antes de tocar los pesos (con Edgar).

## Fuera de alcance

- Procesamiento geoespacial en la API: va al pipeline.
- Migrar a H3, grafos, Contraction Hierarchies o D* Lite.
- Inventar parámetros: si falta uno, `[__]` y avisar a Edgar.
