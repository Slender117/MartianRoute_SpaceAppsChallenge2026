# Data credits

Every product the pipeline downloads is recorded here in APA 7 format, with its local file and the page it
came from. When a page asks to cite the authors, the publication that describes the product is included too.

The files of each region are versioned in `data/raw/<region>/` with the name shown here, so the regions can
be built without downloading anything. They are redistributed with their citation.

## Jezero

### Elevation: 20 m CTX DTM

- File: `JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic
- Download: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif
- Float32 in meters, equirectangular on a 3,396,190 m sphere, controlled to MOLA and aligned to the HRSC
  DTM.

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation CTX DTM mosaic*
(JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0) [Data set]. U.S. Geological
Survey. https://doi.org/10.5066/P906QQT8

### Image: 6 m CTX orthomosaic

- File: `JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_context_camera_orthorectified_image_mosaic
- Download: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif
  (also available in NASA Mars Trek)
- 8-bit grayscale. It is the map of the Mars 2020 lander vision system (LVS), orthorectified with the DTM
  above. Mean horizontal offset between the CTX images that make it up: 9.6 m.

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation Context Camera
orthorectified image mosaic* (JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0) [Data set]. U.S.
Geological Survey. https://doi.org/10.5066/P9GV1ND3

### Publication of the two products above

Fergason, R. L., Hare, T. M., Mayer, D. P., Galuszka, D. M., Redding, B. L., Smith, E. D., Shinaman,
J. R., Cheng, Y., & Otero, R. E. (2020). *Mars 2020 Terrain Relative Navigation flight product
generation: Digital terrain model and orthorectified image mosaics* [Abstract 2020]. 51st Lunar and
Planetary Science Conference. https://www.hou.usra.edu/meetings/lpsc2020/pdf/2020.pdf

### Thermal inertia: quantitative THEMIS at 100 m

- File: `THEMIS_TI_Mosaic_Quant_00N060E_100mpp_jezero.tif`, a Jezero crop (the region bbox plus 0.05° per
  side) read by window from the remote cube, without downloading the full 2.5 GB tile.
- Page: https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_00n060e_100mpp
- Origin: https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.cub
- Float32 in J m⁻² K⁻¹ s⁻½, equirectangular on a 3,396,190 m sphere. Absolute accuracy ~20 % and relative
  ~10 % within an image (according to the page). No DOI.

USGS Astrogeology Science Center, Arizona State University Mars Space Flight Facility, & NASA Mars Data
Analysis Program. (2014). *THEMIS thermal inertia mosaic quantitative 00N060E 100mpp* [Data set]. U.S.
Geological Survey. https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_00n060e_100mpp

## Jezero, walking zone (`jezero_walk`)

Window crops (the region bbox plus 0.003° per side) read from the remote files, without downloading the full
mosaics. The thermal inertia is the same THEMIS product as above, cropped to this zone.

### Elevation: 1 m HiRISE DTM

- File: `JEZ_hirise_soc_006_DTM_1m_jezero_walk.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic
- Origin: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif
  (1.8 GB in full)

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation HiRISE DTM mosaic*
(JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40) [Data set]. U.S.
Geological Survey. https://doi.org/10.5066/P9REJ9JN

### Image: 25 cm HiRISE orthomosaic

- File: `JEZ_hirise_soc_006_orthoMosaic_25cm_jezero_walk.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_orthorectified_image_mosaic
- Origin: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first.tif
  (6.9 GB in full)

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation HiRISE orthorectified
image mosaic* (JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first) [Data set]. U.S. Geological
Survey. https://doi.org/10.5066/P9QJDP48

## Terrain risk: NOAH-H (`jezero` and `jezero_walk` regions)

- File: `Jezero_NOAHH_mosaic_IG.tif` (five interpretive groups, nodata 127), extracted from
  `NOAH-H_mosaics/Intrepretative_groups/` in the .zip. Next to it, `Jezero_NOAHH_readme.txt` and the color
  table.
- Page: https://ordo.open.ac.uk/articles/dataset/NOAH-H_terrain_classifications_of_Jezero_Crater_Mars_zip/17121482/2
- Download: https://ordo.open.ac.uk/ndownloader/files/33917705 (336 MB .zip). The server blocks automated
  downloads: it is downloaded from a browser.
- In the repo: the same mosaic losslessly recompressed, from LZW to ZSTD level 9 with the same 128-pixel
  blocks, because the original weighs 125 MB and GitHub does not accept files over 100 MB. The pixels, the CRS
  and the georeference are identical to the original (checked pixel by pixel), and `build` reads it as fast as
  the original. ZSTD requires GDAL with ZSTD support, which the pipeline's rasterio wheels include.
