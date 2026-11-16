# Martian Route

A multi-layer 3D map of Jezero Crater that plans human walks on Mars by oxygen, risk and safe return to
base, not just by distance.

Project for the NASA Space Apps Challenge 2026, *Interplanetary Survival Guide: Martian Map* challenge. The
explorer picks a start and a destination and gets three routes, Safe, Fast and Science, compared with the
shortest route. Each one comes with its oxygen use, risk, time, radiation dose and point of no return.

![The planner in Jezero Crater: the route from the base to the destination over the CTX relief and orthophoto, with the safe-return map in green, yellow and red](apps/web/public/img/planificador.webp)

## The problem

On a walk on Mars, the limit is not distance but the oxygen the explorer carries in the suit. Between the
base and the destination there are scarps, boulder fields and loose sand. Rovers have lived through it:
Curiosity has had to adapt its routes for years because of rocks and sand (Rankin et al., 2021), and
Perseverance relies on its autonomous navigation to cross Jezero (Verma et al., 2023).

For a person, a short route that climbs a steep slope or crosses rough terrain can use more oxygen than a
detour and leave no margin to get back. Planning a walk means knowing, before leaving, how much oxygen each
segment costs, which areas cannot be crossed and from where there is no longer enough to return.

## What exists and what is missing

We ran a systematic review following the PRISMA 2020 guideline (Page et al., 2021): out of 2,448 records we
included 97 studies.

| Prior work | What it does | What it does not cover |
| --- | --- | --- |
| Minimum metabolic workload traverses (Peña-Asensio et al., 2024) | Computes astronaut routes that minimize effort toward shadowed regions near the lunar south pole | It is for the Moon; no Mars layers or point of no return |
| NaviGATOR (Richardson et al., 2024) | Assigns a metabolic cost per cell and visualizes lunar EVA routes | It is for the Moon; no Martian data |
| CSRM from NASA's Johnson Space Center (Kim et al., 2025) | Plans traverses by metabolic workload; demonstrated on a virtual Jezero | Limited to terrestrial applications by its authors; not checked against a real Mars traverse |
| Rover route metrics (Muñoz et al., 2023) and AutoNav (Verma et al., 2023) | Plan and evaluate rover routes on Mars | They optimize a rover's mobility, not a person's oxygen |
| Data viewers, such as NASA Mars Trek | Publish orbital layers and measure distances and elevation profiles | They do not propose routes or compute their cost for a person |

**The gap:** we found no tool that plans a person's walks on Mars with real data and is checked against a
rover's traverse. Our contribution is not the idea of optimizing by energy, but integrating those pieces for
Mars and validating them.

## Data and what each one is used for

The data is public and comes from several NASA missions. In the Jezero region, every layer is brought to a
common grid of 600 × 600 cells of about 25 m. Every layer and every figure in the app states its provenance:
observed, derived or modeled. Full sources and citations: [docs/creditos.md](docs/creditos.md).

| Layer | Mission or product | Use in the engine |
| --- | --- | --- |
| Relief and slope | CTX terrain model for Mars 2020 (MRO, USGS), 20 m | Slope, ascent and impassable cells |
| Terrain image | CTX orthomosaic for Mars 2020, 6 m | Texture of the 3D map |
| Terrain hazard | NOAH-H classes on HiRISE (Barrett et al., 2022; Wright et al., 2022) | Hazard from 0 to 1 and impassable areas; it classifies 95.4 % of the cells |
| Ground firmness | THEMIS thermal inertia (Mars Odyssey), 100 m | Ground instability |
| Minerals | CRISM mineralogy (MRO) | Science value for the Science mode; being integrated (today only in the test region) |
| Real traverse | Perseverance's path (Mars 2020, JPL MMGIS) | Route validation |
| Radiation | Curiosity RAD in Gale (Hassler et al., 2014; Guo et al., 2021) | Dose per walk, with the value measured in Gale |
| Space weather | NASA DONKI (CCMC, WSA-ENLIL) | Solar ejections forecast for Mars, in the "Mars today" panel |
| Live rover | Perseverance's position and raw images | Rover location and its recent images, in the "Mars today" panel |

