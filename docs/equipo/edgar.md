# Edgar · Ciencia y validación

**Objetivo:** OE3 · HE3 y la hipótesis general.
**Hitos:** responsable de H1; participa en H2 y H3. **Respaldo:** Tulio. Es respaldo de Tulio y de
Miguel. **Presenta** el pitch y responde las preguntas técnicas.

## Alcance

Que cada número del modelo tenga fuente o esté marcado como supuesto, clasificar el terreno por
riesgo y demostrar con el recorrido real de Perseverance que las rutas son creíbles.

## Carpetas

- `science/` (`model/eva_cost.py`, `calibrate.py`, `convert_traverse.py`)
- `docs/supuestos.md`

## Tareas

- [ ] Parámetros con fuente en `docs/supuestos.md`: tasas de Apollo vía Bellcomm, curva de Minetti,
      RAD 0.64 mSv/día (H1)
- [ ] Fijar los tramos: calibración con sol 606 o menos, medición con los posteriores, no contiguos
      (H1). Dentro del mosaico NOAH-H quedan 18 de calibración y 20 de medición; con el corte en 1000
      serían 31 y 7, muy pocos para la Wilcoxon pareada
      (`science/validation/trechos.csv`)
- [ ] Tabla clase a riesgo de NOAH-H con fuente, para Tulio (H2)
- [ ] Recorrido de Perseverance recortado y con elevación, junto con Tulio (H2)
- [ ] Acompañar a Miguel en la integración de su modelo de O₂ (H3)
- [ ] Script de métricas: separación media, distancia, desnivel y Wilcoxon pareada (HE3) (H3)
- [ ] Correr la validación con las rutas congeladas y armar la tabla de resultados, incluido lo que falló (H4)
- [ ] Elegir con Miguel los puntos de demo donde la ruta corta gaste más O₂ (H4)
- [ ] Fotos de Perseverance por tramo para las paradas (H4) **(recortable)**

## Por día

| 13 nov | 14 nov | 15 nov |
| --- | --- | --- |
| Parámetros, tramos y tabla clase a riesgo | Validación con rutas congeladas; hablar con mentores | Presenta y responde preguntas técnicas |

## Recibe y entrega

- **Recibe** de Tulio: recorrido con elevación. De Miguel: rutas congeladas para validar.
- **Entrega** a Tulio: tabla clase a riesgo. A Miguel: modelo de O₂ y parámetros. Al pitch: cifras
  citables y la tabla de validación.

## Fuera de alcance

- Trasladar a Marte el paso a saltos lunar, el balance térmico de Apollo o el comportamiento del
  polvo lunar.
- Revisión sistemática de literatura.
- Inventar cifras: si no hay fuente abierta, `[__]` y avisar.
