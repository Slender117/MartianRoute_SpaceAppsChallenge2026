# WazeMars: contexto del proyecto

Mapa interactivo por capas y planificador de caminatas (EVA) para astronautas en Marte.
Proyecto para NASA Space Apps Challenge 2026, reto "Interplanetary Survival Guide: Martian Map".
Hackatón: 14 y 15 de noviembre de 2026. Nombre provisional (en el deck aparece como "Ruta Roja").

La interfaz y la documentación van en español. El código (identificadores, commits) puede ir en inglés.

## Qué pide el reto (resumen del statement)

Crear una vista integrada y por capas de un lugar o ruta en Marte, con datos de varias misiones
científicas de NASA, que ayude a un astronauta a planear y ejecutar una Marswalk segura mientras hace
ciencia. Puntos que el statement menciona explícitamente y que el proyecto debe cubrir:

- Al menos tres tipos de datos (óptico, térmico, espectral, topográfico, atmosférico, radiación...).
- Seguridad primero: radiación y clima espacial, movilidad con traje y carga, evitar obstáculos grandes.
- Ruta que muestre por dónde caminar para cumplir objetivos científicos.
- Escala hiperlocal: Mars Trek ya resuelve lo regional y global; el valor está en la zona de una caminata.
- Sugerido: imágenes desde el suelo (fotos de rovers) para que el astronauta sepa qué verá al llegar.
- Sugerido: partir de un objetivo científico concreto y un lugar con muchos datos.

## Decisiones tomadas (no reabrir sin preguntar al equipo)

- **Pregunta central:** qué ruta de EVA a pie maximiza el valor científico sin romper límites de
  pendiente, autonomía del traje, dosis de radiación y regreso a la base. Problema multiobjetivo.
  Los modos Segura, Rápida y Científica son pesos distintos sobre la misma función de costo.
- **Región de demo:** cráter Jezero (18.4° N, 77.5° E). Gale como segunda región en `regions.yaml`.
  La arquitectura es genérica por región.
- **Escenario:** EVA a pie, ida y vuelta, en pareja, desde un nodo base fijo (hábitat o rover
  presurizado estacionado). Modo con rover de apoyo: opcional.
- **Objetivo científico de la demo:** carbonatos del delta de Jezero y búsqueda de biofirmas, con
  puntos de interés con nombre.
- **Resolución:** región con DTM de CTX (~20 m). Zona de caminata con DTM de HiRISE reducido a 2 a 4 m
  por celda. No hay datos orbitales de 10 cm; ese nivel lo dan las fotos de los rovers.
- **Stack:** Next.js + React Three Fiber (frontend), FastAPI + NumPy + scikit-image (API),
  Python + Rasterio/GDAL (pipeline offline). Despliegue: Vercel, Render o Railway, Cloudflare R2.
  Sin Unity y sin modelado 3D manual.
- **Todo lo pesado se precalcula** en el pipeline. La API no hace procesamiento geoespacial: solo
  combina grillas normalizadas y corre el ruteo. La imagen de la API no necesita GDAL.
- **El costo se combina en la API**, no en el pipeline, para cambiar modos y pesos sin reprocesar.
- **Algoritmo:** A*/Dijkstra sobre grilla con `skimage.graph.MCP_Geometric` (8 vecinos, diagonales con
  costo geométrico). No migrar a H3, grafos, Contraction Hierarchies ni D* Lite salvo que el recálculo
  se vuelva lento.
- **Ruta y tiempo van separados:** la ruta sale del costo; el tiempo y los consumibles, del modelo de
  caminata (Tobler escalado con traje).

## Arquitectura

```
Navegador -> apps/web (Next.js + R3F, Vercel) --REST--> apps/api (FastAPI, Render/Railway)
                 |                                           |
                 +-- texturas y heightmap --> Cloudflare R2 <-- grillas .npy
                                                  ^
                     pipeline (Python + Rasterio/GDAL, offline, antes del evento)
                                                  ^
                                Datos de NASA: PDS, Mars Trek, USGS, SWIM, MMGIS
```

En desarrollo, la API lee `ASSETS_DIR` (disco) y sirve `data/regions` en `/assets`.
En producción, lee `ASSETS_URL` (R2).

## Estructura del repo

```
apps/api/app/engine/     cost, pathfind, consumables, science, constraints, planner
apps/api/app/routers/    health, regions, routes
apps/api/app/schemas/    modelos Pydantic (contrato de la API)
apps/api/app/storage/    lectura de regiones desde disco o R2, con caché
apps/api/tests/          conftest, test_engine, test_api
apps/web/components/scene/  Scene, Globe, CameraRig, RegionTerrain, RoutePath, TraverseOverlay
apps/web/components/ui/     SitePanel, LayerPanel, RoutePanel, NavPanel
apps/web/components/debug/  controles Leva
apps/web/lib/            api, geo, store (Zustand), types, theatre
pipeline/config/regions.yaml
pipeline/marsdata/       fetch, process, export, synthetic, publish, run (CLI)
packages/contracts/      tipos TS generados desde el OpenAPI
data/regions/            salida del pipeline (no se versiona)
docs/                    arquitectura, reportes, capturas
```

