import geopandas as gpd
import pandas as pd

gdf = gpd.read_file("data/geological-map/geology_campania.geojson")

# Normalize nome_ulf for matching
gdf["nome_norm"] = gdf["nome_ulf"].str.lower().str.strip()

# Define lithology classes — domain knowledge encoded here
# This is part of your KB: expert rules mapping formation names to stability classes
litho_map = {
    "volcanic_pyroclastic": [
        "tufo", "tufi", "ignimbrite", "pomici", "piroclastic",
        "piroclastici", "tefrite", "tefriti", "ceneri", "pozzolan",
        "lapilli", "scorie", "vulcan", "neosomma", "lahar",
        "lave", "trachitic", "foitid", "leucit"
    ],
    "slope_deposits": [
        "detrito di falda", "detriti di falda", "detrito in parte",
        "detrito sciolto", "eluvial", "colluvial", "accumulo",
        "dilavamento", "olistolit"
    ],
    "clay_marl": [
        "argill", "marn", "argilloscist", "flysch",
        "scisti silicei", "diaspri", "silicei"
    ],
    "sandstone_arenite": [
        "arenacea", "arenarie", "sabbie", "quarzos", "arenaceo",
        "monte facito", "daunia"          # formation names known to be sandy
    ],
    "limestone_dolomite": [
        "calcar", "calcilutit", "calcarenit", "dolomie", "dolomit",
        "calcari", "calcare", "travertino"
    ],
    "alluvial": [
        "alluvion", "alluviali", "fluvial", "depositi alluvion",
        "fluvio-lacustr", "lacustr", "ciottolami", "conoide",
        "conoidi", "terrazzo", "spiagge", "duna", "litoranea",
        "bonifica"
    ],
    "conglomerate_breccia": [
        "conglomer", "brecce", "brecciole", "puddinghe"
    ],
    "residual_soil": [
        "terre rosse", "terra rossa", "suoli", "paleosuol",
        "serie comprensiva"
    ],
}

def classify_litho(name):
    if pd.isna(name):
        return "unknown"
    name_lower = name.lower()
    for cls, keywords in litho_map.items():
        if any(kw in name_lower for kw in keywords):
            return cls
    return "other"

gdf["litho_class"] = gdf["nome_norm"].apply(classify_litho)

print("Lithology class distribution:")
print(gdf["litho_class"].value_counts())
print(f"\nUnclassified 'other': {(gdf['litho_class'] == 'other').sum()}")
print(f"Unclassified 'unknown': {(gdf['litho_class'] == 'unknown').sum()}")

# Show what's in 'other' so we can add missing keywords
print("\nSample 'other' nome_ulf values:")
print(gdf[gdf["litho_class"] == "other"]["nome_ulf"].value_counts().head(20))

gdf.to_file("data/geological-map/geology_campania_classified.geojson", driver="GeoJSON")
print("\nSaved classified geology.")