- uint8 at 25 cm, Plate Carrée on a 3,396,190 m sphere. According to the readme, the HiRISE images were
  georeferenced to the Mars 2020 HiRISE orthomosaic (the same one as `jezero_walk`). CC BY 4.0 license.
- Risk per group: `science/validation/noahh_ig_risk.csv` (Edgar), based on Barrett et al. (2022).

Wright, J., Barrett, A., Fawdon, P., Favaro, E., Balme, M., Woods, M., Karachalios, S., & Gerdes, L.
(2022). *NOAH-H terrain classifications of Jezero Crater, Mars* (Version 2) [Data set]. The Open
University. https://doi.org/10.21954/ou.rd.17121482.v2

## Gale (`gale`, around Curiosity)

Window crops (the region bbox plus 0.02° per side) of the remote mosaics, without downloading them in full.
The DEM and the orthophoto are stored at 5 m: each pixel averages a block of the original, read from the
mosaic's overviews. There is no NOAH-H classification of Gale: its risk layer is derived from the DEM
roughness, with no other source (method in `docs/supuestos.md`).

### Elevation: 1 m HiRISE DEM, stored at 5 m

- File: `MSL_Gale_DEM_Mosaic_5m_gale.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_msl_gale_merged_dem_1m
- Origin: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSL/MSL_Gale_DEM_Mosaic_1m_v3.tif
  (3.9 GB in full)
- Float32 in meters. At Curiosity's position on sol 5073 it reads −3472.16 m, and MMGIS reports −3472.09 m
  for the same point.
- The page's recommended citation repeats the orthomosaic title; below is the title of the DEM page.

Calef, F. J., III, & Parker, T. (2016). *MSL Gale merged DEM 1m* [Data set]. PDS Annex, U.S.
Geological Survey. https://astrogeology.usgs.gov/search/map/mars_msl_gale_merged_dem_1m

### Image: 25 cm HiRISE orthomosaic, stored at 5 m

- File: `MSL_Gale_Orthophoto_Mosaic_5m_gale.tif`
- Page: https://astrogeology.usgs.gov/search/map/mars_msl_gale_merged_orthophoto_mosaic_25cm
- Origin: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSL/MSL_Gale_Orthophoto_Mosaic_25cm_v3.tif
  (24 GB in full)

Calef, F. J., III, & Parker, T. (2016). *MSL Gale merged orthophoto mosaic* [Data set]. PDS Annex,
U.S. Geological Survey. https://astrogeology.usgs.gov/search/map/mars_msl_gale_merged_orthophoto_mosaic_25cm

### Thermal inertia: quantitative THEMIS at 100 m

- File: `THEMIS_TI_Mosaic_Quant_30S120E_100mpp_gale.tif`, from the tile covering 30° S to 0° and 120° E to
  180° E.
- Page: https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_30s120e_100mpp
- Origin: https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit/THEMIS_TI_Mosaic_Quant_30S120E_100mpp.cub

USGS Astrogeology Science Center, Arizona State University Mars Space Flight Facility, & NASA Mars Data
Analysis Program. (2014). *THEMIS thermal inertia mosaic quantitative 30S120E 100mpp* [Data set]. U.S.
Geological Survey. https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_30s120e_100mpp

### Curiosity traverse

- File: `MSL_traverse_2026-11-14.json` (repo root). The MMGIS traverse does not carry the sol of each
  segment; it is taken from the waypoint where each one ends (1316 of 1317 segments end less than 1 m from
  their waypoint). It is regenerated with `python -m marsdata.fetch.mmgis MSL ../MSL_traverse_<date>.json`
  from `pipeline/`.
- Origin: https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_traverse.json and
  https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_waypoints.json, queried on 14 November 2026 (last
  sol: 5073).

NASA/JPL-Caltech. (2026). *MSL traverse and waypoints* [Data set]. Multi-Mission Geographic Information
System (MMGIS). Retrieved 14 November 2026 from https://mars.nasa.gov/mmgis-maps/MSL/

## Live data (`GET /live`)

- Solar ejections: NASA's DONKI (CCMC), `api.nasa.gov/DONKI/WSAEnlilSimulations`.
- Perseverance position: JPL MMGIS, `M20_waypoints.json`.
- Perseverance raw images: `mars.nasa.gov/rss/api/?feed=raw_images`.

The saved copy for offline use is `apps/api/app/live/snapshot.json`.

## Still to record

- Thermal inertia method: Fergason, Christensen and Kieffer (2006), *Journal of Geophysical Research*. The
  page asks to cite the authors; the full reference and its DOI still have to be checked.
- Perseverance traverse: JPL MMGIS (`M20_traverse_2026-11-12.json`).
