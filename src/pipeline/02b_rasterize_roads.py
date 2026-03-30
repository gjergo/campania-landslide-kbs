"""
02b_rasterize_roads.py – Euclidean distance to major roads raster.

Loads OSM roads, keeps only major road classes, reprojects to EPSG:32633,
clips to Campania, burns onto the reference grid, computes per-pixel
Euclidean distance to the nearest road (metres), applies log1p, and saves.

Output:
  outputs/rasters/dist_roads.tif  – float32, nodata=-9999, log1p(metres)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt
from utils.raster_utils import campania_mask

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROADS_PATH    = Path("data/osm-roads/gis_osm_roads_free_1.shp")
BOUNDARY_PATH = Path("data/campania.geojson")
DEM_PATH      = Path("outputs/terrain/dem.tif")
OUT_PATH      = Path("outputs/rasters/dist_roads.tif")

TARGET_CRS = "EPSG:32633"

KEEP_FCLASSES = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
}

NODATA = np.float32(-9999)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_ref_profile() -> dict:
    with rasterio.open(DEM_PATH) as src:
        return src.profile.copy()


def pixel_resolution(profile: dict) -> float:
    """Return pixel size in metres (assumes square pixels)."""
    return abs(profile["transform"].a)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # --- Reference grid ---
    print(f"Reading reference grid from {DEM_PATH} …")
    ref = read_ref_profile()
    height, width = ref["height"], ref["width"]
    res_m = pixel_resolution(ref)

    # --- Campania outside mask ---
    print("Building Campania boundary mask …")
    outside = campania_mask(ref)

    # --- Load roads ---
    print(f"Loading roads from {ROADS_PATH} …")
    roads = gpd.read_file(ROADS_PATH)

    all_fclasses = sorted(roads["fclass"].dropna().unique().tolist())
    print(f"\nAll fclass values in dataset ({len(all_fclasses)}):")
    for fc in all_fclasses:
        print(f"  {fc}")
    print()

    # --- Filter to major roads ---
    roads = roads[roads["fclass"].isin(KEEP_FCLASSES)].copy()
    print(f"Kept {len(roads):,} features after fclass filter.")

    # --- Reproject ---
    roads = roads.to_crs(TARGET_CRS)

    # --- Clip to Campania boundary ---
    print("Clipping to Campania boundary …")
    boundary = gpd.read_file(BOUNDARY_PATH).to_crs(TARGET_CRS)
    roads = gpd.clip(roads, boundary)
    print(f"  {len(roads):,} features after clip.")

    # --- Burn roads onto reference grid ---
    print("Burning roads onto reference grid …")
    road_mask = rasterize(
        shapes=(
            (geom, 1)
            for geom in roads.geometry
            if geom is not None and not geom.is_empty
        ),
        out_shape=(height, width),
        transform=ref["transform"],
        fill=0,
        dtype="uint8",
        all_touched=True,  # thin lines: capture every touched pixel
    )

    # --- Euclidean distance transform ---
    # distance_transform_edt returns distance in pixels for non-zero background;
    # we want distance FROM road pixels, so invert: background = no road (0).
    print("Computing Euclidean distance transform …")
    # True = background (no road), False = foreground (road)
    no_road = road_mask == 0
    dist_px = distance_transform_edt(no_road)
    dist_m = dist_px * res_m  # convert pixels → metres

    # --- log1p transform ---
    dist_log = np.log1p(dist_m).astype(np.float32)

    # --- Apply Campania mask ---
    dist_log[outside] = NODATA

    # --- Save ---
    profile = ref.copy()
    profile.update(
        dtype="float32",
        nodata=float(NODATA),
        count=1,
        compress="deflate",
        tiled=True,
    )
    with rasterio.open(OUT_PATH, "w", **profile) as dst:
        dst.write(dist_log, 1)
    print(f"\nSaved {OUT_PATH}")

    # --- Sanity check ---
    valid = dist_log[~outside]
    print(f"  min  : {valid.min():.4f}")
    print(f"  max  : {valid.max():.4f}")
    print(f"  mean : {valid.mean():.4f}")
    print("Done.")


if __name__ == "__main__":
    main()
