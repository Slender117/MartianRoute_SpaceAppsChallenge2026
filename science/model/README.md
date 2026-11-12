# Modelo predictivo de costo de EVA (costo por celda + A*)

Prototipo de Edgar (Ciencia y validación), 2026-11-12. Código: [eva_cost.py](eva_cost.py). Prueba: [test_eva_cost.py](test_eva_cost.py).
Necesita `numpy`, `scipy` y `scikit-image`, que el motor del equipo ya usa, y `pytest` para las pruebas:

```bash
cd science/model && python -m pytest -q
```

## Qué hace

Predice cuánto O₂ cuesta cada metro de una EVA que vuelve por el mismo camino. Esa curva se vuelve la
penalización por pendiente de la grilla que recorre el A*, y también un intervalo de O₂ por ruta. Tiene dos partes:

| Parte | Qué es | Se entrena |
| --- | --- | --- |
| Pendiente y gravedad | Curva de Minetti et al. (2002), escalada con una cota inferior y una superior de gravedad | No: es física con intervalo |
| Riesgo e inestabilidad | Pesos de `hazard` y `1 − inercia térmica` | Sí, contra el recorrido real, con tramos reservados para medir |

La salida de una ruta es un **intervalo** de O₂ (`o2_interval_kg`), no una cifra. El valor central no existe
porque no hay fuente para cómo cambia el costo en plano con 0.38 g.

## Qué entra

| Dato | De dónde | Dueño |
| --- | --- | --- |
| `dem.npy`, `slope.npy` | `data/regions/jezero/` | Datos |
| `layers/hazard.npy`, `layers/thermal_inertia.npy` | `data/regions/jezero/layers/` | Datos |
| Recorrido de Perseverance | `M20_traverse_2026-11-12.json` (559 tramos por sol, sol 14 a 2022, CRS84) y `M20_waypoints_2026-11-12.json`. `science/convert_traverse.py` lo convierte a una sola LineString; quedan 4,688 puntos de los sols 1698 a 2022 al oeste del bbox de `regions.yaml` (lon < 77.25): ampliar el bbox o recortar | Ciencia con Datos |
| `o2_flat_kg_per_m` | `o2_rate / base_speed` de `docs/supuestos.md`: 0.07 kg/h ÷ 2500 m/h = 2.8e-5 kg/m, hoy `[__]` | Backend |
| Gravedad | 0.38 g del plan | Ciencia |

## Qué sale y cómo se entrega

1. **Función `slope_penalty`** que sustituye el término de pendiente de `engine/cost.py`
   (el parche `integracion_motor.patch` no va en este PR). Se entrega por PR, acordando antes la interfaz
   con Backend: el código del motor es suyo. `cell_cost` queda como variante en unidades físicas, que no recomiendo.
2. **Dos pesos calibrados** (`w_hazard`, `w_instability`) con su etiqueta `modeled` y la leyenda «calibrado con el
   recorrido de Perseverance», para `docs/supuestos.md`.
3. **`o2_interval_kg`** para el panel de la EVA, con el intervalo en lugar de la cifra única.
4. **Nota de métricas** con la separación en tramos no vistos, para H3.

## Encaje en `engine/cost.py` (probado en una copia local, sin tocar `apps/`)

El cambio son dos líneas y un import en `cost.py`, más copiar `eva_cost.py` a `engine/`. Lo probé sobre una
copia limpia de `main` del 12 de noviembre. El parche no se incluye en este PR hasta acordarlo con Backend.

```diff
-    slope_n = np.clip(grids.slope / max_slope_deg, 0, 1)
+    slope_n = slope_penalty(grids.slope, max_slope_deg)
...
-        + w["slope"] * slope_n**2
+        + w["slope"] * slope_n
```

Conserva la estructura y los pesos por modo del equipo; solo cambia la forma de la penalización por pendiente.

- Las **51 pruebas del equipo pasan** antes y después (con la región sintética de `marsdata synthetic`).
- **Demo sintético:** las rutas cambian de celdas, pero la distancia y la duración cambian 1 % o menos.

| Modo | Ida (km) antes → después | Pendiente máxima | Riesgo máximo |
| --- | --- | --- | --- |
| Segura | 6.74 → 6.80 | 7.6° → 5.6° | 0.06 → 0.06 |
| Rápida | 5.87 → 5.87 | 24.9° → 24.9° | 0.87 → 0.89 |
| Científica | 7.50 → 7.50 | 10.2° → 7.6° | 0.00 → 0.00 |

- **Variante en unidades físicas (`cell_cost`):** también pasa las 51 pruebas, pero la Rápida deja de cruzar
  pendientes (máxima de 24.9° a 4.7°) porque todos los modos comparten la misma penalización. Pierde lo que
  distingue a los modos, así que no la recomiendo para el motor actual.
- **Lo que las pruebas no protegen:** no fijan cifras de costo ni de ruta, por eso pasan con tres cálculos
  distintos. Un error de escala en la pendiente también pasaría. Las 6 pruebas propias cubren la curva.
- **O₂:** `test_consumables_cover_the_pair` fija `o2_estimate_kg = duración × 0.07`, y el parche no la toca.
  Mostrar el intervalo exige campos nuevos en `RouteResponse`, su etiqueta de procedencia (la exige
  `test_every_figure_has_a_provenance_label`), regenerar `packages/contracts` y la interfaz. Es trabajo de Backend
  y Frontend, y va aparte.
