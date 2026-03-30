"""
Train and evaluate ML models for landslide susceptibility.

Steps:
  1. KB standalone evaluation (expert-rules baseline)
  2. Stratified k-fold CV for LogisticRegression and RandomForest
     - with and without kb_susceptibility feature
  3. Feature importance from RandomForest (full fit)
  4. Save cv_results.csv and feature_importance.csv
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

OUTPUTS = Path("outputs/features")
FEATURE_MATRIX = OUTPUTS / "feature_matrix.parquet"

ALL_FEATURES = [
    "slope",
    "aspect",
    "profile_curvature",
    "planform_curvature",
    "twi",
    "flow_accumulation",
    "litho_class",
    "corine",
    "dist_drainage",
    "dist_roads",
    "kb_susceptibility",
]
LABEL = "label"


def kb_evaluate(df: pd.DataFrame) -> None:
    """Evaluate kb_susceptibility as a standalone rule-based classifier."""
    print("\n=== Step 1: KB standalone evaluation ===")
    y_true = df[LABEL].values
    # Scores >= 1 are treated as positive (landslide susceptible)
    y_pred = (df["kb_susceptibility"].values >= 1).astype(int)
    y_score = df["kb_susceptibility"].values.astype(float)

    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_score)

    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1        : {f1:.4f}")
    print(f"  AUC-ROC   : {auc:.4f}")


def run_cv(
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    feature_set_name: str,
    scale: bool,
) -> list[dict]:
    """Run stratified k-fold CV and return per-fold metrics."""
    # NOTE: Spatial block CV would be more rigorous (avoids spatial
    # autocorrelation leakage between folds) but standard stratified CV
    # is used here given project scope constraints.
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    fold_results = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        t0 = time.time()
        print(f"  [{model_name} | {feature_set_name}] fold {fold_idx}/5 ...", end=" ", flush=True)

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if scale:
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

        if model_name == "LogisticRegression":
            model = LogisticRegression(max_iter=1000, random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        fold_results.append(
            {
                "model": model_name,
                "feature_set": feature_set_name,
                "fold": fold_idx,
                "auc": roc_auc_score(y_test, y_prob),
                "f1": f1_score(y_test, y_pred, average="binary", zero_division=0),
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
            }
        )
        print(f"done ({time.time() - t0:.1f}s) | AUC={fold_results[-1]['auc']:.4f} F1={fold_results[-1]['f1']:.4f}")

    return fold_results


def summarise(fold_records: list[dict]) -> pd.DataFrame:
    """Aggregate fold metrics to mean ± std summary rows."""
    df = pd.DataFrame(fold_records)
    rows = []
    for (model, fset), grp in df.groupby(["model", "feature_set"]):
        for metric in ("auc", "f1", "precision", "recall"):
            rows.append(
                {
                    "model": model,
                    "feature_set": fset,
                    "metric": metric,
                    "mean": grp[metric].mean(),
                    "std": grp[metric].std(),
                }
            )
    return pd.DataFrame(rows)


def feature_importance(df: pd.DataFrame, features_with_kb: list[str]) -> None:
    """Refit RF on full data and save feature importances."""
    print("\n=== Step 4: Feature importance (RandomForest, full fit) ===")
    X = df[features_with_kb].values
    y = df[LABEL].values

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    print("  Fitting RandomForest on full dataset ...", end=" ", flush=True)
    t0 = time.time()
    rf.fit(X, y)
    print(f"done ({time.time() - t0:.1f}s)")

    imp = pd.DataFrame(
        {"feature": features_with_kb, "importance": rf.feature_importances_}
    ).sort_values("importance", ascending=False)

    out_path = OUTPUTS / "feature_importance.csv"
    imp.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")
    print(imp.to_string(index=False))


def main() -> None:
    print(f"Loading {FEATURE_MATRIX} ...")
    df = pd.read_parquet(FEATURE_MATRIX)
    print(f"  Shape: {df.shape}")
    print(f"  Label balance: {df[LABEL].value_counts().to_dict()}")

    # ------------------------------------------------------------------ #
    # Step 1: KB baseline
    # ------------------------------------------------------------------ #
    kb_evaluate(df)

    # ------------------------------------------------------------------ #
    # Feature sets
    # ------------------------------------------------------------------ #
    features_with_kb = ALL_FEATURES
    features_without_kb = [f for f in ALL_FEATURES if f != "kb_susceptibility"]

    # ------------------------------------------------------------------ #
    # Step 2 & 3: CV
    # ------------------------------------------------------------------ #
    print("\n=== Step 2 & 3: Stratified k-fold CV ===")
    all_fold_records: list[dict] = []

    for model_name, scale in [("LogisticRegression", True), ("RandomForest", False)]:
        for feat_name, feat_cols in [
            ("with_kb", features_with_kb),
            ("without_kb", features_without_kb),
        ]:
            X = df[feat_cols].values
            y = df[LABEL].values
            records = run_cv(X, y, model_name, feat_name, scale=scale)
            all_fold_records.extend(records)

    # ------------------------------------------------------------------ #
    # Step 4: Feature importance
    # ------------------------------------------------------------------ #
    feature_importance(df, features_with_kb)

    # ------------------------------------------------------------------ #
    # Step 5: Save and print summary
    # ------------------------------------------------------------------ #
    print("\n=== Step 5: Summary ===")
    summary = summarise(all_fold_records)

    out_path = OUTPUTS / "cv_results.csv"
    summary.to_csv(out_path, index=False)
    print(f"Saved → {out_path}\n")

    # Pretty-print: show mean ± std side-by-side
    pivot = summary.copy()
    pivot["value"] = pivot.apply(lambda r: f"{r['mean']:.4f} ± {r['std']:.4f}", axis=1)
    table = pivot.pivot_table(
        index=["model", "feature_set"], columns="metric", values="value", aggfunc="first"
    )
    print(table.to_string())


if __name__ == "__main__":
    main()
