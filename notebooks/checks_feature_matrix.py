# %% Imports & load
import json
import pandas as pd

df = pd.read_parquet("outputs/features/feature_matrix.parquet")

with open("data/geological-map/litho_class_mapping.json") as f:
    _litho_map = json.load(f)
LITHO_LABELS = {v: k for k, v in _litho_map.items()}  # int → name
print(f"Shape: {df.shape}")
print(df.dtypes.to_string())

# %% Label distribution
print("Label distribution:")
print(df["label"].value_counts().to_string())
print(f"\nPositive rate: {df['label'].mean():.3f}")

# %% Missing / nodata check
print("Null counts per column:")
print(df.isnull().sum().to_string())
print(f"\nRows with any null: {df.isnull().any(axis=1).sum()}")

# %% Feature summary stats
FEATURE_COLS = [
    "slope", "aspect", "profile_curvature", "planform_curvature",
    "twi", "flow_accumulation", "litho_class", "corine",
    "dist_drainage", "dist_roads",
]
print(df[FEATURE_COLS].describe().round(3).to_string())

# %% Slope by litho_class
print("Mean slope by litho_class (landslide pixels only):")
print(df[df["label"]==1].groupby("litho_class")["slope"].mean().rename(LITHO_LABELS).sort_values(ascending=False).round(2))

print("\nMean slope by litho_class (ALL pixels):")
print(df.groupby("litho_class")["slope"].mean().rename(LITHO_LABELS).sort_values(ascending=False).round(2))

# %% Pixel count of corine land cover
print(df[df["corine"].isin([331,332,333,334])]["label"].value_counts())
print(f"Bare/sparse pixels: {df['corine'].isin([331,332,333,334]).sum():,} out of {len(df):,}")
print(f"{(df['corine'].isin([331,332,333,334]).sum()/len(df))*100}% of total data")


# %% Pixel counts and landslide rate by litho_class
print("Pixel count and landslide rate by litho_class:")
print(df.groupby("litho_class")["label"].agg(["sum","count","mean"]).rename(
    index=LITHO_LABELS, columns={"sum":"n_landslide","count":"n_total","mean":"rate"}
).round(3).to_string())

# %% Median terrain metrics by litho_class (landslide pixels)
print("Median slope of landslide pixels by litho_class:")
print(df[df["label"]==1].groupby("litho_class")["slope"].median().rename(LITHO_LABELS).sort_values(ascending=False).round(1))

print("\nMedian TWI of landslide pixels by litho_class:")
print(df[df["label"]==1].groupby("litho_class")["twi"].median().rename(LITHO_LABELS).sort_values(ascending=False).round(2))

print("\nMedian dist_drainage of landslide pixels by litho_class:")
print(df[df["label"]==1].groupby("litho_class")["dist_drainage"].median().rename(LITHO_LABELS).sort_values().round(0))

# %% Spatial block distribution
block_stats = df.groupby("spatial_block")["label"].agg(["sum","count","mean"]).rename(
    columns={"sum":"n_landslide","count":"n_total","mean":"rate"}
)
print("Spatial block distribution:")
print(block_stats.to_string())
print(f"\nBlocks with >0 samples: {(block_stats['n_total']>0).sum()} / 25")

# %% Corine land cover distribution (landslide pixels)
print("Corine class distribution (landslide pixels):")
print(df[df["label"]==1]["corine"].value_counts().head(15).to_string())
