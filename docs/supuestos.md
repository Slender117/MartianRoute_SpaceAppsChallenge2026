# Supuestos y límites del modelo

Cada parámetro numérico del motor aparece aquí con su fuente. La API sirve la misma lista en
`GET /assumptions`, leída de las constantes del código (`apps/api/app/engine/assumptions.py`), y una
prueba falla si un parámetro de la API no está en este archivo.

**`[__]`** significa que el valor es un supuesto sin fuente abierta confirmada: no es un dato de
misión ni una especificación de traje. Son preguntas abiertas del proyecto.

## Parámetros

| ID | Parámetro | Valor | Etiqueta | Fuente |
| --- | --- | --- | --- | --- |
| `base_speed` | Velocidad con traje en terreno plano | 2 km/h | modeled | Coan (2020), §4.2.1.3.1.1: ritmo lunar sobre regolito casi plano |
| `tobler_coefficient` | Coeficiente de la función de Tobler | 3.5 | modeled | Tobler (1993), escalada a la velocidad con traje |
| `o2_rate` | Consumo de O₂ por persona | 0.07 kg/h | modeled | `[__]` |
| `o2_flat_per_m` | O₂ por metro en terreno plano | 3.5 × 10⁻⁵ kg/m | modeled | `[__]` (consumo de O₂ ÷ velocidad en plano) |
| `slope_cost_curve` | Costo de caminar según la pendiente | 1.64 J/kg/m en plano; 17.33 a +45 % | observed | Minetti et al. (2002); solo la forma |
| `mars_gravity` | Gravedad en la superficie de Marte | 3.728 m/s² | derived | GM / R² con GM = 42,828.37 km³/s² de Konopliv et al. (2020) y el radio medio de 3,389.5 km |
| `crew_size` | Integrantes de la EVA | 2 | modeled | Decisión del proyecto |
| `autonomy` | Autonomía del traje | 8 h | modeled | Coan (2020), §4.1.4: EVA de hasta 8 h (6 ± 2 h), más 1 h de O₂ secundario; Drake y Watts (2014), §9.2 |
| `autonomy_reserve` | Reserva de autonomía | 20 % | modeled | Decisión del proyecto |
| `task_time` | Trabajo fijo de la EVA (sin caminar) | 0 h | modeled | `[__]`: se ajusta por petición con `suit.task_h` |
| `walkback_reserve` | Reserva mínima al volver a la base | 30 min | modeled | Decisión del proyecto (plan del equipo); falta fuente con DOI. Se aplica la más estricta entre esta y el 20 % |
| `max_slope` | Pendiente máxima caminable | 20° | modeled | Coan (2020), §4.2.1.3: subir, bajar o cruzar pendientes de hasta 20° |
| `max_distance` | Distancia máxima a la base | 10 km | modeled | Regreso a pie de emergencia: Coan (2020), §4.2.1.3.1.1; NASA (2025), [V2 11030]; Drake y Watts (2014), §9.2 |
| `max_dose` | Límite de dosis por EVA | sin valor | modeled | NASA (2022), §4.8: no hay límite por EVA |
| `career_dose_limit` | Límite de dosis efectiva de carrera | 600 mSv | observed | NASA (2022), [V1 4030] |
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
| `weights_baseline` | Pesos de la línea base (mínima distancia) | todos en 0 | modeled | Decisión del proyecto |

## Notas sobre la radiación

- **Tasa de fondo.** `CLAUDE.md` pedía verificar el valor aproximado de 0.67 mSv/día. Hassler et al.
  (2014) reportan 0.64 ± 0.12 mSv/día (0.21 ± 0.04 mGy/día de dosis absorbida) en los primeros 300 días
  de Curiosity en Gale. Una revisión posterior cita 0.67 para otro periodo de promedio; se usa el valor
  del artículo original. La dosis real varía con el ciclo solar y con la presión de la atmósfera.