## Endpoints

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/health` | Estado del servicio (también sirve para despertar el servidor) |
| GET | `/regions` | Lista de regiones |
| GET | `/regions/{id}` | Manifest completo de una región |
| GET | `/regions/{id}/traverse/{rover}` | Recorrido real del rover en GeoJSON |
| POST | `/routes` | Una ruta en el modo pedido |
| POST | `/routes/compare` | Las tres rutas a la vez |

Errores: 404 región inexistente; 422 punto fuera de la región, en pendiente intransitable o sin ruta.

## Modelo de costo y consumibles

Costo por celda (`engine/cost.py`):

```
costo = 1 + w_pendiente*(pendiente/máx)^2 + w_riesgo*hazard + w_inestabilidad*(1 - inercia_térmica)
costo *= (1 - w_ciencia*minerales)      # mínimo 0.1 por celda
pendiente > máx del traje -> infinito (intransitable)
```

| Modo | Pendiente | Riesgo | Inestabilidad | Ciencia |
| --- | --- | --- | --- | --- |
| Segura | 4.0 | 4.0 | 2.0 | 0 |
| Rápida | 0.5 | 1.0 | 0.3 | 0 |
| Científica | 1.5 | 2.0 | 1.0 | 0.8 |

Consumibles (`engine/consumables.py`): Tobler escalado a 2.5 km/h en plano con traje, distancia 3D por
segmento, duración en horas y soles (1 sol = 24.66 h), O₂ de referencia 0.07 kg/h. Punto de no retorno:
primer punto donde se gastó la mitad de la autonomía. Paradas: celdas con minerales o hielo > 0.6,
separadas al menos 15 puntos. Alertas: tramos con más del 80 % de la pendiente máxima, exceso de
autonomía y distancia a la base mayor que la permitida.

## Convenciones obligatorias

- **Coordenadas:** planetocéntricas, longitud este, rango -180 a 180 en toda la app. Convertir al
  ingerir cada producto. Radio de Marte 3,389.5 km. Verificar siempre que el marcador de Jezero caiga
  sobre el cráter en la textura del globo.
- **CRS en archivos:** GeoTIFF con el sistema de referencia de Marte de la IAU (PROJ, por ejemplo
  `IAU_2015:49900`; verificar el código). GeoJSON se usa por convención aunque el estándar asume WGS84:
  documentar el CRS en el manifest.
- **Unidades:** metros, grados, horas, kg. Mostrar soles junto a horas.
- **Procedencia:** toda capa y toda cifra mostrada lleva etiqueta `observed`, `derived` o `modeled`.
  Todo parámetro numérico del modelo (pendiente máxima, consumo de O₂, tasa de radiación) se documenta
  con su fuente en `docs/` y en el panel de supuestos de la app.
- **Manifest de región:** versión semántica del dataset, ID de cada producto de origen, commit del
  pipeline y checksum por archivo.
- **Créditos:** cada dato descargado se registra en el archivo de créditos en formato APA 7
  (`Autor. (Año). Título (ID) [Data set]. Editor. DOI o URL`).
- **Texto en Windows:** siempre `encoding="utf-8"` al leer o escribir texto. Usar `StrEnum` (Python 3.11+).

## Reglas de trabajo

- No inventar cifras científicas. Si falta un valor, usar un marcador `[__]`, dejarlo como supuesto
  explícito y avisar.
- No agregar procesamiento geoespacial a la API: va al pipeline.
- Cualquier cambio en pesos o en `synthetic.py` debe mantener la prueba de que los tres modos dan rutas
  distintas en el escenario de demo.
- No usar el logo de NASA en la app ni sugerir aval de NASA.
- `@theatre/studio` es AGPL 3.0: solo en desarrollo, nunca en el build público. `@theatre/core` es Apache 2.0.
- Leva se oculta por defecto; aparece solo con `?debug` en la URL.
- Antes de dar por terminado: `pytest`, `ruff check` y `ruff format --check` (API y pipeline);
  `eslint`, `tsc --noEmit` y `next build` (web).
- En Git Bash de Windows, evitar scripts largos con heredocs: escribir cada archivo por separado.

## Problemas ya conocidos (no repetir)

- `<Html>` de drei falla con React 19 ("synchronously unmount a root"). Las etiquetas van en paneles
  HTML fuera del `<Canvas>`.
- `MeshBasicMaterial` no soporta `displacementMap`: usar `MeshLambertMaterial` para las capas.
- `OrbitControls` guarda su propio estado: registrarlo con `makeDefault` y sincronizar su objetivo en
  cada cambio de vista.
- El navegador lee el heightmap de 16 bits como 8 bits. Con relieve real se ven escalones: pasar a
  `Float32Array` (`.bin` crudo) o malla glTF.
- Render y Railway duermen en el plan gratuito: hacer `GET /health` al cargar la página y un ping
  programado el día del evento.

## Prioridades (en orden)

Imprescindible para cumplir el statement:

1. Fijar la convención de coordenadas y validar el marcador de Jezero.
2. DEM real de Jezero (mosaicos de navegación de Mars 2020 de USGS: DTM de CTX y ortomosaico de HiRISE,
   ya alineados) e implementar `fetch/sources.py` con productos exactos.
3. Recorrido real de Perseverance (MMGIS de JPL) a GeoJSON, con elevación muestreada del DEM.
4. Que los tres modos difieran en la región de demo: puntos de demo fijos, las tres líneas visibles a
   la vez y la diferencia contra la ruta segura en la tabla.
5. Dosis de radiación (referencia de Curiosity RAD, ~0.67 mSv/día; verificar) por duración de la EVA,
   escenario de evento solar y margen de reserva del 20 % en la autonomía.
6. Etiquetas de procedencia y panel "Supuestos y límites".
7. Métricas de validación contra Perseverance: distancia, desnivel acumulado, separación media.

Diferenciadores si da tiempo:

8. Zona de caminata con HiRISE (tercer nivel de zoom en la misma escena).
9. Línea de vista con la base (viewshed desde el DEM) y alerta de comunicación.
10. Fotos de Navcam o Mastcam-Z de Perseverance por parada (guardar URLs en el manifest, no imágenes).
11. Bloque `mission` en `regions.yaml`: objetivo, puntos de interés con nombre, tabla de relevancia por
    mineral. Valor científico = relevancia × novedad × confianza.
12. Hora de salida: alertas de clima con valores típicos de MEDA por hora local y sombras con el DEM.
13. Botón "reportar obstáculo": bloquear celdas y recalcular.
14. Textura MOLA del globo (equirectangular 4096 × 2048, USGS Astropedia) como `map` y `bumpMap`.
15. Punto de aproximación por objetivo científico: la celda caminable más cercana con pendiente aceptable.

Fuera de alcance del hackatón: localización sin GPS, D* Lite, MDP, simulación estocástica,
exportación a Unreal, Gazebo o ROS, revisión sistemática de literatura.

## Datos y fuentes

| Capa | Misión e instrumento | Fuente |
| --- | --- | --- |
| Elevación global | MGS MOLA | USGS Astropedia, PDS |
| Elevación local | MRO CTX y HiRISE (DTM) | Productos de Mars 2020 en USGS, PDS, HiRISE |
| Imagen óptica | MRO HiRISE, CTX | Mars Trek (WMTS), PDS |
| Inercia térmica | Mars Odyssey THEMIS | Mosaico global |
| Minerales | MRO CRISM | PDS; si se complica, mapa mineral publicado de Jezero con cita |
| Hielo subsuperficial | SWIM | Cubre latitudes medias del norte: verificar cobertura en Jezero |
| Clima | Perseverance MEDA, Curiosity REMS | PDS Atmospheres |
| Radiación | Curiosity RAD | Hassler et al., 2014 |
| Recorridos | Perseverance, Curiosity | MMGIS de JPL |
| Nombres | IAU/USGS | Gazetteer of Planetary Nomenclature |
| Hora marciana | NASA GISS Mars24 | Algoritmo |

## Comandos

Requisitos: Node 22+, Python 3.11+. En Windows `.venv/Scripts/`; en macOS y Linux `.venv/bin/`.

```bash
# Datos de prueba
cd pipeline && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]" && .venv/Scripts/marsdata synthetic