- **Documentos:** la fórmula de `docs/arquitectura.md` y de `CLAUDE.md` debe cambiar `(pendiente/máx)²` por la
  penalización de O₂. Si se agregan parámetros a `/assumptions`, `test_every_assumption_is_documented` los exige
  en `docs/supuestos.md`; el parche no agrega ninguno.
- **Alcance del parche:** lleva solo lo físico (`slope_penalty`, `o2_*`). La calibración (`route`, `separation_m`,
  `fit_weights`) queda en [calibrate.py](calibrate.py), un script offline que no va al motor.
- **La gravedad no llega a la ruta.** `slope_penalty` se normaliza contra la pendiente máxima y la escala `s` se
  cancela, así que cambiar de 0.38 g a 0.16 g no cambia el camino del A*; solo cambia el O₂ que se reporta
  (`o2_interval_kg`). Es coherente con no tener fuente para el efecto de la gravedad sobre la preferencia de ruta,
  pero limita la reutilización: cambiar de planeta cambia la cifra de O₂, no la ruta.
- **Cambia la forma, y eso es lo que Backend va a preguntar.** La penalización es casi lineal en vez de
  cuadrática, porque la curva de Minetti subiendo se interpola entre solo dos nudos. A la mitad de la pendiente
  máxima pasa de 0.25 a 0.45:

| Pendiente | 5° | 10° | 12.5° | 20° | 25° |
| --- | --- | --- | --- | --- | --- |
| Antes, (pendiente/máx)² | 0.04 | 0.16 | 0.25 | 0.64 | 1.00 |
| Ahora | 0.13 | 0.34 | 0.45 | 0.79 | 1.00 |

  Por eso la Segura baja su pendiente máxima de 7.6° a 5.6°: las pendientes moderadas cuestan casi el doble
  frente a las empinadas. Con más nudos de la curva el tramo subiendo ganaría curvatura.
- El terreno del demo casi no tiene pendiente (media de 1° a 3°): ahí el O₂ por tiempo del equipo queda 2 a 4 % por
  debajo de la cota inferior de Minetti. Con el Jezero real el efecto puede ser mayor; no lo medí.

## Lo que verifiqué y lo que no

- Las 6 pruebas pasan: la curva reproduce los cuatro puntos del resumen de Minetti, la penalización vale 0 en
  plano y 1 en el límite y no depende de la gravedad, el intervalo está ordenado y es exacto en plano, y el
  ajuste mejora la ruta en tramos no vistos.
- **Prueba sintética:** con pesos conocidos (3.0 y 1.0) el ajuste devolvió 4.64 y 1.00. En tramos no vistos la
  separación fue de 7.0 m, contra 25.6 m con pesos por defecto. Los datos salen de la misma familia de modelo, así
  que esto prueba la mecánica y no la ciencia.
- **Contra el modelo por tiempo del equipo** (O₂ por metro relativo al plano, ida y vuelta):

| Pendiente | Equipo | Minetti, cota inferior | Minetti, cota superior |
| --- | --- | --- | --- |
| 5 % | 1.02 | 1.15 | 1.40 |
| 10 % | 1.21 | 1.31 | 1.81 |
| 20 % | 1.72 | 1.80 | 3.10 |
| 30 % | 2.44 | 2.29 | 4.40 |
| 45 % | 4.12 | 3.03 | 6.34 |

  El modelo del equipo queda unos 5 a 10 % por debajo de la cota inferior entre 5 y 20 %, y dentro del intervalo
  desde 30 %. No lo desmiente: lo pone dentro de un rango con fuente.
- Nada de esto se probó con datos reales de Jezero todavía.

## Límites

- La curva es de 10 corredores en caminadora, a 1 g y sin traje. Solo sirve para la forma; los nudos son los
  cuatro del resumen y no el polinomio del texto completo, al que no pude acceder.
- Falta la fuente para escalar a 0.38 g y para el factor de traje. El traje queda dentro de `o2_flat_kg_per_m`.
- `slope.npy` es magnitud sin dirección: seguir una curva de nivel se penaliza como subir. Corregirlo exige costos
  por arista con el DEM, que implica otro Dijkstra y es de Backend.
- Perseverance maneja con objetivos científicos y navegación autónoma. Los pesos calibrados son de un rover, no
  de una persona, y la validación (H3) debe medirse en tramos que no se usaron para calibrar.
- Los modos Segura, Rápida y Científica quedan como están: este modelo no los reemplaza.

## Fuentes (DOI resuelve en doi.org; solo resúmenes leídos)

- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and running at
  extreme uphill and downhill slopes. *Journal of Applied Physiology*. https://doi.org/10.1152/japplphysiol.01177.2001
- Richter, C., Braunstein, B., Winnard, A., Nasser, M., & Weber, T. (2017). Human biomechanical and cardiopulmonary
  responses to partial gravity: A systematic review. *Frontiers in Physiology*. https://doi.org/10.3389/fphys.2017.00583
  (leído en texto completo: recoge que Shavelson (1968) halló bajada de la tasa metabólica con la gravedad en 4 de
  5 estudios, salvo con alto trabajo mecánico; no da un factor para 0.38 g, así que no lo uso como número).

## Uso de IA

Escrito con ayuda de Claude Code. Las pruebas y la comparación con el motor del equipo se ejecutaron en una copia
local de `main`; los DOI se resolvieron en doi.org.
