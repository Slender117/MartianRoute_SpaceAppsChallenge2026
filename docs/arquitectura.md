# Arquitectura

## Flujo de una ruta

1. El explorador elige inicio, destino y modo en la web (clic sobre el terreno).
2. Next.js manda `POST /routes/compare` a la API.
3. FastAPI carga (y cachea) las grillas de la región desde disco o R2.
4. `engine/cost.py` combina las capas con los pesos del modo; `engine/pathfind.py` corre A* (MCP de scikit-image).
5. `engine/planner.py` calcula la EVA completa (ida, y regreso por el mismo camino): tiempo, O₂, dosis, punto de no retorno, paradas, alertas, y la diferencia contra la ruta segura.
6. La web dibuja las tres rutas sobre el terreno y el detalle de la activa.

Todo lo pesado (reproyección, pendientes, normalización, texturas) se hace **offline** en el pipeline.

## Formato de una región

```
data/regions/                      (en producción: R2, prefijo regions/)
├── index.json                     {"regions": ["jezero", ...]}
└── jezero/
    ├── manifest.json              ver abajo
    ├── dem.npy                    float32, metros
    ├── slope.npy                  float32, grados
    ├── layers/{hazard,thermal_inertia,ice,minerals}.npy   float32 0–1
    ├── heightmap.png              16 bits, DEM normalizado (terreno 3D)
    ├── textures/<capa>.png        RGBA, overlays
    └── traverses/<rover>.geojson  recorrido real
```

Convenciones: grilla equirectangular sobre el bbox, fila 0 = latitud máxima, columna 0 = longitud mínima,
longitudes este-positivas de -180 a 180. Todas las capas comparten shape.

El manifest trae `bbox`, `shape`, `resolution_m`, `elevation_range`, `base`, `layers` y `traverses`, más:

| Campo | Contenido |
|---|---|
| `dataset_version` | versión semántica del dataset (`regions.yaml`) |
| `pipeline_commit` | commit del pipeline; `null` si la carpeta no está en un repositorio |
| `crs` | CRS de grillas y recorridos, como cadena PROJ |
| `synthetic` | `true` si los datos son de prueba |
| `layer_meta` | por capa, `provenance` (`observed`, `derived`, `modeled`) y `source` (ID del producto) |
| `checksums` | SHA-256 por archivo; la API los comprueba al leer y responde 503 si no coinciden |
| `demo` | puntos del escenario de demo, si la región tiene uno |

| Capa | Fuente | Significado de 1.0 |
|---|---|---|
| hazard | HiRISE / CTX | muchos obstáculos |
| thermal_inertia | THEMIS | roca firme (0 = arena suelta) |
| ice | SWIM | hielo somero probable |
| minerals | CRISM | alto valor científico |

## Contrato propuesto para los datos reales (pendiente de acordar)

Propuesta de Tulio (pipeline) para Miguel (esquemas) y Jairo (escena), del 13 de noviembre. Todo es
**aditivo y opcional**: cada campo nuevo tiene un valor por defecto, así que la API y la web actuales siguen
funcionando mientras cada uno lo adopta. Los valores de los ejemplos son ilustrativos; `[__]` marca lo que
falta definir.

### Archivos del terreno 3D

Bloque `assets` en el manifest:

```json
"assets": {
  "heightmap": { "path": "heightmap.bin", "dtype": "float32", "byte_order": "little",
                 "shape": [600, 600], "row0": "north" },
  "normal_map": { "path": "textures/normal.png", "space": "object", "exaggeration": "[__]" },
  "ortho": { "path": "textures/ortho.jpg", "size": [2400, 2400],
             "provenance": "observed", "source": "[__] ID del ortomosaico de CTX" }
}
```

- `heightmap.bin`: alturas en metros sin normalizar; el rango está en `elevation_range`.
- `exaggeration`: la exageración vertical con la que se calculó el normal map. La escena la usa como valor
  predeterminado, porque si no coincide con la malla la luz sale mal. La define Jairo.
- `heightmap.png` se queda hasta que la escena cargue el `.bin`; después se elimina.

