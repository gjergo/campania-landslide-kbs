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
