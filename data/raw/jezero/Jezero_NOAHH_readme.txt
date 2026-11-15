This readme.txt file was generated on 2021/12/01 by Jack Wright.

GENERAL INFORMATION

Dataset title: NOAH-H terrain classifications of Jezero Crater, Mars

Dataset manuscript: "Deep learning-generated map of Jezero Crater, Mars: Application of the NOAH-H terrain classification system" submitted to Journal of Maps.

Dataset authors:
	1. Jack Wright, jack.wright@esa.int, jack.wright@open.ac.uk, European Space Agency (ESA), European Space Astronomy Centre (ESAC), Camino Bajo del Castillo, s/n, 28692 Villanueva de la Cañada, Madrid, Spain.
	2. Alexander M. Barrett, alexander.barrett@open.ac.uk, School of Physical Sciences, The Open University, Walton Hall, Milton Keynes, MK7 6AA, UK
	3. Peter Fawdon, peter.fawdon@open.ac.uk, School of Physical Sciences, The Open University, Walton Hall, Milton Keynes, MK7 6AA, UK
	4. Elena A. Favaro, elena.favaro@open.ac.uk, School of Physical Sciences, The Open University, Walton Hall, Milton Keynes, MK7 6AA, UK
	5. Matthew R. Balme, matt.balme@open.ac.uk, School of Physical Sciences, The Open University, Walton Hall, Milton Keynes, MK7 6AA, UK
	6. Mark J. Woods, mark.woods@cgi.com
	7. Spyridon Karachalios, spirdonkarachalios@gmail.com

Dataset description: These folders contain rasters and mosaics of terrain classifications of Jezero Crater, Mars, made by the
		     Novelty or Anomaly Hunter - HiRISE (NOAH-H) deep learning convolutional neural network developed by SCISYS Ltd.
		     These folders also contain ancilliary file needed to display the NOAH-H products in geographic information
		     software. Four 25 cm/pixel HiRISE images of Jezero Crater were used as input for NOAH-H. NOAH-H produced four
		     25 cm/pixel rasters where each pixel is assigned a terrain class based on the corresponding pixels in the
		     input HiRISE image. To mosaic the NOAH-H rasters together, first the input HiRISE images were georeferenced to
		     an orthorectified HiRISE mosaic created by the NASA Mars 2020 team. The NOAH-H terrain classification took place
		     using raw HiRISE images before the orthomosaic was publicly available. High order (spline, in ArcGIS Pro 2.8)
		     transformations were used to make the HiRISE images georeference closely onto the target layers. Most HiRISE
		     images were georeferenced only to the Mars 2020 orthomosaic. The final HiRISE image to be georeferenced had
		     control points tying it to the previously georeferenced images, as well as the Mars 2020 orthomosaic, to make
		     the NOAH-H mosaic as seamless as possible within the bounds of this method. Once the HiRISE images were
		     georeferenced, the same control points and transformations were applied to the corresponding NOAH-H rasters.
		     To mosaic the georeferenced NOAH-H rasters the pixel values for the classes needed to be changed so that
		     more confidently identified and more dangerous classes made it into the mosaic (see dataset manuscript for
		     details. Therefore, pixel values are different for the individual NOAH-H rasters and the mosaics in this
		     dataset. There are two mosaics, one with the 14 descriptive classes of the terrain, and the other with the
		     five interpretative groups (Barrett et al., 2022).

Related public datasets:
	- Mars 2020 Terrain Relative Navigation HiRISE Orthorectified Image Mosaic of Jezero Crater, Mars: https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first
	- Mars 2020 Terrain Relative Navigation Context Camera Orthorectified Image Mosaic of Jezero Crater, Mars: https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0
	- Raw HiRISE images: https://www.uahirise.org/
		     

FILE STRUCTURE AND FILE DESCRIPTIONS

NOAH-H_Jezero_dataset
|——readme.txt - This file. Contains information about the dataset (who made the data, what the data are, where to find the data, how to use the data).
|
|——Control_Points - Contains text files of tables of control points used to georeference raw HiRISE images and raw NOAH-H rasters.
|	|
|	|—ESP_042315_1985_RED_hand_2_HiRISE.txt
|	|—ESP_046060_1985_RED_hand_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.txt
|	|—ESP_048908_1985_RED_hand_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.txt
|	|—PSP_003798_1985_RED_hand_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.txt
|
|
|—NOAH-H_mosaics - Contains folders containing files pertaining to the descriptive classes and interpretative groups versions of the NOAH-H mosaics
|	|
|	|—Descriptive_classes - Contains files pertaining to the descriptive classes version of the NOAH-H terrain classification of Jezero Crater, Mars
|	|	|
|	|	|—DescriptiveClasses.clr - colour map for symbolising the descriptive class mosaic in an image processor
|	|	|
|	|	|—DescriptiveClasses_rank_DC.lyrx - ArcGIS Pro layerx file containing the symbology for the descriptive classes NOAH-H mosaic
|	|	|
|	|	|—Jezero_NOAHH_mosaic_DC.tif - NOAH-H terrain classification map of Jezero Crater showing 14 descriptive classes (georeferenced)
|	|
|	|—Interpretative groups - Contains files pertaining to the interpretative groups version of the NOAH-H terrain classification of Jezero Crater, Mars
|		|
|		|—Interpretativegroups.clr - colour map for symbolising the interpretative group mosaic in an image processor
|		|
|		|—InterpretativeGroups_rank_IG.lyrx - ArcGIS Pro layerx file containing the symbology for the interpretative groups NOAH-H mosaic
|		|
|		|—Jezero_NOAHH_mosaic_IG.tif - NOAH-H terrain classification map of Jezero Crater showing five interpretative groups (georeferenced)
|
|
|—NOAH-H_rasters_rectified - Contains the four individual georeferenced NOAH-H rasters that make up the mosaics and their symbology file
	|
	|—DescriptiveClasses.clr - colour map for symbolising the descriptive class rasters in an image processor
	|
	|—DescriptiveClasses.lyrx - ArcGIS Pro layerx file containing the symbology for the NOAH-H rasters
	|
	|—ESP_042315_1985_RED_NOAHHv10_2_HiRISE.tif						}
	|—ESP_046060_1985_RED_NOAHHv10_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.tif	} Individual 25 cm/pixel NOAH-H terrain classified rasters (georeferenced)
	|—ESP_048908_1985_RED_NOAHHv10_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.tif	}
	|—PSP_003798_1985_RED_NOAHHv10_2_JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0.tif	}