### Calidad por capa (HE1)

Tres campos nuevos en cada entrada de `layer_meta`:

| Campo | Contenido |
|---|---|
| `coverage` | fracción de celdas con dato antes de rellenar huecos (0 a 1) |
| `registration_cells` | desplazamiento medido contra la ortofoto, en celdas; `null` si no se midió |
| `native_resolution_m` | resolución del producto de origen, en metros |

```json
"hazard": { "provenance": "modeled",
            "source": "Wright et al. (2022), NOAH-H IG, doi:10.21954/ou.rd.17121482.v2",
            "coverage": 0.97, "registration_cells": 0.6, "native_resolution_m": "[__]" }
```

Con esto, el reporte de HE1 (corregistro de 1 celda o menos y al menos 95 % con dato) sale del manifest.

### Huecos del DEM

`"masks": { "no_data": "layers/no_data.npy" }`: `uint8` con la forma de la grilla, 1 donde el DEM original
no tenía dato. El DEM se rellena por interpolación solo para que la malla sea continua, y la API trata esas
celdas como intransitables, igual que la pendiente excesiva. Así no se mezcla "sin dato" con "peligroso".

### Fracción intransitable

`layers/impassable_fraction.npy`, float32 de 0 a 1: la parte de cada celda cubierta por ondulaciones grandes
de NOAH-H, que Barrett et al. (2022) consideran nunca transitables. `hazard` es un promedio por celda y no
basta: una celda con 40 % de ondulaciones grandes quedaría caminable. La API bloquea la celda si supera un
umbral (`[__]`, sin fuente todavía). Hay que agregarla a `OPTIONAL_LAYERS`; si falta, vale 0 y no bloquea nada.

### Pendiente

`slope.npy` cambia de significado: pasa a ser el percentil 90 de la pendiente calculada sobre el DEM de
20 m dentro de cada celda, en vez de la pendiente del DEM ya reducido, que la suaviza y hace permisivo el
límite de 20°. Se documenta con `"slope_method": "p90_native_20m"`. Con datos reales se espera que más
celdas queden bloqueadas.

### Tamaño de celda

`"cell_size_m": [norte_sur, este_oeste]`, por ejemplo `[28.6, 26.7]` en Jezero. La API ya corrige el lado
este-oeste por su cuenta; esto es para el normal map y las proporciones de la escena.

### Recorridos

- `traverses/<rover>.geojson` sigue siendo un `LineString`, con coordenadas `[lon, lat, elev_m]` (elevación
  de `dem.npy`) y, en `properties`, `sol_range: [min, max]` y `elevation_source: "dem.npy"`. La API ya lee
  solo los dos primeros valores; en la web, `types.ts` pasa a `[number, number, number?][]` y
  `TraverseOverlay` usa la elevación en vez de dibujar a la altura máxima.
- `traverses/<rover>_sols.geojson`: `FeatureCollection` con un tramo por sol (`properties.sol`), para la
  validación de Edgar. No entra al endpoint.

### Créditos

`"credits": ["Autor. (Año). Título (ID) [Data set]. Editor. DOI o URL"]`: la lista en APA 7 de los productos
de la región, para que el panel de supuestos la muestre.

### Decisiones abiertas

| Tema | Propuesta | Alternativa | Deciden |
|---|---|---|---|
| Huecos del DEM | máscara `no_data` | rellenar y marcar `hazard = 1` | Miguel y Tulio |
| Umbral de `impassable_fraction` | constante en la API con `[__]` | parámetro en `SuitLimits` | Miguel y Edgar |
| `slope_method` | percentil 90 | máximo (más estricto, puede cerrar pasos estrechos) | Miguel y Edgar |
| Retiro de `heightmap.png` | cuando la escena cargue el `.bin` | | Jairo |
| `exaggeration` y sombreado | normal map con valor fijo | sombreado plano | Jairo |