# API en http://localhost:8000 (docs en /docs)
cd apps/api && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
cp .env.example .env && .venv/Scripts/uvicorn app.main:app --reload

# Web en http://localhost:3000
npm install && cp apps/web/.env.example apps/web/.env.local && npm run dev:web
```

Comandos del pipeline: `marsdata synthetic | fetch | build | publish`.

## Glosario

- **EVA / Marswalk:** actividad extravehicular a pie sobre la superficie.
- **Walkback:** regla de Apollo: no alejarse más de lo que se puede regresar a pie si falla el vehículo.
  Aquí equivale a la distancia máxima a la base y al punto de no retorno.
- **Sol:** día marciano, 24.66 h.
- **DTM/DEM:** modelo digital de elevación.
- **Grilla de costo:** raster con el costo de cruzar cada celda, insumo del ruteo.
- **Tau:** opacidad atmosférica por polvo.

## Preguntas abiertas

- Valores reales de autonomía del traje, pendiente máxima caminable y consumo de O₂ (fuentes abiertas).
- Código exacto del CRS de Marte en PROJ que usará el pipeline.
- Cobertura de SWIM en Jezero.
- Criterios de evaluación y requisitos de entrega (guías publicadas el 13 de noviembre), incluida la
  declaración de uso de IA.
- Nombre final del proyecto (evitar "Waze", que es marca registrada).