Besides `jezero`, the repository has two more regions with the same architecture:

- `jezero_walk`: the area of one walk with the HiRISE terrain model and orthomosaic, at about 3 m per cell.
- `gale`: around Curiosity, with the HiRISE DEM and orthomosaic from the MSL mission. Gale has no NOAH-H,
  so its hazard is derived from the roughness of the relief.

## How it works

- **Walking modes.** Safe gives more weight to slope, hazard and ground instability. Fast prioritizes time.
  Science adds the value of the minerals along the way. The baseline, the minimum-distance route that
  respects the maximum slope, is the reference.
- **Oxygen.** The engine starts from 0.07 kg of O₂ per hour per person on flat ground at 2 km/h (about
  3.5 × 10⁻⁵ kg per meter), the mean of the Apollo lunar walks, and adjusts it by slope (Minetti et al., 2002)
  and terrain. That is the lunar scenario. NASA's suited tests at Mars gravity (3/8 g) give 0.12 to 0.15 kg
  per hour, 1.6 to 2.2 times more: that is the Mars scenario, documented in
  [docs/supuestos.md](docs/supuestos.md). Oxygen is always reported as an interval.
- **Suit limits, editable.** Maximum slope of 20°, 2 km/h on flat ground, 8 h of autonomy with a 20 % reserve
  and 10 km from the base.
- **Point of no return.** Each route marks the point from which the way back no longer fits the plannable
  autonomy.
- **Safe-return map.** It colors in green the areas from which you get back within the autonomy, in yellow
  the ones that require using the reserve and in red the ones you cannot return from.
- **Live data.** The "Mars today" panel queries NASA live: solar ejections reaching Mars (DONKI), and
  Perseverance's position and latest images. If an ejection arrives close to the walk, the app suggests the
  solar event scenario.
- **Architecture.** The heavy work (crops, reprojection and grids) is done offline in the pipeline. The API
  combines the grids by mode and computes the route in seconds with a least-cost path search (Dijkstra), and
  the web draws it in 3D.

Every model parameter, with its source and limits, is in [docs/supuestos.md](docs/supuestos.md).

## Impact

- **Exploration:** supports walk planning and training in Earth analogs.
- **Education:** turns public NASA data into an experience that students and the public can use.
- **Open science:** the code, the raw region data and the assumptions are open, and the method can be
  repeated at other sites, as was already done with Gale.

## Status and limits

**Done:** real Jezero region on a common grid, an engine with three modes, baseline, point of no return,
safe-return map and dose, a 3D viewer with a comparison table and an assumptions panel, and live NASA data.

**Measured:** we compared the planner with Perseverance's traverse using a method fixed before measuring
(HE3, `science/validation/`). The terrain map marks the right zone: Perseverance drove over terrain with a
mean risk of 0.28 against 0.42 for the crater. With 25 m cells it does not predict the rover's exact track
(9 against 8, p = 0.25), a null result we report as is: the rover chooses its path on board about 6 m ahead.
In scenarios on real Jezero, when the short path climbs, the safe route uses 13 to 29 % less oxygen, and on
flat ground it cuts risk by 65 % for 11 to 12 % more oxygen.

**Known limits:** the oxygen cost in the app is the lunar scenario, and the radiation rate was measured in
Gale, not in Jezero.

**Future work:**

- Repeat the validation against Perseverance at HiRISE scale (1 m), where the rover makes its decisions.
- Bring the Mars oxygen scenario into the app and integrate the mineral map on real Jezero.
- Test the viewer with five evaluators from outside the team.
- Add to the DONKI alerts a warning for particle storms measured on Mars.

## Team

Master's in Engineering for Innovation and Technological Development (MIIDT), Universidad Autónoma de
Guerrero, Chilpancingo, Guerrero, Mexico.

| Member | Role |
| --- | --- |
| Marco Tulio Ramirez Reyes | Team lead; layer pipeline, infrastructure and deployment |
| Edgar David Mariano Ruiz | Science and validation |
| Miguel Ángel Florencio Flores | Backend and frontend direction |
| Milton Azael Jiménez Gregorio | Interface components |
| Williams Reyna Pérez | Usability testing, demo and video |
| Jairo A. Hernández | Initial project idea |

