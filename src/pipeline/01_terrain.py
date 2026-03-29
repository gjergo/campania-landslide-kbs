"""
01_terrain.py – DEM → slope, aspect, profile/planform curvature, TWI, flow accumulation.
All outputs saved to outputs/rasters/ as GeoTIFFs in EPSG:32633, 30 m resolution.
"""
from pathlib import Path
import tempfile

import numpy as np

# pysheds 0.5 uses np.in1d which was removed in NumPy 2.0
if not hasattr(np, "in1d"):
    np.in1d = lambda ar1, ar2, **kw: np.isin(ar1, ar2, **kw).ravel()

import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pysheds.grid import Grid

DEM_PATH = Path("data/copernicus-dem-30/output_hh.tif")
OUT_DIR = Path("outputs/rasters")
TARGET_CRS = CRS.from_epsg(32633)
TARGET_RES = 30  # metres
NODATA = np.float32(-9999.0)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def reproject_dem() -> tuple[np.ndarray, dict]:
    """Reproject source DEM to EPSG:32633 at 30 m. Returns (array, rasterio profile)."""
    with rasterio.open(DEM_PATH) as src:
        transform, width, height = calculate_default_transform(
            src.crs, TARGET_CRS, src.width, src.height,
            *src.bounds, resolution=TARGET_RES,
        )
        profile = src.profile.copy()
        profile.update(
            crs=TARGET_CRS, transform=transform,
            width=width, height=height,
            count=1, dtype="float32", nodata=float(NODATA),
            compress="deflate", tiled=True,
        )
        dem = np.full((height, width), NODATA, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=dem,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear,
            dst_nodata=float(NODATA),
        )
    return dem, profile


def save_raster(name: str, data: np.ndarray, profile: dict) -> None:
    path = OUT_DIR / f"{name}.tif"
    p = {**profile, "dtype": str(data.dtype)}
    with rasterio.open(path, "w", **p) as dst:
        dst.write(data, 1)
    print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Terrain derivatives (numpy only)
# ---------------------------------------------------------------------------

def compute_slope_aspect(
    dem: np.ndarray, c: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Slope in degrees, aspect in degrees clockwise from north (downhill convention),
    and slope in radians (used internally for TWI).

    Uses np.gradient (central differences) in raster space:
      row axis increases southward, col axis increases eastward.
    """
    drow, dcol = np.gradient(dem, c)
    p = dcol    # dZ/dEast
    q = -drow   # dZ/dNorth (flip: row increases south)

    slope_rad = np.arctan(np.hypot(p, q))
    slope_deg = np.degrees(slope_rad).astype(np.float32)

    # Downhill aspect: direction of steepest descent, CW from north
    aspect_deg = (np.degrees(np.arctan2(-p, -q)) % 360).astype(np.float32)

    return slope_deg, aspect_deg, slope_rad


def compute_curvatures(dem: np.ndarray, c: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Profile and planform curvature after Evans (1980).

    Profile curvature: curvature along the direction of steepest slope.
      Negative = concave (convergent flow), positive = convex.
    Planform curvature: curvature perpendicular to the slope direction.
      Negative = divergent, positive = convergent.
    """
    drow, dcol = np.gradient(dem, c)
    p = dcol    # dZ/dEast
    q = -drow   # dZ/dNorth

    # Second derivatives in geographic (East, North) space.
    # np.gradient(dcol, c, axis=1)  = d²Z/dE²
    # np.gradient(drow, c, axis=0)  = d²Z/drow²  = d²Z/d(-N)² = d²Z/dN²
    # np.gradient(dcol, c, axis=0)  = d(dZ/dE)/drow = -d²Z/(dE·dN)  → negate for s
    r = np.gradient(dcol, c, axis=1)           # d²Z/dE²
    t = np.gradient(drow, c, axis=0)           # d²Z/dN²
    s = -np.gradient(dcol, c, axis=0)          # d²Z/(dE·dN)

    grad2 = p**2 + q**2
    valid = grad2 > 1e-8

    prof_num = p**2 * r + 2 * p * q * s + q**2 * t
    prof_den = np.where(valid, grad2 * (1 + grad2) ** 1.5, 1.0)
    profile_curv = np.where(valid, -prof_num / prof_den, 0.0).astype(np.float32)

    plan_num = q**2 * r - 2 * p * q * s + p**2 * t
    plan_den = np.where(valid, grad2 ** 1.5, 1.0)
    planform_curv = np.where(valid, -plan_num / plan_den, 0.0).astype(np.float32)

    return profile_curv, planform_curv


# ---------------------------------------------------------------------------
# Flow accumulation and TWI (pysheds)
# ---------------------------------------------------------------------------

def compute_flow_and_twi(
    dem: np.ndarray, profile: dict, slope_rad: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    D8 flow accumulation via pysheds, then TWI = ln(acc_area / tan(slope)).
    slope_rad may contain NaN where dem is nodata; those cells are masked later.
    """
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        tmp = Path(f.name)

    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(dem, 1)

    grid = Grid.from_raster(str(tmp))
    dem_g = grid.read_raster(str(tmp))
    pit_filled = grid.fill_pits(dem_g)
    flooded = grid.fill_depressions(pit_filled)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated)
    acc = grid.accumulation(fdir)

    tmp.unlink(missing_ok=True)

    acc_arr = np.array(acc, dtype=np.float32)

    # TWI: clamp slope to ≥ 0.1° so denominator never blows up
    slope_tan = np.tan(np.maximum(slope_rad, np.radians(0.1)))
    acc_area = acc_arr * (TARGET_RES ** 2)           # m²
    twi = np.log(np.maximum(acc_area, 1.0) / slope_tan).astype(np.float32)

    return acc_arr, twi


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Reprojecting DEM → EPSG:32633 at 30 m …")
    dem, profile = reproject_dem()
    save_raster("dem", dem, profile)

    # Working array: NODATA → NaN so numpy propagates correctly at edges
    dem_f = dem.astype(np.float64)
    dem_f[dem == NODATA] = np.nan
    nodata_mask = np.isnan(dem_f)

    print("Computing slope and aspect …")
    slope, aspect, slope_rad = compute_slope_aspect(dem_f, TARGET_RES)

    print("Computing profile and planform curvature …")
    profile_curv, planform_curv = compute_curvatures(dem_f, TARGET_RES)

    print("Computing flow accumulation and TWI (pysheds D8) …")
    flow_acc, twi = compute_flow_and_twi(dem, profile, slope_rad)

    # Stamp nodata mask onto all outputs
    for arr in (slope, aspect, profile_curv, planform_curv, flow_acc, twi):
        arr[nodata_mask] = NODATA

    print("Saving rasters …")
    for name, arr in [
        ("slope",             slope),
        ("aspect",            aspect),
        ("profile_curvature", profile_curv),
        ("planform_curvature",planform_curv),
        ("flow_accumulation", flow_acc),
        ("twi",               twi),
    ]:
        save_raster(name, arr, profile)

    print("Done.")


if __name__ == "__main__":
    main()
