# API image for Render with the real regions inside it (no R2 needed).
# Build context: the repository root (render.yaml sets it). The first stage builds the regions
# from data/raw with the pipeline; the API image only carries the result and serves it at /assets.

FROM python:3.12-slim AS regions
# The rasterio wheel bundles GDAL but links to the system libexpat.
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
COPY pipeline/pyproject.toml pipeline/
COPY pipeline/marsdata pipeline/marsdata
# Editable: the pipeline finds config/ and data/ relative to its own source folder.
RUN pip install --no-cache-dir -e ./pipeline
COPY pipeline/config pipeline/config
COPY data/raw data/raw
COPY science/validation/noahh_ig_risk.csv science/validation/
COPY M20_traverse_2026-11-12.json MSL_traverse_2026-11-14.json ./
WORKDIR /repo/pipeline
RUN set -e; for r in jezero jezero_walk gale; do marsdata build --region "$r" --out /regions; done
# The planner opens the first region of the index: Jezero, the demo region, goes first.
RUN printf '{"regions": ["jezero", "jezero_walk", "gale"]}' > /regions/index.json

FROM python:3.12-slim
WORKDIR /srv
COPY apps/api/pyproject.toml .
COPY apps/api/app ./app
RUN pip install --no-cache-dir .
COPY --from=regions /regions /srv/regions
# Read-only public API with no cookies: any origin may call it (the Vercel web included).
ENV ASSETS_DIR=/srv/regions PORT=8000 CORS_ORIGINS=*
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
