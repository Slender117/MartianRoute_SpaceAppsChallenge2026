# Supuestos y límites del modelo

Cada parámetro numérico del motor aparece aquí con su fuente. La API sirve la misma lista en
`GET /assumptions`, leída de las constantes del código (`apps/api/app/engine/assumptions.py`), y una
prueba falla si un parámetro de la API no está en este archivo.

**`[__]`** significa que el valor es un supuesto sin fuente abierta confirmada: no es un dato de
misión ni una especificación de traje. Son preguntas abiertas del proyecto.

## Parámetros

| ID | Parámetro | Valor | Etiqueta | Fuente |
| --- | --- | --- | --- | --- |
| `base_speed` | Velocidad con traje en terreno plano | 2.5 km/h | modeled | `[__]` |
| `tobler_coefficient` | Coeficiente de la función de Tobler | 3.5 | modeled | Tobler (1993), escalada a la velocidad con traje |
| `o2_rate` | Consumo de O₂ por persona | 0.07 kg/h | modeled | `[__]` |
| `crew_size` | Integrantes de la EVA | 2 | modeled | Decisión del proyecto |
| `autonomy` | Autonomía del traje | 8 h | modeled | `[__]` |
| `autonomy_reserve` | Reserva de autonomía | 20 % | modeled | Decisión del proyecto |
| `max_slope` | Pendiente máxima caminable | 25° | modeled | `[__]` |
| `max_distance` | Distancia máxima a la base | 10 km | modeled | `[__]` |
| `max_dose` | Límite de dosis por EVA | sin valor | modeled | `[__]` |
| `radiation_rate` | Dosis equivalente en la superficie | 0.64 ± 0.12 mSv/día | observed | Hassler et al. (2014) |
| `solar_event_dose` | Dosis absorbida del escenario de evento solar | 8.1 mGy | observed | NASA JPL (2024) |
| `sol_length` | Duración de un sol | 24.6598 h | observed | NASA GISS Mars24 |
| `mars_radius` | Radio de Marte | 3,389.5 km | observed | Convención del proyecto (radio medio) |
| `slope_warning` | Aviso de tramo empinado | 80 % de la pendiente máxima | modeled | Decisión del proyecto |
| `science_threshold` | Umbral de parada por minerales | índice 0.6 | modeled | Decisión del proyecto |
| `ice_threshold` | Umbral de parada por hielo | índice 0.6 | modeled | Decisión del proyecto |
| `stop_gap` | Separación mínima entre paradas | 15 puntos | modeled | Decisión del proyecto |
| `min_cell_cost` | Costo mínimo por celda | 0.1 | modeled | Decisión del proyecto |
| `weights_safe` | Pesos del modo Segura | pendiente 4, riesgo 4, inestabilidad 2, ciencia 0 | modeled | Decisión del proyecto |
| `weights_fast` | Pesos del modo Rápida | pendiente 0.5, riesgo 1, inestabilidad 0.3, ciencia 0 | modeled | Decisión del proyecto |
| `weights_science` | Pesos del modo Científica | pendiente 1.5, riesgo 2, inestabilidad 1, ciencia 0.8 | modeled | Decisión del proyecto |

## Notas sobre la radiación

- **Tasa de fondo.** `CLAUDE.md` pedía verificar el valor aproximado de 0.67 mSv/día. Hassler et al.
  (2014) reportan 0.64 ± 0.12 mSv/día (0.21 ± 0.04 mGy/día de dosis absorbida) en los primeros 300 días
  de Curiosity en Gale. Una revisión posterior cita 0.67 para otro periodo de promedio; se usa el valor
  del artículo original. La dosis real varía con el ciclo solar y con la presión de la atmósfera.
- **Evento solar.** El escenario usa el evento del 20 de mayo de 2024: 8.1 mGy junto al rover, el mayor
  medido por RAD hasta esa fecha. Se aplica completo como peor caso observado, no como predicción: un
  evento futuro podría ser mayor. Es dosis absorbida, así que no se suma a los mSv de fondo: convertirla
  requiere el factor de calidad de ese evento, que no tenemos.
- **Sin límite por defecto.** No hay un límite de dosis por EVA con fuente. La API reporta la dosis y
  solo genera una alerta si el cliente manda `max_dose_msv`.

## Límites conocidos

- Mientras una región tenga `synthetic: true`, sus cifras no describen el terreno real de Marte.
- La duración de la EVA solo cuenta la caminata: no incluye el trabajo en las paradas.
- El regreso se calcula por el mismo camino de la ida.
- La tasa de radiación se midió en Gale, no en Jezero.
- Las distancias siguen una grilla de 8 vecinos, que las sobrestima hasta cerca de 8 %. La validación
  contra el rover mide los dos caminos igual, para que la proporción no herede ese sesgo.
- La pendiente del pipeline asume celdas cuadradas: lejos del ecuador pierde precisión.
- No hay alertas de clima todavía: la API no recibe la hora de salida.

## Referencias

- Hassler, D. M., et al. (2014). Mars' surface radiation environment measured with the Mars Science
  Laboratory's Curiosity rover. *Science, 343*(6169), 1244797. https://doi.org/10.1126/science.1244797
- NASA Jet Propulsion Laboratory. (2024, 10 de junio). *NASA watches Mars light up during epic solar
  storm*. https://www.jpl.nasa.gov/news/nasa-watches-mars-light-up-during-epic-solar-storm/
- Tobler, W. (1993). *Three presentations on geographical analysis and modeling* (Technical Report
  93-1). National Center for Geographic Information and Analysis.
