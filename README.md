# ischia-landslide-kbs

ICon course project. KBS for landslide susceptibility in Campania, Italy.

## Data locations
data/ispra-landslide/     → IFFI polygons (ground truth)
data/geological-map/geology_campania_classified.geojson → litho classes
data/copernicus-dem-30/   → GeoTIFF DEM (drives grid)
data/corine-land-cover/   → CORINE .gpkg
data/era5rainfall/        → NetCDF files per year (still downloading)
data/cft-landslides/      → earthquake-triggered slides

### data sources:

- (ispra-landslide) National mosaic 2024 of landslide hazard: [https://idrogeo.isprambiente.it/opendata/wms/Mosaicatura_ISPRA_2024_pericolosita_frana_PAI.zip] (gpkg)
- (ispra-landslide) Campania, Frane IFFI poligonali: [https://idrogeo.isprambiente.it/opendata/wms/Mosaicatura_ISPRA_2024_pericolosita_frana_PAI.zip] (gpkg)
- (ispra-landslide) Campania, Landslide events: [https://idrogeo.isprambiente.it/opendata/eventi/eventi_campania_opendata.gpkg] (gpkg)
- (copernicus-dem-30) Copernicus GLO-30 Digital Elevation Model: [https://portal.opentopography.org/raster?opentopoID=OTSDEM.032021.4326.3] (GeoTIFF)
- (corine-land-cover) CORINE Land Cover 2018: [https://land.copernicus.eu/en/products/corine-land-cover/clc2018#download] (gpkg) 
- (cfti-landslides) CTFIlandslides: [https://data.ingv.it/dataset/964] (GeoJSON, .shp)

other can be downloaded via scripts/

### Dem rasters:

- dem.tif — the reprojected DEM in EPSG:32633. This is the reference grid everything else aligns to. Not used directly as a feature (elevation alone is a weak predictor) but it's the base.
- slope.tif — slope angle in degrees at each pixel. The single most important landslide predictor. Steep slopes fail, flat slopes don't.
- aspect.tif — the direction a slope faces (north, south, east, west) in degrees. Affects moisture retention and vegetation — north-facing slopes in the northern hemisphere stay wetter, which matters for failure.
- profile_curvature.tif — curvature measured along the direction of steepest descent. Positive values = slope is accelerating downhill (convex, erosion-prone). Negative = decelerating (concave, deposition zone). Affects how water and debris flow.
- planform_curvature.tif — curvature measured perpendicular to slope direction. Negative values = converging flow (hollows, where water concentrates). Positive = diverging flow (ridges). Hollows are where debris flows initiate.
- flow_accumulation.tif — how many upslope pixels drain through each pixel. High values = valley bottoms and drainage channels. Used to compute TWI and to identify drainage proximity.
- twi.tif — Topographic Wetness Index. Combines slope and flow accumulation into a single measure of how wet a pixel tends to be. Formula is ln(flow_accumulation / tan(slope)). High TWI = wet, flat, drainage-collecting areas. One of the strongest predictors of shallow landslide initiation.
