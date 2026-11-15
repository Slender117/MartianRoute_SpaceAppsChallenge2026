# Martian Route

Mapa interactivo por capas y planificador de caminatas para los primeros exploradores humanos de Marte.
NASA Space Apps Challenge 2026: *Interplanetary Survival Guide: Martian Map*.

```
apps/web       Next.js + React Three Fiber  → Vercel
apps/api       FastAPI + motor de rutas A*  → Render / Railway
pipeline       GDAL/Rasterio, offline       → Cloudflare R2
packages/contracts  tipos TS generados del OpenAPI
data/raw       crudos de cada región (sí se versionan)
data/regions   salida del pipeline (no se versiona)
```

Arquitectura, contrato de la API y formato de datos: [docs/arquitectura.md](docs/arquitectura.md).

## Arranque local

Requisitos: Node 22+, Python 3.11+.

**1. Datos de prueba** (región sintética de Jezero en `data/regions/`; vuelve a generarla cuando un pull cambie
`pipeline/`):

```bash
cd pipeline
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"   # macOS/Linux: .venv/bin/pip
.venv/Scripts/marsdata synthetic
```

**2. API** en http://localhost:8000 (docs en `/docs`):

```bash
cd apps/api
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/uvicorn app.main:app --reload
```

El panel "Marte hoy" consulta a NASA en vivo (`GET /live`). Saca una llave gratuita en https://api.nasa.gov y
ponla en `apps/api/.env` como `NASA_API_KEY`; sin internet, la API usa la copia de `app/live/snapshot.json`.
Para actualizar esa copia antes de una demo: `.venv/Scripts/python -m app.live` desde `apps/api`.

**3. Web** en http://localhost:3000 (repite `npm install` cuando un pull cambie `package-lock.json`):

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
npm run dev:web
```

La portada está en `/` y el planificador de rutas en `/planner` (el botón **Start** de la portada lleva ahí).

## Jezero y Gale con datos reales

`marsdata synthetic` genera una región inventada para las pruebas. Las regiones reales, `jezero` (CTX, ~25 m por
celda), `jezero_walk` (HiRISE, ~3 m por celda) y `gale` (HiRISE leído a 5 m, alrededor de Curiosity), se construyen
en `data/regions-real/`, que no se versiona. Fuentes y citas: [docs/creditos.md](docs/creditos.md).

**1. Datos.** Los archivos crudos de cada región ya vienen en el repo, en `data/raw/<región>/`, así que no hay que
descargar nada: basta con construir.

```bash
cd pipeline
.venv/Scripts/marsdata build --region jezero --out ../data/regions-real
.venv/Scripts/marsdata build --region jezero_walk --out ../data/regions-real
.venv/Scripts/marsdata build --region gale --out ../data/regions-real
```

Sin `--out`, `build` reemplaza la región sintética de `data/regions/`, que es la que esperan las pruebas de la API.
Gale no tiene NOAH-H: su capa de riesgo sale de la rugosidad del DEM (ver `docs/supuestos.md`). Minerales e hielo
todavía no tienen producto: `build` los omite.

`marsdata fetch --region <región>` solo hace falta para regenerar los crudos o agregar una región: baja completos el
DEM y la ortofoto de CTX, y de THEMIS y HiRISE lee solo la ventana de cada región. NOAH-H no se descarga solo,
porque su repositorio bloquea las descargas automáticas. El del repo es el mosaico de
[doi:10.21954/ou.rd.17121482.v2](https://doi.org/10.21954/ou.rd.17121482.v2) recomprimido sin pérdida, para que
quepa en GitHub.

**2. API.** En `apps/api/.env`, pon `ASSETS_DIR=../../data/regions-real` y reinicia la API; la web no cambia. Para
volver a la sintética, regresa a `ASSETS_DIR=../../data/regions`.

## Pruebas

```bash
cd apps/api && .venv/Scripts/pytest -q
```

```bash
npm run lint:web && npm run typecheck:web
```

## Roles → carpetas

| Rol | Dónde trabaja |
|---|---|
| Producto y pitch | `docs/`, guion de la demo, `apps/web/lib/theatre.ts` |
| Visualización 3D | `apps/web/components/scene/` |
| Frontend y UX | `apps/web/components/ui/`, `apps/web/lib/` |
| Backend y rutas | `apps/api/app/engine/`, `apps/api/app/routers/` |
| Datos geoespaciales | `pipeline/marsdata/fetch/`, `pipeline/marsdata/process/` |
| Ciencia y validación | pesos en `apps/api/app/engine/cost.py`, umbrales en `science.py`, recorridos reales |
