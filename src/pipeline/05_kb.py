"""
05_kb.py – Apply Prolog KB inference to add kb_susceptibility column.

For each unique (litho_class, slope_bin, dist_bin, corine) combination in the
feature matrix, queries susceptibility_score/5 from the Prolog KB and maps the
result (0=low, 1=medium, 2=high) back to all matching rows via a join.

Slope is binned to 0.5° increments and dist_drainage to 50 m increments to
keep the number of unique Prolog calls in the low thousands rather than the
~6 M rows in the full matrix.  CORINE codes are integer categoricals and are
not binned.

Output: outputs/features/feature_matrix.parquet (overwrite, adds kb_susceptibility)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from pyswip import Prolog

KB_PATH      = Path("src/kb/landslide_kb.pl")
LITHO_MAP    = Path("data/geological-map/litho_class_mapping.json")
FEATURE_PATH = Path("outputs/features/feature_matrix.parquet")

SLOPE_BIN_SIZE = 0.5   # degrees
DIST_BIN_SIZE  = 50.0  # metres


def load_litho_labels() -> dict[int, str]:
    with open(LITHO_MAP) as f:
        mapping = json.load(f)
    return {v: k for k, v in mapping.items()}  # int → name


def query_kb(
    prolog: Prolog,
    combos: pd.DataFrame,
    litho_labels: dict[int, str],
) -> pd.DataFrame:
    """Query susceptibility_score for each unique combo row.

    Takes only the first Prolog solution (highest-priority match) since the
    catch-all clause would otherwise add spurious lower-score solutions.
    """
    scores: list[int] = []
    for row in combos.itertuples(index=False):
        litho_name = litho_labels.get(int(row.litho_class), "unknown")
        slope  = float(row.slope_bin)
        dist   = float(row.dist_bin)
        corine = int(row.corine)
        query  = f"susceptibility_score({litho_name}, {slope}, {dist}, {corine}, Score)"
        result = next(prolog.query(query), None)
        scores.append(int(result["Score"]) if result is not None else 0)

    combos = combos.copy()
    combos["kb_susceptibility"] = np.array(scores, dtype=np.int8)
    return combos


def print_summary(df: pd.DataFrame) -> None:
    print("\n--- KB susceptibility summary ---")
    for label_val, label_name in [(1, "landslide (label=1)"), (0, "background (label=0)")]:
        sub = df[df["label"] == label_val]["kb_susceptibility"]
        total = len(sub)
        print(f"\n  {label_name}  (n={total:,})")
        for score, sname in [(2, "high"), (1, "medium"), (0, "low")]:
            n = (sub == score).sum()
            print(f"    score={score} ({sname:6s}): {n:7,}  ({100 * n / total:.1f}%)")


def main() -> None:
    print("Loading feature matrix …")
    df = pd.read_parquet(FEATURE_PATH)
    print(f"  {df.shape[0]:,} rows, {df.shape[1]} columns")

    litho_labels = load_litho_labels()
    print(f"  litho labels: {litho_labels}")

    # Bin continuous features to reduce unique Prolog calls
    df["slope_bin"] = (df["slope"] / SLOPE_BIN_SIZE).round() * SLOPE_BIN_SIZE
    df["dist_bin"]  = (df["dist_drainage"] / DIST_BIN_SIZE).round() * DIST_BIN_SIZE

    combos = (
        df[["litho_class", "slope_bin", "dist_bin", "corine"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    print(f"  unique (litho, slope_bin, dist_bin, corine) combos: {len(combos):,}")

    print(f"Loading Prolog KB from {KB_PATH} …")
    prolog = Prolog()
    prolog.consult(str(KB_PATH.resolve()))

    print("Querying KB for unique combinations …")
    combos = query_kb(prolog, combos, litho_labels)
    score_dist = combos["kb_susceptibility"].value_counts().sort_index()
    print(f"  score distribution across combos:\n{score_dist.to_string()}")

    # Join scores back to main dataframe (drop stale column if re-running)
    if "kb_susceptibility" in df.columns:
        df = df.drop(columns=["kb_susceptibility"])
    df = df.merge(combos, on=["litho_class", "slope_bin", "dist_bin", "corine"], how="left")
    df["kb_susceptibility"] = df["kb_susceptibility"].fillna(0).astype(np.int8)
    df = df.drop(columns=["slope_bin", "dist_bin"])

    print_summary(df)

    print(f"\nSaving → {FEATURE_PATH} …")
    df.to_parquet(FEATURE_PATH, index=False)
    size_mb = FEATURE_PATH.stat().st_size / 1e6
    print(f"  saved {FEATURE_PATH}  ({size_mb:.1f} MB,  {len(df):,} rows)")

    print("\nDone.")


if __name__ == "__main__":
    main()