- **Evento solar.** El escenario usa el evento del 20 de mayo de 2024: 8.1 mGy junto al rover, el mayor
  medido por RAD hasta esa fecha. Se aplica completo como peor caso observado, no como predicción: un
  evento futuro podría ser mayor. Es dosis absorbida, así que no se suma a los mSv de fondo: convertirla
  requiere el factor de calidad de ese evento, que no tenemos.
- **Sin límite por EVA.** NASA-STD-3001 Vol. 1 Rev. B (NASA, 2022, §4.8) no define un límite por
  EVA. Define dos: la dosis efectiva de carrera debe ser menor a 600 mSv para cualquier edad y sexo,
  sumando todas las misiones ([V1 4030]), y el diseño debe proteger a la tripulación del evento solar
  de referencia (los eventos de octubre de 1989) por debajo de 250 mSv ([V1 4031]). La API informa el
  límite de carrera (`career_dose_limit`), reporta la dosis de la EVA y solo genera una alerta si el
  cliente manda `max_dose_msv`.

## Notas sobre los límites de la EVA

- **Son valores lunares.** Velocidad, autonomía, pendiente máxima y distancia a la base salen de
  documentos de Artemis para la Luna. Coan (2020, §4.1.4.4) dice que la planeación de EVA en Marte
  sigue en curso; se aplican a Marte como supuesto (`modeled`), sin prueba en 0.38 g.
- **Distancia a la base: 10 km.** Es el límite de regreso a pie si falla el rover. Coan (2020,
  §4.2.1.3.1.1) da menos de 5 h de caminata a 2 km/h, unos 10 km, todavía por confirmar (TBR). La
  justificación del requisito [V2 11030] de NASA-STD-3001 Vol. 2 Rev. E (NASA, 2025, §11.2.3.2) recoge
  que los astronautas de Apolo pidieron agua para un regreso de 10 km si falla el vehículo. La DRA 5.0
  (Drake y Watts, 2014, §9.2, supuesto l.6) asume 10 km en la Luna y deja Marte por definir, porque no
  se ha probado en gravedad marciana. Para una EVA solo a pie, sin rover, Coan (2020) da 2 km radiales
  y 16 km acumulados.
- **Velocidad: 2 km/h.** Coan (2020) la da sobre regolito casi plano, sin pendiente ni rocas; la
  función de Tobler del motor la reduce con la pendiente.
- **Pendiente: 20°.** Coan (2020, §4.2.1.3) pide caminar subiendo, bajando o de través en pendientes de
  hasta 20°; Apolo 15 anduvo en pendientes de unos 17°.
- **Autonomía: 8 h.** Coan (2020, §4.1.4) fija EVA de hasta 8 h (6 ± 2 h) con 1 h extra de O₂
  secundario para contingencias; la DRA 5.0 (§9.2) pide un traje para EVA de 8 h. La reserva del 20 %
  (`autonomy_reserve`) sigue siendo decisión del proyecto.

## Costo de O₂ por pendiente (`science/model/eva_cost.py`)

Forma de la curva de costo de caminar según la pendiente, de Minetti et al. (2002), medida en 1 g y
sin traje (valores del resumen). Solo se usa como multiplicador respecto al terreno plano. Entra
al motor de la API en `apps/api/app/engine/o2_model.py`.

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

## Punto de no retorno

Hay una sola regla de reserva: la **autonomía planeable** es la autonomía menos la reserva más
estricta entre el 20 % (`autonomy_reserve`) y 30 min (`walkback_reserve`). Con el traje de 8 h manda el
20 % (1.6 h, límite planeable de 6.4 h); los 30 min solo mandan con trajes de menos de 2.5 h. La misma
regla alimenta la factibilidad de la ruta, el punto de no retorno y el mapa de regreso seguro.

El punto de no retorno es el primer punto de la ida donde
`tiempo gastado + tiempo de regreso ≥ autonomía planeable − trabajo fijo (task_h)`. Los 30 min son una
decisión del plan del equipo y no tienen todavía una fuente con DOI.

