# Créditos de datos

Cada producto que descarga el pipeline se registra aquí en formato APA 7, con su archivo local y la
ficha de donde salió. Cuando una ficha pide citar a los autores, también va la publicación que describe
el producto.

## Jezero

### Elevación: DTM de CTX a 20 m

- Archivo: `JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif`
- Ficha: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic
- Descarga: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif
- Float32 en metros, equirectangular sobre esfera de 3,396,190 m, controlado a MOLA y alineado al DTM
  de HRSC.

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation CTX DTM mosaic*
(JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0) [Data set]. U.S. Geological
Survey. https://doi.org/10.5066/P906QQT8

### Imagen: ortomosaico de CTX a 6 m

- Archivo: `JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif`
- Ficha: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_context_camera_orthorectified_image_mosaic
- Descarga: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif
  (también disponible en NASA Mars Trek)
- 8 bits en escala de grises. Es el mapa del sistema de visión del aterrizador (LVS) de Mars 2020,
  ortorrectificado con el DTM anterior. Desplazamiento horizontal medio entre las imágenes CTX que lo
  forman: 9.6 m.

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation Context Camera
orthorectified image mosaic* (JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0) [Data set]. U.S.
Geological Survey. https://doi.org/10.5066/P9GV1ND3

### Publicación de los dos productos anteriores

Fergason, R. L., Hare, T. M., Mayer, D. P., Galuszka, D. M., Redding, B. L., Smith, E. D., Shinaman,
J. R., Cheng, Y., & Otero, R. E. (2020). *Mars 2020 Terrain Relative Navigation flight product
generation: Digital terrain model and orthorectified image mosaics* [Resumen 2020]. 51st Lunar and
Planetary Science Conference. https://www.hou.usra.edu/meetings/lpsc2020/pdf/2020.pdf

### Inercia térmica: THEMIS cuantitativo a 100 m

- Archivo: `THEMIS_TI_Mosaic_Quant_00N060E_100mpp_jezero.tif`, recorte de Jezero (bbox de la región más
  0.05° por lado) leído por ventana del cubo remoto, sin descargar el tile completo de 2.5 GB.
- Ficha: https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_00n060e_100mpp
- Origen: https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.cub
- Float32 en J m⁻² K⁻¹ s⁻½, equirectangular sobre esfera de 3,396,190 m. Precisión absoluta ~20 % y
  relativa ~10 % dentro de una imagen (según la ficha). Sin DOI.

USGS Astrogeology Science Center, Arizona State University Mars Space Flight Facility, & NASA Mars Data
Analysis Program. (2014). *THEMIS thermal inertia mosaic quantitative 00N060E 100mpp* [Data set]. U.S.
Geological Survey. https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_00n060e_100mpp

## Jezero, zona de caminata (`jezero_walk`)

Recortes por ventana (bbox de la región más 0.003° por lado) leídos de los archivos remotos, sin bajar
los mosaicos completos. La inercia térmica es el mismo producto THEMIS de arriba, recortado a esta zona.

### Elevación: DTM de HiRISE a 1 m

- Archivo: `JEZ_hirise_soc_006_DTM_1m_jezero_walk.tif`
- Ficha: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_dtm_mosaic
- Origen: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif
  (1.8 GB completo)

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation HiRISE DTM mosaic*
(JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40) [Data set]. U.S.
Geological Survey. https://doi.org/10.5066/P9REJ9JN

### Imagen: ortomosaico de HiRISE a 25 cm

- Archivo: `JEZ_hirise_soc_006_orthoMosaic_25cm_jezero_walk.tif`
- Ficha: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_hirise_orthorectified_image_mosaic
- Origen: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first.tif
  (6.9 GB completo)

USGS Astrogeology Science Center. (2020). *Mars 2020 Terrain Relative Navigation HiRISE orthorectified
image mosaic* (JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first) [Data set]. U.S. Geological
Survey. https://doi.org/10.5066/P9QJDP48

## Riesgo de terreno: NOAH-H (regiones `jezero` y `jezero_walk`)

- Archivo: `Jezero_NOAHH_mosaic_IG.tif` (cinco grupos interpretativos, nodata 127), extraído de
  `NOAH-H_mosaics/Intrepretative_groups/` del .zip. Junto a él, `Jezero_NOAHH_readme.txt` y la tabla
  de colores.
- Ficha: https://ordo.open.ac.uk/articles/dataset/NOAH-H_terrain_classifications_of_Jezero_Crater_Mars_zip/17121482/2
- Descarga: https://ordo.open.ac.uk/ndownloader/files/33917705 (.zip de 336 MB). El servidor bloquea
  las descargas automáticas: se baja desde un navegador.
- uint8 a 25 cm, Plate Carrée sobre esfera de 3,396,190 m. Según el readme, las imágenes HiRISE se
  georreferenciaron al ortomosaico HiRISE de Mars 2020 (el mismo de `jezero_walk`). Licencia CC BY 4.0.
- Riesgo por grupo: `science/validation/noahh_ig_risk.csv` (Edgar), basado en Barrett et al. (2022).

Wright, J., Barrett, A., Fawdon, P., Favaro, E., Balme, M., Woods, M., Karachalios, S., & Gerdes, L.
(2022). *NOAH-H terrain classifications of Jezero Crater, Mars* (Version 2) [Data set]. The Open
University. https://doi.org/10.21954/ou.rd.17121482.v2

### Pendientes de registrar

- Método de la inercia térmica: Fergason, Christensen y Kieffer (2006), *Journal of Geophysical
  Research*. La ficha pide citar a los autores; falta verificar la referencia completa y su DOI.
- Recorrido de Perseverance: MMGIS de JPL (`M20_traverse_2026-11-12.json`).
