# Martian Route: project context

Interactive layered map and walk (EVA) planner for astronauts on Mars.
Project for the NASA Space Apps Challenge 2026, "Interplanetary Survival Guide: Martian Map" challenge.
Hackathon: 14 and 15 November 2026. Name: Martian Route since 14 November (before that WazeMars,
provisional, and "Ruta Roja" in the deck). Internal names keep the old one: `@wazemars/*` packages,
the `wazemars-assets` bucket, the Theatre project and the `wazemars.lang` key.

The code, comments, API texts and documentation are in English. The interface opens in English and keeps
a Spanish version (ES / EN buttons, `apps/web/lib/i18n.ts`). Identifiers, JSON keys and file names do not
change with the language (`docs/supuestos.md`, `docs/creditos.md` and the `science/validation/` files keep
their Spanish names because code and tests point to them).

## What the challenge asks (summary of the statement)

Create an integrated, layered view of a place or route on Mars, with data from several NASA science
missions, that helps an astronaut plan and carry out a safe Marswalk while doing science. Points the
statement mentions explicitly and the project must cover:

- At least three data types (optical, thermal, spectral, topographic, atmospheric, radiation...).
- Safety first: radiation and space weather, mobility with a suit and load, avoiding large obstacles.
- A route that shows where to walk to meet science goals.
- Hyperlocal scale: Mars Trek already covers the regional and global; the value is in the area of one walk.
- Suggested: ground images (rover photos) so the astronaut knows what they will see on arrival.
- Suggested: start from a concrete science goal and a data-rich place.

## Decisions made (do not reopen without asking the team)

- **Central question:** which walking EVA route maximizes science value without breaking the limits of
  slope, suit autonomy, radiation dose and return to base. A multi-objective problem. The Safe, Fast and
  Science modes are different weights on the same cost function.
- **Demo region:** Jezero Crater (18.4° N, 77.5° E). Gale as the second region in `regions.yaml`. The
  architecture is generic per region.
- **Scenario:** walking EVA, out and back, in pairs, from a fixed base node (habitat or parked pressurized
  rover). Mode with a support rover: optional.
- **Demo science goal:** carbonates of the Jezero delta and the search for biosignatures, with named points
  of interest.
- **Resolution:** region with the CTX DTM (~20 m). Walking zone with the HiRISE DTM reduced to 2 to 4 m per
  cell. There is no 10 cm orbital data; that level comes from rover photos.
- **Stack:** Next.js + React Three Fiber (frontend), FastAPI + NumPy + scikit-image (API),
  Python + Rasterio/GDAL (offline pipeline). Deployment: Vercel, Render or Railway, Cloudflare R2.
  No Unity and no manual 3D modeling.
- **Everything heavy is precomputed** in the pipeline. The API does no geospatial processing: it only
  combines normalized grids and runs the routing. The API image does not need GDAL.
- **The cost is combined in the API**, not in the pipeline, to change modes and weights without reprocessing.
- **Algorithm:** least-cost path search (Dijkstra) on the grid with `skimage.graph.MCP_Geometric`
  (8 neighbors, diagonals with geometric cost). Do not migrate to H3, graphs, Contraction Hierarchies or
  D* Lite unless recomputing becomes slow.
- **Route and time are separate:** the route comes from the cost; time and consumables from the walking
  model (Tobler scaled for the suit).

## Architecture

```
Browser -> apps/web (Next.js + R3F, Vercel) --REST--> apps/api (FastAPI, Render/Railway)
                 |                                           |
                 +-- textures and heightmap --> Cloudflare R2 <-- .npy grids
                                                  ^
                     pipeline (Python + Rasterio/GDAL, offline, before the event)
                                                  ^
                                NASA data: PDS, Mars Trek, USGS, SWIM, MMGIS
```

In development, the API reads `ASSETS_DIR` (disk) and serves `data/regions` at `/assets`.
In production, it reads `ASSETS_URL` (R2).

## Repo structure

```
apps/api/app/engine/     cost, pathfind, consumables, science, constraints, planner
apps/api/app/routers/    health, regions, routes
apps/api/app/schemas/    Pydantic models (the API contract)
apps/api/app/storage/    reading regions from disk or R2, with a cache
apps/api/tests/          conftest, test_engine, test_api
apps/web/components/scene/  Scene, Globe, CameraRig, RegionTerrain, RoutePath, TraverseOverlay
apps/web/components/ui/     SitePanel, LayerPanel, RoutePanel, NavPanel
apps/web/components/debug/  Leva controls
apps/web/lib/            api, geo, store (Zustand), types, theatre
pipeline/config/regions.yaml
pipeline/marsdata/       fetch, process, export, synthetic, publish, run (CLI)
packages/contracts/      TS types generated from the OpenAPI
data/raw/                raw files of each region (versioned: building needs no download)
data/regions/            pipeline output (not versioned)
docs/                    architecture, reports, screenshots
```

