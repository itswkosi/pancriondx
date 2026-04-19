"""
SMAD4 Role Analysis in PDAC Classification
===========================================

Four modular analyses that together determine whether SMAD4 should be
kept, removed, or treated differently in the RandomForest model:

  1. analyze_distribution  – mutation frequency across classes
  2. analyze_correlation   – redundancy with other panel genes
  3. stratified_performance – AUC within SMAD4-positive vs negative patients
  4. compare_models        – full-feature vs SMAD4-dropped model comparison
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20
GENE = "SMAD4"

# ── Paths ────────────────────────────────────────────────────────────────────
DEFAULT_DATA_PATH = Path("mutation_matrix.csv")
DEFAULT_GENE_PANEL_PATH = Path("src/data/gene_panel.json")


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


def build_model(random_state: int = RANDOM_STATE) -> RandomForestClassifier:
    """Return an untrained RandomForestClassifier with fixed hyper-parameters."""
    return RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        class_weight="balanced",
    )


def _train_and_score(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = RANDOM_STATE,
) -> tuple[float, float]:
    """Split, train, and return (roc_auc, brier_score) on the test set."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=random_state, stratify=y
    )
    model = build_model(random_state)
    model.fit(X_tr, y_tr)
    y_prob = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, y_prob)
    brier = brier_score_loss(y_te, y_prob)
    return auc, brier


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — DISTRIBUTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_distribution(X: pd.DataFrame, y: pd.Series, gene: str = GENE) -> None:
    """
    Print overall mutation frequency and per-class breakdown for `gene`.

    Covers:
    - Raw value counts across the whole cohort
    - Mutation rate in early-stage (y==0) vs late-stage (y==1) patients
    """
    if gene not in X.columns:
        print(f"[skip] '{gene}' not found in feature matrix.")
        return

    col = X[gene]
    total = len(col)

    print(f"\n── Part 1: Distribution of {gene} ─────────────────────────────────")

    # Overall counts
    counts = col.value_counts().sort_index()
    print(f"\n  Overall value counts (n = {total}):")
    for val, cnt in counts.items():
        print(f"    {gene} = {val} : {cnt:>4}  ({cnt / total * 100:.1f}%)")

    # Per-class breakdown
    print(f"\n  Per-class mutation frequency:")
    for label, label_name in [(0, "early-stage (y=0)"), (1, "late-stage  (y=1)")]:
        mask = y == label
        n_class = int(mask.sum())
        n_mutated = int(col[mask].sum())
        freq = n_mutated / n_class if n_class > 0 else float("nan")
        print(
            f"    {label_name} — {n_mutated}/{n_class} mutated "
            f"({freq * 100:.1f}%)"
        )

    # Interpretation nudge
    early_mask = y == 0
    late_mask = y == 1
    early_rate = col[early_mask].mean()
    late_rate = col[late_mask].mean()
    diff = late_rate - early_rate
    print(f"\n  Δ mutation rate (late − early): {diff:+.3f}")
    if abs(diff) < 0.05:
        print("  → Mutation rate is similar across classes. SMAD4 may not be discriminative.")
    elif diff > 0:
        print("  → Higher rate in late-stage. SMAD4 may carry predictive signal.")
    else:
        print("  → Higher rate in early-stage. Unusual pattern; worth investigating.")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — CORRELATION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_correlation(X: pd.DataFrame, gene: str = GENE, top_n: int = 10) -> None:
    """
    Print Pearson correlations of `gene` with every other feature, sorted by
    absolute magnitude.

    High correlations with other drivers (e.g. TP53, CDKN2A) suggest
    redundancy, which would explain why removing SMAD4 does not hurt AUC.
    """
    if gene not in X.columns:
        print(f"[skip] '{gene}' not found in feature matrix.")
        return

    print(f"\n── Part 2: Correlation of {gene} with Other Genes ──────────────────")

    corr_series = X.corr()[gene].drop(labels=[gene])
    corr_sorted = corr_series.reindex(
        corr_series.abs().sort_values(ascending=False).index
    )

    print(f"\n  Top {min(top_n, len(corr_sorted))} correlates (by |r|):\n")
    print(f"  {'Gene':<12} {'r':>7}")
    print(f"  {'-'*12} {'-------':>7}")
    for gene_name, r in corr_sorted.head(top_n).items():
        bar = "█" * int(abs(r) * 20)
        print(f"  {gene_name:<12} {r:>+7.4f}  {bar}")

    # Redundancy check
    high_corr = corr_sorted[corr_sorted.abs() >= 0.30]
    if not high_corr.empty:
        partners = ", ".join(high_corr.index.tolist())
        print(f"\n  Genes with |r| ≥ 0.30: {partners}")
        print(f"  → {gene} may be partially redundant with these genes.")
    else:
        print(f"\n  No genes with |r| ≥ 0.30.")
        print(f"  → {gene} is not strongly correlated with other features.")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 — STRATIFIED PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