FILENAMING

- Control point (.txt) and individual NOAH-H raster (.tif) files form pairs with matching filenames. Their filenames have three or four parts:
	- The corresponding HiRISE image product ID, e.g. "ESP_042315_1985_RED"
	- "_NOAHHv10", present only for NOAH-H files, "v10" indicates that these are version 1.0 NOAH-H rasters for the corresponding HiRISE image
	- "_hand_2_", indicating that the HiRISE image was georeferenced by hand to the target
	- The name of the primary georeferencing target, either:
		-"JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0", indicating that the control points used to georeference the raw HiRISE image connect to the Mars 2020 Terrain Relative Navigation HiRISE Orthorectified Image Mosaic of Jezero Crater, Mars only
		-"HiRISE", indicating that the control points used to georeference the raw HiRISE image connect to the Mars 2020 orthomosaic AND some of the other HiRISE images that were previously georeferenced in this work

SPATIAL DATA COORDINATE SYSTEM INFORMATION

All georeferenced NOAH-H .tif files for Jezero Crater have the same projected coordinate system:
	- Projection: Plate Carree
	- Sphere radius: 3396190.0 m

SOFTWARE INFORMATION

All GIS workflows (georeferencing, mosaicking) were conducted in ArcGIS Pro 2.8. NOAH-H is a deep learning semantic segmentation software
developed by SciSys Ltd for the European Space Agency to aid preparation for the ExoMars rover mission.

INSTRUCTIONS FOR GEOREFERENCING

To reproduce our georeferencing on publicly available HiRISE images, use the following workflow in ArcGIS Pro (adapt for other geographic information system software):

	1. Download one of the raw HiRISE images and add it to a map
	2. Set the coordinate system of the map to match the raw HiRISE image
	3. Import the corresponding control points
	4. Apply a spline transformation to the image
	5. Export the transformed image

FUNDING INFORMATION

JW, AMB, and MRB acknowledge funding from the UK Research and Innovation (UKRI) Science and Technology Facilities Council (STFC; grant ST/T000228/1),
and the European Space Agency (ESA; contract 4000118843/16/ NL/LvH1145 – Novelty or Anomaly Hunter (NOAH)). PF, EAF, and MRB acknowledge funding from
the UK Space Agency (UKSA: grants ST/V001965/1 and ST/R001413/1). EAF and MRB also acknowledge UKSA grant ST/T002913/1.

SHARING/ACCESS INFORMATION

These data are available for use according to the CC BY 4.0 licence.

REFERENCES

Barrett, A. M., Balme, M. R., Woods, M., Karachalios, S., Petrocelli, D., Joudrier, L., & Sefton-Nash, E. (2022). NOAH-H, a deep-learning, terrain classification system for Mars: Results for the ExoMars Rover candidate landing sites. Icarus, 371, 114701.