## Endpoints

| Method | Path | Function |
| --- | --- | --- |
| GET | `/health` | Service status (also used to wake the server) |
| GET | `/regions` | List of regions |
| GET | `/regions/{id}` | Full manifest of a region |
| GET | `/regions/{id}/traverse/{rover}` | The rover's real traverse as GeoJSON |
| POST | `/routes` | One route in the requested mode |
| POST | `/routes/compare` | The three routes and the baseline at once |
| POST | `/routes/safe-return` | Safe-return map: minutes to return to base per cell |

Errors: 404 nonexistent region; 422 point outside the region, on an impassable slope or no route.

## Cost and consumables model

Cost per cell (`engine/cost.py`):

```
cost = 1 + w_slope*O2_penalty(slope) + w_hazard*hazard + w_instability*(1 - thermal_inertia)
cost *= (1 - w_science*minerals)      # minimum 0.1 per cell
slope > suit maximum -> infinite (impassable)
```

`O2_penalty` (`engine/o2_model.py`, Edgar's model) is the extra round-trip O₂ relative to flat ground from
the curve of Minetti et al. (2002), normalized to 0 on flat ground and 1 at the maximum slope. It replaced
`(slope/max)²`: it is almost linear, so it penalizes moderate slopes more.

| Mode | Slope | Hazard | Instability | Science |
| --- | --- | --- | --- | --- |
| Safe | 4.0 | 4.0 | 2.0 | 0 |
| Fast | 0.5 | 1.0 | 0.3 | 0 |
| Science | 1.5 | 2.0 | 1.0 | 0.8 |
| Baseline | 0 | 0 | 0 | 0 |

The baseline (`baseline`) is the minimum-distance route that respects the maximum slope. It is not a mode
for the astronaut: it is the reference for HE2 and HE3 (`vs_baseline` on each route).

Consumables (`engine/consumables.py`): Tobler scaled to 2 km/h on flat ground with a suit, 3D distance per
segment, duration in hours and sols (1 sol = 24.66 h), reference O₂ 0.07 kg/h (lunar scenario; the Mars
scenario is in `docs/supuestos.md`). Plannable autonomy: the autonomy minus the stricter reserve between
20 % and 30 min. Fixed work `suit.task_h` (0 by default) added to the duration. Point of no return: first
point where what was spent plus the return exceeds the plannable autonomy minus the fixed work. Official O₂
(`o2_interval_kg`): an interval per astronaut with the Minetti curve between two gravity bounds, plus the
fixed work; it does not change the route. Stops: cells with minerals or ice > 0.6, at least 15 points apart.
Alerts: segments above 80 % of the maximum slope, exceeded autonomy and distance to base larger than allowed.

## Mandatory conventions

- **Coordinates:** planetocentric, east longitude, range -180 to 180 across the app. Convert when ingesting
  each product. Mars radius 3,389.5 km. Always check that the Jezero marker falls on the crater in the globe
  texture.
- **CRS in files:** GeoTIFF with the IAU Mars reference system (PROJ, for example `IAU_2015:49900`; check the
  code). GeoJSON is used by convention even though the standard assumes WGS84: document the CRS in the
  manifest.
- **Units:** meters, degrees, hours, kg. Show sols next to hours.
- **Provenance:** every displayed layer and figure carries an `observed`, `derived` or `modeled` label. Every
  numeric model parameter (maximum slope, O₂ use, radiation rate) is documented with its source in `docs/`
  and in the app's assumptions panel.
- **Region manifest:** semantic dataset version, ID of each source product, pipeline commit and checksum per
  file.
- **Credits:** every downloaded dataset is recorded in the credits file in APA 7 format
  (`Author. (Year). Title (ID) [Data set]. Publisher. DOI or URL`).
- **Language:** new code, comments, API texts and docs in English. Interface texts go in both languages in
  `apps/web/lib/i18n.ts`; alerts carry `code` and `values` so the web can translate them.
- **Text on Windows:** always `encoding="utf-8"` when reading or writing text. Use `StrEnum` (Python 3.11+).

## Working rules

- Do not invent scientific figures. If a value is missing, use a `[__]` marker, leave it as an explicit
  assumption and say so.
- Do not add geospatial processing to the API: it goes in the pipeline.
- Any change to weights or to `synthetic.py` must keep the test that the three modes give different routes in
  the demo scenario.
- Do not use the NASA logo in the app or suggest NASA endorsement.
- `@theatre/studio` is AGPL 3.0: development only, never in the public build. `@theatre/core` is Apache 2.0.
- Leva is hidden by default; it only shows with `?debug` in the URL.
- Before calling something done: `pytest`, `ruff check` and `ruff format --check` (API and pipeline);
  `eslint`, `tsc --noEmit` and `next build` (web).
- In Git Bash on Windows, avoid long heredoc scripts: write each file separately.

## Known problems (do not repeat)

- drei's `<Html>` fails with React 19 ("synchronously unmount a root"). Labels go in HTML panels outside the
  `<Canvas>`.
- `MeshBasicMaterial` does not support `displacementMap`: use `MeshLambertMaterial` for the layers.
- `OrbitControls` keeps its own state: register it with `makeDefault` and sync its target on every view
  change.
- The browser reads the 16-bit heightmap as 8-bit. With real relief, steps show up: move to a `Float32Array`
  (raw `.bin`) or a glTF mesh.
- Render and Railway sleep on the free plan: call `GET /health` when the page loads and schedule a ping on
  event day.

## Priorities (in order)

Essential to meet the statement:

1. Fix the coordinate convention and validate the Jezero marker.
2. Real Jezero DEM (USGS Mars 2020 navigation mosaics: CTX DTM and HiRISE orthomosaic, already aligned) and
   implement `fetch/sources.py` with exact products.
3. Perseverance's real traverse (JPL MMGIS) to GeoJSON, with elevation sampled from the DEM.
4. Make the three modes differ in the demo region: fixed demo points, the three lines visible at once and
   the difference against the safe route in the table.
5. Radiation dose (Curiosity RAD reference, ~0.67 mSv/day; check) by EVA duration, a solar event scenario
   and a 20 % autonomy reserve.
6. Provenance labels and an "Assumptions and limits" panel.
7. Validation metrics against Perseverance: distance, cumulative ascent, mean separation.

Differentiators if there is time:

8. Walking zone with HiRISE (third zoom level in the same scene).
9. Line of sight to the base (viewshed from the DEM) and a communication alert.
10. Perseverance Navcam or Mastcam-Z photos per stop (store URLs in the manifest, not images).
11. A `mission` block in `regions.yaml`: goal, named points of interest, relevance table per mineral.
    Science value = relevance × novelty × confidence.
12. Departure time: weather alerts with typical MEDA values per local hour and shadows from the DEM.
13. A "report obstacle" button: block cells and recompute.
14. MOLA globe texture (equirectangular 4096 × 2048, USGS Astropedia) as `map` and `bumpMap`.
15. Approach point per science goal: the nearest walkable cell with an acceptable slope.

Out of scope for the hackathon: GPS-free localization, D* Lite, MDP, stochastic simulation, export to
Unreal, Gazebo or ROS.

## Data and sources

| Layer | Mission and instrument | Source |
| --- | --- | --- |
| Global elevation | MGS MOLA | USGS Astropedia, PDS |
| Local elevation | MRO CTX and HiRISE (DTM) | Mars 2020 products at USGS, PDS, HiRISE |
| Optical image | MRO HiRISE, CTX | Mars Trek (WMTS), PDS |
| Thermal inertia | Mars Odyssey THEMIS | Global mosaic |
| Minerals | MRO CRISM | PDS; if it gets complicated, a published Jezero mineral map with a citation |
| Subsurface ice | SWIM | Covers northern mid-latitudes: check coverage in Jezero |
| Weather | Perseverance MEDA, Curiosity REMS | PDS Atmospheres |
| Radiation | Curiosity RAD | Hassler et al., 2014 |
| Traverses | Perseverance, Curiosity | JPL MMGIS |
| Names | IAU/USGS | Gazetteer of Planetary Nomenclature |
| Martian time | NASA GISS Mars24 | Algorithm |

## Commands

Requirements: Node 22+, Python 3.11+. On Windows `.venv/Scripts/`; on macOS and Linux `.venv/bin/`.

```bash
# Test data
cd pipeline && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]" && .venv/Scripts/marsdata synthetic

# API at http://localhost:8000 (docs at /docs)
cd apps/api && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
cp .env.example .env && .venv/Scripts/uvicorn app.main:app --reload

# Web at http://localhost:3000
npm install && cp apps/web/.env.example apps/web/.env.local && npm run dev:web
```

Pipeline commands: `marsdata synthetic | fetch | build | publish`.

## Glossary

- **EVA / Marswalk:** extravehicular activity on foot on the surface.
- **Walkback:** Apollo rule: do not go farther than you can walk back if the vehicle fails. Here it equals the
  maximum distance to base and the point of no return.
- **Sol:** Martian day, 24.66 h.
- **DTM/DEM:** digital elevation model.
- **Cost grid:** raster with the cost of crossing each cell, the input to routing.
- **Tau:** atmospheric opacity due to dust.

## Open questions

- Real values of suit autonomy, maximum walkable slope and O₂ use (open sources).
- Exact Mars CRS code in PROJ that the pipeline will use.
- SWIM coverage in Jezero.
- Judging criteria and submission requirements (guidelines published on 13 November), including the AI use
  statement.
