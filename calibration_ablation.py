"""
Calibration analysis and single-gene ablation for the PDAC RandomForest classifier.

Two modular analyses:
  1. run_calibration  – reliability of predicted probabilities (calibration curve + Brier score)
  2. run_ablation     – single-gene knockout robustness (KRAS, TP53, SMAD4)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20

# ── Paths ────────────────────────────────────────────────────────────────────
DEFAULT_DATA_PATH = Path("mutation_matrix.csv")
DEFAULT_GENE_PANEL_PATH = Path("src/data/gene_panel.json")
CALIBRATION_PLOT_PATH = Path("calibration_curve.png")

# ── Genes to ablate ──────────────────────────────────────────────────────────
ABLATION_GENES: list[str] = ["KRAS", "TP53", "SMAD4"]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_gene_panel_genes(gene_panel_path: Path) -> list[str]:
    """Return ordered gene symbols from the panel JSON."""
    panel = json.loads(gene_panel_path.read_text())
    genes = [g["gene_symbol"] for g in panel.get("genes", [])]
    if not genes:
        raise ValueError(f"No genes found in panel file: {gene_panel_path}")
    return genes


def load_data(
    data_path: Path = DEFAULT_DATA_PATH,
    gene_panel_path: Path = DEFAULT_GENE_PANEL_PATH,
) -> tuple[pd.DataFrame, pd.Series]:
    """Load mutation-matrix CSV, keeping only gene-panel columns as features."""
    df = pd.read_csv(data_path)

    if "label" not in df.columns:
        raise ValueError("CSV must contain a 'label' column.")

    panel_genes = load_gene_panel_genes(gene_panel_path)
    available = [g for g in panel_genes if g in df.columns]

    if not available:
        raise ValueError("No gene-panel columns found in dataset.")

    y = df["label"].astype(int)
    X = df[available].copy()
    return X, y


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def build_model(random_state: int = RANDOM_STATE) -> RandomForestClassifier:
    """Return an untrained RandomForestClassifier with fixed hyper-parameters."""
    return RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        class_weight="balanced",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════════

def run_calibration(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_bins: int = 10,
    plot_path: Path = CALIBRATION_PLOT_PATH,
) -> float:
    """
    Evaluate probability calibration of a fitted model on held-out test data.

    Steps
    -----
    1. Obtain predicted probabilities for the positive class.
    2. Compute calibration curve (fraction of positives vs mean predicted probability).
    3. Plot calibration curve with a perfect-calibration diagonal.
    4. Compute and return Brier score.

    Parameters
    ----------
    model      : Fitted sklearn classifier with predict_proba.
    X_test     : Test feature matrix.
    y_test     : True binary labels.
    n_bins     : Number of bins for the calibration curve.
    plot_path  : Where to save the calibration curve PNG.

    Returns
    -------
    brier : float  Brier score (lower is better; 0 = perfect).
    """
    y_prob = model.predict_proba(X_test)[:, 1]

    # Calibration curve ---------------------------------------------------------
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_test, y_prob, n_bins=n_bins, strategy="uniform"
    )

    brier = brier_score_loss(y_test, y_prob)

    # ── Plot ───────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 6))

    ax.plot(
        mean_predicted_value,
        fraction_of_positives,
        marker="o",
        label="RandomForest",
    )
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")

    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives (true probability)")
    ax.set_title("Calibration Curve — PDAC Classifier")
    ax.legend()
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)

    # ── Console output ─────────────────────────────────────────────────────────
    print("\n── Calibration Analysis ────────────────────────────────────────────")
    print(f"  Brier score          : {brier:.4f}")

    if brier < 0.10:
        interpretation = "Excellent — probabilities are highly reliable."
    elif brier < 0.20:
        interpretation = "Good — probabilities are reasonably reliable."
    elif brier < 0.25:
        interpretation = "Moderate — some probability over/under-confidence."
    else:
        interpretation = "Poor — probabilities are not well calibrated."

    print(f"  Interpretation       : {interpretation}")
    print(f"  Calibration plot     : {plot_path}")

    return brier


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — SINGLE-GENE ABLATION
# ═══════════════════════════════════════════════════════════════════════════════

def _auc_for_features(
    X: pd.DataFrame,
    y: pd.Series,
    features: list[str],
    random_state: int = RANDOM_STATE,
) -> float:
    """Train a fresh model on `features` subset and return test ROC-AUC."""
    X_sub = X[features]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_sub, y, test_size=TEST_SIZE, random_state=random_state, stratify=y
    )
    clf = build_model(random_state)
    clf.fit(X_tr, y_tr)
    y_prob = clf.predict_proba(X_te)[:, 1]
    return roc_auc_score(y_te, y_prob)


def run_ablation(
    X: pd.DataFrame,
    y: pd.Series,
    genes_to_ablate: list[str] = ABLATION_GENES,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Single-gene ablation study: measure AUC drop when each driver gene is removed.

    For each gene in `genes_to_ablate`:
      - Drop that column from X.
      - Retrain from scratch using the same train/test split seed.
      - Record ROC-AUC and ΔAUC vs baseline (all genes).

    Parameters
    ----------
    X               : Full feature matrix (all genes).
    y               : Binary labels.
    genes_to_ablate : Genes to test; skipped if not present as a column in X.
    random_state    : Seed passed to train_test_split and RandomForestClassifier.

    Returns
    -------
    results_df : DataFrame with columns [gene_removed, auc, delta_vs_baseline].
    """
    all_features = list(X.columns)

    # ── Baseline ───────────────────────────────────────────────────────────────
    baseline_auc = _auc_for_features(X, y, all_features, random_state)

    rows: list[dict] = [
        {"gene_removed": "None (Baseline)", "auc": baseline_auc, "delta_vs_baseline": None}
    ]

    # ── Per-gene ablation ──────────────────────────────────────────────────────
    for gene in genes_to_ablate:
        if gene not in X.columns:
            print(f"  [skip] '{gene}' not found in feature matrix — skipping ablation.")
            continue

        reduced_features = [f for f in all_features if f != gene]
        auc = _auc_for_features(X, y, reduced_features, random_state)
        delta = auc - baseline_auc
        rows.append({"gene_removed": gene, "auc": auc, "delta_vs_baseline": delta})

    results_df = pd.DataFrame(rows)

    # ── Console output ─────────────────────────────────────────────────────────
    print("\n── Single-Gene Ablation ────────────────────────────────────────────")
    header = f"{'Gene Removed':<20} | {'AUC':>6} | {'Δ vs Baseline':>14}"
    print(header)
    print("-" * len(header))

    for _, row in results_df.iterrows():
        gene_col = str(row["gene_removed"])
        auc_col = f"{row['auc']:.4f}"
        if pd.isna(row["delta_vs_baseline"]):
            delta_col = "—"
        else:
            delta_val = float(row["delta_vs_baseline"])
            sign = "+" if delta_val >= 0 else ""
            delta_col = f"{sign}{delta_val:.4f}"
        print(f"{gene_col:<20} | {auc_col:>6} | {delta_col:>14}")

    return results_df


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Load data, train baseline model, run calibration, run ablation."""
    print("═" * 60)
    print("  PDAC Classifier — Calibration & Ablation Analysis")
    print("═" * 60)

    # ── Load ───────────────────────────────────────────────────────────────────
    X, y = load_data()
    print(f"\nDataset : {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Classes : 0 = {int((y == 0).sum())}, 1 = {int((y == 1).sum())}")

    # ── Train/test split ───────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # ── Baseline model ─────────────────────────────────────────────────────────
    model = build_model(RANDOM_STATE)
    model.fit(X_train, y_train)
    print(f"\nBaseline model trained on {X_train.shape[0]} samples.")

    # ── Part 1: Calibration ────────────────────────────────────────────────────
    run_calibration(model, X_test, y_test)

    # ── Part 2: Ablation ───────────────────────────────────────────────────────
    run_ablation(X, y)

    print("\n" + "═" * 60)
    print("  Analysis complete.")
    print("═" * 60)


if __name__ == "__main__":
    main()