def stratified_performance(X: pd.DataFrame, y: pd.Series, gene: str = GENE) -> None:
    """
    Evaluate model performance separately on SMAD4-mutated and non-mutated patients.

    A large AUC gap between subgroups indicates the model behaves inconsistently
    depending on SMAD4 status.

    Note: subgroups with fewer than 20 samples or a single class are skipped.
    """
    if gene not in X.columns:
        print(f"[skip] '{gene}' not found in feature matrix.")
        return

    print(f"\n── Part 3: Stratified Performance by {gene} Status ─────────────────")

    features_without_gene = [c for c in X.columns if c != gene]

    for val, label in [(1, f"{gene} = 1 (mutated)"), (0, f"{gene} = 0 (non-mutated)")]:
        mask = X[gene] == val
        X_sub = X.loc[mask, features_without_gene]
        y_sub = y.loc[mask]

        n = len(y_sub)
        n_classes = y_sub.nunique()

        if n < 20:
            print(f"\n  {label}: only {n} samples — too few to evaluate reliably.")
            continue
        if n_classes < 2:
            print(f"\n  {label}: only one class present — AUC undefined.")
            continue

        # Attempt stratified split; fall back to non-stratified for tiny minorities
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_sub, y_sub,
                test_size=TEST_SIZE,
                random_state=RANDOM_STATE,
                stratify=y_sub,
            )
        except ValueError:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_sub, y_sub,
                test_size=TEST_SIZE,
                random_state=RANDOM_STATE,
            )

        if y_te.nunique() < 2:
            print(f"\n  {label}: test split contains only one class — AUC undefined.")
            continue

        model = build_model(RANDOM_STATE)
        model.fit(X_tr, y_tr)
        y_prob = model.predict_proba(X_te)[:, 1]
        auc = roc_auc_score(y_te, y_prob)

        print(f"\n  {label}")
        print(f"    Subgroup size : {n} samples")
        print(f"    Train / Test  : {len(X_tr)} / {len(X_te)}")
        print(f"    ROC-AUC       : {auc:.4f}")

    print()
    print("  Interpretation:")
    print("  A large AUC gap between subgroups suggests the model relies on")
    print(f"  {gene} status as an implicit stratifier rather than a true feature.")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4 — MODEL COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

def compare_models(X: pd.DataFrame, y: pd.Series, gene: str = GENE) -> None:
    """
    Head-to-head comparison of:
      Model A — all features (including SMAD4)
      Model B — SMAD4 column dropped

    Same train/test split for a fair comparison.
    Reports ROC-AUC and Brier score for both.
    """
    print(f"\n── Part 4: Model Comparison — With vs Without {gene} ───────────────")

    # Model A: full feature set
    auc_a, brier_a = _train_and_score(X, y)

    # Model B: drop the target gene
    if gene not in X.columns:
        print(f"  [skip] '{gene}' not in feature matrix — cannot compare.")
        return

    X_dropped = X.drop(columns=[gene])
    auc_b, brier_b = _train_and_score(X_dropped, y)

    # Table
    print(f"\n  {'Model':<20} {'AUC':>7} {'Brier':>8}")
    print(f"  {'-'*20} {'-------':>7} {'--------':>8}")
    print(f"  {'With ' + gene:<20} {auc_a:>7.4f} {brier_a:>8.4f}")
    print(f"  {'Without ' + gene:<20} {auc_b:>7.4f} {brier_b:>8.4f}")

    delta_auc = auc_b - auc_a
    delta_brier = brier_b - brier_a
    sign_auc = "+" if delta_auc >= 0 else ""
    sign_brier = "+" if delta_brier >= 0 else ""

    print(f"\n  ΔAUC  (without − with) : {sign_auc}{delta_auc:.4f}")
    print(f"  ΔBrier(without − with) : {sign_brier}{delta_brier:.4f}")

    print("\n  Recommendation:")
    if delta_auc > 0.01 and delta_brier <= 0.01:
        verdict = (
            f"  Removing {gene} improves AUC without worsening calibration.\n"
            f"  → {gene} is likely adding noise. Consider dropping it."
        )
    elif delta_auc > 0.01 and delta_brier > 0.01:
        verdict = (
            f"  Removing {gene} improves AUC but worsens calibration.\n"
            f"  → Trade-off. Investigate further before dropping."
        )
    elif abs(delta_auc) <= 0.01:
        verdict = (
            f"  Removing {gene} has negligible impact on AUC.\n"
            f"  → {gene} is likely redundant with other features."
        )
    else:
        verdict = (
            f"  Removing {gene} hurts AUC.\n"
            f"  → {gene} carries unique predictive signal. Keep it."
        )
    print(verdict)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Load data and run all four SMAD4 analyses."""
    print("═" * 65)
    print(f"  PDAC Classifier — {GENE} Role Analysis")
    print("═" * 65)

    X, y = load_data()
    print(f"\nDataset : {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Classes : 0 (early) = {int((y == 0).sum())}, 1 (late) = {int((y == 1).sum())}")
    print(f"Target  : {GENE}")

    analyze_distribution(X, y)
    analyze_correlation(X)
    stratified_performance(X, y)
    compare_models(X, y)

    print("\n" + "═" * 65)
    print("  Analysis complete.")
    print("═" * 65)


if __name__ == "__main__":
    main()
