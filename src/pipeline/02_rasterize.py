"""
02_rasterize.py – Rasterize vector layers onto the reference grid (dem.tif).

Outputs (all EPSG:32633, 30 m, same extent as outputs/terrain/dem.tif):
  outputs/rasters/litho_class.tif          – int16, nodata=-1, RAT with class names
  outputs/rasters/litho_class_mapping.json – {class_name: int_code}
  outputs/rasters/raw_geology.tif          – int16, nome_ulf → int, RAT with names
  outputs/rasters/raw_geology_mapping.json – {nome_ulf: int_code}
  outputs/rasters/corine.tif               – int16, nodata=-1
  outputs/rasters/labels.tif               – uint8 binary, nodata=255
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import generic_filter
from shapely.geometry import box
from utils.raster_utils import campania_mask

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DEM_PATH     = Path("outputs/terrain/dem.tif")
GEOLOGY_PATH = Path("data/geological-map/geology_campania_classified.geojson")
CLC_PATH     = Path("data/corine-land-cover/DATA/U2018_CLC2018_V2020_20u1.gpkg")
IFFI_PATH    = Path("data/ispra-landslide/frane_poly_campania_opendata.gpkg")
OUT_DIR      = Path("outputs/rasters")

TARGET_CRS = "EPSG:32633"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_ref_profile() -> dict:
    with rasterio.open(DEM_PATH) as src:
        return src.profile.copy()


def ref_bbox_gdf(ref: dict) -> gpd.GeoDataFrame:
    """Bounding box of the reference grid as a GeoDataFrame (EPSG:32633)."""
    t = ref["transform"]
    minx = t.c
    maxy = t.f
    maxx = minx + t.a * ref["width"]
    miny = maxy + t.e * ref["height"]  # t.e is negative
    return gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs="EPSG:32633")


def base_profile(ref: dict, dtype: str, nodata) -> dict:
    p = ref.copy()
    p.update(dtype=dtype, nodata=nodata, count=1, compress="deflate", tiled=True)
    return p


def majority_filter(arr: np.ndarray, nodata, size: int = 3) -> np.ndarray:
    """Replace each cell with the most common valid value in its neighbourhood."""
    nd = int(nodata)
    def _mode(window):
        valid = window[window != nd].astype(np.int32)
        if len(valid) == 0:
            return nd
        counts = np.bincount(valid - valid.min())
        return int(valid.min() + counts.argmax())
    result = generic_filter(arr.astype(np.int32), _mode, size=size)
    return result.astype(arr.dtype)


def burn(gdf: gpd.GeoDataFrame, burn_col: str, profile: dict) -> np.ndarray:
    """Rasterize `burn_col` (int) column from gdf onto the reference grid."""
    shapes = (
        (geom, val)
        for geom, val in zip(gdf.geometry, gdf[burn_col])
        if geom is not None and not geom.is_empty
    )
    arr = rasterize(
        shapes=shapes,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=profile["nodata"],
        dtype=profile["dtype"],
        all_touched=False,
    )
    return arr


def save_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)
    print(f"  saved {path}")


def write_qml(raster_path: Path, int_to_name: dict) -> None:
    """Write a QGIS .qml style file alongside the raster.

    QGIS auto-applies it on load (same base name). Uses a seeded palette so
    colors are stable across reloads.
    """
    rng = np.random.default_rng(42)

    entries = ""
    for val, name in sorted(int_to_name.items()):
        r, g, b = rng.integers(30, 230, size=3)
        escaped = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        entries += (
            f'        <paletteEntry value="{val}" label="{escaped}" '
            f'color="#{r:02x}{g:02x}{b:02x}" alpha="255"/>\n'
        )

    xml = (
        '<!DOCTYPE qgis PUBLIC \'http://mrcc.com/qgis.dtd\' \'SYSTEM\'>\n'
        '<qgis version="3.0" styleCategories="AllStyleCategories">\n'
        '  <pipe>\n'
        '    <rasterrenderer type="paletted" band="1" opacity="1" alphaBand="-1">\n'
        '      <rasterTransparency/>\n'
        '      <colorPalette>\n'
        f'{entries}'
        '      </colorPalette>\n'
        '    </rasterrenderer>\n'
        '    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>\n'
        '    <huesaturation saturation="0" grayscaleMode="0" colorizeOn="0"/>\n'
        '    <rasterresampler maxOversampling="2"/>\n'
        '  </pipe>\n'
        '</qgis>\n'
    )
    qml_path = raster_path.with_suffix(".qml")
    qml_path.write_text(xml)
    print(f"  saved {qml_path}")


# ---------------------------------------------------------------------------
# Step 1 – litho_class (classified) + raw_geology (nome_ulf)
# ---------------------------------------------------------------------------

def rasterize_geology(ref_profile: dict, outside: np.ndarray) -> None:
    print("Reading geology …")
    gdf = gpd.read_file(GEOLOGY_PATH, bbox=ref_bbox_gdf(ref_profile))
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf.to_crs(TARGET_CRS)

    profile = base_profile(ref_profile, dtype="int16", nodata=np.int16(-1))

    # --- litho_class raster ---
    classes = sorted(gdf["litho_class"].dropna().unique().tolist())
# Use the fixed mapping from the classification script
    with open("data/geological-map/litho_class_mapping.json") as f:
        cls_mapping = json.load(f)

    mapping_path = OUT_DIR / "litho_class_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(cls_mapping, f, indent=2)
    print(f"  saved {mapping_path}")

    gdf["litho_code"] = gdf["litho_class"].map(cls_mapping)
    gdf_cls = gdf[gdf["litho_code"].notna()].copy()
    gdf_cls["litho_code"] = gdf_cls["litho_code"].astype(np.int16)

    arr = burn(gdf_cls, "litho_code", profile)
    arr = majority_filter(arr, nodata=-1, size=3)
    arr[outside] = profile["nodata"]

    out_path = OUT_DIR / "litho_class.tif"
    save_raster(out_path, arr, profile)
    write_qml(out_path, {v: k for k, v in cls_mapping.items()})

    # --- raw_geology raster (nome_ulf, no classification) ---
    names = sorted(gdf["nome_ulf"].dropna().unique().tolist())
    name_mapping = {name: i for i, name in enumerate(names)}

    name_mapping_path = OUT_DIR / "raw_geology_mapping.json"
    with open(name_mapping_path, "w") as f:
        json.dump(name_mapping, f, indent=2, ensure_ascii=False)
    print(f"  saved {name_mapping_path}")

    gdf["nome_code"] = gdf["nome_ulf"].map(name_mapping)
    gdf_raw = gdf[gdf["nome_code"].notna()].copy()
    gdf_raw["nome_code"] = gdf_raw["nome_code"].astype(np.int16)

    arr_raw = burn(gdf_raw, "nome_code", profile)
    arr_raw[outside] = profile["nodata"]

    raw_path = OUT_DIR / "raw_geology.tif"
    save_raster(raw_path, arr_raw, profile)
    write_qml(raw_path, {v: k for k, v in name_mapping.items()})


# ---------------------------------------------------------------------------
# Step 2 – Corine land cover
# ---------------------------------------------------------------------------

def rasterize_corine(ref_profile: dict, outside: np.ndarray) -> None:
    print("Reading Corine land cover …")
    gdf = gpd.read_file(CLC_PATH, layer="U2018_CLC2018_V2020_20u1", bbox=ref_bbox_gdf(ref_profile))
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf.to_crs(TARGET_CRS)

    gdf["code_int"] = gdf["Code_18"].astype(int).astype(np.int16)

    profile = base_profile(ref_profile, dtype="int16", nodata=np.int16(-1))
    arr = burn(gdf, "code_int", profile)
    arr[outside] = profile["nodata"]
    save_raster(OUT_DIR / "corine.tif", arr, profile)


# ---------------------------------------------------------------------------
# Step 3 – IFFI landslide polygons (binary labels)
# ---------------------------------------------------------------------------

def rasterize_labels(ref_profile: dict, outside: np.ndarray) -> None:
    print("Reading IFFI landslide polygons …")
    gdf = gpd.read_file(IFFI_PATH, layer="frane_poly_opendata", bbox=ref_bbox_gdf(ref_profile))
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf.to_crs(TARGET_CRS)

    profile = base_profile(ref_profile, dtype="uint8", nodata=np.uint8(255))
    # Fill background with 0, not nodata, so every pixel has a defined label
    shapes = (
        (geom, 1)
        for geom in gdf.geometry
        if geom is not None and not geom.is_empty
    )
    arr = rasterize(
        shapes=shapes,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(np.uint8)
    arr[outside] = profile["nodata"]

    save_raster(OUT_DIR / "labels.tif", arr, profile)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading reference grid from {DEM_PATH} …")
    ref_profile = read_ref_profile()

    print("Building Campania boundary mask …")
    outside = campania_mask(ref_profile)

    rasterize_geology(ref_profile, outside)
    rasterize_corine(ref_profile, outside)
    rasterize_labels(ref_profile, outside)

    print("Done.")


if __name__ == "__main__":
    main()
