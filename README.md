# campania-landslide-kbs

ICon course project. Knowledge-based system for landslide susceptibility mapping in Campania, Italy.
Combines a Prolog rule engine with supervised ML classifiers (Logistic Regression, Random Forest, SVM).
The key experiment is whether adding a `kb_susceptibility` feature derived from Prolog rules improves model AUC-ROC and F1.

All processing uses EPSG:32633 (UTM 33N) at 30m resolution, anchored to the Copernicus DEM grid.

## Pipeline

Run steps in order with `uv run src/pipeline/<script>.py`:

| Step | Script | What it does |
|------|--------|--------------|
| 01 | `01_terrain.py` | DEM → slope, aspect, curvature, TWI, flow accumulation |
| 02 | `02_rasterize.py` | Litho classes, CORINE land cover, IFFI landslide polygons → rasters |
| 02b | `02b_rasterize_roads.py` | OSM roads → distance raster |
| 03 | `03_era5.py` | ERA5 NetCDF → max 1-day, max 3-day, mean annual precip rasters |
| 04 | `04_sample.py` | Stack all rasters → sample → `outputs/features/feature_matrix.parquet` |
| 05 | `05_kb.py` | Prolog rules → append `kb_susceptibility` column to feature matrix |

Then train and evaluate:

```bash
uv run src/models/train.py
```

## Data

Download data into `data/` before running the pipeline. Most sources are one-time downloads (scripts in `scripts/` have already been run).

| Folder | Source | How to get it |
|--------|--------|---------------|
| `data/ispra-landslide/` | IFFI landslide polygons + events + P1-P4 hazard mosaic | Download from [ISPRA IdroGEO opendata](https://idrogeo.isprambiente.it/app/page/open-data) |
| `data/copernicus-dem-30/` | Copernicus GLO-30 DEM | [OpenTopography](https://portal.opentopography.org/raster?opentopoID=OTSDEM.032021.4326.3) |
| `data/corine-land-cover/` | CORINE Land Cover 2018 | [Copernicus Land Service](https://land.copernicus.eu/en/products/corine-land-cover/clc2018#download) |
| `data/geological-map/` | Litho polygons (pre-classified) | Already in repo as `geology_campania_classified.geojson` |
| `data/cfti-landslides/` | Earthquake-triggered slides | [INGV CFTI dataset](https://data.ingv.it/dataset/964) |
| `data/osm-roads/` | OSM road network (sud-italy) | See below |
| `data/era5/` | ERA5 daily precipitation 1990–2023 | `uv run scripts/download_era5.py` (CDS API key required) |

**OSM roads:**
```bash
curl -L -o data/osm-roads/sud-italy-free.shp.zip \
  https://download.geofabrik.de/europe/italy/sud-latest-free.shp.zip && \
  unzip data/osm-roads/sud-italy-free.shp.zip -d data/osm-roads/
```

## Project structure

```
src/pipeline/   → numbered pipeline steps
src/models/     → training and evaluation
src/utils/      → shared helpers (raster ops, reprojection)
scripts/        → one-off download scripts (already run, don't re-run)
data/           → raw inputs, read-only
outputs/        → all generated files (rasters, feature matrix, figures)
```

## Dependencies

```bash
uv sync
```

Requires Python ≥ 3.11. Key packages: `geopandas`, `rasterio`, `richdem`, `pysheds`, `xarray`, `scikit-learn`, `pyswip`.
