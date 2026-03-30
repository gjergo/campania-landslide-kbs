"""
04_sample.py – Stack rasters → feature matrix parquet.

Positive samples  : all pixels where labels == 1 and no feature is nodata.
Negative samples  : stratified random sample at 5:1 ratio (neg:pos),
                    stratified by litho_class value.
Spatial block     : 5x5 grid over the Campania extent → 25 blocks (0-24),
                    used for spatial cross-validation.

Output: outputs/features/feature_matrix.parquet
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy

# ---------------------------------------------------------------------------
# Raster catalogue  {column_name: path}
# ---------------------------------------------------------------------------
TERRAIN_DIR = Path("outputs/terrain")
RASTERS_DIR = Path("outputs/rasters")

RASTER_PATHS: dict[str, Path] = {
    "slope":              TERRAIN_DIR / "slope.tif",
    "aspect":             TERRAIN_DIR / "aspect.tif",
    "profile_curvature":  TERRAIN_DIR / "profile_curvature.tif",
    "planform_curvature": TERRAIN_DIR / "planform_curvature.tif",
    "twi":                TERRAIN_DIR / "twi.tif",
    "flow_accumulation":  TERRAIN_DIR / "flow_accumulation.tif",
    "litho_class":        RASTERS_DIR / "litho_class.tif",
    "corine":             RASTERS_DIR / "corine.tif",
    "dist_drainage":      RASTERS_DIR / "dist_drainage.tif",
    "dist_roads":         RASTERS_DIR / "dist_roads.tif",
    "labels":             RASTERS_DIR / "labels.tif",
}

FEATURE_COLS = [
    "slope", "aspect", "profile_curvature", "planform_curvature",
    "twi", "flow_accumulation", "litho_class", "corine",
    "dist_drainage", "dist_roads",
]

OUT_PATH   = Path("outputs/features/feature_matrix.parquet")
NEG_RATIO  = 5          # negatives per positive
GRID_SIZE  = 5          # 5×5 spatial blocks
RNG_SEED   = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_rasters() -> tuple[dict[str, np.ndarray], dict, dict[str, float]]:
    """Return {name: 2-D array}, ref_profile, {name: nodata_value}."""
    arrays: dict[str, np.ndarray] = {}
    nodatas: dict[str, float]     = {}
    ref_profile: dict             = {}

    for name, path in RASTER_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing raster: {path}\n"
                f"  Run the relevant pipeline step first."
            )
        with rasterio.open(path) as src:
            arrays[name] = src.read(1)
            nodatas[name] = src.nodata
            if not ref_profile:
                ref_profile = src.profile.copy()
    return arrays, ref_profile, nodatas


def build_valid_mask(
    arrays: dict[str, np.ndarray],
    nodatas: dict[str, float],
) -> np.ndarray:
    """True where every feature AND label has a valid (non-nodata) value."""
    height, width = next(iter(arrays.values())).shape
    valid = np.ones((height, width), dtype=bool)

    for name, arr in arrays.items():
        nd = nodatas[name]
        if nd is not None:
            if np.issubdtype(arr.dtype, np.floating):
                valid &= ~np.isnan(arr) & (arr != nd)
            else:
                valid &= arr != int(nd)
        else:
            if np.issubdtype(arr.dtype, np.floating):
                valid &= ~np.isnan(arr)
    return valid


def assign_spatial_blocks(
    rows: np.ndarray,
    cols: np.ndarray,
    height: int,
    width: int,
    grid_size: int = 5,
) -> np.ndarray:
    """Assign each pixel to a block in a grid_size × grid_size grid (row-major)."""
    block_row = (rows * grid_size // height).clip(0, grid_size - 1)
    block_col = (cols * grid_size // width).clip(0, grid_size - 1)
    return (block_row * grid_size + block_col).astype(np.int8)


def stratified_negative_sample(
    neg_rows: np.ndarray,
    neg_cols: np.ndarray,
    litho_arr: np.ndarray,
    n_total: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample n_total negatives from (neg_rows, neg_cols), stratified by
    litho_class.  Each stratum is sampled proportionally to its size.
    If a stratum is smaller than its quota, all of its pixels are taken.
    """
    litho_vals = litho_arr[neg_rows, neg_cols]
    classes, counts = np.unique(litho_vals, return_counts=True)
    total_neg = len(neg_rows)

    chosen_rows: list[np.ndarray] = []
    chosen_cols: list[np.ndarray] = []

    remaining = n_total
    for cls, cnt in zip(classes, counts):
        quota = round(n_total * cnt / total_neg)
        quota = min(quota, cnt, remaining)
        if quota <= 0:
            continue
        mask = litho_vals == cls
        idx  = np.where(mask)[0]
        sel  = rng.choice(idx, size=quota, replace=False)
        chosen_rows.append(neg_rows[sel])
        chosen_cols.append(neg_cols[sel])
        remaining -= quota

    # If rounding left us short, top up from any remaining negatives
    if remaining > 0:
        already = np.concatenate(chosen_rows) if chosen_rows else np.array([], int)
        used    = set(zip(already.tolist(), np.concatenate(chosen_cols).tolist())) if chosen_rows else set()
        all_idx = np.arange(len(neg_rows))
        spare   = np.array([i for i in all_idx if (neg_rows[i], neg_cols[i]) not in used])
        if len(spare) > 0:
            extra = rng.choice(spare, size=min(remaining, len(spare)), replace=False)
            chosen_rows.append(neg_rows[extra])
            chosen_cols.append(neg_cols[extra])

    out_rows = np.concatenate(chosen_rows) if chosen_rows else np.array([], int)
    out_cols = np.concatenate(chosen_cols) if chosen_cols else np.array([], int)
    return out_rows, out_cols


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    print("Loading rasters …")
    arrays, ref_profile, nodatas = load_rasters()

    height = ref_profile["height"]
    width  = ref_profile["width"]
    transform = ref_profile["transform"]

    print(f"  grid: {height} × {width} = {height * width:,} pixels")

    print("Building valid-pixel mask …")
    valid = build_valid_mask(arrays, nodatas)
    labels_arr = arrays["labels"]

    pos_mask = valid & (labels_arr == 1)
    neg_mask = valid & (labels_arr == 0)

    pos_rows, pos_cols = np.where(pos_mask)
    neg_rows, neg_cols = np.where(neg_mask)

    n_pos = len(pos_rows)
    n_neg_target = n_pos * NEG_RATIO

    print(f"  valid pixels  : {valid.sum():,}")
    print(f"  positives     : {n_pos:,}")
    print(f"  available neg : {len(neg_rows):,}  →  target {n_neg_target:,} ({NEG_RATIO}:1)")

    if len(neg_rows) < n_neg_target:
        print(f"  WARNING: fewer negatives available than target; taking all {len(neg_rows):,}")
        n_neg_target = len(neg_rows)

    print("Stratified sampling of negatives by litho_class …")
    litho_arr = arrays["litho_class"]
    samp_neg_rows, samp_neg_cols = stratified_negative_sample(
        neg_rows, neg_cols, litho_arr, n_neg_target, rng
    )
    n_neg_sampled = len(samp_neg_rows)
    print(f"  sampled negatives: {n_neg_sampled:,}")

    # --- Concatenate positives + negatives ---
    all_rows = np.concatenate([pos_rows, samp_neg_rows])
    all_cols = np.concatenate([pos_cols, samp_neg_cols])
    all_labels = np.concatenate([
        np.ones(n_pos, dtype=np.int8),
        np.zeros(n_neg_sampled, dtype=np.int8),
    ])

    # Shuffle so positives and negatives are interleaved
    order = rng.permutation(len(all_rows))
    all_rows   = all_rows[order]
    all_cols   = all_cols[order]
    all_labels = all_labels[order]

    print("Assigning spatial blocks (5×5 grid) …")
    spatial_block = assign_spatial_blocks(all_rows, all_cols, height, width, GRID_SIZE)
    block_counts = pd.Series(spatial_block).value_counts().sort_index()
    print(f"  blocks used: {(block_counts > 0).sum()} / {GRID_SIZE**2}")

    print("Building feature matrix …")
    xs, ys = xy(transform, all_rows, all_cols)  # centre of each pixel

    records: dict[str, np.ndarray] = {
        "row":           all_rows,
        "col":           all_cols,
        "x":             np.array(xs, dtype=np.float64),
        "y":             np.array(ys, dtype=np.float64),
        "spatial_block": spatial_block,
        "label":         all_labels,
    }
    for feat in FEATURE_COLS:
        arr = arrays[feat]
        records[feat] = arr[all_rows, all_cols]

    df = pd.DataFrame(records)

    # Reorder columns for readability
    col_order = (
        ["row", "col", "x", "y", "spatial_block", "label"]
        + FEATURE_COLS
    )
    df = df[col_order]

    print(f"\nDataFrame shape: {df.shape}")
    print(df.dtypes.to_string())
    print(f"\nLabel distribution:\n{df['label'].value_counts().to_string()}")

    print(f"\nSaving → {OUT_PATH} …")
    df.to_parquet(OUT_PATH, index=False)
    size_mb = OUT_PATH.stat().st_size / 1e6
    print(f"  saved {OUT_PATH}  ({size_mb:.1f} MB,  {len(df):,} rows)")

    print("\nFeature summary (valid pixels):")
    print(df[FEATURE_COLS].describe().to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
