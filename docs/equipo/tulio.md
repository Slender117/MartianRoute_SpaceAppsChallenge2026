# Tulio · Team lead: layer pipeline, navigation, 3D and infrastructure

**Objective:** OE1 · HE1: registration of 1 cell or less and at least 95 % of the area with data.
**Milestones:** owner of H2, H4 and H5; takes part in H3. **Backup:** Edgar. **Presents** the pitch.

## Scope

Turn the NASA and USGS products into the real Jezero region (grids, textures, traverse and manifest), show
it in 3D with the routes and layers, deploy the app and take it to the frozen demo and the submission. It is
the critical path.

## Folders

- `pipeline/` (`fetch/sources.py`, `process/`, `export.py`, `publish.py`, `config/regions.yaml`)
- `data/raw/` (raw files of each region, versioned) and `data/regions/` (output, not versioned)
- `apps/web/components/scene/` and `apps/web/components/debug/` (3D scene and Leva)
- Deployment configuration (Vercel, Render or Railway, Cloudflare R2)

## Tasks

- [x] Box decided (13 Nov): `[77.316, 18.339, 77.566, 18.590]`, where NOAH-H has data in 95.4 % of the
      cells, with a 600 × 600 grid (~24.8 m per cell). The traverse is cropped to that area (H2)
- [ ] Real DEM cropped and validated as Float32; heightmap and normal map for the 3D scene (H2)
- [ ] Orthophoto, Parente mineral map and THEMIS on the common grid; measure the registration error and the
      % with data for HE1 (H2)
- [ ] NOAH-H layer on the grid with Edgar's class-to-risk table. Protocol cutoff: if it is not ready by the
      end of today, THEMIS is used (H2)
- [ ] Perseverance traverse cropped and with elevation, together with Edgar (H2)
- [ ] Manifest with provenance and the credits file (H2)
- [ ] Stable deployment on Vercel, Render or Railway and R2, with a scheduled ping to `/health` (H3)
- [ ] With the region published, real terrain in 3D with the routes, the baseline and the safe-return
      map (H3)
- [ ] Integrate and freeze the demo; review the submission and judging guidelines and build the submission
      checklist (H4)
- [ ] Record the backup video of the frozen demo with Williams (H4)
- [ ] Upload the submission (H5)

## Per day

| 13 Nov | 14 Nov | 15 Nov |
| --- | --- | --- |
| Box decided, real layers published, NOAH-H cutoff at end of day; review the deployment | Integrate, deploy and freeze the demo; terrain, routes and layers in 3D | Presents and uploads the submission |

## Receives and delivers

- **Receives** from Edgar: the NOAH-H class-to-risk table and help with Perseverance's traverse. From
  Miguel: route geometry, baseline and the safe-return grid for the 3D scene.
- **Delivers** to Miguel: `.npy` grids and manifest.
  To Edgar: the traverse with elevation for the validation.

## Out of scope

- Geospatial processing inside the API: it all goes in the pipeline.
- Combining the cost in the pipeline: the cost is combined in the API.
- Products that are not Jezero DEMs (InSight, Color Hillshade, "Jezero NE Syrtis Midway").
- After H4, merging anything that is not a fix.
