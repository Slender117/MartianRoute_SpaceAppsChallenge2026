# Architecture

## Flow of a route

1. The explorer picks start, destination and mode on the web (click on the terrain).
2. Next.js sends `POST /routes/compare` to the API.
3. FastAPI loads (and caches) the region grids from disk or R2.
4. `engine/cost.py` combines the layers with the mode weights; `engine/pathfind.py` runs a least-cost path
   search (Dijkstra, scikit-image's `MCP_Geometric`).
5. `engine/planner.py` computes the whole EVA (out, and back along the same path): time, O₂ (a figure by time
   and an interval by slope), dose, point of no return, stops, alerts, and the difference against the safe
   route and against the baseline.
6. The web draws the three routes and the baseline on the terrain, the comparison table and the detail of
   the active one.

Everything heavy (reprojection, slopes, normalization, textures) is done **offline** in the pipeline.

## Region format

```
data/regions/                      (in production: R2, prefix regions/)
├── index.json                     {"regions": ["jezero", ...]}
└── jezero/
    ├── manifest.json              see below
    ├── dem.npy                    float32, meters
    ├── slope.npy                  float32, degrees
    ├── layers/{hazard,thermal_inertia,ice,minerals}.npy   float32 0–1
    ├── heightmap.png              16-bit, normalized DEM (3D terrain)
    ├── textures/<layer>.png       RGBA, overlays
    └── traverses/<rover>.geojson  real traverse
```

Conventions: equirectangular grid over the bbox, row 0 = maximum latitude, column 0 = minimum longitude,
east-positive longitudes from -180 to 180. All layers share the same shape.

The manifest has `bbox`, `shape`, `resolution_m`, `elevation_range`, `base`, `layers` and `traverses`, plus:

| Field | Content |
|---|---|
| `dataset_version` | semantic version of the dataset (`regions.yaml`) |
| `pipeline_commit` | pipeline commit; `null` if the folder is not in a repository |
| `crs` | CRS of grids and traverses, as a PROJ string |
| `synthetic` | `true` if the data is test data |
| `layer_meta` | per layer, `provenance` (`observed`, `derived`, `modeled`) and `source` (product ID) |
| `checksums` | SHA-256 per file; the API checks them on read and answers 503 if they do not match |
| `demo` | demo scenario points, if the region has one |

| Layer | Source | Meaning of 1.0 |
|---|---|---|
| hazard | HiRISE / CTX | many obstacles |
| thermal_inertia | THEMIS | firm rock (0 = loose sand) |
| ice | SWIM | probable shallow ice |
| minerals | CRISM | high science value |

## Proposed contract for the real data (to be agreed)

Proposal from Tulio (pipeline) to Miguel (schemas) and the 3D scene, from 13 November. Everything is
**additive and optional**: each new field has a default value, so the current API and web keep working while
each one adopts it. The example values are illustrative; `[__]` marks what is still to be defined.

### 3D terrain files

`assets` block in the manifest:

```json
"assets": {
  "heightmap": { "path": "heightmap.bin", "dtype": "float32", "byte_order": "little",
                 "shape": [600, 600], "row0": "north" },
  "normal_map": { "path": "textures/normal.png", "space": "object", "exaggeration": "[__]" },
  "ortho": { "path": "textures/ortho.jpg", "size": [2400, 2400],
             "provenance": "observed", "source": "[__] CTX orthomosaic ID" }
}
```

- `heightmap.bin`: heights in meters, not normalized; the range is in `elevation_range`.
- `exaggeration`: the vertical exaggeration the normal map was computed with. The scene uses it as the
  default, because if it does not match the mesh the lighting comes out wrong. The 3D scene sets it.
- `heightmap.png` stays until the scene loads the `.bin`; then it is removed.

### Quality per layer (HE1)

Three new fields in each `layer_meta` entry:

| Field | Content |
|---|---|
| `coverage` | fraction of cells with data before filling gaps (0 to 1) |
| `registration_cells` | offset measured against the orthophoto, in cells; `null` if not measured |
| `native_resolution_m` | resolution of the source product, in meters |

```json
"hazard": { "provenance": "modeled",
            "source": "Wright et al. (2022), NOAH-H IG, doi:10.21954/ou.rd.17121482.v2",
            "coverage": 0.97, "registration_cells": 0.6, "native_resolution_m": "[__]" }
```

With this, the HE1 report (registration of 1 cell or less and at least 95 % with data) comes from the
manifest.

### DEM gaps

`"masks": { "no_data": "layers/no_data.npy" }`: `uint8` with the grid shape, 1 where the original DEM had no
data. The DEM is filled by interpolation only so the mesh is continuous, and the API treats those cells as
impassable, like an excessive slope. That way "no data" is not mixed with "dangerous".

### Impassable fraction

`layers/impassable_fraction.npy`, float32 from 0 to 1: the part of each cell covered by NOAH-H large ripples,
which Barrett et al. (2022) consider never traversable. `hazard` is a per-cell average and is not enough: a
cell with 40 % large ripples would stay walkable. The API blocks the cell if it exceeds a threshold (`[__]`,
no source yet). It has to be added to `OPTIONAL_LAYERS`; if it is missing, it is 0 and blocks nothing.

### Slope

`slope.npy` changes meaning: it becomes the 90th percentile of the slope computed on the 20 m DEM inside each
cell, instead of the slope of the already reduced DEM, which smooths it and makes the 20° limit permissive.
It is documented with `"slope_method": "p90_native_20m"`. With real data more cells are expected to be
blocked.

### Cell size

`"cell_size_m": [north_south, east_west]`, for example `[28.6, 26.7]` in Jezero. The API already corrects the
east-west side on its own; this is for the normal map and the scene proportions.

### Traverses

- `traverses/<rover>.geojson` is still a `LineString`, with `[lon, lat, elev_m]` coordinates (elevation from
  `dem.npy`) and, in `properties`, `sol_range: [min, max]` and `elevation_source: "dem.npy"`. The API already
  reads only the first two values; on the web, `types.ts` becomes `[number, number, number?][]` and
  `TraverseOverlay` uses the elevation instead of drawing at the maximum height.
- `traverses/<rover>_sols.geojson`: a `FeatureCollection` with one segment per sol (`properties.sol`), for
  Edgar's validation. It does not go to the endpoint.

### Credits

`"credits": ["Author. (Year). Title (ID) [Data set]. Publisher. DOI or URL"]`: the APA 7 list of the region's
products, so the assumptions panel can show it.

### Open decisions

| Topic | Proposal | Alternative | Who decides |
|---|---|---|---|
| DEM gaps | `no_data` mask | fill and mark `hazard = 1` | Miguel and Tulio |
| `impassable_fraction` threshold | constant in the API with `[__]` | parameter in `SuitLimits` | Miguel and Edgar |
| `slope_method` | 90th percentile | maximum (stricter, may close narrow passes) | Miguel and Edgar |
| Removing `heightmap.png` | when the scene loads the `.bin` | | Tulio |
| `exaggeration` and shading | normal map with a fixed value | flat shading | Tulio |

Order: Miguel adds the optional fields to `schemas/region.py`, `lib/types.ts` and `OPTIONAL_LAYERS`; the
pipeline generates them first in `marsdata synthetic` so the web can test them, and then with real data in
`marsdata build`.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | status |
| GET | `/regions` | summary list |
| GET | `/regions/{id}` | manifest |
| GET | `/regions/{id}/traverse/{rover}` | real traverse (GeoJSON) |
| POST | `/routes` | one route (`mode`: safe, fast, science or baseline) |
| POST | `/routes/compare` | the three modes and the baseline; each with `vs_safe` and `vs_baseline` |
| POST | `/routes/validate` | metrics of the three modes and the baseline against a rover's traverse |
| POST | `/routes/safe-return` | safe-return map: minutes to walk back to base from each cell |
| GET | `/assumptions` | model parameters with their source, and known limits (English by default, `?lang=es` for Spanish) |
| GET | `/live?region=` | Mars today: solar ejection arrivals at Mars (DONKI), Perseverance's position (MMGIS) and its latest images |
| GET | `/assets/...` | development only: serves `data/regions` |

Errors, always with the reason in `detail` (in English):

| Code | When |
|---|---|
| 404 | region or traverse does not exist |
| 422 | point outside the region or the longitude convention, impassable slope, start equal to destination, no route |
| 503 | missing or inconsistent data: a file is missing, the checksum or grid size does not match, invalid manifest |

Schemas: `apps/api/app/schemas/`. With the API running, `npm run contracts` generates the TS types.

## Language

The API texts are in English. Alerts also carry `code` and `values`, so the web builds their text in English or
Spanish without asking the API again; `/assumptions` serves both languages. The web opens in English and the
ES / EN buttons switch the language (`apps/web/lib/i18n.ts`). Data names that come from the regions (labels,
terrain classes) are translated both ways by the web, so older Spanish data and newer English data both work.

## Live NASA data (`/live`)

`apps/api/app/live/` queries three public NASA sources while the API runs:

| Source | What it gives | Label |
|---|---|---|
| CCMC's DONKI (`api.nasa.gov/DONKI/WSAEnlilSimulations`, last 30 days) | Forecast arrivals at Mars of coronal mass ejections; for each ejection the newest simulation is kept | modeled |
| JPL's MMGIS (`M20_waypoints.json`) | Perseverance's last located point: sol, site/drive, lat/lon, odometry | observed |
| Perseverance raw images (`mars.nasa.gov/rss/api/?feed=raw_images`) | Latest images, one per camera | observed |

- Each source is requested at most once every 30 min. If NASA does not answer, the last good response of that
  run is used and, if there is none, the copy in `apps/api/app/live/snapshot.json`. Each block has `status`
  (`live` or `snapshot`), `fetched_at` and `error`, so the interface says when the data is from.
- `python -m app.live` (from `apps/api`, with internet) refreshes the copy before an offline demo.
- `NASA_API_KEY` in `apps/api/.env`: free key from api.nasa.gov. `DEMO_KEY` works for testing, but runs out
  after a few requests per hour. `LIVE_DATA=false` uses only the copy.
- The solar alert turns on from 72 h before to 48 h after a forecast arrival at Mars, and only suggests turning
  on the solar event scenario (`solar_event`). The tests simulate NASA and never go to the internet.
- Discarded: Perseverance's weather (`feed=weather&category=mars2020`) stopped updating in April 2024,
  Curiosity's is from Gale and months behind, and the Mars Rover Photos API is retired.

## The EVA in the response

`POST /routes` and `/routes/compare` describe the whole EVA, in pairs, from the base node and back:

- `start` is the base node. If it is missing, the region's `base` is used.
- `path` is the way out. `distance_km` and `duration_h` count out and back; `outbound_km`, `outbound_h` and
  `return_h` give the breakdown. Climbing back up what was walked down takes longer, so out and back do not
  always take the same time.
- `usable_autonomy_h` is the plannable autonomy: the autonomy minus the stricter reserve between 20 % and
  30 min (with 8 h the 20 % rules). `margin_h` is what is left of that autonomy.
- `duration_h` adds the fixed work `suit.task_h` (stops and sampling at the destination; 0 by default, no
  source).
- `point_of_no_return` is the first outbound point where the time spent plus the real return exceeds the
  plannable autonomy minus the fixed work. `point_of_no_return_km` says at which outbound kilometer it falls.
  On flat ground it matches half of that budget.
- `o2_interval_kg` is the official O₂ figure: the walk with the Minetti curve, as a `low_kg`–`high_kg`
  interval per astronaut, plus the fixed work at the hourly rate. `o2_estimate_kg` (rate × duration) stays
  only as a reference and is not shown in the interface.
- `radiation_msv` is the background dose equivalent during the EVA. With `solar_event: true`,
  `solar_event_mgy` carries the absorbed dose of the worst observed event and an alert appears with the return
  time; mGy are not added to mSv.
- `feasible` is false if any alert has `severity: critical`: using the reserve, going farther than allowed or
  exceeding the dose limit (`max_dose_msv`, no default).
- `provenance` labels each figure and `synthetic_data` warns if the region is test data.

The values and their sources are in [supuestos.md](supuestos.md).

## Validation against the rover

`POST /routes/validate` draws the three routes between the first and last point of the real traverse inside
the region, and reports distance, cumulative ascent, distance ratio and mean and maximum separation. The rover
and the routes are measured the same way, cell by cell on the same DEM. With `synthetic_data: true` the
traverse is also test data: those figures test the calculation and validate nothing.

The pre-registered HE3 test (`science/validation/he3.py`) uses the same engine on real Jezero; its result is
in `science/validation/he3_resultados.md`.

## Modes

Cost per cell = `1 + w_slope·O2_penalty(slope) + w_hazard·hazard + w_inst·(1 − inertia)`, multiplied by
`(1 − w_sci·minerals)`. Cells with a slope above the maximum are impassable. The weights are in
`apps/api/app/engine/cost.py`.

`O2_penalty` comes from `apps/api/app/engine/o2_model.py` (Edgar's model, `science/model/eva_cost.py`): the
extra round-trip O₂ relative to flat ground according to Minetti et al. (2002), normalized to 0 on flat ground
and 1 at the maximum slope. Gravity cancels in that normalization, so it only changes the reported O₂, not the
route.

The **baseline** (`baseline`) uses all weights at 0: it is the minimum-distance route that respects the
maximum slope. `POST /routes/compare` returns it with the three modes, and each route has `vs_safe` and
`vs_baseline`.

Each route has `o2_interval_kg` (`low_kg`, `high_kg`): O₂ per astronaut for the whole EVA according to the
slope of each segment, between the low bound (flat-ground cost does not change with gravity) and the high one
(it changes in proportion).

## Safe-return map

`POST /routes/safe-return` runs a single Dijkstra from the base (`MCP_Geometric.find_costs`) over the time per
meter of each cell and returns the minutes to walk back from every cell (uint16 in base64, north row first;
65535 = no return). To make the cost symmetric, each cell uses the slower of climbing and descending its
slope: the time is a pessimistic bound. It has two thresholds to color the map: `planned_limit_min` (out,
fixed work and return within the plannable autonomy) and `total_limit_min` (the same using the whole autonomy,
reserve included), and the background dose of an EVA that uses the whole plannable autonomy. The three map
zones are: plannable return, return only by using the reserve, and no return even with the full autonomy.

## Known pending work

- Mineral (CRISM) and ice (SWIM) layers on the real regions.
- Theatre.js sequence for the demo and the globe's MOLA texture.
- Weather alerts (REMS / MEDA).
- The pipeline slope uses square cells; far from the equator it is better to reproject to a local
  equidistant projection. The API already corrects the east-west side of the cell when measuring distances
  and drawing routes.
