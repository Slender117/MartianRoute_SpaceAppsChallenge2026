# Milton · Componentes de interfaz

**Objetivo:** apoya OE4.
**Hitos:** participa en H3. **Respaldo:** Miguel, que guía y revisa cada componente.

## Alcance

Construir los componentes de la interfaz que muestran qué ruta conviene, cuánto O₂ gasta y de dónde
sale cada número. Cada componente entra por PR revisado por Miguel.

## Carpetas

- `apps/web/components/ui/` (`RoutePanel`, `LayerPanel`, `NavPanel`, `SitePanel`, y los nuevos)

## Tareas

- [ ] Componente de la tabla comparativa: O₂ como intervalo, tiempo, riesgo y diferencia contra la
      línea base (H3)
- [ ] Componente del panel "Supuestos y límites" con etiquetas de procedencia (H3)
- [ ] Interruptor y leyenda del mapa de regreso seguro (H3)
- [ ] Puntos de demo precargados en la interfaz (H4)
- [ ] Aplicar con Williams la prueba de HE4 (H4)

## Por día

| 13 nov | 14 nov | 15 nov |
| --- | --- | --- |
| Componentes de tabla y panel con datos simulados | Conectar los componentes a la API real y cargar los puntos de demo | Pulir textos y estados de carga |

## Recibe y entrega

- **Recibe** de Miguel: contrato de la API (`schemas/` y `packages/contracts`) y revisión de PR. De
  Miguel y Edgar: los puntos de demo.
- **Entrega** a Miguel: componentes listos para integrar.

## Reglas de la interfaz

- Texto en español; unidades en metros, grados, horas (con soles) y kg.
- Toda cifra con etiqueta `observed`, `derived` o `modeled`; los `[__]` se muestran como supuestos.

## Fuera de alcance

- Lógica de ruteo o de consumibles en el navegador: viene de la API.
- Escena 3D (`components/scene/`), que es de Tulio.
