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

## Costo de O₂ por pendiente (`science/model/eva_cost.py`)

Forma de la curva de costo de caminar según la pendiente, de Minetti et al. (2002), medida en 1 g y
sin traje (valores del resumen). Solo se usa como multiplicador respecto al terreno plano. Todavía no
entra al motor de la API.

| Pendiente (subida / avance) | Costo de caminar | Etiqueta | Fuente |
| --- | --- | --- | --- |
| -45 % | 3.46 J/kg/m | observed | Minetti et al. (2002) |
| -10 % (mínimo) | 0.81 J/kg/m | observed | Minetti et al. (2002) |
| 0 % (plano, 1.0 m/s) | 1.64 J/kg/m | observed | Minetti et al. (2002) |
| +45 % | 17.33 J/kg/m | observed | Minetti et al. (2002) |

- Entre nudos se interpola linealmente y fuera de ±45 % se satura (`modeled`).
- En Marte (0.38 g) la penalización por pendiente se acota en un intervalo y no en un valor único:
  entre g/g_Tierra (el costo en plano no cambia con la gravedad) y 1 (cambia en proporción). Richter
  et al. (2017) no dan un factor para 0.38 g, así que no se usa ningún número de ahí.

## Riesgo de terreno de NOAH-H (validación, `science/validation/`)

Riesgo por grupo interpretativo del mosaico NOAH-H de Jezero (Wright et al., 2022b), escalado por
rango según lo que Barrett et al. (2022) afirman de cada grupo. Etiqueta `modeled`. Todavía no entra
al motor de la API: lo usa la validación de HE3.

| Grupo | Riesgo | Base | Barrett et al. (2022) |
| --- | --- | --- | --- |
| Roca madre | 0 | Cita directa | §2.3: da agarre sea rugosa o lisa |
| No roca madre | 0.25 | Interpolación lineal supuesta | §2.3 y §6.3: peligro incierto, puede ser arena |
| Campos de rocas | 0.5 | Interpolación lineal supuesta | §7.2: peligro sea cual sea el sustrato |
| Ondulaciones pequeñas | 0.75 | Interpolación lineal supuesta | §6.3: a veces transitables |
| Ondulaciones grandes | 1 | Cita directa | §6.3: nunca transitables |

- Los extremos tienen cita directa. El orden de los tres grupos del medio y la escala lineal son
  supuestos del proyecto.
- Sin dato (0) y nodata (127) no entran al costo: no se leen como terreno seguro.
- Las 14 etiquetas de clase de Barrett (Tabla 2), pensadas para el rover ExoMars en Oxia Planum,
  ponen a la roca madre por encima de la no roca madre si se promedian por área en Jezero, también
  sobre el camino de Perseverance. Por eso no se usan; quedan como trabajo a futuro.
- Barrett (§6.3) considera de impacto alto la roca madre rugosa y la fracturada: el 0 del grupo las
  subestima.

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

- Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., &
  Sefton-Nash, E. (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results
  for the ExoMars Rover candidate landing sites. *Icarus, 371*, 114701.
  https://doi.org/10.1016/j.icarus.2021.114701
- Hassler, D. M., et al. (2014). Mars' surface radiation environment measured with the Mars Science
  Laboratory's Curiosity rover. *Science, 343*(6169), 1244797. https://doi.org/10.1126/science.1244797
- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and
  running at extreme uphill and downhill slopes. *Journal of Applied Physiology, 93*(3), 1039–1046.
  https://doi.org/10.1152/japplphysiol.01177.2001
- NASA Jet Propulsion Laboratory. (2024, 10 de junio). *NASA watches Mars light up during epic solar
  storm*. https://www.jpl.nasa.gov/news/nasa-watches-mars-light-up-during-epic-solar-storm/
- Richter, C., Braunstein, B., Winnard, A., Nasser, M., & Weber, T. (2017). Human biomechanical and
  cardiopulmonary responses to partial gravity – A systematic review. *Frontiers in Physiology, 8*,
  583. https://doi.org/10.3389/fphys.2017.00583
- Tobler, W. (1993). *Three presentations on geographical analysis and modeling* (Technical Report
  93-1). National Center for Geographic Information and Analysis.
- Wright, J., Barrett, A. M., Fawdon, P., Favaro, E. A., Balme, M. R., Woods, M. J., &
  Karachalios, S. (2022a). Jezero crater, Mars: Application of the deep learning NOAH-H terrain
  classification system. *Journal of Maps, 18*(2), 484–496.
  https://doi.org/10.1080/17445647.2022.2095935
- Wright, J., Barrett, A., Fawdon, P., Favaro, E., Balme, M., Woods, M., Karachalios, S., & Gerdes, L.
  (2022b). *NOAH-H_terrain_classifications_of_Jezero_Crater_Mars.zip* (Versión 2) [Data set]. The
  Open University. https://doi.org/10.21954/ou.rd.17121482.v2