El mapa de regreso seguro tiene tres zonas: (1) se vuelve dentro de la autonomía planeable; (2) solo
se vuelve consumiendo la reserva; (3) ni con la autonomía total alcanza para volver.

## Cifra oficial de O₂

La cifra oficial es `o2_interval_kg`: la caminata con la curva de Minetti entre las dos cotas de
gravedad, más el trabajo fijo a la tasa por hora. `o2_estimate_kg` (duración × 0.07 kg/h) queda como
referencia en la API y no se muestra en la interfaz.

## Límites conocidos

- Mientras una región tenga `synthetic: true`, sus cifras no describen el terreno real de Marte.
- La duración de la EVA cuenta la caminata más el trabajo fijo (`task_h`), que vale 0 hasta que el
  equipo fije un valor con fuente. No modela paradas de descanso.
- El regreso usa la misma velocidad que la ida (Tobler a 2 km/h en plano): no hay una velocidad de
  contingencia con fuente con DOI.
- Velocidad, autonomía, pendiente máxima y distancia a la base salen de documentos lunares de Artemis
  y se aplican a Marte sin prueba en 0.38 g.
- El regreso se calcula por el mismo camino de la ida.
- La tasa de radiación se midió en Gale, no en Jezero.
- Las distancias siguen una grilla de 8 vecinos, que las sobrestima hasta cerca de 8 %. La validación
  contra el rover mide los dos caminos igual, para que la proporción no herede ese sesgo.
- La pendiente del pipeline asume celdas cuadradas: lejos del ecuador pierde precisión.
- No hay alertas de clima todavía: la API no recibe la hora de salida.
- La curva de O₂ por pendiente (Minetti et al., 2002) se midió en la Tierra, a 1 g y sin traje: solo
  aporta la forma. Como no hay fuente de cómo cambia el costo en plano con la gravedad, el O₂ por
  pendiente se reporta como intervalo (`o2_interval_kg`) entre dos cotas.

## Referencias

- Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., &
  Sefton-Nash, E. (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results
  for the ExoMars Rover candidate landing sites. *Icarus, 371*, 114701.
  https://doi.org/10.1016/j.icarus.2021.114701
- Coan, D. (2020). *Exploration EVA system concept of operations* (EVA-EXP-0042, Rev. B). NASA
  Johnson Space Center. https://ntrs.nasa.gov/citations/20205008200
- Drake, B. G., & Watts, K. D. (Eds.). (2014). *Human exploration of Mars Design Reference
  Architecture 5.0, addendum #2* (NASA/SP-2009-566-ADD2). NASA.
  https://ntrs.nasa.gov/citations/20160003093
- Hassler, D. M., et al. (2014). Mars' surface radiation environment measured with the Mars Science
  Laboratory's Curiosity rover. *Science, 343*(6169), 1244797. https://doi.org/10.1126/science.1244797
- Konopliv, A. S., Park, R. S., Rivoldini, A., Baland, R.-M., Le Maistre, S., Van Hoolst, T., Yseboodt, M.,
  & Dehant, V. (2020). Detection of the Chandler wobble of Mars from orbiting spacecraft. *Geophysical
  Research Letters, 47*, e2020GL090568. https://doi.org/10.1029/2020GL090568
- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and
  running at extreme uphill and downhill slopes. *Journal of Applied Physiology, 93*(3), 1039–1046.
  https://doi.org/10.1152/japplphysiol.01177.2001
- NASA. (2022). *NASA space flight human-system standard, volume 1, revision B: Crew health*
  (NASA-STD-3001 Vol. 1 Rev. B). https://www.nasa.gov/wp-content/uploads/2020/10/2022-01-05_nasa-std-3001_vol.1_rev._b_final_draft_with_signature_010522.pdf
- NASA. (2025). *NASA spaceflight human-system standard, volume 2, revision E: Human factors,
  habitability, and environmental health* (NASA-STD-3001 Vol. 2 Rev. E).
  https://ntrs.nasa.gov/citations/20250004555
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
