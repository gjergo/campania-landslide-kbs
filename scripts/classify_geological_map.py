"""
clean_geological_map.py

Classifies ISPRA geological units into 5 geotechnically meaningful groups
based on failure mechanism, following Catani et al. (2013) grouping approach.

Classes:
  1 - unconsolidated_weak     (slope deposits, alluvial, residual soils)
  2 - volcanic_pyroclastic    (tuffs, lavas, pyroclastics - unique Campanian behavior)
  3 - flysch_clastic          (clay, marl, sandstone - same flysch sequence, diff names)
  4 - competent_clastic       (conglomerates, breccias - cemented, stronger)
  5 - hard_rock               (limestone, dolomite - high strength, karst drainage)
  0 - unknown                 (nodata)

Reference: Catani F. et al. (2013), Landslide susceptibility estimation by random
forests technique, Nat. Hazards Earth Syst. Sci., 13, 2815-2831.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

SRC = Path("data/geological-map/geology_campania.geojson")
DST = Path("data/geological-map/geology_campania_classified.geojson")

# ---------------------------------------------------------------------------
# Keyword lists — order within each group does not matter,
# but groups are checked in priority order below.
# ---------------------------------------------------------------------------

KEYWORDS = {
    # Group 2 — volcanic/pyroclastic first because some names contain both
    # volcanic AND clastic terms (e.g. "breccia vulcanica")
    "volcanic_pyroclastic": [
        "tufo", "tufi", "tufite", "tufiti", "ignimbrite",
        "pomici", "pomice", "piroclast", "cinerite", "ceneri",
        "pozzolan", "lapilli", "scorie", "neosomma", "lahar",
        "lave", "lava", "lavici", "lavica",
        "trachit", "fonolite", "fonolit", "leucit", "tefrit",
        "vulcan", "vesuvian", "eruzioni", "solfatara", "fumarol",
        "basalt", "basanit", "agglomerat", "colate di",
        "prodotti piroclast", "prodotti vulcan", "vulsinite", "trachiandesite"
    ],
    # Group 1 — unconsolidated/weak
    "unconsolidated_weak": [
        "detrito di falda", "detriti di falda", "detrito in parte",
        "detrito sciolto", "detrito cementato", "falde detritic",
        "depositi detritici", "depositi eluvial", "depositi di versante",
        "breccia di pendio", "corpi di antiche frane", "frane",
        "olistolit", "accumulo", "colluvial", "dilavamento",
        "alluvion", "alluviali", "fluvial", "fluvio-lacustr", "lacustr",
        "ciottolami", "ciottolame", "depositi di ciottoli",
        "copertura ciottolosa", "conoide", "conoidi",
        "terrazzo", "terrazzi", "spiagge", "duna", "litoranea",
        "bonifica", "terreni umiferi", "colmata",
        "terre rosse", "terra rossa", "suoli", "paleosuol",
        "serie comprensiva", "depositi terrazzati",
        "eluvial", "prodotti di dilavamento", "coni di deiezione",
        "dune", "fogliarina"
    ],
    # Group 3 — flysch/clastic (clay + sandstone merged)
    "flysch_clastic": [
        "argill", "marn", "argilloscist", "flysch",
        "scisti silicei", "diaspri", "silicei", "argillite",
        "arenari", "arenace", "sabbie", "sabbion", "quarzos",
        "molasse", "molassic", "quarzoareniti",
        "daunia", "stigliano", "monte facito", "ascea",
        "complesso calcareo-marnoso", "complesso marnoso",
    ],
    # Group 4 — competent clastic
    "competent_clastic": [
        "conglomer", "brecce", "brecciole", "puddinghe",
        "breccia poligenica", "ciottoli poligenici",
    ],
    # Group 5 — hard rock
    "hard_rock": [
        "calcar", "calcilutit", "calcarenit", "calcirudit",
        "dolomie", "dolomit", "dolomia",
        "calcari", "calcare", "travertino", "travertini",
        "bauxite", "gessi", "gesso", "evaporit",
        "selce", "selciferi", "noduli di selce",
        "serpentin", "ofioliti", "concrezione calcitica",
        "facies paleodetritica", "serie carbonatica",
        "formazione di s. mauro", 
    ],
}

# Named formations with cross-tile inconsistency — pin to correct class
NAMED_OVERRIDES = {
    "daunia": "flysch_clastic",
    "stigliano": "flysch_clastic",
    "monte facito": "flysch_clastic",
    "formazione di ascea": "flysch_clastic",
    "complesso indifferenziato": None,   # genuinely unclassifiable → unknown
    "complesso indiferenziato": None,
    "discariche": None,                  # landfill, not geological
    "resti archeologici": None,
}

# Integer codes for the raster
CLASS_CODES = {
    "unknown":              0,
    "unconsolidated_weak":  1,
    "volcanic_pyroclastic": 2,
    "flysch_clastic":       3,
    "competent_clastic":    4,
    "hard_rock":            5,
}


def classify(name: str) -> str:
    if pd.isna(name) or str(name).strip() == "":
        return "unknown"

    low = name.lower().strip()

    # 1. Named overrides (cross-tile consistency)
    for key, cls in NAMED_OVERRIDES.items():
        if key in low:
            return cls if cls else "unknown"

    # 2. Volcanic check FIRST — some volcanic names contain calcar/brecce terms
    for kw in KEYWORDS["volcanic_pyroclastic"]:
        if kw in low:
            return "volcanic_pyroclastic"

    # 3. Hard rock — check before flysch because "calcari marnosi" starts with calcari
    #    but also contains marn; we want hard_rock to win for carbonate-primary names
    carbonate_starts = (
        "calcarenit", "calcilutit", "calcirudit", "calcari ", "calcare ",
        "dolomie", "dolomia", "dolomit",
    )
    if low.startswith(carbonate_starts):
        return "hard_rock"

    # 4. General keyword matching in priority order
    for cls in ["unconsolidated_weak", "flysch_clastic", "competent_clastic", "hard_rock"]:
        for kw in KEYWORDS[cls]:
            if kw in low:
                return cls

    return "unknown"


def main():
    print(f"Reading {SRC} ...")
    gdf = gpd.read_file(SRC)
    print(f"  {len(gdf)} polygons")

    gdf["litho_class"] = gdf["nome_ulf"].apply(classify)
    gdf["litho_code"] = gdf["litho_class"].map(CLASS_CODES)

    print("\nClass distribution:")
    vc = gdf["litho_class"].value_counts()
    total = len(gdf)
    for cls, count in vc.items():
        code = CLASS_CODES.get(cls, -1)
        print(f"  [{code}] {cls:<25} {count:>5}  ({count/total:.1%})")

    unknown_count = (gdf["litho_class"] == "unknown").sum()
    print(f"\nUnclassified: {unknown_count} ({unknown_count/total:.1%})")
    if unknown_count > 0:
        print("Sample unclassified nome_ulf:")
        print(gdf[gdf["litho_class"] == "unknown"]["nome_ulf"]
              .value_counts().head(15).to_string())

    print(f"\nSaving to {DST} ...")
    gdf.to_file(DST, driver="GeoJSON")
    print("Done.")

    # Also save the mapping for use in rasterization
    import json
    mapping_path = Path("data/geological-map/litho_class_mapping.json")
    with open(mapping_path, "w") as f:
        json.dump(CLASS_CODES, f, indent=2)
    print(f"Saved class mapping to {mapping_path}")


if __name__ == "__main__":
    main()