The work split per member is in [docs/equipo/](docs/equipo/README.md).

---

## Repository structure

```
apps/web       Next.js + React Three Fiber          → Vercel
apps/api       FastAPI + least-cost route engine    → Render / Railway
pipeline       GDAL/Rasterio, offline               → Cloudflare R2
packages/contracts  TS types generated from the OpenAPI
data/raw       raw files of each region (versioned)
data/regions   pipeline output (not versioned)
```

Architecture, API contract and data format: [docs/arquitectura.md](docs/arquitectura.md).

## Local setup

Requirements: Node 22+, Python 3.11+.

**1. Test data** (synthetic Jezero region in `data/regions/`; regenerate it when a pull changes
`pipeline/`):

```bash
cd pipeline
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"   # macOS/Linux: .venv/bin/pip
.venv/Scripts/marsdata synthetic
```

**2. API** at http://localhost:8000 (docs at `/docs`):

```bash
cd apps/api
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/uvicorn app.main:app --reload
```

The "Mars today" panel queries NASA live (`GET /live`). Get a free key at https://api.nasa.gov and put it in
`apps/api/.env` as `NASA_API_KEY`; without internet, the API uses the copy in `app/live/snapshot.json`. To
refresh that copy before a demo: `.venv/Scripts/python -m app.live` from `apps/api`.

