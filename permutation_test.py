"""
Permutation test for validating a PDAC mutation-based classifier.

Usage
-----
    from permutation_test import run_permutation_test
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
    results = run_permutation_test(model, X, y, n_permutations=100)
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def run_permutation_test(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 100,
    test_size: float = 0.2,
    random_state: int = 42,
    plot_path: Optional[Path] = None,
) -> dict:
    """
    Validate a classifier by comparing its ROC-AUC against a null distribution
    produced by training on randomly shuffled labels.

    Parameters
    ----------
    model : sklearn estimator
        An untrained (or freshly cloned) classifier with a predict_proba method.
    X : pd.DataFrame
        Binary gene mutation feature matrix (samples × genes).
    y : pd.Series
        Binary labels — 0 = early-stage, 1 = late-stage.
    n_permutations : int
        Number of shuffle-and-retrain iterations (default 100).
    test_size : float
        Fraction of data held out for evaluation (default 0.2 = 80/20 split).
    random_state : int
        Seed for reproducibility across split, real model, and permutation RNG.
    plot_path : Path or None
        If provided, saves the histogram to this path; otherwise displays inline.

    Returns
    -------
    dict with keys:
        real_auc   (float)  – AUC of the model trained on real labels
        perm_aucs  (list)   – AUC values for each permutation
        mean_perm  (float)  – mean of perm_aucs
        std_perm   (float)  – std  of perm_aucs
        p_value    (float)  – empirical p-value
    """
    # ------------------------------------------------------------------
    # 1) Train the real model on the actual (unshuffled) labels
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    real_model = clone(model)
    real_model.set_params(random_state=random_state)
    real_model.fit(X_train, y_train)
    real_scores = real_model.predict_proba(X_test)[:, 1]
    real_auc = float(roc_auc_score(y_test, real_scores))

    # ------------------------------------------------------------------
    # 2) Permutation loop — shuffle training labels, retrain, evaluate
    # ------------------------------------------------------------------
    perm_aucs: list[float] = []

    for i in range(n_permutations):
        # Shuffle only the training labels so the test set remains intact.
        # reset_index(drop=True) realigns the index to match X_train after shuffling.
        y_train_shuffled = y_train.sample(frac=1, random_state=i).reset_index(drop=True)
        y_train_shuffled.index = y_train.index  # restore original index for alignment

        # Clone ensures a brand-new model each iteration (no state leakage)
        perm_model = clone(model)
        perm_model.set_params(random_state=random_state + i + 1)
        perm_model.fit(X_train, y_train_shuffled)

        perm_scores = perm_model.predict_proba(X_test)[:, 1]
        perm_aucs.append(float(roc_auc_score(y_test, perm_scores)))

    # ------------------------------------------------------------------
    # 3) Statistics
    # ------------------------------------------------------------------
    mean_perm = float(np.mean(perm_aucs))
    std_perm  = float(np.std(perm_aucs, ddof=1))

    # Empirical p-value: proportion of permuted AUCs >= real AUC
    # Adding 1 to numerator and denominator avoids a p-value of exactly 0
    p_value = (sum(auc >= real_auc for auc in perm_aucs) + 1) / (n_permutations + 1)

    # ------------------------------------------------------------------
    # 4) Visualization — histogram of null distribution with real AUC marker
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(perm_aucs, bins=20, color="cornflowerblue", edgecolor="black",
            alpha=0.85, label="Permuted AUC (null distribution)")
    ax.axvline(real_auc, color="crimson", linestyle="--", linewidth=2,
               label=f"Real AUC = {real_auc:.3f}")
    ax.axvline(mean_perm, color="darkorange", linestyle=":", linewidth=1.5,
               label=f"Mean permuted AUC = {mean_perm:.3f}")

    ax.set_title("Permutation Test: ROC-AUC Distribution", fontsize=14)
    ax.set_xlabel("ROC-AUC",  fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.legend()
    fig.tight_layout()

    if plot_path is not None:
        fig.savefig(plot_path, dpi=160)
        plt.close(fig)
    else:
        plt.show()

    # ------------------------------------------------------------------
    # 5) Console output
    # ------------------------------------------------------------------
    print("\nPermutation Test Results")
    print("=" * 32)
    print(f"Real AUC           : {real_auc:.4f}")
    print(f"Mean Permuted AUC  : {mean_perm:.4f}")
    print(f"Std  Permuted AUC  : {std_perm:.4f}")
    print(f"Empirical p-value  : {p_value:.4f}")
    if p_value < 0.05:
        print("→ Model performance is statistically significant (p < 0.05)")
    else:
        print("→ No significant improvement over random (p ≥ 0.05)")

    return {
        "real_auc":  real_auc,
        "perm_aucs": perm_aucs,
        "mean_perm": mean_perm,
        "std_perm":  std_perm,
        "p_value":   p_value,
    }


# ---------------------------------------------------------------------------
# Multi-model permutation test runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import warnings
    warnings.filterwarnings("ignore")

    import numpy as np
    import pandas as pd
    from pathlib import Path
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    ROOT = Path(__file__).parent
    sys.path.insert(0, str(ROOT))
    from create_synthetic_data import generate_multimodal_pdac_data

    N_PERM = 100
    DIVIDER = "═" * 60
    all_results: dict[str, dict] = {}

    # ── Shared data ──────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  Generating biologically realistic PDAC multi-modal dataset …")
    print(DIVIDER)
    X_genomic, X_transcriptomic, y_arr = generate_multimodal_pdac_data(
        n_samples=200, random_state=42
    )
    y_series = pd.Series(y_arr, name="label")
    print(f"  X_genomic        : {X_genomic.shape}")
    print(f"  X_transcriptomic : {X_transcriptomic.shape}")
    print(f"  y                : {y_series.shape}  "
          f"(early={int((y_series==0).sum())}, late={int((y_series==1).sum())})")

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 1 — Genomic · RandomForest
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 1 — Genomic  ·  RandomForestClassifier")
    print(DIVIDER)
    genomic_rf = RandomForestClassifier(
        n_estimators=300, max_depth=6,
        class_weight="balanced", random_state=42,
    )
    res = run_permutation_test(
        genomic_rf, X_genomic, y_series,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_genomic_rf.png",
    )
    all_results["Genomic · RandomForest"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 2 — Genomic · Logistic Regression (L1)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 2 — Genomic  ·  LogisticRegression (L1)")
    print(DIVIDER)
    genomic_lr = LogisticRegression(
        penalty="l1", solver="liblinear", C=1.0,
        class_weight="balanced", max_iter=1000, random_state=42,
    )
    res = run_permutation_test(
        genomic_lr, X_genomic, y_series,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_genomic_lr.png",
    )
    all_results["Genomic · LogisticRegression (L1)"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 3 — Transcriptomic · Logistic Regression
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 3 — Transcriptomic  ·  LogisticRegression")
    print(DIVIDER)
    # log2 + z-score normalisation (mirrors transcriptomic_classifier.py)
    X_trx_raw = np.abs(X_transcriptomic)   # expression values are already z-like
    X_trx_log = np.log2(X_trx_raw + 1.0)
    scaler = StandardScaler()
    X_trx_norm = pd.DataFrame(
        scaler.fit_transform(X_trx_log),
        columns=X_transcriptomic.columns,
    )
    trx_lr = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=42,
    )
    res = run_permutation_test(
        trx_lr, X_trx_norm, y_series,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_transcriptomic_lr.png",
    )
    all_results["Transcriptomic · LogisticRegression"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 4 — Transcriptomic · RandomForest
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 4 — Transcriptomic  ·  RandomForestClassifier")
    print(DIVIDER)
    trx_rf = RandomForestClassifier(
        n_estimators=200, max_depth=6,
        class_weight="balanced", random_state=42,
    )
    res = run_permutation_test(
        trx_rf, X_trx_norm, y_series,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_transcriptomic_rf.png",
    )
    all_results["Transcriptomic · RandomForest"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 5 — Radiomic · RandomForest
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 5 — Radiomic  ·  RandomForestClassifier")
    print(DIVIDER)
    sys.path.insert(0, str(ROOT / "radiomic model"))
    from radiomic_classifier import generate_radiomic_dataset  # type: ignore

    RADIOMIC_FEATURES = [
        "Tumor_Size", "Tumor_Compactness", "Texture_Heterogeneity",
        "Edge_Sharpness", "Necrosis_Score", "Intensity_Variance",
    ]
    rad_df  = generate_radiomic_dataset(n_samples=200, random_state=42)
    X_radio = rad_df[RADIOMIC_FEATURES]
    y_radio = pd.Series(rad_df["Stage"].values, name="label")

    radiomic_rf = RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=42,
    )
    res = run_permutation_test(
        radiomic_rf, X_radio, y_radio,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_radiomic_rf.png",
    )
    all_results["Radiomic · RandomForest"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # MODEL 6 — Hybrid · Logistic Regression (L1, core-amplified)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  MODEL 6 — Hybrid (genomic + interaction terms)  ·  LR (L1)")
    print(DIVIDER)
    CORE_GENES = ["KRAS", "TP53", "SMAD4", "CDKN2A"]
    INTERACTION_PAIRS = [("KRAS", "TP53"), ("KRAS", "SMAD4"), ("TP53", "SMAD4")]
    CORE_AMP = 6.0

    X_hybrid = X_genomic.copy()
    # Amplify core genes
    for g in CORE_GENES:
        if g in X_hybrid.columns:
            X_hybrid[g] = X_hybrid[g] * CORE_AMP
    # Add interaction terms
    for g1, g2 in INTERACTION_PAIRS:
        if g1 in X_hybrid.columns and g2 in X_hybrid.columns:
            X_hybrid[f"{g1}_{g2}"] = X_hybrid[g1] * X_hybrid[g2]

    hybrid_lr = LogisticRegression(
        penalty="l1", solver="liblinear", C=0.5,
        class_weight="balanced", max_iter=1000, random_state=42,
    )
    res = run_permutation_test(
        hybrid_lr, X_hybrid, y_series,
        n_permutations=N_PERM,
        plot_path=ROOT / "perm_hybrid_lr.png",
    )
    all_results["Hybrid · LogisticRegression (L1)"] = res

    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{DIVIDER}")
    print("  PERMUTATION TEST SUMMARY — All Models")
    print(DIVIDER)
    print(f"  {'Model':<42} {'Real AUC':>9} {'Mean Perm':>10} {'p-value':>8}  Verdict")
    print(f"  {'─'*42}  {'─'*8}  {'─'*8}  {'─'*6}  {'─'*20}")
    for model_name, r in all_results.items():
        verdict = "✓ Significant" if r["p_value"] < 0.05 else "✗ Not significant"
        print(f"  {model_name:<42} {r['real_auc']:>9.4f} {r['mean_perm']:>10.4f} "
              f"{r['p_value']:>8.4f}  {verdict}")
    print(f"\n  Plots saved: perm_genomic_rf.png  perm_genomic_lr.png")
    print(f"               perm_transcriptomic_lr.png  perm_transcriptomic_rf.png")
    print(f"               perm_radiomic_rf.png  perm_hybrid_lr.png")
    print(DIVIDER + "\n")
