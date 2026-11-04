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