**3. Web** at http://localhost:3000 (run `npm install` again when a pull changes `package-lock.json`):

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
npm run dev:web
```

The landing page is at `/` and the route planner at `/planner`; the landing's fixed button leads there. The
interface opens in English; the ES / EN buttons switch the language.

## Jezero and Gale with real data

`marsdata synthetic` generates a made-up region for the tests. The real regions, `jezero` (CTX, ~25 m per
cell), `jezero_walk` (HiRISE, ~3 m per cell) and `gale` (HiRISE read at 5 m, around Curiosity), are built in
`data/regions-real/`, which is not versioned. Sources and citations: [docs/creditos.md](docs/creditos.md).

**1. Data.** The raw files of each region are already in the repo, in `data/raw/<region>/`, so nothing has to
be downloaded: building is enough.

```bash
cd pipeline
.venv/Scripts/marsdata build --region jezero --out ../data/regions-real
.venv/Scripts/marsdata build --region jezero_walk --out ../data/regions-real
.venv/Scripts/marsdata build --region gale --out ../data/regions-real
```

Without `--out`, `build` replaces the synthetic region in `data/regions/`, which is the one the API tests
expect. Gale has no NOAH-H: its risk layer comes from DEM roughness (see `docs/supuestos.md`). Minerals and ice
do not have a product yet: `build` skips them.

`marsdata fetch --region <region>` is only needed to regenerate the raw files or add a region: it downloads
the CTX DEM and orthophoto in full, and reads only each region's window from THEMIS and HiRISE. NOAH-H is not
downloaded automatically, because its repository blocks automated downloads. The one in the repo is the
mosaic from [doi:10.21954/ou.rd.17121482.v2](https://doi.org/10.21954/ou.rd.17121482.v2), losslessly
recompressed so it fits on GitHub.

**2. API.** In `apps/api/.env`, set `ASSETS_DIR=../../data/regions-real` and restart the API; the web does
not change. To go back to the synthetic one, return to `ASSETS_DIR=../../data/regions`.

## Tests

```bash
cd apps/api && .venv/Scripts/pytest -q
```

```bash
npm run lint:web && npm run typecheck:web
```

## Roles → folders

| Role | Where they work |
|---|---|
| Product and pitch | `docs/`, demo script, `apps/web/lib/theatre.ts` |
| 3D visualization | `apps/web/components/scene/` |
| Frontend and UX | `apps/web/components/ui/`, `apps/web/lib/` |
| Backend and routes | `apps/api/app/engine/`, `apps/api/app/routers/` |
| Geospatial data | `pipeline/marsdata/fetch/`, `pipeline/marsdata/process/` |
| Science and validation | `science/`, weights in `apps/api/app/engine/cost.py`, thresholds in `science.py`, real traverses |

## References

- Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., & Sefton-Nash, E.
  (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results for the ExoMars Rover
  candidate landing sites. *Icarus, 371*, 114701. https://doi.org/10.1016/j.icarus.2021.114701
- Guo, J., Zeitlin, C., Wimmer-Schweingruber, R. F., Hassler, D. M., Ehresmann, B., Rafkin, S., Freiherr von
  Forstner, J. L., Khaksarighiri, S., Liu, W., & Wang, Y. (2021). Radiation environment for future human
  exploration on the surface of Mars: The current understanding based on MSL/RAD dose measurements. *The
  Astronomy and Astrophysics Review, 29*(1), 8. https://doi.org/10.1007/s00159-021-00136-5
- Hassler, D. M., et al. (2014). Mars' surface radiation environment measured with the Mars Science
  Laboratory's Curiosity rover. *Science, 343*(6169), 1244797. https://doi.org/10.1126/science.1244797
- Kim, K. J., Hoffmann, B., Estep, P. N., Kring, D. A., Marshall-Goebel, K. J., & Buckland, D. M. (2025). *A
  consolidated tool for planning and analyzing simulated exploration traverses and associated metabolic
  workload* (ICES-2025-129). https://doi.org/10.32865/2346/102632
- Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and running at
  extreme uphill and downhill slopes. *Journal of Applied Physiology, 93*(3), 1039–1046.
  https://doi.org/10.1152/japplphysiol.01177.2001
- Muñoz, P., Bellutta, P., & R-Moreno, M. D. (2023). Proposing new path-planning metrics for operating rovers on
  Mars. *Scientific Reports, 13*(1), 22256. https://doi.org/10.1038/s41598-023-49144-8
- Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., et al. (2021). The
  PRISMA 2020 statement: An updated guideline for reporting systematic reviews. *BMJ, 372*, n71.
  https://doi.org/10.1136/bmj.n71
- Peña-Asensio, E., Sutherland, J., Tripathi, P., Mason, K., Goodwin, A., Bickel, V. T., & Kring, D. A. (2024).
  Automated astronaut traverses with minimum metabolic workload: Accessing permanently shadowed regions near
  the lunar south pole. *Acta Astronautica, 214*, 324–342. https://doi.org/10.1016/j.actaastro.2023.10.010
- Rankin, A., Maimone, M., Biesiadecki, J., Patel, N., Levine, D., & Toupet, O. (2021). Mars Curiosity rover
  mobility trends during the first 7 years. *Journal of Field Robotics, 38*(5), 759–800.
  https://doi.org/10.1002/rob.22011
- Richardson, E., Hurd, V., Leary, S., Weinberg, A., Bonarrigo, L., Obaid, L., Storvick, E., Panchal, A., Futch,
  N., Graeber, A., & Anderson, A. (2024). NaviGATOR: An informatics-based path planning and visualization tool
  for lunar extravehicular activity. *53rd International Conference on Environmental Systems*.
  https://doi.org/10.32865/2346/99019
- Verma, V., Maimone, M. W., Gaines, D. M., Francis, R., Estlin, T. A., Kuhn, S. R., Rabideau, G. R., Chien,
  S. A., McHenry, M. M., Graser, E. J., Rankin, A. L., & Thiel, E. R. (2023). Autonomous robotics is driving
  Perseverance rover's progress on Mars. *Science Robotics, 8*(80), eadi3099.
  https://doi.org/10.1126/scirobotics.adi3099
- Wright, J., Barrett, A., Fawdon, P., Favaro, E., Balme, M., Woods, M., Karachalios, S., & Gerdes, L. (2022).
  *NOAH-H terrain classifications of Jezero Crater, Mars* [Data set]. The Open University.
  https://doi.org/10.21954/ou.rd.17121482.v2

Project for the NASA Space Apps Challenge 2026. Not endorsed by NASA.