Orden: Miguel agrega los campos opcionales a `schemas/region.py`, `lib/types.ts` y `OPTIONAL_LAYERS`; el
pipeline los genera primero en `marsdata synthetic` para que la web los pruebe, y después con datos reales
en `marsdata build`.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | estado |
| GET | `/regions` | lista resumida |
| GET | `/regions/{id}` | manifest |
| GET | `/regions/{id}/traverse/{rover}` | recorrido real (GeoJSON) |
| POST | `/routes` | una ruta (`mode`: safe, fast, science) |
| POST | `/routes/compare` | los tres modos; cada uno con `vs_safe`, su diferencia contra la segura |
| POST | `/routes/validate` | métricas de los tres modos contra el recorrido de un rover |
| GET | `/assumptions` | parámetros del modelo con su fuente, y límites conocidos |
| GET | `/assets/...` | solo en desarrollo: sirve `data/regions` |

Errores, siempre con el motivo en `detail`:

| Código | Cuándo |
|---|---|
| 404 | región o recorrido inexistente |
| 422 | punto fuera de la región o de la convención de longitud, pendiente intransitable, inicio igual a destino, sin ruta |
| 503 | datos ausentes o inconsistentes: falta un archivo, no coincide el checksum o el tamaño de la grilla, manifest inválido |

Esquemas: `apps/api/app/schemas/`. Con la API corriendo, `npm run contracts` genera los tipos TS.

## La EVA en la respuesta

`POST /routes` y `/routes/compare` describen la EVA completa, en pareja, desde el nodo base y de regreso:

- `start` es el nodo base. Si falta, se usa la `base` de la región.
- `path` es la ida. `distance_km` y `duration_h` cuentan ida y vuelta; `outbound_km`, `outbound_h` y `return_h`
  dan el desglose. Subir de vuelta lo que se bajó de ida tarda más, así que ida y regreso no siempre duran igual.
- `usable_autonomy_h` descuenta la reserva del 20 %. `margin_h` es lo que sobra de esa autonomía.
- `point_of_no_return` es el primer punto desde donde ya no se regresa a tiempo con la autonomía utilizable, usando
  el tiempo real de regreso. En terreno plano coincide con la mitad de esa autonomía.
- `radiation_msv` es la dosis equivalente de fondo durante la EVA. Con `solar_event: true`, `solar_event_mgy` trae la
  dosis absorbida del peor evento observado y aparece una alerta con el tiempo de regreso; los mGy no se suman a los mSv.
- `feasible` es falso si alguna alerta tiene `severity: critical`: consumir la reserva, alejarse más de lo permitido o
  pasar el límite de dosis (`max_dose_msv`, sin valor por defecto).
- `provenance` etiqueta cada cifra y `synthetic_data` avisa si la región es de prueba.

Los valores y sus fuentes están en [supuestos.md](supuestos.md).

## Validación contra el rover

`POST /routes/validate` traza las tres rutas entre el primer y el último punto del recorrido real dentro de la región,
y reporta distancia, desnivel acumulado, proporción de distancias y separación media y máxima. El rover y las rutas se
miden igual, de celda en celda sobre el mismo DEM. Con `synthetic_data: true` el recorrido también es de prueba: esas
cifras sirven para probar el cálculo y no validan nada.

## Modos

Costo por celda = `1 + w_slope·(pendiente/máx)² + w_hazard·hazard + w_inst·(1 − inercia)`, multiplicado por
`(1 − w_sci·minerals)`. Las celdas con pendiente mayor a la máxima son intransitables. Los pesos están en
`apps/api/app/engine/cost.py`.

## Pendientes conocidos

- `pipeline/marsdata/fetch/sources.py`: descarga real de PDS / Mars Trek / SWIM (hoy solo datos sintéticos).
- Conversión de recorridos reales de Curiosity y Perseverance a GeoJSON.
- Textura MOLA del globo y secuencia de Theatre.js para la demo.
- Alertas de clima (REMS / MEDA).
- La pendiente del pipeline usa celdas cuadradas; al trabajar lejos del ecuador conviene reproyectar a una proyección
  local equidistante. La API ya corrige el lado este-oeste de la celda al medir distancias y al trazar rutas.
