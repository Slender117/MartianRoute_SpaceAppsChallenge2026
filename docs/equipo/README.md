# Equipo: alcance por integrante

Basado en *WazeMars: plan de delegación del equipo* (V2, 9 de noviembre de 2026). Cada integrante es
dueño de un frente, y ese frente corresponde a un objetivo del protocolo (OE1 a OE4). Con el evento
encima, la prioridad sigue siendo una sola: **datos reales de Jezero y tres rutas distintas con su O₂**.

| Integrante | Frente | Objetivo e hipótesis | Entrega clave | Hitos | Respaldo | Archivo |
| --- | --- | --- | --- | --- | --- | --- |
| Tulio | Pipeline de capas, datos de navegación e infraestructura (despliegue, servidor, demo congelada); apoyo en 3D; presenta | OE1 · HE1: corregistro de 1 celda o menos y al menos 95 % de la zona con dato | Región de Jezero real publicada; app desplegada y estable; demo congelada y entrega | H2, H4, H5 | Edgar | [tulio.md](tulio.md) |
| Jairo | Visualización 3D, con apoyo de Tulio | OE4 · HE4: el visor | Terreno real con normal map, rutas y capas en 3D | H2, H3 | Tulio | [jairo.md](jairo.md) |
| Miguel | Backend FastAPI y dirección del frontend y la experiencia de uso | OE2 · HE2 y OE4 · HE4 | Tres modos y línea base sobre datos reales, punto de no retorno, regreso seguro; interfaz final integrada | H3 | Edgar | [miguel.md](miguel.md) |
| Milton | Componentes de interfaz, con la guía de Miguel | Apoya OE4 | Tabla comparativa, panel de supuestos, puntos de demo en la interfaz | H3 | Miguel | [milton.md](milton.md) |
| Edgar | Ciencia y validación: EVA, recorrido de Perseverance y clasificación de terreno; presenta | OE3 · HE3 y la hipótesis general | Parámetros con fuente, tabla clase a riesgo, métricas contra Perseverance | H1, H3 | Tulio | [edgar.md](edgar.md) |
| Williams | Comodín: pruebas de uso, equipo de la demo y video; presenta | Apoya OE4 | Pruebas de punta a punta, equipo y red de la demo, video de respaldo | H4 | Tulio | [williams.md](williams.md) |

Miguel dirige el frontend y la experiencia de uso; Milton construye componentes con su guía y cada
uno entra por PR revisado por Miguel. Tulio integra y despliega, del pipeline a la demo congelada.

## Carpetas por dueño

| Carpeta | Dueño |
| --- | --- |
| `pipeline/`, `data/regions/`, configuración de despliegue | Tulio |
| `apps/web/components/scene/`, `apps/web/components/debug/` | Jairo |
| `apps/api/`, `packages/contracts/`, `apps/web/lib/` | Miguel |
| `apps/web/components/ui/` | Milton (PR revisado por Miguel) |
| `science/`, `docs/supuestos.md` | Edgar |
| `docs/img/`, material del deck | Williams |

## Reglas para no bloquearse

1. **Contrato primero.** El primer día, Backend y Frontend acuerdan los campos nuevos de la API
   (O₂ por ruta, diferencia contra la ruta segura, mapa de regreso seguro, etiquetas de procedencia) y
   los fijan en `schemas/`. Desde ese momento, Frontend trabaja contra datos simulados con esa forma.
2. **Los datos sintéticos siguen vivos.** Nadie espera los datos reales para avanzar: Backend,
   Frontend y 3D trabajan sobre la región sintética hasta que se publique Jezero. El cambio debe ser
   solo cambiar el ID de región.
3. **Un dueño por carpeta.** Si necesitas tocar la carpeta de otro, avisa antes.
4. **Ramas cortas y PR pequeños.** Una rama por tarea, fusionada el mismo día. Antes de fusionar:
   `pytest`, `ruff`, `eslint`, `tsc` y `next build` en verde.
5. **Sincronización diaria de 15 minutos.** Cada uno dice qué terminó, qué sigue y qué lo bloquea.

Todos usan Claude Code con el mismo `CLAUDE.md` en la raíz del repositorio.

## Hitos

No hay fechas, solo compuertas: un hito se cumple cuando su responsable confirma el criterio en la
sincronización diaria. H2 y H3 son el camino crítico.

| Hito | Criterio | Responsable | Participan | Cuándo |
| --- | --- | --- | --- | --- |
| H1 · Acuerdos fijados | Contrato de API, coordenadas y escenario; parámetros del modelo con su fuente | Edgar | Todos | 13 nov |
| H2 · Jezero real publicado | DEM validado, minerales y THEMIS; recorrido de Perseverance; terreno 3D | Tulio | Edgar, Jairo | 13 nov |
| H3 · Motor de O₂ con datos reales | Costo en O₂ y tres modos distintos; mapa de regreso seguro y radiación | Miguel | Todos | 14 nov |
| H4 · Demo congelada | Ensayo completo y video de respaldo; desde aquí solo se fusionan correcciones | Tulio | Todos | Cierre del 14 nov |
| H5 · Entrega en el hackatón | Presentación el 15 de noviembre | Tulio | Todos | 15 nov |

Las tareas marcadas **(recortable)** se cortan primero si falta tiempo, en este orden: entrenar una
red propia, fotos por tramo y HiRISE.

## Pitch (todos)

- [ ] Definir el guion conforme avance el desarrollo; presentan Tulio, Edgar y Williams (H4)
- [ ] Cada integrante aporta el material de su frente para el deck (H4)
- [ ] Ensayo completo antes de congelar la demo (H4)

Los tres presentadores deben poder explicar la demo completa, por si alguien se traba.

## Riesgos y plan B

| Riesgo | Señal temprana | Plan B | Responsable |
| --- | --- | --- | --- |
| Los datos reales no quedan listos | H2 no se cumple | Demo sobre la región sintética con más contraste, mostrando el DEM real solo como imagen | Tulio |
| El costo asimétrico con `MCP_Flexible` se complica | Sin avance tras un día de trabajo | Costo simétrico en O₂ para el ruteo y velocidades asimétricas solo para el tiempo | Miguel |
| Los tres modos siguen dando la misma ruta | Falla la prueba automática | Cambiar los puntos de demo antes de tocar los pesos | Miguel y Edgar |
| El servidor gratuito se duerme o falla en vivo | `/health` tarda más de unos segundos | Video de respaldo y API corriendo en una laptop | Miguel, Tulio y Williams |
| Una persona se enferma o se atrasa | Una tarea imprescindible sin avance en la sincronización | Entra su respaldo (columna "Respaldo") | Quien coordine la sincronización |
| Se agregan funciones nuevas a última hora | PR grandes después de H4 | Después de H4 solo se fusionan correcciones | Tulio |
