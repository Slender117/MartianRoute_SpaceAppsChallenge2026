# WazeMars

Mapa interactivo por capas y planificador de caminatas para los primeros exploradores humanos de Marte.
NASA Space Apps Challenge 2026: *Interplanetary Survival Guide: Martian Map*.

```
apps/web       Next.js + React Three Fiber  → Vercel
apps/api       FastAPI + motor de rutas A*  → Render / Railway
pipeline       GDAL/Rasterio, offline       → Cloudflare R2
packages/contracts  tipos TS generados del OpenAPI
data/regions   salida del pipeline (no se versiona)
```

Arquitectura, contrato de la API y formato de datos: [docs/arquitectura.md](docs/arquitectura.md).

## Arranque local

Requisitos: Node 22+, Python 3.11+.

**1. Datos de prueba** (región sintética de Jezero en `data/regions/`):

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

**3. Web** en http://localhost:3000:

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
npm run dev:web
```

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
