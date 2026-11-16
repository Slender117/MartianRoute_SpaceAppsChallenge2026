# Imagen de la API con las regiones reales ya construidas.
#
# Se construye desde la raíz del repositorio, porque necesita pipeline/, data/raw/, la tabla de riesgo
# de science/validation/ y los recorridos de los rovers:
#   docker build -f apps/api/Dockerfile -t martian-route-api .
#
# Etapa 1 (regions): instala el pipeline (rasterio trae GDAL en sus wheels) y construye cada región con
# los crudos versionados en data/raw/. Etapa 2: la API, sin GDAL, con las regiones copiadas en
# /srv/regions; la API las sirve en /assets.

FROM python:3.12-slim AS regions

# El GDAL de los wheels de rasterio enlaza libexpat, que la imagen slim no trae.
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pipeline/pyproject.toml pipeline/
COPY pipeline/marsdata pipeline/marsdata
COPY pipeline/config pipeline/config
# Editable: marsdata busca data/raw/ y config/ relativos a su propio código.
RUN pip install --no-cache-dir -e pipeline

COPY data/raw data/raw
# regions.yaml nombra estos archivos relativos a la raíz: la tabla clase a riesgo de NOAH-H y los
# recorridos de Perseverance y Curiosity.
COPY science/validation science/validation
COPY *_traverse_*.json ./
ARG REGIONS="jezero jezero_walk gale"
RUN for r in $REGIONS; do marsdata build --region "$r" --out /regions || exit 1; done


FROM python:3.12-slim

WORKDIR /srv
COPY apps/api/pyproject.toml .
COPY apps/api/app ./app
RUN pip install --no-cache-dir .

COPY --from=regions /regions /srv/regions

ENV ASSETS_DIR=/srv/regions
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
