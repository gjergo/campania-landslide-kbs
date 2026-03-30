# %% Imports & load
import geopandas as gpd

gdf = gpd.read_file("data/geological-map/geology_campania_classified.geojson")
gdf = gdf.to_crs("EPSG:32633")
print(f"{len(gdf)} polygons")
print(gdf.columns.tolist())

# %% Class distribution
CLASS_CODES = {
    "unknown":              0,
    "unconsolidated_weak":  1,
    "volcanic_pyroclastic": 2,
    "flysch_clastic":       3,
    "competent_clastic":    4,
    "hard_rock":            5,
}

vc = gdf["litho_class"].value_counts()
total = len(gdf)
print("Class distribution (polygon count):")
for cls, count in vc.items():
    code = CLASS_CODES.get(cls, -1)
    print(f"  [{code}] {cls:<25} {count:>5}  ({count/total:.1%})")

# %% Area coverage by class
gdf["area_km2"] = gdf.geometry.area / 1e6
area_by_class = gdf.groupby("litho_class")["area_km2"].sum().sort_values(ascending=False)
total_area = area_by_class.sum()
print("Area coverage by class (km²):")
for cls, area in area_by_class.items():
    print(f"  {cls:<25} {area:>8.1f} km²  ({area/total_area:.1%})")

# %% Unknown polygons — what is unclassified?
unk = gdf[gdf["litho_class"] == "unknown"]
print(f"Unknown polygons: {len(unk)} ({len(unk)/total:.1%})")
print("\nTop unclassified nome_ulf values:")
print(unk["nome_ulf"].value_counts().head(20).to_string())

# %% Spot-check per class — sample names for each class
for cls in CLASS_CODES:
    sub = gdf[gdf["litho_class"] == cls]["nome_ulf"].dropna()
    sample = sub.value_counts().head(5).index.tolist()
    print(f"\n[{cls}]")
    for name in sample:
        print(f"  {name}")

# %% Tile boundary artifact check
# The geological map was assembled from tiles — check for suspicious alignment
bounds = gdf.bounds
print("Y extents (northing), rounded to nearest km — repeating values = tile edges:")
print(sorted(bounds["maxy"].round(-3).unique())[:20])
print("\nX extents (easting):")
print(sorted(bounds["maxx"].round(-3).unique())[:20])

# %% Geometry validity
invalid = gdf[~gdf.geometry.is_valid]
print(f"Invalid geometries: {len(invalid)}")
empty = gdf[gdf.geometry.is_empty]
print(f"Empty geometries:   {len(empty)}")

