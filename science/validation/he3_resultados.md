# HE3: resultados contra el recorrido de Perseverance (14 de noviembre de 2026)

**Hipótesis:** la ruta segura con la capa de terreno NOAH-H queda más cerca de la traza real de
Perseverance que sin ella, y esta más cerca que la ruta de mínima distancia.

**Veredicto: no se sostiene.** Ninguna de las dos comparaciones fijadas de antemano cumple
p < 0.025 y r ≥ 0.3.

## Método

- Región real `jezero` (dataset 0.4.0, celdas de 24.8 × 23.4 m), con las grillas del pipeline
  leídas como `.npy`.
- Trechos rectos de 0.5 a 1 km de `trechos.csv`: 18 de calibración (sol ≤ 606) y 18 de medición.
  Los trechos 37 y 38 quedan fuera del recuadro de la región.
- Brazos: A, Segura con NOAH-H; B, Segura sin NOAH-H; C, línea base de mínima distancia. El peso de
  pendiente queda fijo en 4.0 y la pendiente máxima en 20°.
- Pesos calibrados en la rejilla {0, 0.1 … 10} con la separación media simétrica, y congelados en el
  commit `eb6b7ae` antes de medir: A y B quedan con w_riesgo = 0 y w_inestabilidad = 2.15.
- Pruebas: Wilcoxon pareada unilateral, aproximación normal, r = |z|/√n con n los pares sin empate.

## Resultados (18 trechos de medición)

| Comparación | Gana | Pierde | Empates | p | r | Veredicto |
| --- | --- | --- | --- | --- | --- | --- |
| A < B (con NOAH-H frente a sin NOAH-H) | 0 | 0 | 18 | — | — | No soporta: sin pares discordantes |
| B < C (sin NOAH-H frente a línea base) | 9 | 8 | 1 | 0.25 | 0.17 | No soporta |

- **A < B se decidió en la calibración.** La pérdida crece de forma pareja con el peso de NOAH-H, y
  el mínimo quedó en w_riesgo = 0. Con eso, A y B son la misma ruta.
- **B < C:** las medianas (17.6 m y 25.3 m) parecen una ventaja, pero la diferencia pareada es de
  −2.9 m de mediana (rango −32.9 a +27.5 m), menos de una celda.

## Descriptivos (no son pruebas)

| Brazo | Separación mediana | Distancia / rover | Desnivel − rover | Riesgo NOAH-H medio |
| --- | --- | --- | --- | --- |
| A = B | 17.6 m | 0.68 | −4.6 m | 0.25 |
| C, línea base | 25.3 m | 0.66 | −4.8 m | 0.26 |
| Segura de la app (4, 4, 2) | 30.2 m | 0.71 | −4.5 m | 0.16 |
| Rover | — | 1 | 0 | 0.28 |

- La Segura de la app es la más lejana de Perseverance y es peor que la línea base en 11 de 18
  trechos. Es más conservadora que el rover; para una persona a pie puede ser lo correcto.
- El rover recorrió terreno de riesgo NOAH-H medio de 0.28, mientras que el promedio de la región
  es 0.42.

## Límites

- **Resolución.** Todas las separaciones están alrededor de una celda (unos 25 m). Con esta grilla
  no se distingue una diferencia menor a una celda. La zona HiRISE de 3 m solo cubre 5 trechos, todos
  de calibración.
- **Selección.** El sitio de aterrizaje y los recorridos de Perseverance se planearon por seguridad
  con imágenes HiRISE. Que NOAH-H coincida con las zonas donde se manejó es evidencia a escala de
  planeación, no dentro de cada trecho.
- **Un rover no es una persona.** Se calibra contra las decisiones de un rover, y las etiquetas de
  NOAH-H se hicieron para el rover ExoMars.
- Los pesos congelados valen solo para el dataset 0.4.0. Si cambia la región, hay que volver a
  calibrar.

## Reproducir

```bash
python science/validation/he3.py calibrar --assets ../regions_real
python science/validation/he3.py medir --assets ../regions_real
```

Detalle por trecho y brazo en `he3_resultados.csv`; pesos, superficie de pérdida y pruebas en
`he3_resumen.json`.
