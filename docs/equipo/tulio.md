# Tulio · Pipeline de capas, navegación e infraestructura

**Objetivo:** OE1 · HE1: corregistro de 1 celda o menos y al menos 95 % de la zona con dato.
**Hitos:** responsable de H2, H4 y H5. **Respaldo:** Edgar. **Presenta** el pitch.

## Alcance

Convertir los productos de NASA y USGS en la región de Jezero real (grillas, texturas, recorrido y
manifest), desplegar la app y llevarla hasta la demo congelada y la entrega. Es el camino crítico.

## Carpetas

- `pipeline/` (`fetch/sources.py`, `process/`, `export.py`, `publish.py`, `config/regions.yaml`)
- `data/regions/` (salida, no se versiona)
- Configuración de despliegue (Vercel, Render o Railway, Cloudflare R2)

## Tareas

- [x] Recuadro decidido (13 nov): `[77.316, 18.339, 77.566, 18.590]`, donde NOAH-H tiene dato en el
      95.4 % de las celdas, con grilla de 600 × 600 (~24.8 m por celda). El recorrido se recorta a
      esa zona (H2)
- [ ] DEM real recortado y validado como Float32; heightmap y normal map para Jairo (H2)
- [ ] Ortofoto, mapa mineral de Parente y THEMIS en la grilla común; medir el error de corregistro y
      el % con dato para HE1 (H2)
- [ ] Capa NOAH-H en la grilla con la tabla clase a riesgo de Edgar. Corte del protocolo: si al cierre
      de hoy no está, se usa THEMIS (H2)
- [ ] Recorrido de Perseverance recortado y con elevación, junto con Edgar (H2)
- [ ] Manifest con procedencia y archivo de créditos (H2)
- [ ] Despliegue estable en Vercel, Render o Railway y R2, con ping programado a `/health` (H3)
- [ ] Con la región publicada, apoyar a Jairo en 3D (H3)
- [ ] Integrar y congelar la demo; revisar las guías de entrega y evaluación y armar la lista de entrega (H4)
- [ ] Grabar con Williams el video de respaldo de la demo congelada (H4)
- [ ] Subir la entrega (H5)

## Por día

| 13 nov | 14 nov | 15 nov |
| --- | --- | --- |
| Recuadro decidido, capas reales publicadas, corte de NOAH-H al cierre; revisar el despliegue | Integrar, desplegar y congelar la demo; apoyar a Jairo en 3D | Presenta y sube la entrega |

## Recibe y entrega

- **Recibe** de Edgar: tabla clase a riesgo de NOAH-H y apoyo con el recorrido de Perseverance.
- **Entrega** a Jairo: heightmap Float32, ortofoto y normal map. A Miguel: grillas `.npy` y manifest.
  A Edgar: recorrido con elevación para la validación.

## Fuera de alcance

- Procesamiento geoespacial dentro de la API: todo va en el pipeline.
- Combinar el costo en el pipeline: el costo se combina en la API.
- Productos que no son DEM de Jezero (InSight, Color Hillshade, "Jezero NE Syrtis Midway").
- Después de H4, fusionar algo que no sea una corrección.
